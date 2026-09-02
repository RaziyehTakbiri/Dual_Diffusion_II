"""Exact, nonconfirmatory CP58 bounded-feature and SIR diagnostics.

The bounded-feature distance in this module is the finite IPM

    max[f in +/-F] (mean_A(f) - mean_B(f)),

where ``F`` is a fixture-locked finite registry.  Coordinates are canonical
built-in binary64 values, but every feature is evaluated exactly after
``Fraction.from_float``.  The registry uses saturating maps so denominator
growth is bounded: ``odd(z)=clip(z,-1,1)`` and
``even(z)=min(z*z,1)``.

The SIR records deliberately distinguish proposal *values*, local particle
slots, and ancestry.  A current kernel request makes one categorical
selection, hence has one selected local ancestor.  The separate T28-AESS
occupancy record is a conditional, hypothetical eight-draw calculation over
eight particle slots; it performs no draw and observes no production behavior.

This stdlib-only module does not import or replay a provider, kernel, reference
sampler, NumPy, SciPy, or an RNG.  It makes no source-law claim, no target-law
claim, and no IID, operational, confirmatory, or Formal-Test-28 closure claim.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from fractions import Fraction
import hashlib
import json
import math
from typing import Mapping, Tuple


CP58_TEST28_DIAGNOSTIC_SCHEMA_VERSION = "cp58-test28-bounded-feature-sir-diagnostics-v1"
CP58_TEST28_DIAGNOSTIC_SCOPE = (
    "fixture-locked-exact-finite-sign-closed-bounded-feature-ipm;"
    "canonical-binary64-to-exact-rational-coordinate-semantics;"
    "proposal-value-uniqueness-separated-from-local-particle-ancestry;"
    "one-selection-local-ancestor-contract;"
    "t28-aess-conditional-hypothetical-r8-slot-occupancy;"
    "no-rng-no-provider-no-kernel-replay-no-source-law-no-iid-no-target-law-"
    "no-operational-no-confirmatory-no-test28-closure"
)
CP58_TEST28_FORMAL_TEST_28_STATUS = "OPEN"
CP58_TEST28_MAX_SAMPLE_SIZE = 65_536
CP58_TEST28_MAX_PARTICLE_SLOTS = 512
CP58_TEST28_MAX_FEATURES = 33
CP58_TEST28_MAX_FRACTION_BITS = 8_192
CP58_TEST28_MAX_TEXT_BYTES = 512

_ZERO_SHA256 = "0" * 64
_M1 = "T28-M1-Q"
_M2 = "T28-M2-Q"
_AESS = "T28-AESS"
_CALIBRATION_TOKEN = object()


class _SealedRecord:
    __slots__ = ()

    def __init__(self, *args: object, **kwargs: object) -> None:
        del args, kwargs
        raise TypeError("CP58 records are module-created")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP58 records are not pickle objects")


def _seal(cls: type, values: Mapping[str, object]) -> object:
    if set(values) != {item.name for item in fields(cls)}:
        raise TypeError("sealed record field set differs")
    result = object.__new__(cls)
    for name, value in values.items():
        object.__setattr__(result, name, value)
    return result


def _text(value: object, name: str, maximum: int = CP58_TEST28_MAX_TEXT_BYTES) -> str:
    if type(value) is not str:
        raise TypeError(name + " must be exact text")
    if not value or len(value.encode("utf-8")) > maximum:
        raise ValueError(name + " must be bounded nonempty text")
    return value


def _integer(value: object, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int:
        raise TypeError(name + " must be an exact integer")
    if value < minimum or value > maximum:
        raise ValueError(name + " lies outside its frozen bound")
    return value


def _boolean(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise TypeError(name + " must be bool")
    return value


def _sha256(value: object, name: str) -> str:
    checked = _text(value, name, 64)
    if len(checked) != 64 or any(c not in "0123456789abcdef" for c in checked):
        raise ValueError(name + " must be lowercase SHA-256 text")
    return checked


def _tuple(value: object, name: str, minimum: int, maximum: int) -> tuple:
    if type(value) is not tuple:
        raise TypeError(name + " must be an exact tuple")
    if len(value) < minimum or len(value) > maximum:
        raise ValueError(name + " has an invalid bounded length")
    return value


def _fraction(value: object, name: str) -> Fraction:
    if type(value) is not Fraction:
        raise TypeError(name + " must be an exact Fraction")
    if max(value.numerator.bit_length(), value.denominator.bit_length()) > (
        CP58_TEST28_MAX_FRACTION_BITS
    ):
        raise ValueError(name + " exceeds the exact arithmetic bit bound")
    return value


def _checked_fraction(value: Fraction, name: str) -> Fraction:
    return _fraction(value, name)


def _add(left: Fraction, right: Fraction, name: str) -> Fraction:
    return _checked_fraction(left + right, name)


def _mul(left: Fraction, right: Fraction, name: str) -> Fraction:
    return _checked_fraction(left * right, name)


def _div(left: Fraction, right: int, name: str) -> Fraction:
    _integer(right, name + " denominator", 1, CP58_TEST28_MAX_SAMPLE_SIZE)
    return _checked_fraction(left / right, name)


def _canonical(value: object) -> object:
    if value is None or type(value) in (bool, int, str):
        return value
    if type(value) is Fraction:
        return {"denominator": value.denominator, "numerator": value.numerator}
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("canonical floats must be finite")
        if value == 0.0 and math.copysign(1.0, value) < 0.0:
            raise ValueError("canonical floats must use positive zero")
        return {"binary64_hex": value.hex()}
    if type(value) is tuple:
        return [_canonical(item) for item in value]
    if type(value) is dict:
        if not all(type(key) is str for key in value):
            raise TypeError("canonical mapping keys must be exact text")
        return {key: _canonical(value[key]) for key in sorted(value)}
    if isinstance(value, _SealedRecord):
        return {
            item.name: _canonical(getattr(value, item.name))
            for item in fields(type(value))
        }
    raise TypeError("unsupported CP58 canonical value")


def cp58_canonical_json_bytes(value: object) -> bytes:
    """Return the frozen canonical JSON encoding used by CP58 digests."""

    return json.dumps(
        _canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")


def _digest(domain: bytes, value: object) -> str:
    return hashlib.sha256(domain + cp58_canonical_json_bytes(value)).hexdigest()


@dataclass(frozen=True, eq=False, init=False, slots=True)
class FrozenProjectionV1(_SealedRecord):
    projection_id: str
    type_index: int
    coefficients: Tuple[Fraction, ...]
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("FrozenProjectionV1 cannot be subclassed")


@dataclass(frozen=True, eq=False, init=False, slots=True)
class BoundedFeatureDefinitionV1(_SealedRecord):
    feature_id: str
    family: str
    type_indices: Tuple[int, ...]
    projection_ids: Tuple[str, ...]
    formula_id: str
    normalization_denominator: int
    lower_bound: Fraction
    upper_bound: Fraction
    sign_closed: bool
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("BoundedFeatureDefinitionV1 cannot be subclassed")


@dataclass(frozen=True, eq=False, init=False, slots=True)
class BoundedFeatureRegistryV1(_SealedRecord):
    schema_version: str
    fixture_id: str
    count_cap: int
    event_dimensions: Tuple[int, ...]
    projections: Tuple[FrozenProjectionV1, ...]
    features: Tuple[BoundedFeatureDefinitionV1, ...]
    odd_transform_formula: str
    even_transform_formula: str
    coordinate_semantics: str
    ipm_formula: str
    witness_tie_rule: str
    finite_sign_closed_class: bool
    metric_is_finite_class_pseudometric: bool
    source_law_verified: bool
    target_law_verified: bool
    probability_law_equality_certified: bool
    continuous_total_variation_claim: bool
    sliced_wasserstein_registry: bool
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("BoundedFeatureRegistryV1 cannot be subclassed")


@dataclass(frozen=True, eq=False, init=False, slots=True)
class BoundedFeatureIPMResultV1(_SealedRecord):
    schema_version: str
    fixture_id: str
    registry_sha256: str
    sample_a_size: int
    sample_b_size: int
    sample_a_configurations: Tuple[tuple, ...]
    sample_b_configurations: Tuple[tuple, ...]
    sample_a_sha256: str
    sample_b_sha256: str
    feature_ids: Tuple[str, ...]
    sample_a_feature_means: Tuple[Fraction, ...]
    sample_b_feature_means: Tuple[Fraction, ...]
    signed_base_discrepancies: Tuple[Fraction, ...]
    absolute_base_discrepancies: Tuple[Fraction, ...]
    ipm: Fraction
    witness_feature_id: str
    witness_sign: int
    input_is_predeclared_calibration: bool
    input_sample_digest_provenance_verified: bool
    sampled_output_observed: bool
    source_laws_verified: bool
    target_comparison: bool
    finite_class_pseudometric_only: bool
    probability_law_equality_certified: bool
    finite_categorical_total_variation: bool
    sliced_wasserstein: bool
    confirmatory_evidence: bool
    formal_test_28_status: str
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("BoundedFeatureIPMResultV1 cannot be subclassed")


@dataclass(frozen=True, eq=False, init=False, slots=True)
class ProposalConfigurationUniquenessV1(_SealedRecord):
    schema_version: str
    fixture_id: str
    cloud_id: str
    particle_slot_count: int
    canonical_configurations_or_state_vectors: Tuple[tuple, ...]
    configuration_value_sha256s: Tuple[str, ...]
    distinct_value_sha256s: Tuple[str, ...]
    value_multiplicities: Tuple[int, ...]
    unique_configuration_value_count: int
    repeated_value_excess: int
    maximum_value_multiplicity: int
    configuration_value_uniqueness_is_ancestor_occupancy: bool
    particle_slots_remain_distinct_when_values_equal: bool
    supplied_configuration_values_only: bool
    production_behavior_observed: bool
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("ProposalConfigurationUniquenessV1 cannot be subclassed")


@dataclass(frozen=True, eq=False, init=False, slots=True)
class SameCloudAncestorOccupancyV1(_SealedRecord):
    schema_version: str
    scope_id: str
    cloud_id: str
    particle_slot_count: int
    selection_count: int
    selected_slot_indices: Tuple[int, ...]
    slot_multiplicities: Tuple[int, ...]
    unique_selected_ancestor_count: int
    duplicate_selection_count: int
    selected_unique_fraction: Fraction
    particle_slot_occupancy_fraction: Fraction
    maximum_slot_multiplicity: int
    all_supplied_cloud_labels_equal: bool
    physical_same_cloud_provenance_verified: bool
    cross_cloud_pooling_permitted: bool
    single_kernel_selection_contract: bool
    supplied_selection_positions_only: bool
    production_boundary_verified: bool
    production_behavior_observed: bool
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("SameCloudAncestorOccupancyV1 cannot be subclassed")


@dataclass(frozen=True, eq=False, init=False, slots=True)
class AESSExpectedAncestorOccupancyV1(_SealedRecord):
    schema_version: str
    fixture_id: str
    particle_slot_count: int
    diagnostic_resample_count: int
    exact_slot_weights: Tuple[Fraction, ...]
    slot_inclusion_probabilities: Tuple[Fraction, ...]
    conditional_expected_unique_particle_slot_occupancy: Fraction
    conditional_expected_particle_slot_occupancy_fraction: Fraction
    conditional_particle_slot_occupancy_variance: Fraction
    conditional_expected_duplicate_selections: Fraction
    conditional_expected_duplicate_selection_fraction: Fraction
    expectation_formula_id: str
    variance_formula_id: str
    equal_configuration_values_collapsed: bool
    particle_slots_not_configuration_values: bool
    extra_resampling_draws_executed: int
    analytic_report_only: bool
    production_behavior_observed: bool
    categorical_source_law_verified: bool
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("AESSExpectedAncestorOccupancyV1 cannot be subclassed")


@dataclass(frozen=True, eq=False, init=False, slots=True)
class CP58DiagnosticBundleV1(_SealedRecord):
    schema_version: str
    scope: str
    m1_registry: BoundedFeatureRegistryV1
    m2_registry: BoundedFeatureRegistryV1
    m1_calibration: BoundedFeatureIPMResultV1
    m2_calibration: BoundedFeatureIPMResultV1
    aess_proposal_value_uniqueness: ProposalConfigurationUniquenessV1
    one_selection_contract: SameCloudAncestorOccupancyV1
    aess_expected_occupancy: AESSExpectedAncestorOccupancyV1
    predeclared_calibration_inputs_only: bool
    operational_predictions: bool
    production_runner_evidence: bool
    confirmatory_evidence: bool
    manuscript_claim: bool
    formal_test_28_status: str
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP58DiagnosticBundleV1 cannot be subclassed")


def _projection(
    projection_id: str, type_index: int, coefficients: tuple
) -> FrozenProjectionV1:
    values = {
        "projection_id": projection_id,
        "type_index": type_index,
        "coefficients": coefficients,
        "record_sha256": _ZERO_SHA256,
    }
    values["record_sha256"] = _digest(b"cp58-projection-v1\x00", values)
    return _seal(FrozenProjectionV1, values)  # type: ignore[return-value]


def _feature(
    feature_id: str,
    family: str,
    type_indices: tuple,
    projection_ids: tuple,
    formula_id: str,
    denominator: int,
    lower: int,
) -> BoundedFeatureDefinitionV1:
    values = {
        "feature_id": feature_id,
        "family": family,
        "type_indices": type_indices,
        "projection_ids": projection_ids,
        "formula_id": formula_id,
        "normalization_denominator": denominator,
        "lower_bound": Fraction(lower, 1),
        "upper_bound": Fraction(1, 1),
        "sign_closed": True,
        "record_sha256": _ZERO_SHA256,
    }
    values["record_sha256"] = _digest(b"cp58-feature-v1\x00", values)
    return _seal(BoundedFeatureDefinitionV1, values)  # type: ignore[return-value]


def _registry_components(fixture_id: str) -> tuple:
    if fixture_id == _M1:
        cap, dimensions = 1, (0, 1)
        projections = (_projection("axis0", 1, (Fraction(1, 1),)),)
    elif fixture_id == _M2:
        cap, dimensions = 2, (1, 2)
        projections = (
            _projection("axis0", 0, (Fraction(1, 1),)),
            _projection("axis0", 1, (Fraction(1, 1), Fraction(0, 1))),
            _projection("axis1", 1, (Fraction(0, 1), Fraction(1, 1))),
            _projection("diag-plus-3-4", 1, (Fraction(3, 5), Fraction(4, 5))),
            _projection("diag-minus-3-4", 1, (Fraction(3, 5), Fraction(-4, 5))),
        )
    else:
        raise ValueError("fixture_id must be T28-M1-Q or T28-M2-Q")
    features = []
    for count in range(cap + 1):
        features.append(
            _feature(
                "count/eq/%d" % count,
                "count-one-hot",
                (),
                (),
                "indicator-count-equals-v1",
                1,
                0,
            )
        )
    for type_index in range(len(dimensions)):
        features.append(
            _feature(
                "type/%d/occupancy" % type_index,
                "type-occupancy",
                (type_index,),
                (),
                "type-count-divided-by-cap-v1",
                cap,
                0,
            )
        )
    for projection in projections:
        for parity in ("odd", "even"):
            features.append(
                _feature(
                    "coordinate/%d/%s/%s"
                    % (projection.type_index, projection.projection_id, parity),
                    "coordinate-" + parity,
                    (projection.type_index,),
                    (projection.projection_id,),
                    (
                        "sum-clipped-projection-divided-by-cap-v1"
                        if parity == "odd"
                        else "sum-saturated-square-projection-divided-by-cap-v1"
                    ),
                    cap,
                    -1 if parity == "odd" else 0,
                )
            )
    if cap >= 2:
        by_type = {
            index: tuple(p for p in projections if p.type_index == index)
            for index in range(len(dimensions))
        }
        pair_denominator = cap * (cap - 1) // 2
        for left_type in range(len(dimensions)):
            for right_type in range(left_type, len(dimensions)):
                features.append(
                    _feature(
                        "pair-type/%d/%d" % (left_type, right_type),
                        "pair-type-occupancy",
                        (left_type, right_type),
                        (),
                        "unordered-type-pair-count-divided-by-cap-choose-two-v1",
                        pair_denominator,
                        0,
                    )
                )
        for left_type in range(len(dimensions)):
            for right_type in range(left_type, len(dimensions)):
                for left_position, left_projection in enumerate(by_type[left_type]):
                    candidates = by_type[right_type]
                    for right_position, right_projection in enumerate(candidates):
                        if left_type == right_type and right_position < left_position:
                            continue
                        features.append(
                            _feature(
                                "pair-projection/%d/%s/%d/%s"
                                % (
                                    left_type,
                                    left_projection.projection_id,
                                    right_type,
                                    right_projection.projection_id,
                                ),
                                "pair-projected-product",
                                (left_type, right_type),
                                (
                                    left_projection.projection_id,
                                    right_projection.projection_id,
                                ),
                                (
                                    "unordered-distinct-event-odd-product-symmetrized-when-same-type-distinct-projections-divided-by-cap-choose-two-v1"
                                ),
                                pair_denominator,
                                -1,
                            )
                        )
    if len(features) > CP58_TEST28_MAX_FEATURES:
        raise AssertionError("frozen feature registry exceeds bound")
    return cap, dimensions, projections, tuple(features)


def cp58_feature_registry(fixture_id: object) -> BoundedFeatureRegistryV1:
    """Return the fixture-locked finite, sign-closed feature registry."""

    checked = _text(fixture_id, "fixture_id", 16)
    cap, dimensions, projections, features_ = _registry_components(checked)
    values = {
        "schema_version": CP58_TEST28_DIAGNOSTIC_SCHEMA_VERSION,
        "fixture_id": checked,
        "count_cap": cap,
        "event_dimensions": dimensions,
        "projections": projections,
        "features": features_,
        "odd_transform_formula": "odd_sat(z)=max(-1,min(1,z)) over exact Q",
        "even_transform_formula": "even_sat(z)=min(1,z*z) over exact Q",
        "coordinate_semantics": "finite canonical built-in binary64; reject negative zero; convert with Fraction.from_float before projection",
        "ipm_formula": "max over sign in {-1,+1} and frozen base feature f of sign*(mean_A(f)-mean_B(f))",
        "witness_tie_rule": "lexicographically-smallest base feature_id; sign follows discrepancy and is +1 when discrepancy is zero",
        "finite_sign_closed_class": True,
        "metric_is_finite_class_pseudometric": True,
        "source_law_verified": False,
        "target_law_verified": False,
        "probability_law_equality_certified": False,
        "continuous_total_variation_claim": False,
        "sliced_wasserstein_registry": False,
        "record_sha256": _ZERO_SHA256,
    }
    values["record_sha256"] = _digest(b"cp58-feature-registry-v1\x00", values)
    return validate_cp58_feature_registry(_seal(BoundedFeatureRegistryV1, values))


def _validate_projection(value: object) -> FrozenProjectionV1:
    if type(value) is not FrozenProjectionV1:
        raise TypeError("projection has wrong exact type")
    _text(value.projection_id, "projection_id", 64)
    _integer(value.type_index, "projection type_index", 0, 1)
    coefficients = _tuple(value.coefficients, "projection coefficients", 1, 2)
    for i, coefficient in enumerate(coefficients):
        _fraction(coefficient, "projection coefficient[%d]" % i)
    _sha256(value.record_sha256, "projection digest")
    payload = {
        item.name: getattr(value, item.name)
        for item in fields(type(value))
        if item.name != "record_sha256"
    }
    payload["record_sha256"] = _ZERO_SHA256
    if value.record_sha256 != _digest(b"cp58-projection-v1\x00", payload):
        raise ValueError("projection digest differs")
    return value


def _validate_feature(value: object) -> BoundedFeatureDefinitionV1:
    if type(value) is not BoundedFeatureDefinitionV1:
        raise TypeError("feature definition has wrong exact type")
    _text(value.feature_id, "feature_id", 160)
    _text(value.family, "feature family", 64)
    type_indices = _tuple(value.type_indices, "feature type_indices", 0, 2)
    for item in type_indices:
        _integer(item, "feature type index", 0, 1)
    projection_ids = _tuple(value.projection_ids, "feature projection_ids", 0, 2)
    for item in projection_ids:
        _text(item, "feature projection_id", 64)
    _text(value.formula_id, "feature formula_id", 256)
    _integer(value.normalization_denominator, "feature denominator", 1, 2)
    _fraction(value.lower_bound, "feature lower bound")
    _fraction(value.upper_bound, "feature upper bound")
    if value.lower_bound not in (Fraction(-1, 1), Fraction(0, 1)):
        raise ValueError("feature lower bound differs")
    if value.upper_bound != Fraction(1, 1) or value.sign_closed is not True:
        raise ValueError("feature bound or sign-closed flag differs")
    _sha256(value.record_sha256, "feature-definition digest")
    payload = {item.name: getattr(value, item.name) for item in fields(type(value))}
    payload["record_sha256"] = _ZERO_SHA256
    if value.record_sha256 != _digest(b"cp58-feature-v1\x00", payload):
        raise ValueError("feature-definition digest differs")
    return value


def validate_cp58_feature_registry(value: object) -> BoundedFeatureRegistryV1:
    if type(value) is not BoundedFeatureRegistryV1:
        raise TypeError("feature registry has wrong exact type")
    _text(value.schema_version, "registry schema_version", 80)
    _text(value.fixture_id, "registry fixture_id", 16)
    _integer(value.count_cap, "registry count_cap", 1, 2)
    dimensions_value = _tuple(value.event_dimensions, "registry event_dimensions", 2, 2)
    for dimension in dimensions_value:
        _integer(dimension, "registry event dimension", 0, 2)
    cap, dimensions, projections, features_ = _registry_components(value.fixture_id)
    projection_values = _tuple(
        value.projections,
        "registry projections",
        len(projections),
        len(projections),
    )
    feature_values = _tuple(
        value.features,
        "registry features",
        len(features_),
        len(features_),
    )
    if (
        value.schema_version != CP58_TEST28_DIAGNOSTIC_SCHEMA_VERSION
        or value.count_cap != cap
        or value.event_dimensions != dimensions
    ):
        raise ValueError("feature registry header differs")
    for projection in projection_values:
        _validate_projection(projection)
    for feature in feature_values:
        _validate_feature(feature)
    if cp58_canonical_json_bytes(value.projections) != cp58_canonical_json_bytes(
        projections
    ):
        raise ValueError("frozen projections differ")
    if cp58_canonical_json_bytes(value.features) != cp58_canonical_json_bytes(
        features_
    ):
        raise ValueError("frozen feature definitions differ")
    if (
        value.odd_transform_formula,
        value.even_transform_formula,
        value.coordinate_semantics,
        value.ipm_formula,
        value.witness_tie_rule,
    ) != (
        "odd_sat(z)=max(-1,min(1,z)) over exact Q",
        "even_sat(z)=min(1,z*z) over exact Q",
        "finite canonical built-in binary64; reject negative zero; convert with Fraction.from_float before projection",
        "max over sign in {-1,+1} and frozen base feature f of sign*(mean_A(f)-mean_B(f))",
        "lexicographically-smallest base feature_id; sign follows discrepancy and is +1 when discrepancy is zero",
    ):
        raise ValueError("feature registry semantics differ")
    if (
        value.finite_sign_closed_class is not True
        or value.metric_is_finite_class_pseudometric is not True
        or value.source_law_verified is not False
        or value.target_law_verified is not False
        or value.probability_law_equality_certified is not False
        or value.continuous_total_variation_claim is not False
        or value.sliced_wasserstein_registry is not False
    ):
        raise ValueError("feature registry semantics differ")
    _sha256(value.record_sha256, "feature registry digest")
    payload = {item.name: getattr(value, item.name) for item in fields(type(value))}
    payload["record_sha256"] = _ZERO_SHA256
    if value.record_sha256 != _digest(b"cp58-feature-registry-v1\x00", payload):
        raise ValueError("feature registry digest differs")
    return value


def _canonical_configuration(
    registry: BoundedFeatureRegistryV1, value: object
) -> tuple:
    events = _tuple(value, "configuration", 0, registry.count_cap)
    checked = []
    for event_index, raw_event in enumerate(events):
        event = _tuple(raw_event, "event[%d]" % event_index, 2, 2)
        type_index = _integer(
            event[0], "event type_index", 0, len(registry.event_dimensions) - 1
        )
        coordinates = _tuple(
            event[1],
            "event coordinates",
            registry.event_dimensions[type_index],
            registry.event_dimensions[type_index],
        )
        exact_coordinates = []
        for coordinate_index, coordinate in enumerate(coordinates):
            if type(coordinate) is not float:
                raise TypeError("coordinate must be exact built-in float")
            if not math.isfinite(coordinate):
                raise ValueError("coordinate must be finite")
            if coordinate == 0.0 and math.copysign(1.0, coordinate) < 0.0:
                raise ValueError("coordinate must use canonical positive zero")
            exact_coordinates.append(
                _checked_fraction(
                    Fraction.from_float(coordinate), "coordinate exact value"
                )
            )
        checked.append((type_index, tuple(exact_coordinates)))
    if tuple(checked) != tuple(sorted(checked)):
        raise ValueError("events must use canonical nondecreasing order")
    return tuple(checked)


def _retained_configuration(registry: BoundedFeatureRegistryV1, value: object) -> tuple:
    events = _tuple(value, "retained configuration", 0, registry.count_cap)
    checked = []
    for event_index, raw_event in enumerate(events):
        event = _tuple(raw_event, "retained event[%d]" % event_index, 2, 2)
        type_index = _integer(
            event[0],
            "retained event type_index",
            0,
            len(registry.event_dimensions) - 1,
        )
        coordinates = _tuple(
            event[1],
            "retained event coordinates",
            registry.event_dimensions[type_index],
            registry.event_dimensions[type_index],
        )
        exact_coordinates = []
        for coordinate in coordinates:
            exact = _fraction(coordinate, "retained exact coordinate")
            try:
                represented = float(exact)
            except OverflowError as error:
                raise ValueError(
                    "retained coordinate is not finite binary64"
                ) from error
            if (
                not math.isfinite(represented)
                or Fraction.from_float(represented) != exact
            ):
                raise ValueError("retained coordinate is not an exact binary64 value")
            exact_coordinates.append(exact)
        checked.append((type_index, tuple(exact_coordinates)))
    if tuple(checked) != tuple(sorted(checked)):
        raise ValueError("retained events must use canonical nondecreasing order")
    return tuple(checked)


def _projection_map(registry: BoundedFeatureRegistryV1) -> dict:
    return {(p.type_index, p.projection_id): p for p in registry.projections}


def _z(event: tuple, projection: FrozenProjectionV1) -> Fraction:
    total = Fraction(0, 1)
    for coefficient, coordinate in zip(projection.coefficients, event[1]):
        total = _add(
            total, _mul(coefficient, coordinate, "projection product"), "projection sum"
        )
    return total


def _odd(value: Fraction) -> Fraction:
    return max(Fraction(-1, 1), min(Fraction(1, 1), value))


def _even(value: Fraction) -> Fraction:
    if abs(value) >= 1:
        return Fraction(1, 1)
    return _mul(value, value, "saturated square")


def _feature_value(
    registry: BoundedFeatureRegistryV1,
    configuration: tuple,
    feature: BoundedFeatureDefinitionV1,
) -> Fraction:
    count = len(configuration)
    if feature.family == "count-one-hot":
        return Fraction(int(count == int(feature.feature_id.rsplit("/", 1)[1])), 1)
    if feature.family == "type-occupancy":
        total = sum(1 for event in configuration if event[0] == feature.type_indices[0])
        return Fraction(total, registry.count_cap)
    projections = _projection_map(registry)
    if feature.family in ("coordinate-odd", "coordinate-even"):
        type_index = feature.type_indices[0]
        projection = projections[(type_index, feature.projection_ids[0])]
        total = Fraction(0, 1)
        transform = _odd if feature.family == "coordinate-odd" else _even
        for event in configuration:
            if event[0] == type_index:
                total = _add(
                    total, transform(_z(event, projection)), "coordinate feature sum"
                )
        return _div(total, registry.count_cap, "coordinate feature normalization")
    left_type, right_type = feature.type_indices
    pairs = tuple(
        (configuration[i], configuration[j])
        for i in range(count)
        for j in range(i + 1, count)
    )
    denominator = registry.count_cap * (registry.count_cap - 1) // 2
    if feature.family == "pair-type-occupancy":
        total = sum(
            1 for left, right in pairs if (left[0], right[0]) == (left_type, right_type)
        )
        return Fraction(total, denominator)
    left_projection = projections[(left_type, feature.projection_ids[0])]
    right_projection = projections[(right_type, feature.projection_ids[1])]
    total = Fraction(0, 1)
    for left, right in pairs:
        if (left[0], right[0]) != (left_type, right_type):
            continue
        if (
            left_type == right_type
            and left_projection.projection_id != right_projection.projection_id
        ):
            direct = _mul(
                _odd(_z(left, left_projection)),
                _odd(_z(right, right_projection)),
                "pair direct",
            )
            reverse = _mul(
                _odd(_z(left, right_projection)),
                _odd(_z(right, left_projection)),
                "pair reverse",
            )
            value = _div(
                _add(direct, reverse, "pair symmetrized sum"),
                2,
                "pair symmetrization",
            )
        else:
            value = _mul(
                _odd(_z(left, left_projection)),
                _odd(_z(right, right_projection)),
                "pair product",
            )
        total = _add(total, value, "pair feature sum")
    return _div(total, denominator, "pair feature normalization")


def cp58_bounded_feature_vector(
    fixture_id: object, configuration: object
) -> Tuple[Fraction, ...]:
    """Evaluate every frozen base feature exactly on one configuration."""

    registry = cp58_feature_registry(fixture_id)
    checked = _canonical_configuration(registry, configuration)
    return tuple(
        _feature_value(registry, checked, feature) for feature in registry.features
    )


def _sample(registry: BoundedFeatureRegistryV1, value: object, name: str) -> tuple:
    raw = _tuple(value, name, 1, CP58_TEST28_MAX_SAMPLE_SIZE)
    return tuple(_canonical_configuration(registry, item) for item in raw)


def _retained_sample(
    registry: BoundedFeatureRegistryV1, value: object, name: str
) -> tuple:
    raw = _tuple(value, name, 1, CP58_TEST28_MAX_SAMPLE_SIZE)
    return tuple(_retained_configuration(registry, item) for item in raw)


def _sample_digest(fixture_id: str, sample: tuple) -> str:
    return _digest(
        b"cp58-feature-sample-v1\x00", {"fixture_id": fixture_id, "sample": sample}
    )


def _means(registry: BoundedFeatureRegistryV1, sample: tuple) -> tuple:
    totals = [Fraction(0, 1) for _ in registry.features]
    for configuration in sample:
        for index, feature in enumerate(registry.features):
            totals[index] = _add(
                totals[index],
                _feature_value(registry, configuration, feature),
                "sample feature sum",
            )
    return tuple(_div(value, len(sample), "sample feature mean") for value in totals)


def _build_bounded_feature_ipm(
    fixture_id: object,
    sample_a: object,
    sample_b: object,
    *,
    _calibration_token: object = None,
) -> BoundedFeatureIPMResultV1:
    registry = cp58_feature_registry(fixture_id)
    left = _sample(registry, sample_a, "sample_a")
    right = _sample(registry, sample_b, "sample_b")
    if _calibration_token not in (None, _CALIBRATION_TOKEN):
        raise TypeError("invalid private calibration construction token")
    calibration = _calibration_token is _CALIBRATION_TOKEN
    left_means, right_means = _means(registry, left), _means(registry, right)
    differences = tuple(
        _checked_fraction(a - b, "feature discrepancy")
        for a, b in zip(left_means, right_means)
    )
    absolute = tuple(abs(value) for value in differences)
    ipm = max(absolute)
    tied_ids = sorted(
        registry.features[i].feature_id
        for i, value in enumerate(absolute)
        if value == ipm
    )
    witness_id = tied_ids[0]
    witness_index = next(
        i
        for i, feature in enumerate(registry.features)
        if feature.feature_id == witness_id
    )
    witness_sign = 1 if differences[witness_index] >= 0 else -1
    values = {
        "schema_version": CP58_TEST28_DIAGNOSTIC_SCHEMA_VERSION,
        "fixture_id": registry.fixture_id,
        "registry_sha256": registry.record_sha256,
        "sample_a_size": len(left),
        "sample_b_size": len(right),
        "sample_a_configurations": left,
        "sample_b_configurations": right,
        "sample_a_sha256": _sample_digest(registry.fixture_id, left),
        "sample_b_sha256": _sample_digest(registry.fixture_id, right),
        "feature_ids": tuple(feature.feature_id for feature in registry.features),
        "sample_a_feature_means": left_means,
        "sample_b_feature_means": right_means,
        "signed_base_discrepancies": differences,
        "absolute_base_discrepancies": absolute,
        "ipm": ipm,
        "witness_feature_id": witness_id,
        "witness_sign": witness_sign,
        "input_is_predeclared_calibration": calibration,
        "input_sample_digest_provenance_verified": False,
        "sampled_output_observed": False,
        "source_laws_verified": False,
        "target_comparison": False,
        "finite_class_pseudometric_only": True,
        "probability_law_equality_certified": False,
        "finite_categorical_total_variation": False,
        "sliced_wasserstein": False,
        "confirmatory_evidence": False,
        "formal_test_28_status": CP58_TEST28_FORMAL_TEST_28_STATUS,
        "record_sha256": _ZERO_SHA256,
    }
    values["record_sha256"] = _digest(b"cp58-bounded-feature-ipm-v1\x00", values)
    return validate_cp58_bounded_feature_ipm(_seal(BoundedFeatureIPMResultV1, values))


def cp58_bounded_feature_ipm(
    fixture_id: object,
    sample_a: object,
    sample_b: object,
) -> BoundedFeatureIPMResultV1:
    """Compute an exact finite IPM from two supplied, unauthenticated samples."""

    return _build_bounded_feature_ipm(fixture_id, sample_a, sample_b)


def validate_cp58_bounded_feature_ipm(value: object) -> BoundedFeatureIPMResultV1:
    if type(value) is not BoundedFeatureIPMResultV1:
        raise TypeError("bounded-feature IPM has wrong exact type")
    _text(value.schema_version, "IPM schema_version", 80)
    _text(value.fixture_id, "IPM fixture_id", 16)
    registry = cp58_feature_registry(value.fixture_id)
    if (
        value.schema_version != CP58_TEST28_DIAGNOSTIC_SCHEMA_VERSION
        or value.registry_sha256 != registry.record_sha256
    ):
        raise ValueError("bounded-feature IPM header differs")
    _integer(value.sample_a_size, "sample_a_size", 1, CP58_TEST28_MAX_SAMPLE_SIZE)
    _integer(value.sample_b_size, "sample_b_size", 1, CP58_TEST28_MAX_SAMPLE_SIZE)
    _sha256(value.sample_a_sha256, "sample_a digest")
    _sha256(value.sample_b_sha256, "sample_b digest")
    retained_left = _retained_sample(
        registry, value.sample_a_configurations, "retained sample_a"
    )
    retained_right = _retained_sample(
        registry, value.sample_b_configurations, "retained sample_b"
    )
    if (
        len(retained_left) != value.sample_a_size
        or len(retained_right) != value.sample_b_size
    ):
        raise ValueError("retained IPM sample sizes differ")
    if value.sample_a_sha256 != _sample_digest(
        value.fixture_id, retained_left
    ) or value.sample_b_sha256 != _sample_digest(value.fixture_id, retained_right):
        raise ValueError("retained IPM sample digest differs")
    expected_ids = tuple(feature.feature_id for feature in registry.features)
    if value.feature_ids != expected_ids:
        raise ValueError("bounded-feature IDs differ")
    for vector_name in (
        "sample_a_feature_means",
        "sample_b_feature_means",
        "signed_base_discrepancies",
        "absolute_base_discrepancies",
    ):
        vector = _tuple(
            getattr(value, vector_name),
            vector_name,
            len(expected_ids),
            len(expected_ids),
        )
        for index, item in enumerate(vector):
            _fraction(item, "%s[%d]" % (vector_name, index))
    for index, feature in enumerate(registry.features):
        for vector_name in ("sample_a_feature_means", "sample_b_feature_means"):
            mean = getattr(value, vector_name)[index]
            if mean < feature.lower_bound or mean > feature.upper_bound:
                raise ValueError(vector_name + " lies outside its feature bound")
    if value.sample_a_feature_means != _means(
        registry, retained_left
    ) or value.sample_b_feature_means != _means(registry, retained_right):
        raise ValueError("retained IPM feature means differ")
    expected_differences = tuple(
        a - b
        for a, b in zip(value.sample_a_feature_means, value.sample_b_feature_means)
    )
    expected_absolute = tuple(abs(item) for item in expected_differences)
    expected_ipm = max(expected_absolute)
    witness_id = sorted(
        expected_ids[i]
        for i, item in enumerate(expected_absolute)
        if item == expected_ipm
    )[0]
    witness_index = expected_ids.index(witness_id)
    witness_sign = 1 if expected_differences[witness_index] >= 0 else -1
    _fraction(value.ipm, "IPM")
    _integer(value.witness_sign, "witness_sign", -1, 1)
    if value.witness_sign == 0:
        raise ValueError("witness_sign must be -1 or +1")
    if (
        any(item < 0 or item > 2 for item in expected_absolute)
        or value.ipm < 0
        or value.ipm > 2
    ):
        raise ValueError("bounded-feature discrepancy exceeds its analytic bound")
    if (
        value.signed_base_discrepancies != expected_differences
        or value.absolute_base_discrepancies != expected_absolute
        or value.ipm != expected_ipm
        or value.witness_feature_id != witness_id
        or value.witness_sign != witness_sign
    ):
        raise ValueError("bounded-feature IPM arithmetic differs")
    if (
        any(
            getattr(value, name) is not False
            for name in (
                "sampled_output_observed",
                "source_laws_verified",
                "target_comparison",
                "probability_law_equality_certified",
                "finite_categorical_total_variation",
                "sliced_wasserstein",
                "confirmatory_evidence",
            )
        )
        or value.finite_class_pseudometric_only is not True
        or value.formal_test_28_status != "OPEN"
    ):
        raise ValueError("bounded-feature IPM claim scope differs")
    _boolean(value.input_is_predeclared_calibration, "calibration flag")
    if value.input_sample_digest_provenance_verified is not False:
        raise ValueError("input sample digest provenance must remain unverified")
    if value.input_is_predeclared_calibration:
        m1a, m1b, m2a, m2b = _calibration_samples()
        expected_left, expected_right = (
            (m1a, m1b) if value.fixture_id == _M1 else (m2a, m2b)
        )
        canonical_left = _sample(registry, expected_left, "calibration sample_a")
        canonical_right = _sample(registry, expected_right, "calibration sample_b")
        if (
            value.sample_a_sha256 != _sample_digest(value.fixture_id, canonical_left)
            or value.sample_b_sha256
            != _sample_digest(value.fixture_id, canonical_right)
            or value.sample_a_feature_means != _means(registry, canonical_left)
            or value.sample_b_feature_means != _means(registry, canonical_right)
        ):
            raise ValueError("predeclared calibration inputs or vectors differ")
    _sha256(value.record_sha256, "bounded-feature IPM digest")
    payload = {item.name: getattr(value, item.name) for item in fields(type(value))}
    payload["record_sha256"] = _ZERO_SHA256
    if value.record_sha256 != _digest(b"cp58-bounded-feature-ipm-v1\x00", payload):
        raise ValueError("bounded-feature IPM digest differs")
    return value


def _aess_state_vectors() -> tuple:
    return ((0, 0), (1, 0), (0, 1), (2, 0), (1, 1), (0, 2), (0, 0), (1, 0))


def cp58_proposal_configuration_uniqueness(
    fixture_id: object, cloud_id: object, configurations: object
) -> ProposalConfigurationUniquenessV1:
    checked_fixture = _text(fixture_id, "fixture_id", 16)
    if checked_fixture not in (_M1, _M2, _AESS):
        raise ValueError("unsupported uniqueness fixture")
    registry = (
        cp58_feature_registry(checked_fixture)
        if checked_fixture in (_M1, _M2)
        else None
    )
    cloud = _text(cloud_id, "cloud_id", 128)
    raw = _tuple(configurations, "configurations", 1, CP58_TEST28_MAX_PARTICLE_SLOTS)
    if checked_fixture == _AESS:
        canonical_items = []
        for item in raw:
            vector = _tuple(item, "AESS state count vector", 2, 2)
            counts = tuple(
                _integer(component, "AESS state count", 0, 2) for component in vector
            )
            if sum(counts) > 2:
                raise ValueError("AESS state count vector exceeds cap two")
            canonical_items.append(counts)
        canonical = tuple(canonical_items)
        if canonical != _aess_state_vectors():
            raise ValueError("AESS proposal-value sequence differs from the fixture")
    else:
        canonical = tuple(_canonical_configuration(registry, item) for item in raw)  # type: ignore[arg-type]
    digests = tuple(
        _digest(
            b"cp58-proposal-configuration-value-v1\x00",
            {"fixture_id": checked_fixture, "configuration": item},
        )
        for item in canonical
    )
    distinct_values = tuple(dict.fromkeys(canonical))
    distinct = tuple(
        _digest(
            b"cp58-proposal-configuration-value-v1\x00",
            {"fixture_id": checked_fixture, "configuration": item},
        )
        for item in distinct_values
    )
    multiplicities = tuple(canonical.count(item) for item in distinct_values)
    values = {
        "schema_version": CP58_TEST28_DIAGNOSTIC_SCHEMA_VERSION,
        "fixture_id": checked_fixture,
        "cloud_id": cloud,
        "particle_slot_count": len(digests),
        "canonical_configurations_or_state_vectors": canonical,
        "configuration_value_sha256s": digests,
        "distinct_value_sha256s": distinct,
        "value_multiplicities": multiplicities,
        "unique_configuration_value_count": len(distinct),
        "repeated_value_excess": len(digests) - len(distinct),
        "maximum_value_multiplicity": max(multiplicities),
        "configuration_value_uniqueness_is_ancestor_occupancy": False,
        "particle_slots_remain_distinct_when_values_equal": True,
        "supplied_configuration_values_only": True,
        "production_behavior_observed": False,
        "record_sha256": _ZERO_SHA256,
    }
    values["record_sha256"] = _digest(
        b"cp58-proposal-configuration-uniqueness-v1\x00", values
    )
    return validate_cp58_proposal_configuration_uniqueness(
        _seal(ProposalConfigurationUniquenessV1, values)
    )


def validate_cp58_proposal_configuration_uniqueness(
    value: object,
) -> ProposalConfigurationUniquenessV1:
    if type(value) is not ProposalConfigurationUniquenessV1:
        raise TypeError("proposal uniqueness has wrong exact type")
    _text(value.schema_version, "proposal uniqueness schema_version", 80)
    _text(value.fixture_id, "proposal uniqueness fixture_id", 16)
    if (
        value.schema_version != CP58_TEST28_DIAGNOSTIC_SCHEMA_VERSION
        or value.fixture_id not in (_M1, _M2, _AESS)
    ):
        raise ValueError("proposal uniqueness header differs")
    count = _integer(
        value.particle_slot_count,
        "particle_slot_count",
        1,
        CP58_TEST28_MAX_PARTICLE_SLOTS,
    )
    if value.fixture_id == _AESS:
        canonical = tuple(
            tuple(
                _integer(item, "AESS retained state count", 0, 2)
                for item in _tuple(vector, "AESS retained state vector", 2, 2)
            )
            for vector in _tuple(
                value.canonical_configurations_or_state_vectors,
                "retained AESS state vectors",
                count,
                count,
            )
        )
        if canonical != _aess_state_vectors():
            raise ValueError("retained AESS state vectors differ")
    else:
        registry = cp58_feature_registry(value.fixture_id)
        canonical = _retained_sample(
            registry,
            value.canonical_configurations_or_state_vectors,
            "retained proposal configurations",
        )
    hashes = _tuple(
        value.configuration_value_sha256s, "configuration hashes", count, count
    )
    for item in hashes:
        _sha256(item, "configuration hash")
    expected_hashes = tuple(
        _digest(
            b"cp58-proposal-configuration-value-v1\x00",
            {"fixture_id": value.fixture_id, "configuration": item},
        )
        for item in canonical
    )
    if hashes != expected_hashes:
        raise ValueError("retained proposal configuration digests differ")
    distinct_values = tuple(dict.fromkeys(canonical))
    distinct = tuple(
        _digest(
            b"cp58-proposal-configuration-value-v1\x00",
            {"fixture_id": value.fixture_id, "configuration": item},
        )
        for item in distinct_values
    )
    multiplicities = tuple(canonical.count(item) for item in distinct_values)
    supplied_distinct = _tuple(
        value.distinct_value_sha256s,
        "distinct value hashes",
        len(distinct),
        len(distinct),
    )
    for item in supplied_distinct:
        _sha256(item, "distinct value hash")
    supplied_multiplicities = _tuple(
        value.value_multiplicities, "value multiplicities", len(distinct), len(distinct)
    )
    for item in supplied_multiplicities:
        _integer(item, "value multiplicity", 1, count)
    _integer(
        value.unique_configuration_value_count,
        "unique configuration value count",
        1,
        count,
    )
    _integer(value.repeated_value_excess, "repeated value excess", 0, count - 1)
    _integer(value.maximum_value_multiplicity, "maximum value multiplicity", 1, count)
    if (
        supplied_distinct != distinct
        or supplied_multiplicities != multiplicities
        or value.unique_configuration_value_count != len(distinct)
        or value.repeated_value_excess != count - len(distinct)
        or value.maximum_value_multiplicity != max(multiplicities)
    ):
        raise ValueError("proposal uniqueness arithmetic differs")
    if (
        value.configuration_value_uniqueness_is_ancestor_occupancy is not False
        or value.particle_slots_remain_distinct_when_values_equal is not True
        or value.supplied_configuration_values_only is not True
        or value.production_behavior_observed is not False
    ):
        raise ValueError("proposal uniqueness scope differs")
    _text(value.cloud_id, "cloud_id", 128)
    payload = {item.name: getattr(value, item.name) for item in fields(type(value))}
    payload["record_sha256"] = _ZERO_SHA256
    _sha256(value.record_sha256, "proposal uniqueness digest")
    if value.record_sha256 != _digest(
        b"cp58-proposal-configuration-uniqueness-v1\x00", payload
    ):
        raise ValueError("proposal uniqueness digest differs")
    return value


def cp58_same_cloud_ancestor_occupancy(
    observations: object, particle_slot_count: object
) -> SameCloudAncestorOccupancyV1:
    """Summarize explicit local slot selections, rejecting cross-cloud pooling."""
    slots = _integer(
        particle_slot_count, "particle_slot_count", 1, CP58_TEST28_MAX_PARTICLE_SLOTS
    )
    raw = _tuple(observations, "observations", 1, CP58_TEST28_MAX_SAMPLE_SIZE)
    checked = []
    for position, observation in enumerate(raw):
        pair = _tuple(observation, "observation[%d]" % position, 2, 2)
        checked.append(
            (
                _text(pair[0], "observation cloud_id", 128),
                _integer(pair[1], "selected slot index", 0, slots - 1),
            )
        )
    cloud_ids = tuple(item[0] for item in checked)
    if any(item != cloud_ids[0] for item in cloud_ids):
        raise ValueError("cross-cloud ancestor pooling is forbidden")
    indices = tuple(item[1] for item in checked)
    histogram = tuple(indices.count(index) for index in range(slots))
    unique = sum(value > 0 for value in histogram)
    count = len(indices)
    values = {
        "schema_version": CP58_TEST28_DIAGNOSTIC_SCHEMA_VERSION,
        "scope_id": "same-explicit-cloud-local-particle-slot-occupancy-v1",
        "cloud_id": cloud_ids[0],
        "particle_slot_count": slots,
        "selection_count": count,
        "selected_slot_indices": indices,
        "slot_multiplicities": histogram,
        "unique_selected_ancestor_count": unique,
        "duplicate_selection_count": count - unique,
        "selected_unique_fraction": Fraction(unique, count),
        "particle_slot_occupancy_fraction": Fraction(unique, slots),
        "maximum_slot_multiplicity": max(histogram),
        "all_supplied_cloud_labels_equal": True,
        "physical_same_cloud_provenance_verified": False,
        "cross_cloud_pooling_permitted": False,
        "single_kernel_selection_contract": count == 1,
        "supplied_selection_positions_only": True,
        "production_boundary_verified": False,
        "production_behavior_observed": False,
        "record_sha256": _ZERO_SHA256,
    }
    values["record_sha256"] = _digest(
        b"cp58-same-cloud-ancestor-occupancy-v1\x00", values
    )
    return validate_cp58_same_cloud_ancestor_occupancy(
        _seal(SameCloudAncestorOccupancyV1, values)
    )


def validate_cp58_same_cloud_ancestor_occupancy(
    value: object,
) -> SameCloudAncestorOccupancyV1:
    if type(value) is not SameCloudAncestorOccupancyV1:
        raise TypeError("ancestor occupancy has wrong exact type")
    _text(value.schema_version, "ancestor occupancy schema_version", 80)
    _text(value.scope_id, "ancestor occupancy scope_id", 80)
    slots = _integer(
        value.particle_slot_count,
        "particle_slot_count",
        1,
        CP58_TEST28_MAX_PARTICLE_SLOTS,
    )
    count = _integer(
        value.selection_count, "selection_count", 1, CP58_TEST28_MAX_SAMPLE_SIZE
    )
    indices = _tuple(value.selected_slot_indices, "selected indices", count, count)
    for item in indices:
        _integer(item, "selected index", 0, slots - 1)
    histogram = tuple(indices.count(i) for i in range(slots))
    unique = sum(x > 0 for x in histogram)
    supplied_histogram = _tuple(
        value.slot_multiplicities, "slot multiplicities", slots, slots
    )
    for item in supplied_histogram:
        _integer(item, "slot multiplicity", 0, count)
    _integer(
        value.unique_selected_ancestor_count,
        "unique selected ancestor count",
        1,
        min(count, slots),
    )
    _integer(value.duplicate_selection_count, "duplicate selection count", 0, count - 1)
    _integer(value.maximum_slot_multiplicity, "maximum slot multiplicity", 1, count)
    _fraction(value.selected_unique_fraction, "selected unique fraction")
    _fraction(
        value.particle_slot_occupancy_fraction, "particle slot occupancy fraction"
    )
    if (
        supplied_histogram != histogram
        or value.unique_selected_ancestor_count != unique
        or value.duplicate_selection_count != count - unique
        or value.selected_unique_fraction != Fraction(unique, count)
        or value.particle_slot_occupancy_fraction != Fraction(unique, slots)
        or value.maximum_slot_multiplicity != max(histogram)
    ):
        raise ValueError("ancestor occupancy arithmetic differs")
    if value.schema_version != CP58_TEST28_DIAGNOSTIC_SCHEMA_VERSION:
        raise ValueError("ancestor occupancy schema differs")
    if (
        value.scope_id != "same-explicit-cloud-local-particle-slot-occupancy-v1"
        or value.all_supplied_cloud_labels_equal is not True
        or value.physical_same_cloud_provenance_verified is not False
        or value.cross_cloud_pooling_permitted is not False
        or value.single_kernel_selection_contract is not (count == 1)
        or value.supplied_selection_positions_only is not True
        or value.production_boundary_verified is not False
        or value.production_behavior_observed is not False
    ):
        raise ValueError("ancestor occupancy scope differs")
    _text(value.cloud_id, "cloud_id", 128)
    payload = {item.name: getattr(value, item.name) for item in fields(type(value))}
    payload["record_sha256"] = _ZERO_SHA256
    _sha256(value.record_sha256, "ancestor occupancy digest")
    if value.record_sha256 != _digest(
        b"cp58-same-cloud-ancestor-occupancy-v1\x00", payload
    ):
        raise ValueError("ancestor occupancy digest differs")
    return value


def cp58_aess_expected_ancestor_occupancy() -> AESSExpectedAncestorOccupancyV1:
    """Return the fixture-locked, zero-draw T28-AESS conditional calculation."""
    weights = tuple(Fraction(value, 1031) for value in (1, 1, 1, 1, 1, 1024, 1, 1))
    draws = 8
    inclusion = tuple(
        Fraction(1, 1) - (Fraction(1, 1) - weight) ** draws for weight in weights
    )
    expectation = sum(inclusion, Fraction(0, 1))
    variance = sum((p * (1 - p) for p in inclusion), Fraction(0, 1))
    for i in range(len(weights)):
        for j in range(i + 1, len(weights)):
            variance += 2 * (
                (1 - weights[i] - weights[j]) ** draws
                - (1 - weights[i]) ** draws * (1 - weights[j]) ** draws
            )
    values = {
        "schema_version": CP58_TEST28_DIAGNOSTIC_SCHEMA_VERSION,
        "fixture_id": _AESS,
        "particle_slot_count": 8,
        "diagnostic_resample_count": 8,
        "exact_slot_weights": weights,
        "slot_inclusion_probabilities": inclusion,
        "conditional_expected_unique_particle_slot_occupancy": expectation,
        "conditional_expected_particle_slot_occupancy_fraction": expectation / 8,
        "conditional_particle_slot_occupancy_variance": variance,
        "conditional_expected_duplicate_selections": Fraction(draws, 1) - expectation,
        "conditional_expected_duplicate_selection_fraction": Fraction(1, 1)
        - expectation / draws,
        "expectation_formula_id": "sum_i(1-(1-w_i)^R)-over-local-particle-slots-v1",
        "variance_formula_id": "sum_i(a_i*(1-a_i))+2*sum_i_lt_j((1-w_i-w_j)^R-(1-w_i)^R*(1-w_j)^R)-v1",
        "equal_configuration_values_collapsed": False,
        "particle_slots_not_configuration_values": True,
        "extra_resampling_draws_executed": 0,
        "analytic_report_only": True,
        "production_behavior_observed": False,
        "categorical_source_law_verified": False,
        "record_sha256": _ZERO_SHA256,
    }
    values["record_sha256"] = _digest(
        b"cp58-aess-expected-ancestor-occupancy-v1\x00", values
    )
    return validate_cp58_aess_expected_ancestor_occupancy(
        _seal(AESSExpectedAncestorOccupancyV1, values)
    )


def validate_cp58_aess_expected_ancestor_occupancy(
    value: object,
) -> AESSExpectedAncestorOccupancyV1:
    if type(value) is not AESSExpectedAncestorOccupancyV1:
        raise TypeError("AESS occupancy has wrong exact type")
    _text(value.schema_version, "AESS occupancy schema_version", 80)
    _text(value.fixture_id, "AESS occupancy fixture_id", 16)
    weights = tuple(Fraction(x, 1031) for x in (1, 1, 1, 1, 1, 1024, 1, 1))
    inclusion = tuple(1 - (1 - w) ** 8 for w in weights)
    expectation = sum(inclusion, Fraction(0, 1))
    variance = sum((p * (1 - p) for p in inclusion), Fraction(0, 1))
    for i in range(8):
        for j in range(i + 1, 8):
            variance += 2 * (
                (1 - weights[i] - weights[j]) ** 8
                - (1 - weights[i]) ** 8 * (1 - weights[j]) ** 8
            )
    supplied_weights = _tuple(value.exact_slot_weights, "AESS exact slot weights", 8, 8)
    supplied_inclusion = _tuple(
        value.slot_inclusion_probabilities, "AESS slot inclusion probabilities", 8, 8
    )
    for index, weight in enumerate(supplied_weights):
        _fraction(weight, "AESS slot weight[%d]" % index)
    for index, probability in enumerate(supplied_inclusion):
        _fraction(probability, "AESS inclusion probability[%d]" % index)
    for name in (
        "conditional_expected_unique_particle_slot_occupancy",
        "conditional_expected_particle_slot_occupancy_fraction",
        "conditional_particle_slot_occupancy_variance",
        "conditional_expected_duplicate_selections",
        "conditional_expected_duplicate_selection_fraction",
    ):
        _fraction(getattr(value, name), "AESS " + name)
    if (
        value.schema_version != CP58_TEST28_DIAGNOSTIC_SCHEMA_VERSION
        or value.fixture_id != _AESS
        or type(value.particle_slot_count) is not int
        or value.particle_slot_count != 8
        or type(value.diagnostic_resample_count) is not int
        or value.diagnostic_resample_count != 8
        or type(value.exact_slot_weights) is not tuple
        or value.exact_slot_weights != weights
        or type(value.slot_inclusion_probabilities) is not tuple
        or value.slot_inclusion_probabilities != inclusion
        or value.conditional_expected_unique_particle_slot_occupancy != expectation
        or value.conditional_expected_particle_slot_occupancy_fraction
        != expectation / 8
        or value.conditional_particle_slot_occupancy_variance != variance
        or value.conditional_expected_duplicate_selections
        != Fraction(8, 1) - expectation
        or value.conditional_expected_duplicate_selection_fraction
        != Fraction(1, 1) - expectation / 8
    ):
        raise ValueError("AESS occupancy arithmetic differs")
    if (
        value.expectation_formula_id
        != "sum_i(1-(1-w_i)^R)-over-local-particle-slots-v1"
        or value.variance_formula_id
        != "sum_i(a_i*(1-a_i))+2*sum_i_lt_j((1-w_i-w_j)^R-(1-w_i)^R*(1-w_j)^R)-v1"
    ):
        raise ValueError("AESS occupancy formula identifier differs")
    if (
        value.equal_configuration_values_collapsed is not False
        or value.particle_slots_not_configuration_values is not True
        or type(value.extra_resampling_draws_executed) is not int
        or value.extra_resampling_draws_executed != 0
        or value.analytic_report_only is not True
        or value.production_behavior_observed is not False
        or value.categorical_source_law_verified is not False
    ):
        raise ValueError("AESS occupancy scope differs")
    payload = {item.name: getattr(value, item.name) for item in fields(type(value))}
    payload["record_sha256"] = _ZERO_SHA256
    _sha256(value.record_sha256, "AESS occupancy digest")
    if value.record_sha256 != _digest(
        b"cp58-aess-expected-ancestor-occupancy-v1\x00", payload
    ):
        raise ValueError("AESS occupancy digest differs")
    return value


def _calibration_samples() -> tuple:
    m1a = ((), ((0, ()),), ((1, (1.0,)),), ((1, (-1.0,)),))
    m1b = ((), ((0, ()),), ((1, (0.0,)),), ((1, (0.0,)),))
    m2a = ((), ((0, (0.5,)),), ((1, (0.0, 0.5)),), ((0, (-0.5,)), (1, (0.5, -0.5))))
    m2b = ((), ((0, (0.0,)),), ((1, (0.5, 0.0)),), ((1, (-0.5, 0.5)), (1, (0.5, 0.5))))
    return m1a, m1b, m2a, m2b


def _calibration_ipm(fixture_id: str) -> BoundedFeatureIPMResultV1:
    m1a, m1b, m2a, m2b = _calibration_samples()
    left, right = (m1a, m1b) if fixture_id == _M1 else (m2a, m2b)
    return _build_bounded_feature_ipm(
        fixture_id, left, right, _calibration_token=_CALIBRATION_TOKEN
    )


def cp58_diagnostic_bundle() -> CP58DiagnosticBundleV1:
    m1 = _calibration_ipm(_M1)
    m2 = _calibration_ipm(_M2)
    uniqueness = cp58_proposal_configuration_uniqueness(
        _AESS, "T28-AESS-predeclared-j8-cloud", _aess_state_vectors()
    )
    one = cp58_same_cloud_ancestor_occupancy(
        (("one-kernel-request-local-cloud", 0),), 8
    )
    values = {
        "schema_version": CP58_TEST28_DIAGNOSTIC_SCHEMA_VERSION,
        "scope": CP58_TEST28_DIAGNOSTIC_SCOPE,
        "m1_registry": cp58_feature_registry(_M1),
        "m2_registry": cp58_feature_registry(_M2),
        "m1_calibration": m1,
        "m2_calibration": m2,
        "aess_proposal_value_uniqueness": uniqueness,
        "one_selection_contract": one,
        "aess_expected_occupancy": cp58_aess_expected_ancestor_occupancy(),
        "predeclared_calibration_inputs_only": True,
        "operational_predictions": False,
        "production_runner_evidence": False,
        "confirmatory_evidence": False,
        "manuscript_claim": False,
        "formal_test_28_status": "OPEN",
        "record_sha256": _ZERO_SHA256,
    }
    values["record_sha256"] = _digest(b"cp58-diagnostic-bundle-v1\x00", values)
    return validate_cp58_diagnostic_bundle(_seal(CP58DiagnosticBundleV1, values))


def validate_cp58_diagnostic_bundle(value: object) -> CP58DiagnosticBundleV1:
    if type(value) is not CP58DiagnosticBundleV1:
        raise TypeError("CP58 bundle has wrong exact type")
    _text(value.schema_version, "CP58 bundle schema_version", 80)
    _text(value.scope, "CP58 bundle scope", 1024)
    validate_cp58_feature_registry(value.m1_registry)
    validate_cp58_feature_registry(value.m2_registry)
    validate_cp58_bounded_feature_ipm(value.m1_calibration)
    validate_cp58_bounded_feature_ipm(value.m2_calibration)
    validate_cp58_proposal_configuration_uniqueness(
        value.aess_proposal_value_uniqueness
    )
    validate_cp58_same_cloud_ancestor_occupancy(value.one_selection_contract)
    validate_cp58_aess_expected_ancestor_occupancy(value.aess_expected_occupancy)
    expected_m1_registry = cp58_feature_registry(_M1)
    expected_m2_registry = cp58_feature_registry(_M2)
    expected_m1 = _calibration_ipm(_M1)
    expected_m2 = _calibration_ipm(_M2)
    expected_uniqueness = cp58_proposal_configuration_uniqueness(
        _AESS, "T28-AESS-predeclared-j8-cloud", _aess_state_vectors()
    )
    expected_one = cp58_same_cloud_ancestor_occupancy(
        (("one-kernel-request-local-cloud", 0),), 8
    )
    expected_aess = cp58_aess_expected_ancestor_occupancy()
    if (
        value.schema_version != CP58_TEST28_DIAGNOSTIC_SCHEMA_VERSION
        or value.scope != CP58_TEST28_DIAGNOSTIC_SCOPE
    ):
        raise ValueError("CP58 bundle header differs")
    for supplied, expected, name in (
        (value.m1_registry, expected_m1_registry, "M1 registry"),
        (value.m2_registry, expected_m2_registry, "M2 registry"),
        (value.m1_calibration, expected_m1, "M1 calibration"),
        (value.m2_calibration, expected_m2, "M2 calibration"),
        (
            value.aess_proposal_value_uniqueness,
            expected_uniqueness,
            "AESS value uniqueness",
        ),
        (value.one_selection_contract, expected_one, "one-selection contract"),
        (value.aess_expected_occupancy, expected_aess, "AESS expected occupancy"),
    ):
        if (
            supplied.record_sha256 != expected.record_sha256
            or cp58_canonical_json_bytes(supplied)
            != cp58_canonical_json_bytes(expected)
        ):
            raise ValueError("CP58 bundle " + name + " differs")
    if (
        value.m1_calibration.input_is_predeclared_calibration is not True
        or value.m2_calibration.input_is_predeclared_calibration is not True
    ):
        raise ValueError("CP58 calibration authority differs")
    if (
        value.predeclared_calibration_inputs_only is not True
        or any(
            getattr(value, name) is not False
            for name in (
                "operational_predictions",
                "production_runner_evidence",
                "confirmatory_evidence",
                "manuscript_claim",
            )
        )
        or value.formal_test_28_status != "OPEN"
    ):
        raise ValueError("CP58 bundle claim scope differs")
    payload = {item.name: getattr(value, item.name) for item in fields(type(value))}
    payload["record_sha256"] = _ZERO_SHA256
    _sha256(value.record_sha256, "CP58 bundle digest")
    if value.record_sha256 != _digest(b"cp58-diagnostic-bundle-v1\x00", payload):
        raise ValueError("CP58 bundle digest differs")
    return value


__all__ = [
    "CP58_TEST28_DIAGNOSTIC_SCHEMA_VERSION",
    "CP58_TEST28_DIAGNOSTIC_SCOPE",
    "CP58_TEST28_FORMAL_TEST_28_STATUS",
    "CP58_TEST28_MAX_SAMPLE_SIZE",
    "CP58_TEST28_MAX_PARTICLE_SLOTS",
    "CP58_TEST28_MAX_FEATURES",
    "CP58_TEST28_MAX_FRACTION_BITS",
    "FrozenProjectionV1",
    "BoundedFeatureDefinitionV1",
    "BoundedFeatureRegistryV1",
    "BoundedFeatureIPMResultV1",
    "ProposalConfigurationUniquenessV1",
    "SameCloudAncestorOccupancyV1",
    "AESSExpectedAncestorOccupancyV1",
    "CP58DiagnosticBundleV1",
    "cp58_canonical_json_bytes",
    "cp58_feature_registry",
    "validate_cp58_feature_registry",
    "cp58_bounded_feature_vector",
    "cp58_bounded_feature_ipm",
    "validate_cp58_bounded_feature_ipm",
    "cp58_proposal_configuration_uniqueness",
    "validate_cp58_proposal_configuration_uniqueness",
    "cp58_same_cloud_ancestor_occupancy",
    "validate_cp58_same_cloud_ancestor_occupancy",
    "cp58_aess_expected_ancestor_occupancy",
    "validate_cp58_aess_expected_ancestor_occupancy",
    "cp58_diagnostic_bundle",
    "validate_cp58_diagnostic_bundle",
]
