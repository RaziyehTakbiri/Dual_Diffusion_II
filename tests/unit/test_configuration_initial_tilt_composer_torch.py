"""Hostile tests for checkpoint-30 initial-tilt point composition."""

from fractions import Fraction
import inspect
import math
import os
from pathlib import Path
import pickle
import random
import subprocess
import sys

import numpy as np
import pytest


torch = pytest.importorskip(
    "torch", reason="initial-tilt point composition requires PyTorch"
)

import heterodiff.models.configuration_residual_torch as residual  # noqa: E402
from heterodiff.models import (  # noqa: E402
    configuration_initial_tilt_composer_torch as initial_tilt,
)
from heterodiff.models.configuration_energy_torch import (  # noqa: E402
    BoundedConfigurationEnergy,
    ConfigurationEnergyCertificateError,
    ConfigurationEnergyArchitecture,
    SpectralNormCeilings,
    pack_typed_configuration_batch,
)
from heterodiff.models import (  # noqa: E402
    configuration_totalized_jump_residual_torch as totalized_residual,
)
from heterodiff.processes import (  # noqa: E402
    plugin_bridge_counter_keyed_initializer_protocol as initializer_protocol,
)
from heterodiff.processes.plugin_bridge_sampler import (  # noqa: E402
    ProcessValidReferenceJumpComposer,
)
from heterodiff.processes.reversible_hybrid_reference import (  # noqa: E402
    PiecewiseConstantHybridSchedule,
    ReversibleHybridRates,
    ReversibleHybridReference,
)
from heterodiff.theory.association_observation import (  # noqa: E402
    AffineGaussianFiberChannel,
    CollapsedPoissonObservationReference,
    TypedAffineGaussianObservationChannel,
    TypedGaussianClutterIntensity,
)
from heterodiff.theory.association_operational_guide import (  # noqa: E402
    AssociationGuideOperationalError,
    RangeGatedAssociationGuide,
    certify_range_gated_association_guide,
)
from heterodiff.theory.association_preconditioner import (  # noqa: E402
    AnalyticAssociationPreconditioner,
    AssociationPreconditionerNumericalError,
)
from heterodiff.theory.association_totalized_jump_guide import (  # noqa: E402
    NUMERICAL_FALLBACK_BRANCH,
    RANGE_FALLBACK_BRANCH,
    TotalizedAssociationJumpGuide,
    TotalizedJumpGuideEvaluation,
    certify_totalized_association_jump_guide,
)
from heterodiff.theory.configuration_reference import (  # noqa: E402
    CappedPoissonConfigurationReference,
    TransformedEvent,
)
from tests.unit import (  # noqa: E402
    test_configuration_totalized_jump_potential_composer_torch as checkpoint17,
)


_ROLE = "9" * 64
_RESIDUAL_CONTEXT = (-0.4,)


def _certify(bundle):
    return initial_tilt.certify_configuration_initial_tilt_composer(
        bundle["reference_composer"],
        totalized_guide=bundle["totalized_guide"],
        totalized_residual=bundle["totalized_residual"],
        target_policy=initial_tilt.CONFIGURATION_INITIAL_TILT_TARGET_POLICY,
        composition_role_sha256=_ROLE,
    )


@pytest.fixture(scope="module")
def bundle():
    result = checkpoint17._bundle()
    result["initial_tilt"] = _certify(result)
    return result


def _model(architecture, seed):
    generator = torch.Generator(device="cpu")
    generator.manual_seed(seed)
    return BoundedConfigurationEnergy(architecture, generator=generator)


def _continuous_bundle():
    reference = CappedPoissonConfigurationReference(
        {0: 1}, {0: 1.0}, activity=1.2, total_cap=2
    )
    schedule = PiecewiseConstantHybridSchedule(
        (0.0, 0.25, 1.0),
        (0.0, 0.8),
        (0.0, 0.6),
        clean_hold=0.25,
    )
    rates = ReversibleHybridRates(reference, per_particle_death_rate=0.7)
    process = ReversibleHybridReference(reference, schedule, rates)
    observation_reference = CollapsedPoissonObservationReference(
        {10: 1}, {10: 1.0}, retained_cap=2
    )
    channel = TypedAffineGaussianObservationChannel(
        {0: 1},
        observation_reference,
        ((1.0,),),
        fiber_channels={(0, 10): AffineGaussianFiberChannel([[1.4]], [0.2], [[0.6]])},
    )
    clutter = TypedGaussianClutterIntensity(
        observation_reference,
        0.3,
        (1.0,),
        fiber_channels={
            10: AffineGaussianFiberChannel(
                np.zeros((1, 0), dtype=np.float64), [-0.1], [[1.2]]
            )
        },
    )
    preconditioner = AnalyticAssociationPreconditioner(
        process,
        observation_reference,
        channel,
        clutter,
        {0: 0.7},
        contamination_probability=0.08,
        context_key=("checkpoint-30-continuous",),
    )
    outcome = (TransformedEvent(10, (0.3,)),)
    analytic = preconditioner.certify_guide_range(outcome)
    range_gate = certify_range_gated_association_guide(
        preconditioner, analytic, observation=outcome
    )
    guide = certify_totalized_association_jump_guide(
        preconditioner,
        range_gate,
        analytic,
        observation=outcome,
    )
    architecture = ConfigurationEnergyArchitecture.from_process(
        process,
        coordinate_scales_by_type={0: (1.5,)},
        context_dimension=1,
        context_scales=(1.0,),
        context_schema_sha256="f" * 64,
        event_hidden_width=3,
        event_embedding_width=2,
        context_hidden_width=3,
        context_embedding_width=2,
        readout_hidden_width=4,
        value_bound=1.5,
        spectral_ceilings=SpectralNormCeilings(*(100.0,) * 7),
        bias_ceiling=100.0,
        first_derivative_ceiling=1_000_000.0,
        second_derivative_ceiling=1_000_000.0,
    )
    model = _model(architecture, 3001)
    provenance = residual.ConditionalResidualProvenance(
        method_freeze_sha256="1" * 64,
        training_run_sha256="2" * 64,
        data_manifest_sha256="3" * 64,
        selection_rule_sha256="4" * 64,
        observation_schema_sha256="a" * 64,
        task_schema_sha256="b" * 64,
        conditioning_adapter_sha256="d" * 64,
        residual_role_sha256="e" * 64,
    )
    contract = residual.make_conditional_residual_contract(
        architecture,
        observation_schema_sha256="a" * 64,
        task_schema_sha256="b" * 64,
        conditioning_adapter_sha256="d" * 64,
        residual_role_sha256="e" * 64,
    )
    checkpoint = residual.certify_conditional_residual(
        model, contract, provenance=provenance
    )
    residual_owner = totalized_residual.certify_totalized_conditional_jump_residual(
        model, checkpoint, expected_provenance=provenance
    )
    result = {
        "reference_composer": ProcessValidReferenceJumpComposer(process),
        "totalized_guide": guide,
        "totalized_residual": residual_owner,
        "residual_model": model,
    }
    result["initial_tilt"] = _certify(result)
    return result


def _evaluate(bundle, state, *, context=_RESIDUAL_CONTEXT):
    return bundle["initial_tilt"].evaluate(state, residual_context=context)


def _fraction(record, prefix):
    return Fraction(
        getattr(record, "%s_numerator" % prefix),
        getattr(record, "%s_denominator" % prefix),
    )


def _forged_record(record, **updates):
    forged = object.__new__(initial_tilt.InitialTiltPointEvaluation)
    for name in initial_tilt.InitialTiltPointEvaluation.__annotations__:
        object.__setattr__(forged, name, updates.get(name, getattr(record, name)))
    return forged


def _forged_certificate(certificate, **updates):
    annotations = initial_tilt.InitialTiltCompositionCertificate.__annotations__
    values = {
        name: updates.get(name, getattr(certificate, name)) for name in annotations
    }
    values["certificate_sha256"] = initial_tilt._semantic_digest(
        initial_tilt._certificate_payload(values)
    )
    forged = object.__new__(initial_tilt.InitialTiltCompositionCertificate)
    for name, value in values.items():
        object.__setattr__(forged, name, value)
    return forged


def _forged_component_record(record, record_type, **updates):
    forged = object.__new__(record_type)
    for name in record_type.__annotations__:
        object.__setattr__(forged, name, updates.get(name, getattr(record, name)))
    return forged


def _pack_residual_point(bundle, state, context):
    architecture = bundle["residual_model"].architecture
    coordinates = {}
    owners = {}
    for event_type, dimension in zip(
        architecture.type_ids, architecture.type_dimensions
    ):
        events = tuple(event for event in state if event.event_type == event_type)
        if not events:
            continue
        if dimension:
            values = torch.tensor(
                [event.coordinates for event in events], dtype=torch.float64
            )
        else:
            values = torch.empty((len(events), 0), dtype=torch.float64)
        coordinates[event_type] = values
        owners[event_type] = torch.zeros(len(events), dtype=torch.int64)
    return pack_typed_configuration_batch(
        architecture,
        torch.tensor([bundle["process"].schedule.horizon], dtype=torch.float64),
        torch.tensor([context], dtype=torch.float64),
        coordinates,
        owners,
    )


def _assert_tight_lower_witness(represented, exact):
    represented_fraction = Fraction.from_float(represented)
    assert represented_fraction <= exact
    if represented_fraction < exact:
        assert Fraction.from_float(math.nextafter(represented, math.inf)) > exact


def _assert_tight_upper_witness(represented, exact):
    represented_fraction = Fraction.from_float(represented)
    assert represented_fraction >= exact
    if represented_fraction > exact:
        assert Fraction.from_float(math.nextafter(represented, -math.inf)) < exact


def test_exact_rounding_and_directed_witness_white_box_vectors():
    half_ulp_above_one = Fraction(1, 1) + Fraction(1, 2**53)
    three_half_ulps_above_one = Fraction(1, 1) + Fraction(3, 2**53)
    half_minimum_subnormal = Fraction(1, 2**1075)
    minimum_subnormal = math.nextafter(0.0, math.inf)

    assert (
        initial_tilt._round_fraction_once(half_ulp_above_one, name="tie").hex()
        == (1.0).hex()
    )
    assert (
        initial_tilt._round_fraction_once(three_half_ulps_above_one, name="tie").hex()
        == math.nextafter(math.nextafter(1.0, math.inf), math.inf).hex()
    )
    assert (
        initial_tilt._round_fraction_once(
            half_minimum_subnormal, name="positive underflow tie"
        ).hex()
        == (0.0).hex()
    )
    assert (
        initial_tilt._round_fraction_once(
            -half_minimum_subnormal, name="negative underflow tie"
        ).hex()
        == (0.0).hex()
    )

    lower = initial_tilt._outward_lower_fraction(
        half_minimum_subnormal, name="positive tiny lower"
    )
    upper = initial_tilt._outward_upper_fraction(
        half_minimum_subnormal, name="positive tiny upper"
    )
    negative_lower = initial_tilt._outward_lower_fraction(
        -half_minimum_subnormal, name="negative tiny lower"
    )
    negative_upper = initial_tilt._outward_upper_fraction(
        -half_minimum_subnormal, name="negative tiny upper"
    )
    assert lower.hex() == (0.0).hex()
    assert upper.hex() == minimum_subnormal.hex()
    assert negative_lower.hex() == (-minimum_subnormal).hex()
    assert negative_upper.hex() == (0.0).hex()

    overflow = Fraction.from_float(sys.float_info.max) * 2
    for helper in (
        initial_tilt._round_fraction_once,
        initial_tilt._outward_lower_fraction,
        initial_tilt._outward_upper_fraction,
    ):
        with pytest.raises(initial_tilt.ConfigurationInitialTiltError, match="finite"):
            helper(overflow, name="overflow")


def test_factory_is_target_explicit_and_does_not_accept_base_energy(bundle):
    factory_parameters = inspect.signature(
        initial_tilt.certify_configuration_initial_tilt_composer
    ).parameters
    assert "reference_composer" in factory_parameters
    assert "totalized_guide" in factory_parameters
    assert "totalized_residual" in factory_parameters
    assert "target_policy" in factory_parameters
    assert "composition_role_sha256" in factory_parameters
    assert not any("base" in name for name in factory_parameters)
    assert all(
        parameter.kind is not inspect.Parameter.VAR_KEYWORD
        for parameter in factory_parameters.values()
    )

    with pytest.raises(ValueError, match="target|supported"):
        initial_tilt.certify_configuration_initial_tilt_composer(
            bundle["reference_composer"],
            totalized_guide=bundle["totalized_guide"],
            totalized_residual=bundle["totalized_residual"],
            target_policy="base-plus-guide-plus-residual",
            composition_role_sha256=_ROLE,
        )


def test_point_api_has_no_rng_protocol_or_sampling_surface(bundle, monkeypatch):
    owner = bundle["initial_tilt"]
    parameters = inspect.signature(owner.evaluate).parameters
    assert tuple(parameters) == ("configuration", "residual_context")
    assert "rng" not in parameters
    assert "seed" not in parameters
    assert all(
        parameter.kind is not inspect.Parameter.VAR_KEYWORD
        for parameter in parameters.values()
    )
    for name in (
        "sample",
        "draw",
        "allocate",
        "enumerate",
        "rejection",
        "sir",
        "normalize",
        "initial_law",
        "jump_rate",
        "waiting_time",
        "path",
    ):
        assert not hasattr(owner, name)
        assert name not in initial_tilt.__all__

    def forbidden(*args, **kwargs):
        del args, kwargs
        raise AssertionError("point evaluation allocated initializer protocol words")

    monkeypatch.setattr(
        initializer_protocol.CounterKeyedInitializerProtocolOwner,
        "allocate",
        forbidden,
    )
    monkeypatch.setattr(
        ProcessValidReferenceJumpComposer, "sample_candidate", forbidden
    )
    result = _evaluate(bundle, ())
    assert type(result) is initial_tilt.InitialTiltPointEvaluation


def test_point_evaluation_uses_no_numpy_torch_or_stdlib_randomness(bundle, monkeypatch):
    def forbidden(*args, **kwargs):
        del args, kwargs
        raise AssertionError("initial-tilt point evaluation consumed randomness")

    for owner, name in (
        (np.random, "default_rng"),
        (np.random, "random"),
        (np.random, "rand"),
        (np.random, "randn"),
        (np.random, "choice"),
        (random, "random"),
        (random, "randrange"),
        (random, "getrandbits"),
        (torch, "rand"),
        (torch, "randn"),
        (torch, "randint"),
        (torch, "multinomial"),
    ):
        monkeypatch.setattr(owner, name, forbidden)

    record = _evaluate(bundle, (TransformedEvent(0), TransformedEvent(1)))
    assert type(record) is initial_tilt.InitialTiltPointEvaluation


def test_context_and_configuration_inputs_fail_closed(bundle):
    for invalid_context in (
        (),
        (-0.0,),
        (math.nan,),
        (math.inf,),
        (True,),
        "not-a-context",
    ):
        with pytest.raises((TypeError, ValueError), match="context|finite|zero|real"):
            _evaluate(bundle, (), context=invalid_context)

    for invalid_state in (
        (TransformedEvent(0), TransformedEvent(0), TransformedEvent(0)),
        (TransformedEvent(0, (1.0,)),),
        (TransformedEvent(17),),
    ):
        with pytest.raises(
            (TypeError, ValueError), match="state|configuration|cap|type"
        ):
            _evaluate(bundle, invalid_state)


def test_empty_duplicates_and_continuous_configurations_are_admitted(bundle):
    states = (
        (),
        (TransformedEvent(0),),
        (TransformedEvent(0), TransformedEvent(0)),
        (TransformedEvent(0), TransformedEvent(1)),
    )
    records = tuple(_evaluate(bundle, state) for state in states)
    assert all(
        type(record) is initial_tilt.InitialTiltPointEvaluation for record in records
    )
    assert len({record.configuration_sha256 for record in records}) == len(states)

    continuous = _continuous_bundle()
    continuous_states = (
        (),
        (TransformedEvent(0, (-0.3,)),),
        (TransformedEvent(0, (-0.3,)), TransformedEvent(0, (-0.3,))),
    )
    continuous_records = tuple(
        _evaluate(continuous, state) for state in continuous_states
    )
    assert len({record.configuration_sha256 for record in continuous_records}) == 3


def test_records_owners_and_certificates_are_sealed(bundle):
    owner = bundle["initial_tilt"]
    certificate = owner.certificate
    record = _evaluate(bundle, (TransformedEvent(0),))

    with pytest.raises((AttributeError, TypeError)):
        record.initial_tilt_log_value = 0.0
    with pytest.raises((AttributeError, TypeError)):
        certificate.passed = False
    with pytest.raises((AttributeError, TypeError)):
        owner._certificate = certificate
    with pytest.raises(TypeError):
        pickle.dumps(record)
    with pytest.raises(TypeError):
        pickle.dumps(certificate)
    with pytest.raises(TypeError):
        pickle.dumps(owner)
    with pytest.raises(TypeError):
        initial_tilt.InitialTiltPointEvaluation()
    with pytest.raises(TypeError):
        initial_tilt.InitialTiltCompositionCertificate()
    with pytest.raises(TypeError):
        initial_tilt.ConfigurationInitialTiltComposer()


def test_matcher_binds_exact_owners_role_target_and_process(bundle):
    owner = bundle["initial_tilt"]
    assert (
        initial_tilt.require_matching_configuration_initial_tilt_composer(
            bundle["reference_composer"],
            owner,
            totalized_guide=bundle["totalized_guide"],
            totalized_residual=bundle["totalized_residual"],
            target_policy=initial_tilt.CONFIGURATION_INITIAL_TILT_TARGET_POLICY,
            composition_role_sha256=_ROLE,
        )
        is owner
    )
    assert (
        initial_tilt.validate_configuration_initial_tilt_certificate(
            bundle["reference_composer"],
            owner,
            totalized_guide=bundle["totalized_guide"],
            totalized_residual=bundle["totalized_residual"],
            target_policy=initial_tilt.CONFIGURATION_INITIAL_TILT_TARGET_POLICY,
            composition_role_sha256=_ROLE,
        ).certificate_sha256
        == owner.certificate.certificate_sha256
    )

    equivalent = _certify(bundle)
    assert equivalent is not owner
    with pytest.raises(ValueError, match="different|certificate|owner"):
        equivalent.validate_evaluation(
            _evaluate(bundle, ()), (), residual_context=_RESIDUAL_CONTEXT
        )
    with pytest.raises(ValueError, match="role|live|certificate"):
        initial_tilt.require_matching_configuration_initial_tilt_composer(
            bundle["reference_composer"],
            owner,
            totalized_guide=bundle["totalized_guide"],
            totalized_residual=bundle["totalized_residual"],
            target_policy=initial_tilt.CONFIGURATION_INITIAL_TILT_TARGET_POLICY,
            composition_role_sha256="8" * 64,
        )


def test_checkpoint17_base_model_is_not_part_of_the_initial_tilt(bundle):
    state = (TransformedEvent(0), TransformedEvent(1))
    before = _evaluate(bundle, state)
    parameter = bundle["base_model"].readout.linear3.bias
    saved = parameter.detach().clone()
    try:
        with torch.no_grad():
            parameter.add_(1.0)
        after = _evaluate(bundle, state)
    finally:
        with torch.no_grad():
            parameter.copy_(saved)

    assert after.evaluation_sha256 == before.evaluation_sha256
    assert after.initial_log_factor.hex() == before.initial_log_factor.hex()


def test_certificate_states_exact_target_and_every_material_nonclaim(bundle):
    certificate = bundle["initial_tilt"].certificate

    assert certificate.passed is True
    assert certificate.target_policy == (
        initial_tilt.CONFIGURATION_INITIAL_TILT_TARGET_POLICY
    )
    assert certificate.base_initial_law_policy == (
        initial_tilt.CONFIGURATION_INITIAL_TILT_BASE_LAW_POLICY
    )
    assert certificate.reverse_time.hex() == (0.0).hex()
    assert certificate.direct_time.hex() == (bundle["process"].schedule.horizon.hex())
    for name in (
        "operational_surrogate_initial_log_factor_selected",
        "reference_base_initial_law_is_pi_n",
        "base_energy_excluded",
        "observation_only_nuisance_excluded",
        "totalized_guide_required",
        "totalized_residual_required",
        "reverse_time_fixed_at_zero",
        "direct_time_fixed_at_horizon",
        "exact_represented_component_sum",
        "aggregate_rounded_once",
        "deterministic_point_factor_admissible",
    ):
        assert getattr(certificate, name) is True
    for name in (
        "base_energy_included",
        "conditioning_adapter_origin_authenticated",
        "exact_analytic_factor_preserved",
        "exact_conditional_or_posterior_target",
        "exact_factor_exponentiation_certified",
        "normalization_certified",
        "support_enumeration_admissible",
        "rejection_sampling_admissible",
        "sir_admissible",
        "categorical_selection_admissible",
        "randomness_admissible",
        "initializer_admissible",
        "path_admissible",
        "operational_sampler_admissible",
        "coordinate_derivatives_admissible",
        "continuous_drift_admissible",
        "loaded_code_identity_authenticated",
        "runtime_portable",
        "blas_identity_authenticated",
    ):
        assert getattr(certificate, name) is False

    residual_certificate = bundle["totalized_residual"].certificate
    for composer_field, residual_field in (
        ("residual_totalized_certificate_sha256", "certificate_sha256"),
        ("residual_contract_sha256", "residual_contract_sha256"),
        ("residual_core_architecture_sha256", "core_architecture_sha256"),
        ("residual_context_schema_sha256", "context_schema_sha256"),
        ("residual_observation_schema_sha256", "observation_schema_sha256"),
        ("residual_task_schema_sha256", "task_schema_sha256"),
        (
            "residual_conditioning_adapter_sha256",
            "conditioning_adapter_sha256",
        ),
        ("residual_role_sha256", "residual_role_sha256"),
        ("residual_core_checkpoint_sha256", "core_checkpoint_sha256"),
        ("residual_core_certificate_sha256", "core_certificate_sha256"),
        ("residual_certificate_sha256", "residual_certificate_sha256"),
        ("residual_provenance_sha256", "residual_provenance_sha256"),
        ("residual_runtime_sha256", "residual_runtime_sha256"),
        ("residual_evaluator_runtime_sha256", "evaluator_runtime_sha256"),
    ):
        assert getattr(certificate, composer_field) == getattr(
            residual_certificate, residual_field
        )


def test_certificate_interval_is_a_tight_directed_binary64_witness(bundle):
    certificate = bundle["initial_tilt"].certificate
    exact_lower = Fraction.from_float(
        certificate.guide_operational_log_lower_bound
    ) - Fraction.from_float(certificate.residual_global_point_magnitude_bound)
    exact_upper = Fraction.from_float(
        certificate.guide_operational_log_upper_bound
    ) + Fraction.from_float(certificate.residual_global_point_magnitude_bound)

    _assert_tight_lower_witness(certificate.initial_log_factor_lower_bound, exact_lower)
    _assert_tight_upper_witness(certificate.initial_log_factor_upper_bound, exact_upper)
    assert (
        certificate.initial_log_factor_magnitude_bound.hex()
        == max(
            abs(certificate.initial_log_factor_lower_bound),
            abs(certificate.initial_log_factor_upper_bound),
        ).hex()
    )


@pytest.mark.parametrize(
    "state",
    (
        (),
        (TransformedEvent(0),),
        (TransformedEvent(0), TransformedEvent(0)),
        (TransformedEvent(0), TransformedEvent(1)),
    ),
)
def test_point_is_exact_guide_plus_residual_single_round_oracle(bundle, state):
    record = _evaluate(bundle, state)
    guide = bundle["totalized_guide"].evaluate(0.0, state)
    residual_batch = _pack_residual_point(bundle, state, _RESIDUAL_CONTEXT)
    residual_point = bundle["totalized_residual"].evaluate(residual_batch)
    exact = Fraction.from_float(guide.operational_log_density) + Fraction.from_float(
        residual_point.operational_residual
    )
    rounded = 0.0 if exact == 0 else float(exact)
    error = abs(Fraction.from_float(rounded) - exact)

    assert record.reverse_time.hex() == (0.0).hex()
    assert record.direct_time.hex() == bundle["process"].schedule.horizon.hex()
    assert record.guide_evaluation_sha256 == guide.evaluation_sha256
    assert record.residual_evaluation_sha256 == residual_point.evaluation_sha256
    assert record.guide_operational_log_density.hex() == (
        guide.operational_log_density.hex()
    )
    assert record.residual_operational_value.hex() == (
        residual_point.operational_residual.hex()
    )
    assert _fraction(record, "exact_initial_log_factor") == exact
    assert record.initial_log_factor.hex() == rounded.hex()
    assert _fraction(record, "exact_rounding_error") == error
    assert record.residual_mathematical_gate_numerator == 1
    assert record.residual_mathematical_gate_denominator == 1
    assert record.base_energy_excluded is True
    assert record.exact_factor_exponentiation_certified is False
    assert record.normalization_certified is False
    assert record.randomness_admissible is False
    assert record.initializer_admissible is False


def test_point_interval_is_directed_and_contains_the_exact_factor(bundle):
    record = _evaluate(bundle, (TransformedEvent(0), TransformedEvent(1)))
    exact_lower = Fraction.from_float(
        record.guide_operational_log_lower_bound
    ) - Fraction.from_float(record.residual_operational_point_magnitude_bound)
    exact_upper = Fraction.from_float(
        record.guide_operational_log_upper_bound
    ) + Fraction.from_float(record.residual_operational_point_magnitude_bound)
    exact_value = _fraction(record, "exact_initial_log_factor")

    _assert_tight_lower_witness(record.initial_log_factor_lower_bound, exact_lower)
    _assert_tight_upper_witness(record.initial_log_factor_upper_bound, exact_upper)
    assert Fraction.from_float(record.initial_log_factor_lower_bound) <= exact_value
    assert exact_value <= Fraction.from_float(record.initial_log_factor_upper_bound)


def test_replay_is_deterministic_and_refuses_plain_and_redigested_tampering(bundle):
    owner = bundle["initial_tilt"]
    state = (TransformedEvent(0), TransformedEvent(1))
    first = _evaluate(bundle, state)
    second = _evaluate(bundle, state)
    assert second.evaluation_sha256 == first.evaluation_sha256
    assert (
        owner.validate_evaluation(first, state, residual_context=_RESIDUAL_CONTEXT)
        is first
    )

    plain = _forged_record(
        first,
        initial_log_factor=math.nextafter(first.initial_log_factor, math.inf),
    )
    with pytest.raises(ValueError, match="initial log factor|digest|round"):
        owner.validate_evaluation(plain, state, residual_context=_RESIDUAL_CONTEXT)

    values = {
        name: getattr(first, name)
        for name in initial_tilt.InitialTiltPointEvaluation.__annotations__
    }
    values["guide_evaluation_sha256"] = "a" * 64
    values["evaluation_sha256"] = initial_tilt._semantic_digest(
        initial_tilt._evaluation_payload(values)
    )
    redigested = _forged_record(first, **values)
    with pytest.raises(ValueError, match="guide_evaluation_sha256|replay"):
        owner.validate_evaluation(redigested, state, residual_context=_RESIDUAL_CONTEXT)

    alternate_configuration = (TransformedEvent(1),)
    values = {
        name: getattr(first, name)
        for name in initial_tilt.InitialTiltPointEvaluation.__annotations__
    }
    values["configuration"] = alternate_configuration
    values["configuration_sha256"] = initial_tilt._configuration_sha256(
        alternate_configuration
    )
    values["evaluation_sha256"] = initial_tilt._semantic_digest(
        initial_tilt._evaluation_payload(values)
    )
    redigested_configuration = _forged_record(first, **values)
    with pytest.raises(ValueError, match="configuration|replay|field"):
        owner.validate_evaluation(
            redigested_configuration,
            alternate_configuration,
            residual_context=_RESIDUAL_CONTEXT,
        )

    alternate_context = (0.25,)
    values = {
        name: getattr(first, name)
        for name in initial_tilt.InitialTiltPointEvaluation.__annotations__
    }
    values["residual_context"] = alternate_context
    values["residual_context_sha256"] = initial_tilt._context_sha256(alternate_context)
    values["evaluation_sha256"] = initial_tilt._semantic_digest(
        initial_tilt._evaluation_payload(values)
    )
    redigested_context = _forged_record(first, **values)
    with pytest.raises(ValueError, match="context|replay|field"):
        owner.validate_evaluation(
            redigested_context, state, residual_context=alternate_context
        )

    with pytest.raises(ValueError, match="replay|configuration|field"):
        owner.validate_evaluation(
            first, (TransformedEvent(0),), residual_context=_RESIDUAL_CONTEXT
        )
    with pytest.raises(ValueError, match="replay|context|field"):
        owner.validate_evaluation(first, state, residual_context=(0.25,))


def test_semantically_redigested_certificate_role_and_runtime_tampering_refused(
    bundle,
):
    owner = bundle["initial_tilt"]
    original = owner.certificate
    for update in (
        {"composition_role_sha256": "a" * 64},
        {"composer_runtime_sha256": "b" * 64},
        {"reference_base_law_sha256": "c" * 64},
        {"residual_observation_schema_sha256": "d" * 64},
    ):
        forged = _forged_certificate(original, **update)
        initial_tilt._validate_certificate(forged)
        try:
            object.__setattr__(owner, "_certificate", forged)
            with pytest.raises(
                ValueError,
                match="runtime|live state|role|certificate|reference|residual",
            ):
                _evaluate(bundle, ())
        finally:
            object.__setattr__(owner, "_certificate", original)


@pytest.mark.parametrize(
    "invalid_identity", (True, 1 << 1_000_000), ids=("boolean", "huge")
)
def test_invalid_runtime_owner_identity_is_refused_before_digesting(
    bundle, invalid_identity
):
    certificate = bundle["initial_tilt"].certificate
    for field in (
        "reference_composer_runtime_identity",
        "guide_runtime_identity",
        "residual_runtime_identity",
    ):
        forged = object.__new__(initial_tilt.InitialTiltCompositionCertificate)
        for name in initial_tilt.InitialTiltCompositionCertificate.__annotations__:
            value = invalid_identity if name == field else getattr(certificate, name)
            object.__setattr__(forged, name, value)
        with pytest.raises(
            (TypeError, ValueError),
            match="runtime identity|implementation limit|identity range|exact integer",
        ):
            initial_tilt._validate_certificate(forged)


def test_live_runtime_function_tampering_is_refused(bundle, monkeypatch):
    monkeypatch.setattr(initial_tilt, "_runtime_sha256", lambda: "a" * 64)
    with pytest.raises(ValueError, match="runtime"):
        _evaluate(bundle, ())


def test_live_external_and_private_residual_model_tampering_is_refused(bundle):
    owner = bundle["initial_tilt"]
    for model in (
        bundle["residual_model"],
        bundle["totalized_residual"]._evaluation_model,
    ):
        parameter = model.readout.linear3.bias
        saved = parameter.detach().clone()
        try:
            with torch.no_grad():
                parameter.add_(0.5)
            with pytest.raises(ConfigurationEnergyCertificateError, match="live model"):
                owner.evaluate((), residual_context=_RESIDUAL_CONTEXT)
        finally:
            with torch.no_grad():
                parameter.copy_(saved)


def test_resource_preflight_refusal_occurs_before_residual_evaluation(
    bundle, monkeypatch
):
    preconditioner = bundle["totalized_guide"].preconditioner
    original_preflight = (
        AnalyticAssociationPreconditioner.preflight_capped_point_evaluation_resources
    )
    original_work = original_preflight(
        preconditioner, bundle["totalized_guide"].outcome
    )

    def changed_preflight(self, outcome):
        del self, outcome
        return original_work + 1

    def forbidden_residual(self, batch):
        del self, batch
        raise AssertionError("residual evaluation preceded guide resource preflight")

    monkeypatch.setattr(
        AnalyticAssociationPreconditioner,
        "preflight_capped_point_evaluation_resources",
        changed_preflight,
    )
    monkeypatch.setattr(
        totalized_residual.TotalizedConditionalJumpResidual,
        "evaluate",
        forbidden_residual,
    )
    with pytest.raises(ValueError, match="preflight|certificate|live"):
        _evaluate(bundle, ())


def test_nested_guide_and_residual_record_tampering_is_refused(bundle, monkeypatch):
    owner = bundle["initial_tilt"]
    guide_owner = bundle["totalized_guide"]
    original_guide = TotalizedAssociationJumpGuide.evaluate

    def forged_guide(self, reverse_time, state):
        record = original_guide(self, reverse_time, state)
        return _forged_component_record(
            record,
            TotalizedJumpGuideEvaluation,
            evaluation_sha256="a" * 64,
        )

    monkeypatch.setattr(TotalizedAssociationJumpGuide, "evaluate", forged_guide)
    with pytest.raises(ValueError, match="digest|sha256|does not match|recomputation"):
        owner.evaluate((), residual_context=_RESIDUAL_CONTEXT)

    monkeypatch.undo()
    original_residual = totalized_residual.TotalizedConditionalJumpResidual.evaluate

    def forged_residual(self, batch):
        record = original_residual(self, batch)
        return _forged_component_record(
            record,
            totalized_residual.TotalizedResidualPointEvaluation,
            evaluation_sha256="b" * 64,
        )

    monkeypatch.setattr(
        totalized_residual.TotalizedConditionalJumpResidual,
        "evaluate",
        forged_residual,
    )
    with pytest.raises(ValueError, match="digest|replay"):
        owner.evaluate((), residual_context=_RESIDUAL_CONTEXT)
    assert guide_owner is owner.totalized_guide


def test_semantically_equivalent_component_owner_substitution_is_refused(bundle):
    owner = bundle["initial_tilt"]
    original_reference = owner.reference_composer
    original_guide = owner.totalized_guide
    original_residual = owner.totalized_residual
    equivalent_reference = ProcessValidReferenceJumpComposer(bundle["process"])
    equivalent_guide = certify_totalized_association_jump_guide(
        original_guide.preconditioner,
        original_guide.range_gate,
        original_guide.range_certificate,
        observation=original_guide.outcome,
    )
    equivalent_residual = (
        totalized_residual.certify_totalized_conditional_jump_residual(
            original_residual.model,
            original_residual.checkpoint,
            expected_provenance=original_residual.provenance,
        )
    )
    assert equivalent_reference is not original_reference
    assert equivalent_guide is not original_guide
    assert equivalent_residual is not original_residual

    for field, substitute in (
        ("_reference_composer", equivalent_reference),
        ("_guide", equivalent_guide),
        ("_residual", equivalent_residual),
    ):
        original = getattr(owner, field)
        try:
            object.__setattr__(owner, field, substitute)
            with pytest.raises(ValueError, match="owner|identity|live|different"):
                _evaluate(bundle, ())
        finally:
            object.__setattr__(owner, field, original)


def test_precall_simultaneous_twin_slot_owner_substitution_is_refused(bundle):
    owner = bundle["initial_tilt"]
    original_reference = owner.reference_composer
    original_guide = owner.totalized_guide
    original_residual = owner.totalized_residual
    equivalent_reference = ProcessValidReferenceJumpComposer(bundle["process"])
    equivalent_guide = certify_totalized_association_jump_guide(
        original_guide.preconditioner,
        original_guide.range_gate,
        original_guide.range_certificate,
        observation=original_guide.outcome,
    )
    equivalent_residual = (
        totalized_residual.certify_totalized_conditional_jump_residual(
            original_residual.model,
            original_residual.checkpoint,
            expected_provenance=original_residual.provenance,
        )
    )

    for live_field, identity_field, substitute, original in (
        (
            "_reference_composer",
            "_reference_composer_identity",
            equivalent_reference,
            original_reference,
        ),
        ("_guide", "_guide_identity", equivalent_guide, original_guide),
        (
            "_residual",
            "_residual_identity",
            equivalent_residual,
            original_residual,
        ),
    ):
        try:
            object.__setattr__(owner, live_field, substitute)
            object.__setattr__(owner, identity_field, substitute)
            with pytest.raises(ValueError, match="identity|runtime|live state"):
                _evaluate(bundle, ())
        finally:
            object.__setattr__(owner, live_field, original)
            object.__setattr__(owner, identity_field, original)


def test_horizon_tampering_is_refused_and_restored(bundle):
    schedule = bundle["process"].schedule
    original_grid = schedule.time_grid
    altered_grid = np.array(original_grid, dtype=np.float64, copy=True)
    altered_grid[-1] = math.nextafter(float(altered_grid[-1]), math.inf)
    altered_grid.setflags(write=False)
    try:
        object.__setattr__(schedule, "time_grid", altered_grid)
        with pytest.raises(
            (ValueError, RuntimeError), match="process|parameter|horizon|live|binding"
        ):
            _evaluate(bundle, ())
    finally:
        object.__setattr__(schedule, "time_grid", original_grid)


def test_standalone_redigested_residual_branch_and_bound_tampering_refused(bundle):
    owner = bundle["initial_tilt"]
    record = _evaluate(bundle, ())

    for update in (
        {"residual_branch": (totalized_residual.EXACT_GATE_RESCALED_CORE_BRANCH)},
        {
            "residual_operational_point_magnitude_bound": math.nextafter(
                record.residual_operational_point_magnitude_bound,
                -math.inf,
            )
        },
    ):
        values = {
            name: update.get(name, getattr(record, name))
            for name in initial_tilt.InitialTiltPointEvaluation.__annotations__
        }
        values["evaluation_sha256"] = initial_tilt._semantic_digest(
            initial_tilt._evaluation_payload(values)
        )
        forged = _forged_record(record, **values)
        with pytest.raises(
            ValueError, match="residual branch|residual bound|preserved branch"
        ):
            owner.validate_evaluation(forged, (), residual_context=_RESIDUAL_CONTEXT)


def test_guide_state_exact_equality_is_checked_beyond_digest(bundle, monkeypatch):
    owner = bundle["initial_tilt"]
    original_evaluate = TotalizedAssociationJumpGuide.evaluate
    alternate = (TransformedEvent(1),)

    def alternate_state(self, reverse_time, state):
        del state
        return original_evaluate(self, reverse_time, alternate)

    def trust_nested_record(self, evaluation):
        del self
        return evaluation

    monkeypatch.setattr(TotalizedAssociationJumpGuide, "evaluate", alternate_state)
    monkeypatch.setattr(
        TotalizedAssociationJumpGuide,
        "validate_evaluation",
        trust_nested_record,
    )
    monkeypatch.setattr(initial_tilt, "_configuration_sha256", lambda state: "a" * 64)

    with pytest.raises(
        ValueError,
        match="state differs|canonical configuration|state value differs",
    ):
        owner.evaluate((), residual_context=_RESIDUAL_CONTEXT)


def _assert_fallback_point_record(bundle, record, branch):
    exact = Fraction.from_float(
        record.guide_operational_log_density
    ) + Fraction.from_float(record.residual_operational_value)
    assert record.guide_branch == branch
    assert _fraction(record, "exact_initial_log_factor") == exact
    assert record.initial_log_factor.hex() == float(exact).hex()
    assert Fraction.from_float(record.initial_log_factor_lower_bound) <= exact
    assert exact <= Fraction.from_float(record.initial_log_factor_upper_bound)
    assert (
        bundle["initial_tilt"].validate_evaluation(
            record, (), residual_context=_RESIDUAL_CONTEXT
        )
        is record
    )


def test_typed_guide_numerical_fallback_at_initial_endpoint_composes_and_replays(
    bundle, monkeypatch
):
    def typed_failure(*args, **kwargs):
        del args, kwargs
        raise AssociationPreconditionerNumericalError("typed point failure")

    monkeypatch.setattr(AnalyticAssociationPreconditioner, "evaluate", typed_failure)
    record = _evaluate(bundle, ())
    _assert_fallback_point_record(bundle, record, NUMERICAL_FALLBACK_BRANCH)


def test_typed_guide_range_fallback_at_initial_endpoint_composes_and_replays(
    bundle, monkeypatch
):
    def typed_failure(*args, **kwargs):
        del args, kwargs
        raise AssociationGuideOperationalError("typed range failure")

    monkeypatch.setattr(
        RangeGatedAssociationGuide,
        "_validate_raw_evaluation",
        typed_failure,
    )
    record = _evaluate(bundle, ())
    _assert_fallback_point_record(bundle, record, RANGE_FALLBACK_BRANCH)


def test_untyped_guide_failure_at_initial_endpoint_propagates(bundle, monkeypatch):
    def untyped_failure(*args, **kwargs):
        del args, kwargs
        raise ArithmeticError("untyped guide failure")

    monkeypatch.setattr(AnalyticAssociationPreconditioner, "evaluate", untyped_failure)
    with pytest.raises(ArithmeticError, match="untyped guide failure"):
        _evaluate(bundle, ())


def test_midcall_twin_slot_guide_owner_swap_is_refused(bundle, monkeypatch):
    owner = bundle["initial_tilt"]
    original_guide = owner.totalized_guide
    equivalent_guide = certify_totalized_association_jump_guide(
        original_guide.preconditioner,
        original_guide.range_gate,
        original_guide.range_certificate,
        observation=original_guide.outcome,
    )
    original_evaluate = TotalizedAssociationJumpGuide.evaluate

    def evaluate_then_swap(self, reverse_time, state):
        record = original_evaluate(self, reverse_time, state)
        object.__setattr__(owner, "_guide", equivalent_guide)
        object.__setattr__(owner, "_guide_identity", equivalent_guide)
        return record

    monkeypatch.setattr(TotalizedAssociationJumpGuide, "evaluate", evaluate_then_swap)
    try:
        with pytest.raises(
            (ValueError, initial_tilt.ConfigurationInitialTiltError),
            match="changed|identity|owner|guide",
        ):
            _evaluate(bundle, ())
    finally:
        object.__setattr__(owner, "_guide", original_guide)
        object.__setattr__(owner, "_guide_identity", original_guide)


def test_midcall_twin_slot_reference_owner_swap_is_refused(bundle, monkeypatch):
    owner = bundle["initial_tilt"]
    original_reference = owner.reference_composer
    equivalent_reference = ProcessValidReferenceJumpComposer(bundle["process"])
    original_guide_evaluate = TotalizedAssociationJumpGuide.evaluate

    def evaluate_then_swap_reference(self, reverse_time, state):
        record = original_guide_evaluate(self, reverse_time, state)
        object.__setattr__(owner, "_reference_composer", equivalent_reference)
        object.__setattr__(owner, "_reference_composer_identity", equivalent_reference)
        return record

    monkeypatch.setattr(
        TotalizedAssociationJumpGuide,
        "evaluate",
        evaluate_then_swap_reference,
    )
    try:
        with pytest.raises(
            (ValueError, initial_tilt.ConfigurationInitialTiltError),
            match="changed|identity|owner|reference",
        ):
            _evaluate(bundle, ())
    finally:
        object.__setattr__(owner, "_reference_composer", original_reference)
        object.__setattr__(owner, "_reference_composer_identity", original_reference)


def test_midcall_twin_slot_residual_owner_swap_is_refused(bundle, monkeypatch):
    owner = bundle["initial_tilt"]
    original_residual = owner.totalized_residual
    equivalent_residual = (
        totalized_residual.certify_totalized_conditional_jump_residual(
            original_residual.model,
            original_residual.checkpoint,
            expected_provenance=original_residual.provenance,
        )
    )
    original_evaluate = totalized_residual.TotalizedConditionalJumpResidual.evaluate

    def evaluate_then_swap(self, batch):
        record = original_evaluate(self, batch)
        object.__setattr__(owner, "_residual", equivalent_residual)
        object.__setattr__(owner, "_residual_identity", equivalent_residual)
        return record

    monkeypatch.setattr(
        totalized_residual.TotalizedConditionalJumpResidual,
        "evaluate",
        evaluate_then_swap,
    )
    try:
        with pytest.raises(
            (ValueError, initial_tilt.ConfigurationInitialTiltError),
            match="changed|identity|owner|residual|different",
        ):
            _evaluate(bundle, ())
    finally:
        object.__setattr__(owner, "_residual", original_residual)
        object.__setattr__(owner, "_residual_identity", original_residual)


def test_configuration_tensor_adapter_groups_many_types_in_one_pass():
    type_count = 128

    class Architecture:
        type_ids = tuple(range(type_count))
        type_dimensions = (0,) * type_count

    events = tuple(
        event
        for event_type in range(type_count)
        for event in (
            TransformedEvent(event_type),
            TransformedEvent(event_type),
        )
    )

    class CountingIterable:
        def __init__(self, values):
            self.values = values
            self.iteration_count = 0

        def __iter__(self):
            self.iteration_count += 1
            if self.iteration_count > 1:
                raise AssertionError("configuration was rescanned")
            return iter(self.values)

    configuration = CountingIterable(events)
    coordinates, owners = initial_tilt._configuration_tensor_maps(
        Architecture(), configuration
    )

    assert configuration.iteration_count == 1
    assert tuple(coordinates) == tuple(range(type_count))
    assert tuple(owners) == tuple(range(type_count))
    for event_type in range(type_count):
        assert tuple(coordinates[event_type].shape) == (2, 0)
        assert coordinates[event_type].dtype is torch.float64
        assert tuple(owners[event_type].shape) == (2,)
        assert owners[event_type].dtype is torch.int64
        assert torch.equal(owners[event_type], torch.zeros(2, dtype=torch.int64))


def test_optional_torch_import_failure_is_actionable():
    project_root = Path(__file__).resolve().parents[2]
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(project_root / "src")
    missing = subprocess.run(
        [
            sys.executable,
            "-c",
            "import builtins\n"
            "original = builtins.__import__\n"
            "def blocked(name, *args, **kwargs):\n"
            "    if name == 'torch' or name.startswith('torch.'):\n"
            "        raise ModuleNotFoundError('blocked torch', name='torch')\n"
            "    return original(name, *args, **kwargs)\n"
            "builtins.__import__ = blocked\n"
            "try:\n"
            "    import heterodiff.models.configuration_initial_tilt_composer_torch\n"
            "except ModuleNotFoundError as error:\n"
            "    message = str(error)\n"
            "    assert 'initial' in message and 'tilt' in message\n"
            "    assert 'optional PyTorch' in message\n"
            "else:\n"
            "    raise AssertionError('optional import unexpectedly succeeded')\n",
        ],
        cwd=str(project_root),
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert missing.returncode == 0, missing.stderr
