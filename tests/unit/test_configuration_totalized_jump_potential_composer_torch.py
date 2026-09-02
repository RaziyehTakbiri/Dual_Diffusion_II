"""Hostile tests for checkpoint-17 totalized jump-potential composition."""

from fractions import Fraction
import copy
import hashlib
import inspect
import math
import os
from pathlib import Path
import pickle
import subprocess
import sys

import numpy as np
import pytest


torch = pytest.importorskip(
    "torch", reason="totalized jump-potential composition requires PyTorch"
)

import heterodiff.models.configuration_residual_torch as residual  # noqa: E402
from heterodiff.models import (  # noqa: E402
    configuration_totalized_jump_potential_composer_torch as potential,
)
from heterodiff.models import (  # noqa: E402
    configuration_totalized_jump_residual_torch as totalized_residual,
)
from heterodiff.models.configuration_energy_torch import (  # noqa: E402
    BoundedConfigurationEnergy,
    ConfigurationEnergyCertificateError,
    ConfigurationEnergyArchitecture,
    ConfigurationEnergyProvenance,
    SpectralNormCeilings,
    certify_configuration_energy,
)
from heterodiff.processes.plugin_bridge_sampler import (  # noqa: E402
    ProcessValidReferenceJumpComposer,
)
from heterodiff.processes.reversible_hybrid_reference import (  # noqa: E402
    HybridJumpKind,
    PiecewiseConstantHybridSchedule,
    ReversibleHybridRates,
    ReversibleHybridReference,
)
from heterodiff.theory.association_observation import (  # noqa: E402
    CollapsedPoissonObservationReference,
    TypedAffineGaussianObservationChannel,
    TypedGaussianClutterIntensity,
)
from heterodiff.theory.association_operational_guide import (  # noqa: E402
    certify_range_gated_association_guide,
)
from heterodiff.theory.association_preconditioner import (  # noqa: E402
    AnalyticAssociationPreconditioner,
)
from heterodiff.theory.association_totalized_jump_guide import (  # noqa: E402
    NUMERICAL_FALLBACK_BRANCH,
    TotalizedAssociationJumpGuide,
    certify_totalized_association_jump_guide,
)
from heterodiff.theory.configuration_reference import (  # noqa: E402
    CappedPoissonConfigurationReference,
    TransformedEvent,
)


_CHECKPOINT14_SOURCE_SHA256 = (
    "2b1d60e4da640edb0e5be5bcfe90012d9b08a1f48af56f8240dcbdb1d4abe0cf"
)


def _process(*, activity=1.4):
    reference = CappedPoissonConfigurationReference(
        {0: 0, 1: 0},
        {0: 0.4, 1: 0.6},
        activity=activity,
        total_cap=2,
    )
    schedule = PiecewiseConstantHybridSchedule(
        (0.0, 0.5, 1.0),
        (0.0, 0.8),
        (0.0, 1.1),
        clean_hold=0.5,
    )
    rates = ReversibleHybridRates(
        reference,
        per_particle_death_rate=0.45,
        replacement_fluxes={(0, 1): 0.05},
    )
    return ReversibleHybridReference(reference, schedule, rates)


def _architecture(process, *, schema, value_bound):
    return ConfigurationEnergyArchitecture.from_process(
        process,
        coordinate_scales_by_type={0: (), 1: ()},
        context_dimension=1,
        context_scales=(1.0,),
        context_schema_sha256=schema,
        event_hidden_width=3,
        event_embedding_width=2,
        context_hidden_width=3,
        context_embedding_width=2,
        readout_hidden_width=4,
        value_bound=value_bound,
        spectral_ceilings=SpectralNormCeilings(*(100.0,) * 7),
        bias_ceiling=100.0,
        first_derivative_ceiling=1_000_000.0,
        second_derivative_ceiling=1_000_000.0,
    )


def _model(architecture, seed):
    generator = torch.Generator(device="cpu")
    generator.manual_seed(seed)
    return BoundedConfigurationEnergy(architecture, generator=generator)


def _guide(process):
    observation_reference = CollapsedPoissonObservationReference(
        {10: 0, 11: 0},
        {10: 0.35, 11: 0.65},
        retained_cap=2,
    )
    channel = TypedAffineGaussianObservationChannel(
        {0: 0, 1: 0},
        observation_reference,
        ((0.75, 0.25), (0.2, 0.8)),
    )
    clutter = TypedGaussianClutterIntensity(
        observation_reference,
        0.3,
        (0.45, 0.55),
    )
    preconditioner = AnalyticAssociationPreconditioner(
        process,
        observation_reference,
        channel,
        clutter,
        {0: 0.3, 1: 0.7},
        contamination_probability=0.1,
        context_key=("checkpoint-17",),
    )
    outcome = (TransformedEvent(10),)
    analytic = preconditioner.certify_guide_range(outcome)
    range_gate = certify_range_gated_association_guide(
        preconditioner,
        analytic,
        observation=outcome,
    )
    owner = certify_totalized_association_jump_guide(
        preconditioner,
        range_gate,
        analytic,
        observation=outcome,
    )
    return analytic, range_gate, owner


def _bundle():
    process = _process()
    reference_composer = ProcessValidReferenceJumpComposer(process)
    base_architecture = _architecture(process, schema="c" * 64, value_bound=2.0)
    residual_architecture = _architecture(process, schema="f" * 64, value_bound=1.5)
    base_model = _model(base_architecture, 1701)
    residual_model = _model(residual_architecture, 1702)
    base_provenance = ConfigurationEnergyProvenance(
        method_freeze_sha256="1" * 64,
        training_run_sha256="2" * 64,
        data_manifest_sha256="3" * 64,
        selection_rule_sha256="4" * 64,
    )
    base_checkpoint = certify_configuration_energy(
        base_model, provenance=base_provenance
    )
    residual_provenance = residual.ConditionalResidualProvenance(
        method_freeze_sha256="5" * 64,
        training_run_sha256="6" * 64,
        data_manifest_sha256="7" * 64,
        selection_rule_sha256="8" * 64,
        observation_schema_sha256="a" * 64,
        task_schema_sha256="b" * 64,
        conditioning_adapter_sha256="d" * 64,
        residual_role_sha256="e" * 64,
    )
    contract = residual.make_conditional_residual_contract(
        residual_architecture,
        observation_schema_sha256="a" * 64,
        task_schema_sha256="b" * 64,
        conditioning_adapter_sha256="d" * 64,
        residual_role_sha256="e" * 64,
    )
    residual_checkpoint = residual.certify_conditional_residual(
        residual_model,
        contract,
        provenance=residual_provenance,
    )
    totalized_residual_owner = (
        totalized_residual.certify_totalized_conditional_jump_residual(
            residual_model,
            residual_checkpoint,
            expected_provenance=residual_provenance,
        )
    )
    analytic, range_gate, totalized_guide = _guide(process)
    composer = potential.certify_totalized_configuration_jump_potential_composer(
        reference_composer,
        base_model=base_model,
        base_checkpoint=base_checkpoint,
        base_provenance=base_provenance,
        totalized_guide=totalized_guide,
        totalized_residual=totalized_residual_owner,
        target_policy=potential.CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_TARGET_POLICY,
        composition_role_sha256="9" * 64,
    )
    return {
        "process": process,
        "reference_composer": reference_composer,
        "base_model": base_model,
        "base_checkpoint": base_checkpoint,
        "base_provenance": base_provenance,
        "analytic": analytic,
        "range_gate": range_gate,
        "totalized_guide": totalized_guide,
        "residual_model": residual_model,
        "residual_checkpoint": residual_checkpoint,
        "residual_provenance": residual_provenance,
        "totalized_residual": totalized_residual_owner,
        "composer": composer,
    }


@pytest.fixture(scope="module")
def bundle():
    return _bundle()


def _candidate_of_kind(reference_composer, kind, *, reverse_time=0.4):
    state = (TransformedEvent(0),)
    for seed in range(10_000):
        candidate = reference_composer.sample_candidate(
            state,
            reverse_time=reverse_time,
            rng=np.random.default_rng(seed),
        )
        assert candidate is not None
        if candidate.kind is kind:
            return candidate
    raise AssertionError("failed to draw requested candidate kind")


def _candidate_between(
    reference_composer,
    source,
    destination,
    *,
    reverse_time=0.4,
):
    for seed in range(10_000):
        candidate = reference_composer.sample_candidate(
            source,
            reverse_time=reverse_time,
            rng=np.random.default_rng(seed),
        )
        assert candidate is not None
        if candidate.destination_configuration == destination:
            return candidate
    raise AssertionError("failed to draw requested directed candidate")


def _evaluate(bundle, candidate, *, base_context=(0.25,), residual_context=(-0.4,)):
    return bundle["composer"].evaluate(
        candidate,
        base_context=base_context,
        residual_context=residual_context,
    )


def _fraction(record, prefix):
    return Fraction(
        getattr(record, "%s_numerator" % prefix),
        getattr(record, "%s_denominator" % prefix),
    )


def _forged_evaluation(record, **updates):
    forged = object.__new__(potential.TotalizedJumpPotentialCandidateEvaluation)
    for name in potential.TotalizedJumpPotentialCandidateEvaluation.__annotations__:
        object.__setattr__(forged, name, updates.get(name, getattr(record, name)))
    return forged


def _forged_certificate(certificate, **updates):
    annotations = potential.TotalizedJumpPotentialCompositionCertificate.__annotations__
    values = {
        name: updates.get(name, getattr(certificate, name)) for name in annotations
    }
    values["certificate_sha256"] = potential._semantic_digest(
        potential._certificate_payload(values)
    )
    forged = object.__new__(potential.TotalizedJumpPotentialCompositionCertificate)
    for name, value in values.items():
        object.__setattr__(forged, name, value)
    return forged


def test_target_is_explicit_and_certificate_states_every_material_nonclaim(bundle):
    certificate = bundle["composer"].certificate

    assert certificate.passed is True
    assert certificate.target_policy == (
        potential.CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_TARGET_POLICY
    )
    assert certificate.operational_surrogate_target_selected is True
    assert certificate.exact_operational_endpoint_coboundary is True
    assert certificate.aggregate_rounded_once is True
    assert certificate.component_rounded_edges_used is False
    assert certificate.external_base_live_custody_authenticated is True
    assert certificate.private_base_checkpoint_materialized is True
    assert certificate.checkpoint14_combined_bits_preserved is False
    for name in (
        "exact_analytic_target_preserved",
        "exact_conditional_or_posterior_target",
        "aggregate_analytic_target_discrepancy_certified",
        "small_forward_error_certified",
        "rounded_edge_cycle_closure_certified",
        "full_composer_totality_certified",
        "rate_space_envelope_certified",
        "controlled_total_exit_certified",
        "waiting_time_admissible",
        "acceptance_decision_admissible",
        "coordinate_derivatives_admissible",
        "continuous_drift_admissible",
        "randomness_admissible",
        "initializer_admissible",
        "path_admissible",
        "operational_sampler_admissible",
    ):
        assert getattr(certificate, name) is False

    with pytest.raises(ValueError, match="operational-surrogate|supported"):
        potential.certify_totalized_configuration_jump_potential_composer(
            bundle["reference_composer"],
            base_model=bundle["base_model"],
            base_checkpoint=bundle["base_checkpoint"],
            base_provenance=bundle["base_provenance"],
            totalized_guide=bundle["totalized_guide"],
            totalized_residual=bundle["totalized_residual"],
            target_policy="analytic-posterior-target",
            composition_role_sha256="9" * 64,
        )


@pytest.mark.parametrize(
    "kind",
    (HybridJumpKind.BIRTH, HybridJumpKind.DEATH, HybridJumpKind.REPLACEMENT),
)
def test_all_edit_families_match_an_independent_exact_fraction_oracle(bundle, kind):
    candidate = _candidate_of_kind(bundle["reference_composer"], kind)
    result = _evaluate(bundle, candidate)

    exact_source = sum(
        (
            Fraction.from_float(result.base_source_operational_energy),
            Fraction.from_float(result.guide_source_operational_log_density),
            Fraction.from_float(result.residual_source_operational_value),
        ),
        Fraction(0),
    )
    exact_destination = sum(
        (
            Fraction.from_float(result.base_destination_operational_energy),
            Fraction.from_float(result.guide_destination_operational_log_density),
            Fraction.from_float(result.residual_destination_operational_value),
        ),
        Fraction(0),
    )
    exact_edge = exact_destination - exact_source
    exact_components = sum(
        (
            _fraction(result, "base_exact_endpoint_difference"),
            _fraction(result, "guide_exact_endpoint_difference"),
            _fraction(result, "residual_exact_endpoint_difference"),
        ),
        Fraction(0),
    )
    rounded = 0.0 if exact_edge == 0 else float(exact_edge)

    assert result.edit_kind == kind.value
    assert result.reverse_time.hex() == candidate.reverse_time.hex()
    assert result.direct_time.hex() == candidate.direct_time.hex()
    assert _fraction(result, "exact_source_target_value") == exact_source
    assert _fraction(result, "exact_destination_target_value") == exact_destination
    assert _fraction(result, "exact_operational_endpoint_difference") == exact_edge
    assert exact_components == exact_edge
    assert result.combined_log_increment.hex() == rounded.hex()
    assert _fraction(result, "exact_rounding_error") == abs(
        Fraction.from_float(rounded) - exact_edge
    )
    assert abs(result.combined_log_increment) <= result.aggregate_edge_magnitude_bound
    assert result.exact_operational_coboundary
    assert not result.rounded_edge_cycle_closure_certified
    assert not result.exact_conditional_or_posterior_target
    assert not result.operational_sampler_admissible


def test_exact_endpoint_composition_reverses_and_telescopes_on_a_cycle(bundle):
    empty = ()
    type_zero = (TransformedEvent(0),)
    type_one = (TransformedEvent(1),)
    directed_cycle = (
        _candidate_between(bundle["reference_composer"], type_zero, empty),
        _candidate_between(bundle["reference_composer"], empty, type_one),
        _candidate_between(bundle["reference_composer"], type_one, type_zero),
    )
    records = tuple(_evaluate(bundle, candidate) for candidate in directed_cycle)
    exact_edges = tuple(
        _fraction(record, "exact_operational_endpoint_difference") for record in records
    )

    assert sum(exact_edges, Fraction(0)) == 0
    assert _fraction(records[0], "exact_destination_target_value") == _fraction(
        records[1], "exact_source_target_value"
    )
    assert _fraction(records[1], "exact_destination_target_value") == _fraction(
        records[2], "exact_source_target_value"
    )
    assert _fraction(records[2], "exact_destination_target_value") == _fraction(
        records[0], "exact_source_target_value"
    )

    reverse = _candidate_between(bundle["reference_composer"], empty, type_zero)
    reverse_record = _evaluate(bundle, reverse)
    assert (
        _fraction(reverse_record, "exact_operational_endpoint_difference")
        == -exact_edges[0]
    )


def test_one_ulp_active_time_totalizes_guide_and_binds_residual_totalizer(bundle):
    reverse_time = math.nextafter(math.nextafter(0.5, -math.inf), -math.inf)
    candidate = _candidate_of_kind(
        bundle["reference_composer"],
        HybridJumpKind.REPLACEMENT,
        reverse_time=reverse_time,
    )
    result = _evaluate(bundle, candidate)

    assert result.direct_time > bundle["process"].schedule.clean_hold
    assert result.guide_fallback_used is True
    assert NUMERICAL_FALLBACK_BRANCH in (
        result.guide_source_branch,
        result.guide_destination_branch,
    )
    # A process-valid reverse-time float cannot resolve a direct-time gap small
    # enough to put this cubic residual gate below binary64's normal range.
    # The certified residual totalizer is nevertheless bound transitively.
    assert result.residual_fallback_used is False
    assert totalized_residual.PRESERVED_CERTIFIED_RESIDUAL_BRANCH in (
        result.residual_source_branch,
        result.residual_destination_branch,
    )
    assert bundle["totalized_residual"].certificate.tiny_gate_exact_rescaling
    assert result.certificate.residual_totalized_certificate_sha256 == (
        bundle["totalized_residual"].certificate.certificate_sha256
    )
    exact = _fraction(result, "exact_operational_endpoint_difference")
    assert result.combined_log_increment.hex() == float(exact).hex()


def test_replay_is_deterministic_and_records_are_sealed_against_tampering(bundle):
    candidate = _candidate_of_kind(
        bundle["reference_composer"], HybridJumpKind.REPLACEMENT
    )
    result = _evaluate(bundle, candidate)
    repeated = _evaluate(bundle, candidate)

    assert repeated.evaluation_sha256 == result.evaluation_sha256
    assert repeated.combined_log_increment.hex() == result.combined_log_increment.hex()
    assert bundle["composer"].validate_evaluation(result, candidate) is result
    assert (
        potential.require_matching_totalized_configuration_jump_potential_composer(
            bundle["reference_composer"],
            bundle["composer"],
            base_model=bundle["base_model"],
            base_checkpoint=bundle["base_checkpoint"],
            base_provenance=bundle["base_provenance"],
            totalized_guide=bundle["totalized_guide"],
            totalized_residual=bundle["totalized_residual"],
            target_policy=(
                potential.CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_TARGET_POLICY
            ),
            composition_role_sha256="9" * 64,
        )
        is bundle["composer"]
    )
    with pytest.raises((AttributeError, TypeError)):
        result.combined_log_increment = 0.0
    with pytest.raises(TypeError):
        pickle.dumps(result)
    with pytest.raises((AttributeError, TypeError)):
        bundle["composer"]._certificate = result.certificate

    forged = _forged_evaluation(result, combined_log_increment=0.0)
    with pytest.raises(ValueError, match="digest|inconsistent"):
        bundle["composer"].validate_evaluation(forged, candidate)

    values = {
        name: getattr(result, name)
        for name in potential.TotalizedJumpPotentialCandidateEvaluation.__annotations__
    }
    values["reference_schedule_rate"] = math.nextafter(
        result.reference_schedule_rate, math.inf
    )
    values["evaluation_sha256"] = potential._semantic_digest(
        potential._evaluation_payload(values)
    )
    redigested = _forged_evaluation(result, **values)
    with pytest.raises(ValueError, match="reference_schedule_rate|replay"):
        bundle["composer"].validate_evaluation(redigested, candidate)

    other = _candidate_of_kind(bundle["reference_composer"], HybridJumpKind.BIRTH)
    with pytest.raises(ValueError, match="candidate"):
        bundle["composer"].validate_evaluation(result, other)


def test_semantically_redigested_composition_role_tamper_is_refused(bundle):
    candidate = _candidate_of_kind(bundle["reference_composer"], HybridJumpKind.DEATH)
    composer = bundle["composer"]
    original = composer.certificate
    forged = _forged_certificate(
        original,
        composition_role_sha256="a" * 64,
    )
    potential._validate_certificate(forged)

    try:
        object.__setattr__(composer, "_certificate", forged)
        with pytest.raises(ValueError, match="composition_role_sha256|live state"):
            _evaluate(bundle, candidate)
    finally:
        object.__setattr__(composer, "_certificate", original)

    assert math.isfinite(_evaluate(bundle, candidate).combined_log_increment)


def test_time_context_and_process_identity_are_bound_and_replayed(bundle):
    candidate = _candidate_of_kind(bundle["reference_composer"], HybridJumpKind.DEATH)
    first = _evaluate(bundle, candidate)
    changed = _evaluate(
        bundle,
        candidate,
        base_context=(0.125,),
        residual_context=(0.75,),
    )

    assert first.reverse_time == 0.4
    assert first.direct_time == 0.6
    assert first.base_context_sha256 != changed.base_context_sha256
    assert first.residual_context_sha256 != changed.residual_context_sha256
    assert first.evaluation_sha256 != changed.evaluation_sha256
    with pytest.raises(ValueError, match="exactly 1 entries"):
        _evaluate(bundle, candidate, base_context=())
    with pytest.raises(ValueError, match="canonical positive zero"):
        _evaluate(bundle, candidate, residual_context=(-0.0,))

    foreign = ProcessValidReferenceJumpComposer(_process(activity=1.7))
    foreign_candidate = _candidate_of_kind(foreign, HybridJumpKind.DEATH)
    with pytest.raises(ValueError, match="process|parameter|candidate"):
        _evaluate(bundle, foreign_candidate)


@pytest.mark.parametrize("distinct_alias", (False, True))
def test_base_and_residual_model_storage_overlap_is_refused(bundle, distinct_alias):
    if distinct_alias:
        base_model = copy.deepcopy(bundle["residual_model"])
        with torch.no_grad():
            for base_parameter, residual_parameter in zip(
                base_model.parameters(), bundle["residual_model"].parameters()
            ):
                base_parameter.set_(residual_parameter)
        assert base_model is not bundle["residual_model"]
    else:
        base_model = bundle["residual_model"]
    base_checkpoint = certify_configuration_energy(
        base_model, provenance=bundle["base_provenance"]
    )

    with pytest.raises(ValueError, match="storage|overlap|disjoint|share|distinct"):
        potential.certify_totalized_configuration_jump_potential_composer(
            bundle["reference_composer"],
            base_model=base_model,
            base_checkpoint=base_checkpoint,
            base_provenance=bundle["base_provenance"],
            totalized_guide=bundle["totalized_guide"],
            totalized_residual=bundle["totalized_residual"],
            target_policy=(
                potential.CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_TARGET_POLICY
            ),
            composition_role_sha256="9" * 64,
        )


def test_live_external_base_custody_is_rechecked_before_evaluation(bundle):
    candidate = _candidate_of_kind(bundle["reference_composer"], HybridJumpKind.BIRTH)
    parameter = bundle["base_model"].readout.linear3.bias
    saved = parameter.detach().clone()
    try:
        with torch.no_grad():
            parameter.add_(1.0)
        with pytest.raises(ConfigurationEnergyCertificateError, match="live model"):
            _evaluate(bundle, candidate)
    finally:
        with torch.no_grad():
            parameter.copy_(saved)

    assert math.isfinite(_evaluate(bundle, candidate).combined_log_increment)


def test_private_base_tamper_is_refused_and_does_not_corrupt_external_custody(bundle):
    candidate = _candidate_of_kind(bundle["reference_composer"], HybridJumpKind.BIRTH)
    private_model = bundle["composer"]._base_evaluation_model
    parameter = private_model.readout.linear3.bias
    saved = parameter.detach().clone()
    try:
        with torch.no_grad():
            parameter.add_(0.5)
        with pytest.raises(ConfigurationEnergyCertificateError, match="live model"):
            _evaluate(bundle, candidate)
    finally:
        with torch.no_grad():
            parameter.copy_(saved)

    assert math.isfinite(_evaluate(bundle, candidate).combined_log_increment)


def test_foreign_guide_endpoint_and_midflight_candidate_mutation_fail_closed(
    bundle, monkeypatch
):
    candidate = _candidate_of_kind(
        bundle["reference_composer"], HybridJumpKind.REPLACEMENT
    )
    original_edit = TotalizedAssociationJumpGuide.edit_log_ratio

    def foreign_edit(self, reverse_time, source, destination):
        del source, destination
        return original_edit(self, reverse_time, (), (TransformedEvent(0),))

    monkeypatch.setattr(TotalizedAssociationJumpGuide, "edit_log_ratio", foreign_edit)
    with pytest.raises(ValueError, match="guide edit kind|endpoints"):
        _evaluate(bundle, candidate)

    monkeypatch.undo()
    original_difference = (
        totalized_residual.TotalizedConditionalJumpResidual.state_pair_difference
    )

    def mutate_candidate(self, source, destination):
        result = original_difference(self, source, destination)
        object.__setattr__(
            candidate,
            "direct_time",
            math.nextafter(candidate.direct_time, math.inf),
        )
        return result

    monkeypatch.setattr(
        totalized_residual.TotalizedConditionalJumpResidual,
        "state_pair_difference",
        mutate_candidate,
    )
    with pytest.raises(ValueError, match="candidate|direct|representation"):
        _evaluate(bundle, candidate)


def test_cross_composer_certificate_identity_is_not_interchangeable(bundle):
    other = potential.certify_totalized_configuration_jump_potential_composer(
        bundle["reference_composer"],
        base_model=bundle["base_model"],
        base_checkpoint=bundle["base_checkpoint"],
        base_provenance=bundle["base_provenance"],
        totalized_guide=bundle["totalized_guide"],
        totalized_residual=bundle["totalized_residual"],
        target_policy=potential.CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_TARGET_POLICY,
        composition_role_sha256="9" * 64,
    )
    candidate = _candidate_of_kind(bundle["reference_composer"], HybridJumpKind.DEATH)
    result = _evaluate(bundle, candidate)

    assert other.certificate.certificate_sha256 == result.certificate_sha256
    assert other.certificate is not result.certificate
    with pytest.raises(ValueError, match="different composer certificate"):
        other.validate_evaluation(result, candidate)


def test_public_surface_has_no_rate_clock_rng_drift_path_or_sampler_api(bundle):
    composer = bundle["composer"]
    parameters = inspect.signature(composer.evaluate).parameters
    assert "rng" not in parameters
    assert "seed" not in parameters
    assert all(
        parameter.kind is not inspect.Parameter.VAR_KEYWORD
        for parameter in parameters.values()
    )
    for name in (
        "exponentiate",
        "jump_rate",
        "rate_envelope",
        "total_exit_rate",
        "waiting_time",
        "operational_clock",
        "accept",
        "rng",
        "coordinate_gradients",
        "continuous_drift",
        "initializer",
        "path",
        "sample",
    ):
        assert not hasattr(composer, name)
        assert name not in potential.__all__


def test_checkpoint17_module_keeps_checkpoint14_source_and_api_isolated():
    project_root = Path(__file__).resolve().parents[2]
    legacy_path = (
        project_root
        / "src"
        / "heterodiff"
        / "models"
        / "configuration_potential_composer_torch.py"
    )
    assert hashlib.sha256(legacy_path.read_bytes()).hexdigest() == (
        _CHECKPOINT14_SOURCE_SHA256
    )

    from heterodiff.models import configuration_potential_composer_torch as legacy

    signature = inspect.signature(legacy.certify_configuration_potential_composer)
    assert "totalized_guide" not in signature.parameters
    assert "totalized_residual" not in signature.parameters
    assert not hasattr(legacy, "TotalizedConfigurationJumpPotentialComposer")


def test_explicit_module_missing_torch_error_is_actionable():
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
            "    import heterodiff.models."
            "configuration_totalized_jump_potential_composer_torch\n"
            "except ModuleNotFoundError as error:\n"
            "    message = str(error)\n"
            "    assert 'jump-potential composition' in message\n"
            "    assert 'optional PyTorch reference dependency' in message\n"
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
