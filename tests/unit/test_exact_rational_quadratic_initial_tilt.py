"""Independent hostile tests for the exact rational quadratic score backend."""

from fractions import Fraction
import ast
import math
from pathlib import Path
import pickle
import struct
from types import MappingProxyType

import pytest

from heterodiff.evaluation import exact_rational_quadratic_initial_tilt as backend
from heterodiff.evaluation import mixed_initializer_test28_oracle as oracle
from heterodiff.theory.configuration_reference import (
    CappedPoissonConfigurationReference,
    TransformedEvent,
)


SOURCE = Path(backend.__file__)
ZERO = Fraction(0, 1)
IDEAL_WEIGHTS = (Fraction(2, 5), Fraction(3, 5))
OPERATIONAL_WEIGHTS = (
    Fraction(3_602_879_701_896_397, 9_007_199_254_740_992),
    Fraction(5_404_319_552_844_595, 9_007_199_254_740_992),
)
OPERATIONAL_WEIGHT_HEXES = (
    "0x1.999999999999ap-2",
    "0x1.3333333333333p-1",
)
CONTEXT_SHA256 = "363bbe2b925643a5b48c0e138b2299b2fbe9a6e1ae023843e69e59ce062c13aa"


@pytest.fixture(scope="module")
def m1():
    return backend.build_t28_m1_q_exact_score_provider()


@pytest.fixture(scope="module")
def m2():
    return backend.build_t28_m2_q_exact_score_provider()


def _forge(record, **updates):
    forged = object.__new__(type(record))
    for name in type(record).__annotations__:
        object.__setattr__(forged, name, updates.get(name, getattr(record, name)))
    return forged


def _redigest_evaluation(record):
    object.__setattr__(
        record,
        "evaluation_sha256",
        backend._semantic_digest(
            backend._evaluation_payload(record),
            domain="exact-rational-quadratic-evaluation-v1",
        ),
    )
    return record


def _redigest_certificate(record):
    object.__setattr__(
        record,
        "certificate_sha256",
        backend._semantic_digest(
            backend._certificate_payload(record),
            domain="exact-rational-quadratic-certificate-v1",
        ),
    )
    return record


def _fully_redigested_mutated_reference_certificate(certificate):
    reference = certificate.reference
    type_ids = tuple(reference.type_ids)
    type_dimensions = tuple(reference.type_dimensions[t] for t in type_ids)
    reference_parameter_key = reference.parameter_key()
    forged = _forge(
        certificate,
        reference_parameter_key=reference_parameter_key,
        reference_parameter_sha256=backend._semantic_digest(
            {"parameter_key": reference_parameter_key},
            domain="exact-rational-quadratic-reference-v1",
        ),
        type_ids=type_ids,
        type_dimensions=type_dimensions,
        total_cap=reference.total_cap,
        fixture_spec_sha256=backend._fixture_spec_sha256(
            fixture_id=certificate.fixture_id,
            ideal_activity=certificate.ideal_activity,
            ideal_type_weights=certificate.ideal_type_weights,
            type_ids=type_ids,
            type_dimensions=type_dimensions,
            total_cap=reference.total_cap,
            count_penalties=certificate.count_penalties,
            quadratic_coefficients=certificate.quadratic_coefficients,
        ),
        qbar_schema_sha256=backend._semantic_digest(
            {
                "ideal_real_formula": certificate.ideal_real_formula,
                "type_ids": type_ids,
                "type_dimensions": type_dimensions,
                "count_penalties": certificate.count_penalties,
                "quadratic_coefficients": certificate.quadratic_coefficients,
            },
            domain="exact-rational-quadratic-qbar-schema-v1",
        ),
        restriction_bridge_sha256=backend._semantic_digest(
            {
                "ideal_real_formula": certificate.ideal_real_formula,
                "represented_formula": certificate.formula,
                "type_ids": type_ids,
                "type_dimensions": type_dimensions,
                "count_penalties": certificate.count_penalties,
                "quadratic_coefficients": certificate.quadratic_coefficients,
                "restriction_domain": "canonical-built-in-binary64-coordinates",
            },
            domain="exact-rational-quadratic-restriction-bridge-v1",
        ),
    )
    return _redigest_certificate(forged)


def _manual_m1_score(configuration):
    assert len(configuration) <= 1
    if not configuration or configuration[0].event_type == 0:
        return ZERO
    coordinate = Fraction.from_float(configuration[0].coordinates[0])
    return -(coordinate * coordinate) / 4


def _manual_m2_score(configuration):
    score = Fraction(-1, 4) if len(configuration) == 2 else ZERO
    coefficients = {
        0: (Fraction(1, 4),),
        1: (Fraction(1, 8), Fraction(1, 6)),
    }
    for event in configuration:
        for coefficient, coordinate in zip(
            coefficients[event.event_type], event.coordinates
        ):
            represented = Fraction.from_float(coordinate)
            score -= coefficient * represented * represented
    return score


def _oracle_m2_score(configuration):
    return oracle.m2_exact_rational_score(
        tuple(event.event_type for event in configuration),
        tuple(event.coordinates for event in configuration),
    ).exact_rational_score


def _forged_event(event_type, coordinates):
    event = object.__new__(TransformedEvent)
    object.__setattr__(event, "event_type", event_type)
    object.__setattr__(event, "coordinates", coordinates)
    return event


def test_public_surface_and_source_dependency_separation_are_frozen():
    expected_exports = {
        "EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_IDEAL_REAL_FORMULA",
        "EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_REPRESENTED_FORMULA",
        "ExactRationalQuadraticInitialTilt",
        "ExactRationalQuadraticInitialTiltCertificate",
        "ExactRationalQuadraticInitialTiltPointEvaluation",
        "build_t28_m1_q_exact_score_provider",
        "build_t28_m2_q_exact_score_provider",
        "certify_exact_rational_quadratic_initial_tilt",
        "require_matching_exact_rational_quadratic_initial_tilt",
        "validate_exact_rational_quadratic_initial_tilt_certificate",
    }
    assert expected_exports <= set(backend.__all__)
    assert backend.EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_LAW_LAYERS == (
        "ideal_rational_analytic_law",
        "binary64_parameter_analytic_law",
        "represented_exact_score_law",
        "operational_runtime_proposal_law",
        "learned_model_separation",
    )

    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.add(node.module)
    forbidden = (
        "mixed_initializer_test28_oracle",
        "plugin_bridge_mixed_support_initial_tilt_initializer_kernel",
        "configuration_initial_tilt_composer_torch",
        "torch",
        "tests",
    )
    assert not any(fragment in module for fragment in forbidden for module in imported)


@pytest.mark.parametrize(
    (
        "builder,fixture_id,type_dimensions,total_cap,spec_sha,qbar_sha,"
        "bridge_sha,certificate_sha"
    ),
    [
        (
            backend.build_t28_m1_q_exact_score_provider,
            "T28-M1-Q",
            (0, 1),
            1,
            "47f869afc6541fd56e59d6e363fc397df2191e346a0e9afcb60b15b10581786d",
            "701e9341bf77ae69d01a7e980dcd700e9786221f09f959e99033b3aa4178b6df",
            "81c0315b641802bcd7d96d4c6fcebc6b11b277c4ab95849af1f2f29ddb434952",
            "3b29d26b3f50d63e6a52ca5033264e2346d7b4175342ac86c20254b98b745cc3",
        ),
        (
            backend.build_t28_m2_q_exact_score_provider,
            "T28-M2-Q",
            (1, 2),
            2,
            "56a3443914e612b523c631836dcb4da46700283537b0897923654607c82d68c4",
            "2a84f00a79b1bf907bc5bdcc12f1a6d4c70c7f9cae7817fed508705af7b89420",
            "46f15204329fe16ae181663549ac0f88453e0b2ec3c740247fcdf34895562ec4",
            "d6f6b25794d3e1759f5a169a9a3c55e94af37d498117cce6dcb0644342edb8de",
        ),
    ],
)
def test_builders_bind_exact_reference_activity_cap_types_dimensions_and_specs(
    builder,
    fixture_id,
    type_dimensions,
    total_cap,
    spec_sha,
    qbar_sha,
    bridge_sha,
    certificate_sha,
):
    provider = builder()
    certificate = provider.certificate
    reference = provider.reference

    assert type(provider) is backend.ExactRationalQuadraticInitialTilt
    assert type(certificate) is backend.ExactRationalQuadraticInitialTiltCertificate
    assert type(reference) is CappedPoissonConfigurationReference
    assert certificate.reference is reference
    assert certificate.fixture_id == fixture_id
    assert certificate.type_ids == (0, 1) == reference.type_ids
    assert certificate.type_dimensions == type_dimensions
    assert tuple(reference.type_dimensions[t] for t in reference.type_ids) == (
        type_dimensions
    )
    assert certificate.total_cap == total_cap == reference.total_cap
    assert certificate.ideal_activity == Fraction(1, 1)
    assert certificate.binary64_parameter_activity == Fraction(1, 1)
    assert reference.activity.hex() == "0x1.0000000000000p+0"
    assert certificate.fixture_spec_sha256 == spec_sha
    assert certificate.qbar_schema_sha256 == qbar_sha
    assert certificate.restriction_bridge_sha256 == bridge_sha
    assert certificate.certificate_sha256 == certificate_sha
    assert certificate.certificate_digest_excludes_runtime_identity is True
    assert certificate.formula == (
        backend.EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_REPRESENTED_FORMULA
    )
    assert certificate.ideal_real_formula == (
        backend.EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_IDEAL_REAL_FORMULA
    )
    assert certificate.formula != certificate.ideal_real_formula
    assert (
        backend.require_matching_exact_rational_quadratic_initial_tilt(
            reference, provider
        )
        is provider
    )
    assert (
        backend.validate_exact_rational_quadratic_initial_tilt_certificate(
            reference, provider
        )
        is certificate
    )


@pytest.mark.parametrize("fixture", ("m1", "m2"))
def test_ideal_rational_and_operational_binary64_reference_layers_never_collapse(
    fixture, request
):
    provider = request.getfixturevalue(fixture)
    certificate = provider.certificate
    reference = provider.reference

    assert certificate.ideal_type_weights == IDEAL_WEIGHTS
    assert certificate.binary64_parameter_type_weights == OPERATIONAL_WEIGHTS
    assert certificate.binary64_parameter_type_weight_hexes == OPERATIONAL_WEIGHT_HEXES
    assert tuple(reference.type_weights[t].hex() for t in (0, 1)) == (
        OPERATIONAL_WEIGHT_HEXES
    )
    assert (
        tuple(Fraction.from_float(reference.type_weights[t]) for t in (0, 1))
        == OPERATIONAL_WEIGHTS
    )
    assert all(
        ideal != operational
        for ideal, operational in zip(IDEAL_WEIGHTS, OPERATIONAL_WEIGHTS)
    )
    assert certificate.ideal_and_binary64_parameter_activity_equal is True
    assert certificate.ideal_and_binary64_parameter_type_weight_equalities == (
        False,
        False,
    )
    assert certificate.ideal_and_binary64_parameter_reference_parameters_equal is False
    assert certificate.binary64_parameter_normalizer_and_marginals_derived is False
    assert certificate.analytic_pi_n_target_equality_verified is False


def test_reference_count_law_binary64_layers_are_explicit_not_rational_aliases(m1, m2):
    assert tuple(value.hex() for value in m1.reference.count_probabilities) == (
        "0x1.0000000000000p-1",
        "0x1.0000000000000p-1",
    )
    assert tuple(value.hex() for value in m2.reference.count_probabilities) == (
        "0x1.999999999999ap-2",
        "0x1.999999999999ap-2",
        "0x1.999999999999ap-3",
    )
    assert tuple(
        Fraction.from_float(float(value)) for value in m2.reference.count_probabilities
    ) != (Fraction(2, 5), Fraction(2, 5), Fraction(1, 5))


def test_fixed_empty_context_and_digest_are_bound_and_wrong_context_refuses(m1, m2):
    for provider in (m1, m2):
        certificate = provider.certificate
        assert provider.residual_context == ()
        assert certificate.residual_context == ()
        assert certificate.residual_context_dimension == 0
        assert certificate.residual_context_sha256 == CONTEXT_SHA256
        result = provider.evaluate((), residual_context=())
        assert result.residual_context == ()
        assert result.residual_context_sha256 == CONTEXT_SHA256
        with pytest.raises(TypeError, match="exact tuple"):
            provider.evaluate((), residual_context=[])
        with pytest.raises(ValueError, match="empty context"):
            provider.evaluate((), residual_context=(0.0,))


@pytest.mark.parametrize(
    "configuration,category,coordinates",
    [
        ((), "empty", ()),
        ((TransformedEvent(0),), "atomic-a", ()),
        ((TransformedEvent(1, (0.0,)),), "continuous-b", (0.0,)),
        ((TransformedEvent(1, (1.25,)),), "continuous-b", (1.25,)),
        (
            (TransformedEvent(1, (math.nextafter(1.0, 2.0),)),),
            "continuous-b",
            (math.nextafter(1.0, 2.0),),
        ),
        ((TransformedEvent(1, (-3.75,)),), "continuous-b", (-3.75,)),
    ],
)
def test_m1_pointwise_exact_q_matches_manual_fraction_and_independent_oracle(
    m1, configuration, category, coordinates
):
    result = m1.evaluate(configuration, residual_context=())
    expected = _manual_m1_score(result.configuration)
    independent = oracle.m1_exact_rational_score(category, coordinates)

    assert result.exact_log_weight == expected
    assert result.exact_log_weight == independent.exact_rational_score
    assert (
        result.exact_log_weight_numerator,
        result.exact_log_weight_denominator,
    ) == (expected.numerator, expected.denominator)
    assert result.rounded_exact_log_weight == float(expected)
    assert result.configuration == configuration
    assert result.count_penalty == ZERO
    assert result.exact_upper_bound_respected is True
    assert m1.validate_evaluation(result, configuration, residual_context=()) is result


@pytest.mark.parametrize(
    "configuration",
    [
        (),
        (TransformedEvent(0, (1.25,)),),
        (TransformedEvent(1, (2.0, -0.5)),),
        (
            TransformedEvent(1, (2.0, -0.5)),
            TransformedEvent(0, (1.0,)),
        ),
        (
            TransformedEvent(0, (0.5,)),
            TransformedEvent(0, (-2.0,)),
        ),
        (
            TransformedEvent(1, (-1.0, 3.0)),
            TransformedEvent(1, (0.25, -0.75)),
        ),
    ],
)
def test_m2_pointwise_exact_q_matches_manual_fraction_oracle_and_multiplicity(
    m2, configuration
):
    result = m2.evaluate(configuration, residual_context=())
    expected = _manual_m2_score(result.configuration)

    assert result.configuration == tuple(
        sorted(configuration, key=TransformedEvent.model_key)
    )
    assert result.exact_log_weight == expected
    assert result.exact_log_weight == _oracle_m2_score(result.configuration)
    assert result.count_penalty == (
        Fraction(-1, 4) if len(configuration) == 2 else ZERO
    )
    assert len(result.configuration) == len(configuration)
    assert m2.validate_evaluation(result, configuration, residual_context=()) is result


def test_m2_exact_score_is_not_replaced_by_direct_binary64_formula(m2):
    first = 0.1
    second = 0.1
    configuration = (TransformedEvent(1, (first, second)),)
    result = m2.evaluate(configuration, residual_context=())
    independent = oracle.m2_exact_rational_score((1,), ((first, second),))

    assert result.exact_log_weight == independent.exact_rational_score
    assert result.rounded_exact_log_weight.hex() == "-0x1.7e4b17e4b17e5p-9"
    assert result.direct_binary64_log_weight.hex() == "-0x1.7e4b17e4b17e6p-9"
    assert (
        result.direct_binary64_log_weight.hex()
        == independent.binary64_formula_score.hex()
    )
    assert struct.pack(">d", result.rounded_exact_log_weight) != struct.pack(
        ">d", result.direct_binary64_log_weight
    )


def test_exact_score_survives_when_both_optional_binary64_displays_are_absent(m1):
    configuration = (TransformedEvent(1, (1.0e200,)),)
    result = m1.evaluate(configuration, residual_context=())
    represented = Fraction.from_float(1.0e200)

    assert result.exact_log_weight == -(represented * represented) / 4
    assert result.exact_log_weight < Fraction(-(10**399), 1)
    assert result.rounded_exact_log_weight is None
    assert result.direct_binary64_log_weight is None
    assert result.exact_upper_bound_respected is True


def test_canonical_order_is_applied_but_wrong_support_and_dimensions_refuse(m1, m2):
    reversed_m2 = (
        TransformedEvent(1, (0.0, 1.0)),
        TransformedEvent(0, (2.0,)),
    )
    result = m2.evaluate(reversed_m2, residual_context=())
    assert tuple(event.event_type for event in result.configuration) == (0, 1)

    with pytest.raises(TypeError, match="exact tuple"):
        m1.evaluate([], residual_context=())
    with pytest.raises(ValueError, match="cardinality"):
        m1.evaluate(
            (TransformedEvent(0), TransformedEvent(1, (0.0,))),
            residual_context=(),
        )
    with pytest.raises(ValueError, match="wrong dimension"):
        m1.evaluate((TransformedEvent(1),), residual_context=())
    with pytest.raises(ValueError, match="unknown event type"):
        m2.evaluate((TransformedEvent(2),), residual_context=())


@pytest.mark.parametrize(
    "event",
    [
        _forged_event(0, (-0.0,)),
        _forged_event(0, (True,)),
        _forged_event(True, (0.0,)),
        _forged_event(0, (float("nan"),)),
        _forged_event(0, (float("inf"),)),
    ],
)
def test_hostile_forged_event_internals_refuse_before_sorting_or_scoring(m2, event):
    with pytest.raises((TypeError, ValueError)):
        m2.evaluate((event,), residual_context=())


def test_normal_event_constructor_canonicalizes_negative_zero_before_provider(m2):
    event = TransformedEvent(0, (-0.0,))
    assert event.coordinates == (0.0,)
    assert math.copysign(1.0, event.coordinates[0]) > 0.0
    result = m2.evaluate((event,), residual_context=())
    assert result.exact_log_weight == ZERO


def test_exact_u_zero_is_certified_attained_and_no_false_finite_l_is_created(m1, m2):
    witnesses = (
        m1.evaluate((), residual_context=()),
        m1.evaluate((TransformedEvent(0),), residual_context=()),
        m2.evaluate((TransformedEvent(0, (0.0,)),), residual_context=()),
        m2.evaluate((TransformedEvent(1, (0.0, 0.0)),), residual_context=()),
    )
    for provider in (m1, m2):
        certificate = provider.certificate
        assert certificate.exact_global_upper_bound == ZERO
        assert certificate.exact_global_lower_bound is None
        assert certificate.exact_upper_bound_verified is True
        assert certificate.ideal_real_global_lower_bound_exists is False
        assert certificate.represented_domain_global_lower_bound_certified is False
        assert all(value <= 0 for value in certificate.count_penalties)
        assert all(
            value >= 0 for row in certificate.quadratic_coefficients for value in row
        )
    assert all(witness.exact_log_weight == ZERO for witness in witnesses)


def test_records_and_owner_are_sealed_immutable_and_nonpickleable(m1):
    evaluation = m1.evaluate((), residual_context=())
    with pytest.raises(TypeError):
        backend.ExactRationalQuadraticInitialTilt()
    with pytest.raises(TypeError):
        backend.ExactRationalQuadraticInitialTiltCertificate(_construction_token=None)
    with pytest.raises(TypeError):
        backend.ExactRationalQuadraticInitialTiltPointEvaluation(
            _construction_token=None
        )
    for value in (m1, m1.certificate, evaluation):
        with pytest.raises((TypeError, AttributeError)):
            pickle.dumps(value)
    with pytest.raises(AttributeError):
        m1._reference = m1.reference
    with pytest.raises((AttributeError, TypeError)):
        m1.certificate.fixture_id = "tampered"


def test_certificate_digest_is_instance_stable_and_owner_twin_custody_refuses():
    first = backend.build_t28_m1_q_exact_score_provider()
    second = backend.build_t28_m1_q_exact_score_provider()
    assert first.reference is not second.reference
    assert first.certificate is not second.certificate
    assert first.certificate.certificate_sha256 == (
        second.certificate.certificate_sha256
    )
    assert first.parameter_key() == second.parameter_key()

    hostile = backend.build_t28_m1_q_exact_score_provider()
    object.__setattr__(hostile, "_reference_identity", second.reference)
    with pytest.raises(ValueError, match="identity sentinel"):
        hostile.revalidate_live_reference()

    hostile = backend.build_t28_m1_q_exact_score_provider()
    object.__setattr__(hostile, "_certificate_identity", second.certificate)
    with pytest.raises(ValueError, match="identity sentinel"):
        hostile.revalidate_live_reference()


def test_reference_identity_cross_fixture_and_replay_input_splices_refuse(m1, m2):
    another_m1 = backend.build_t28_m1_q_exact_score_provider()
    with pytest.raises(ValueError, match="different reference"):
        backend.require_matching_exact_rational_quadratic_initial_tilt(
            another_m1.reference, m1
        )

    evaluation = m1.evaluate((TransformedEvent(1, (1.0,)),), residual_context=())
    with pytest.raises(ValueError, match="different certificate"):
        m2.validate_evaluation(
            evaluation,
            (TransformedEvent(1, (1.0, 0.0)),),
            residual_context=(),
        )
    with pytest.raises(ValueError, match="field"):
        m1.validate_evaluation(
            evaluation,
            (TransformedEvent(1, (2.0,)),),
            residual_context=(),
        )


def test_fully_redigested_score_and_nonclaim_promotions_refuse(m1):
    configuration = (TransformedEvent(1, (1.25,)),)
    evaluation = m1.evaluate(configuration, residual_context=())
    false_score = Fraction(-99, 1)
    forged_evaluation = _forge(
        evaluation,
        exact_log_weight=false_score,
        exact_log_weight_numerator=false_score.numerator,
        exact_log_weight_denominator=false_score.denominator,
        rounded_exact_log_weight=float(false_score),
    )
    _redigest_evaluation(forged_evaluation)
    with pytest.raises(ValueError, match="exact score differs from retained state"):
        m1.validate_evaluation(forged_evaluation, configuration, residual_context=())

    for field in (
        "analytic_pi_n_target_equality_verified",
        "operational_reference_sampling_law_verified",
        "learned_model_quality_evidence",
        "cp50_v1_kernel_type_compatible",
        "normalization_certified",
        "path_or_sampler_admitted",
        "formal_test_28_closed",
    ):
        forged_certificate = _forge(m1.certificate, **{field: True})
        _redigest_certificate(forged_certificate)
        with pytest.raises(ValueError):
            backend._validate_certificate(forged_certificate)


@pytest.mark.parametrize(
    "updates",
    [
        {"cardinality": True},
        {"count_penalty": 0},
        {"exact_log_weight_denominator": 1.0},
    ],
)
def test_fully_redigested_equal_value_wrong_types_refuse(m1, updates):
    evaluation = m1.evaluate((TransformedEvent(0),), residual_context=())
    forged = _forge(evaluation, **updates)
    _redigest_evaluation(forged)
    with pytest.raises((TypeError, ValueError)):
        m1.validate_evaluation(forged, (TransformedEvent(0),), residual_context=())


def test_fully_redigested_certificate_bool_integer_aliases_refuse(m1):
    hostile_updates = (
        {"total_cap": True},
        {"type_ids": (False, True)},
        {"type_dimensions": (False, True)},
        {"residual_context_dimension": False},
    )
    for updates in hostile_updates:
        forged = _forge(m1.certificate, **updates)
        _redigest_certificate(forged)
        with pytest.raises((TypeError, ValueError)):
            backend._validate_certificate(forged)


def test_fully_redigested_equal_float_binary64_weight_aliases_refuse(m1):
    forged = _forge(
        m1.certificate,
        binary64_parameter_type_weights=(0.4, 0.6),
    )
    _redigest_certificate(forged)

    with pytest.raises(TypeError, match="must be an exact Fraction"):
        backend._validate_certificate(forged)


def test_fully_redigested_nested_bool_reference_key_alias_refuses(m1):
    original = m1.certificate.reference_parameter_key
    type_rows = original[1]
    forged_first_row = (False,) + type_rows[0][1:]
    forged_key = (
        original[0],
        (forged_first_row,) + type_rows[1:],
    ) + original[2:]
    assert forged_key == original
    forged = _forge(m1.certificate, reference_parameter_key=forged_key)
    _redigest_certificate(forged)

    with pytest.raises(ValueError, match="reference parameter key differs"):
        backend._validate_certificate(forged)


@pytest.mark.parametrize(
    "mutation,expected_message",
    [
        ("total_cap", "live reference total_cap must be an exact integer"),
        ("type_ids", "live reference type ids must be exact integers"),
        ("type_dimension", "live reference type dimension must be an exact integer"),
    ],
)
def test_fully_redigested_mutated_live_reference_integer_aliases_refuse(
    mutation, expected_message
):
    provider = backend.build_t28_m1_q_exact_score_provider()
    reference = provider.reference
    certificate = provider.certificate
    original_cap = reference.total_cap
    original_ids = reference.type_ids
    original_dimensions = reference.type_dimensions

    try:
        if mutation == "total_cap":
            object.__setattr__(reference, "total_cap", True)
        elif mutation == "type_ids":
            object.__setattr__(reference, "type_ids", (False, True))
        else:
            object.__setattr__(
                reference,
                "type_dimensions",
                MappingProxyType({0: False, 1: 1}),
            )
        forged = _fully_redigested_mutated_reference_certificate(certificate)
        with pytest.raises(TypeError, match=expected_message):
            backend._validate_certificate(forged)
    finally:
        object.__setattr__(reference, "total_cap", original_cap)
        object.__setattr__(reference, "type_ids", original_ids)
        object.__setattr__(reference, "type_dimensions", original_dimensions)

    assert provider.revalidate_live_reference() is certificate


class _OversizedStreamingIntegerMapping(dict):
    def __init__(self):
        super().__init__()
        self.keys_yielded = 0

    def keys(self):
        for key in range(3):
            self.keys_yielded += 1
            yield key


def test_bounded_mapping_key_helper_refuses_streaming_oversize_without_allocation():
    mapping = _OversizedStreamingIntegerMapping()
    with pytest.raises(ValueError, match="mapping-key limit"):
        backend._bounded_exact_integer_mapping_keys(
            mapping,
            name="hostile streaming mapping",
            maximum_items=2,
        )
    assert mapping.keys_yielded == 3


def test_custom_certifier_refuses_invalid_envelopes_dimensions_context_and_weights():
    reference = CappedPoissonConfigurationReference(
        {0: 1}, {0: 1.0}, activity=1.0, total_cap=1
    )
    base = {
        "fixture_id": "hostile",
        "ideal_activity": Fraction(1),
        "ideal_type_weights": {0: Fraction(1)},
        "count_penalties": (ZERO, ZERO),
        "quadratic_coefficients_by_type": {0: (Fraction(1, 4),)},
        "residual_context": (),
        "provider_role_sha256": "7" * 64,
    }
    hostile = (
        ({"ideal_type_weights": {0: 1.0}}, TypeError),
        ({"count_penalties": (ZERO, Fraction(1, 4))}, ValueError),
        ({"quadratic_coefficients_by_type": {0: ()}}, ValueError),
        ({"quadratic_coefficients_by_type": {0: (ZERO,)}}, ValueError),
        ({"residual_context": (0.0,)}, ValueError),
    )
    for updates, error_type in hostile:
        arguments = dict(base)
        arguments.update(updates)
        with pytest.raises(error_type):
            backend.certify_exact_rational_quadratic_initial_tilt(
                reference, **arguments
            )

    reserved = dict(base)
    reserved["fixture_id"] = "T28-M1-Q"
    with pytest.raises(ValueError, match="builder-reserved"):
        backend.certify_exact_rational_quadratic_initial_tilt(reference, **reserved)


def test_fully_redigested_generic_certificate_cannot_claim_reserved_m1_identity():
    reference = CappedPoissonConfigurationReference(
        {0: 1}, {0: 1.0}, activity=1.0, total_cap=1
    )
    generic = backend.certify_exact_rational_quadratic_initial_tilt(
        reference,
        fixture_id="generic-one-type-quadratic",
        ideal_activity=Fraction(1),
        ideal_type_weights={0: Fraction(1)},
        count_penalties=(ZERO, ZERO),
        quadratic_coefficients_by_type={0: (Fraction(1, 4),)},
        residual_context=(),
        provider_role_sha256="8" * 64,
    ).certificate
    forged = _forge(
        generic,
        fixture_id="T28-M1-Q",
        fixture_spec_sha256=backend._fixture_spec_sha256(
            fixture_id="T28-M1-Q",
            ideal_activity=generic.ideal_activity,
            ideal_type_weights=generic.ideal_type_weights,
            type_ids=generic.type_ids,
            type_dimensions=generic.type_dimensions,
            total_cap=generic.total_cap,
            count_penalties=generic.count_penalties,
            quadratic_coefficients=generic.quadratic_coefficients,
        ),
    )
    _redigest_certificate(forged)

    with pytest.raises(
        ValueError, match="canonical Test-28 certificate specification differs"
    ):
        backend._validate_certificate(forged)


def test_no_nuisance_learned_or_downstream_admission_claims_and_m2_quota_blocker(
    m1, m2
):
    evaluation_fields = set(
        backend.ExactRationalQuadraticInitialTiltPointEvaluation.__annotations__
    )
    assert (
        not {
            "guide_evaluation",
            "residual_evaluation",
            "model_output",
            "checkpoint",
            "conditioning_adapter",
            "nuisance_term",
        }
        & evaluation_fields
    )

    false_flags = (
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
    for provider in (m1, m2):
        assert all(
            getattr(provider.certificate, field) is False for field in false_flags
        )
    assert m1.certificate.cp50_v1_dyadic_quota_compatible is True
    assert m2.certificate.cp50_v1_dyadic_quota_compatible is False
    assert Fraction(1, 6).denominator & (Fraction(1, 6).denominator - 1)
    scope = backend.EXACT_RATIONAL_QUADRATIC_INITIAL_TILT_SCOPE
    assert "not-cp50-v1-kernel-compatible" in scope
    assert "not-reference-sampler-law" in scope
    assert "not-formal-test-28-closure" in scope
