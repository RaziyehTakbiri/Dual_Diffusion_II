"""Hostile tests for checkpoint-22 bounded-loop route evidence."""

import ast
import inspect
import math
from pathlib import Path
import pickle
import subprocess
import sys

import numpy as np
import pytest


torch = pytest.importorskip(
    "torch", reason="loop route evidence requires the PyTorch reference stack"
)

import heterodiff.models.configuration_residual_torch as residual  # noqa: E402
from heterodiff.models import (  # noqa: E402
    configuration_totalized_jump_potential_composer_torch as potential,
)
from heterodiff.models import (  # noqa: E402
    configuration_totalized_jump_rate_envelope_torch as rate,
)
from heterodiff.models import (  # noqa: E402
    configuration_totalized_jump_residual_torch as totalized_residual,
)
from heterodiff.models.configuration_energy_torch import (  # noqa: E402
    BoundedConfigurationEnergy,
    ConfigurationEnergyArchitecture,
    ConfigurationEnergyProvenance,
    SpectralNormCeilings,
    certify_configuration_energy,
)
from heterodiff.processes import (  # noqa: E402
    plugin_bridge_continuous_route_evidence as route_evidence,
)
from heterodiff.processes import (  # noqa: E402
    plugin_bridge_operational_thinning as thinning,
)
from heterodiff.processes import (  # noqa: E402
    plugin_bridge_operational_thinning_loop as loop,
)
from heterodiff.processes import (  # noqa: E402
    plugin_bridge_operational_thinning_loop_route_evidence as integration,
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
    certify_totalized_association_jump_guide,
)
from heterodiff.theory.configuration_reference import (  # noqa: E402
    CappedPoissonConfigurationReference,
    TransformedEvent,
)


TYPE_DIMENSIONS = {0: 2, 1: 3}
TYPE_WEIGHTS = {0: 0.4, 1: 0.6}
TYPE_SCALES = {0: (1.0, 1.0), 1: (1.0, 1.0, 1.0)}
STATE_2D = (TransformedEvent(0, (0.25, -0.5)),)
_BASE_CONTEXT = (0.25,)
_RESIDUAL_CONTEXT = (-0.4,)
_INTEGRATION_POLICY = (
    integration.PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_ROUTE_EVIDENCE_POLICY
)

_REJECTED_BIRTH_TIME = 0.00011644833447462895
_TIGHT_FIRST_TIME = 1.0931308479787758
_TIGHT_SECOND_TIME = 1.292430759671919


def _process():
    reference = CappedPoissonConfigurationReference(
        TYPE_DIMENSIONS,
        TYPE_WEIGHTS,
        activity=1.4,
        total_cap=1,
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
        replacement_fluxes={(0, 1): 2.0},
    )
    return ReversibleHybridReference(reference, schedule, rates)


def _architecture(process, *, schema, value_bound, tight):
    return ConfigurationEnergyArchitecture.from_process(
        process,
        coordinate_scales_by_type=TYPE_SCALES,
        context_dimension=1,
        context_scales=(1.0,),
        context_schema_sha256=schema,
        event_hidden_width=3,
        event_embedding_width=2,
        context_hidden_width=3,
        context_embedding_width=2,
        readout_hidden_width=4,
        value_bound=(1.0e-9 if tight else value_bound),
        spectral_ceilings=SpectralNormCeilings(*(100.0,) * 7),
        bias_ceiling=100.0,
        first_derivative_ceiling=(1.0e300 if tight else 1.0e6),
        second_derivative_ceiling=(1.0e300 if tight else 1.0e6),
    )


def _model(architecture, seed):
    generator = torch.Generator(device="cpu")
    generator.manual_seed(seed)
    return BoundedConfigurationEnergy(architecture, generator=generator)


def _guide(process, *, tight):
    observation_reference = CollapsedPoissonObservationReference(
        {10: 0, 11: 0},
        {10: 0.35, 11: 0.65},
        retained_cap=1,
    )
    channel = TypedAffineGaussianObservationChannel(
        TYPE_DIMENSIONS,
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
        ({0: 0.0, 1: 0.0} if tight else {0: 0.3, 1: 0.7}),
        contamination_probability=(0.999999 if tight else 0.1),
        context_key=(("checkpoint-22-tight",) if tight else ("checkpoint-22",)),
    )
    outcome = () if tight else (TransformedEvent(10),)
    analytic = preconditioner.certify_guide_range(outcome)
    range_gate = certify_range_gated_association_guide(
        preconditioner,
        analytic,
        observation=outcome,
    )
    return certify_totalized_association_jump_guide(
        preconditioner,
        range_gate,
        analytic,
        observation=outcome,
    )


def _bundle(*, tight=False):
    process = _process()
    reference_composer = ProcessValidReferenceJumpComposer(process)
    base_architecture = _architecture(
        process,
        schema="c" * 64,
        value_bound=2.0,
        tight=tight,
    )
    residual_architecture = _architecture(
        process,
        schema="f" * 64,
        value_bound=1.5,
        tight=tight,
    )
    base_model = _model(base_architecture, 2101)
    residual_model = _model(residual_architecture, 2102)
    base_provenance = ConfigurationEnergyProvenance(
        method_freeze_sha256="1" * 64,
        training_run_sha256="2" * 64,
        data_manifest_sha256="3" * 64,
        selection_rule_sha256="4" * 64,
    )
    base_checkpoint = certify_configuration_energy(
        base_model,
        provenance=base_provenance,
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
    residual_contract = residual.make_conditional_residual_contract(
        residual_architecture,
        observation_schema_sha256="a" * 64,
        task_schema_sha256="b" * 64,
        conditioning_adapter_sha256="d" * 64,
        residual_role_sha256="e" * 64,
    )
    residual_checkpoint = residual.certify_conditional_residual(
        residual_model,
        residual_contract,
        provenance=residual_provenance,
    )
    totalized_residual_owner = (
        totalized_residual.certify_totalized_conditional_jump_residual(
            residual_model,
            residual_checkpoint,
            expected_provenance=residual_provenance,
        )
    )
    potential_composer = (
        potential.certify_totalized_configuration_jump_potential_composer(
            reference_composer,
            base_model=base_model,
            base_checkpoint=base_checkpoint,
            base_provenance=base_provenance,
            totalized_guide=_guide(process, tight=tight),
            totalized_residual=totalized_residual_owner,
            target_policy=(
                potential.CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_TARGET_POLICY
            ),
            composition_role_sha256="9" * 64,
        )
    )
    rate_owner = rate.certify_totalized_configuration_jump_rate_envelope(
        potential_composer,
        rate_policy=rate.CONFIGURATION_TOTALIZED_JUMP_RATE_POLICY,
        rate_role_sha256="0" * 64,
    )
    thinning_owner = thinning.certify_plugin_bridge_operational_thinning(
        rate_owner,
        thinning_policy=thinning.PLUGIN_BRIDGE_OPERATIONAL_THINNING_POLICY,
        thinning_role_sha256="a" * 64,
    )
    loop_owner = loop.certify_plugin_bridge_operational_thinning_loop(
        thinning_owner,
        loop_policy=loop.PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_POLICY,
        loop_role_sha256="b" * 64,
    )
    route_owner = route_evidence.certify_plugin_bridge_continuous_route_evidence(
        thinning_owner,
        evidence_policy=route_evidence.PLUGIN_BRIDGE_CONTINUOUS_ROUTE_EVIDENCE_POLICY,
        evidence_role_sha256="d" * 64,
    )
    integration_owner = (
        integration.certify_plugin_bridge_operational_thinning_loop_route_evidence(
            loop_owner,
            route_owner,
            integration_policy=_INTEGRATION_POLICY,
            integration_role_sha256="e" * 64,
        )
    )
    return {
        "process": process,
        "reference_composer": reference_composer,
        "potential_composer": potential_composer,
        "rate_owner": rate_owner,
        "thinning_owner": thinning_owner,
        "loop_owner": loop_owner,
        "route_owner": route_owner,
        "integration_owner": integration_owner,
    }


@pytest.fixture(scope="module")
def bundle():
    return _bundle()


@pytest.fixture(scope="module")
def tight_bundle():
    return _bundle(tight=True)


def _philox(seed):
    return np.random.Generator(np.random.Philox(seed))


def _parents(bundle, state=()):
    intensity = bundle["reference_composer"].preflight_candidate_intensity(
        state,
        reverse_time=0.4,
    )
    envelope = bundle["rate_owner"].preflight_envelope(intensity)
    return intensity, envelope


def _run(bundle, intensity, envelope, *, endpoint, budget, rng):
    return bundle["integration_owner"].run(
        intensity,
        envelope,
        clock_start=0.0,
        right_endpoint=endpoint,
        proposal_budget=budget,
        base_context=_BASE_CONTEXT,
        residual_context=_RESIDUAL_CONTEXT,
        rng=rng,
    )


@pytest.fixture(scope="module")
def zero_result(bundle):
    intensity, envelope = _parents(bundle)
    rng = _philox(20)
    result = _run(
        bundle,
        intensity,
        envelope,
        endpoint=0.0,
        budget=0,
        rng=rng,
    )
    return intensity, envelope, rng, result


@pytest.fixture(scope="module")
def rejection_result(bundle):
    intensity, envelope = _parents(bundle)
    rng = _philox(0)
    endpoint = math.nextafter(_REJECTED_BIRTH_TIME, math.inf)
    result = _run(
        bundle,
        intensity,
        envelope,
        endpoint=endpoint,
        budget=2,
        rng=rng,
    )
    assert tuple(item.accepted for item in result.loop_result.iterations) == (False,)
    return intensity, envelope, rng, result


@pytest.fixture(scope="module")
def accepted_result(tight_bundle):
    intensity, envelope = _parents(tight_bundle)
    rng = _philox(7)
    endpoint = math.nextafter(_TIGHT_SECOND_TIME, math.inf)
    result = _run(
        tight_bundle,
        intensity,
        envelope,
        endpoint=endpoint,
        budget=4,
        rng=rng,
    )
    assert tuple(item.accepted for item in result.loop_result.iterations) == (
        True,
        True,
    )
    return intensity, envelope, rng, result


def _forged_record(record, **updates):
    forged = object.__new__(type(record))
    for name in type(record).__annotations__:
        object.__setattr__(forged, name, updates.get(name, getattr(record, name)))
    return forged


def _redigested_certificate(certificate, **updates):
    field_names = (
        integration.OperationalThinningLoopRouteEvidenceCertificate.__annotations__
    )
    values = {
        name: updates.get(name, getattr(certificate, name)) for name in field_names
    }
    values["certificate_sha256"] = "0" * 64
    values["certificate_sha256"] = thinning._semantic_digest(
        integration._certificate_payload(values)
    )
    forged = object.__new__(integration.OperationalThinningLoopRouteEvidenceCertificate)
    for name, value in values.items():
        object.__setattr__(forged, name, value)
    return forged


def _reconstruct_result(result, **updates):
    values = {
        name: updates.get(name, getattr(result, name))
        for name in integration.OperationalLocalThinningRouteEvidence.__annotations__
    }
    values["result_sha256"] = "0" * 64
    values["result_sha256"] = thinning._semantic_digest(
        integration._result_payload(values)
    )
    return integration.OperationalLocalThinningRouteEvidence(
        **values,
        _construction_token=integration._RESULT_TOKEN,
    )


def test_certificate_scope_flags_factory_and_parent_binding(bundle):
    owner = bundle["integration_owner"]
    certificate = owner.certificate
    validate_certificate = getattr(
        integration,
        "validate_plugin_bridge_operational_thinning_loop_route_evidence_certificate",
    )
    for name in (
        "parent_loop_black_box_delegation_certified",
        "exact_loop_entry_exit_philox_snapshots_certified",
        "waiting_acceptance_raw64_prefix_replay_certified",
        "one_route_evidence_per_returned_proposal_certified",
        "ordered_proposal_evidence_binding_certified",
        "same_runtime_route_boundary_reconstruction_certified",
        "candidate_semantic_and_post_state_replay_certified",
        "sequential_wait_route_accept_state_custody_certified",
        "accepted_refresh_rejected_reuse_inherited",
        "terminal_stop_semantics_inherited",
        "offline_validation_no_caller_rng_certified",
        "returned_route_kind_and_continuous_classification_certified",
        "active_cap_no_partial_return_inherited",
        "passed",
    ):
        assert getattr(certificate, name) is True
    for name in (
        "original_route_python_object_identity_certified",
        "live_snapshot_capture_at_original_route_call_certified",
        "bounded_raw_normal_word_trace_certified",
        "exact_categorical_law_certified",
        "exact_integer_law_certified",
        "exact_gaussian_law_certified",
        "analytic_lebesgue_output_law_certified",
        "ideal_distribution_recovery_certified",
        "unconditional_continuous_route_occurrence_certified",
        "unconditional_local_completion_certified",
        "exact_real_time_poisson_or_ctmc_path_certified",
        "unconditional_exact_frozen_jump_law_certified",
        "exact_active_controlled_total_exit_computed",
        "all_route_rate_totality_certified",
        "analytic_target_preserved",
        "conditional_posterior_or_doob_target",
        "rounded_detailed_balance_or_stationarity_certified",
        "sampler_liveness_certified",
        "counter_key_stream_contract_certified",
        "lineage_contract_certified",
        "continuous_drift_admissible",
        "initializer_admissible",
        "path_admissible",
        "strang_sampler_admissible",
        "full_sampler_admissible",
        "runtime_portable",
        "cryptographic_authentication",
    ):
        assert getattr(certificate, name) is False
    assert (
        validate_certificate(
            bundle["loop_owner"],
            bundle["route_owner"],
            owner,
            integration_policy=_INTEGRATION_POLICY,
            integration_role_sha256="e" * 64,
        )
        is certificate
    )


def test_certificate_rejects_flags_aliases_and_oversized_context(bundle):
    certificate = bundle["integration_owner"].certificate
    attacks = (
        {"exact_gaussian_law_certified": True},
        {"passed": 1},
        {"base_context_dimension": (loop._potential._MAX_CONTEXT_DIMENSION + 1)},
        {"maximum_proposals": True},
    )
    for updates in attacks:
        forged = _redigested_certificate(certificate, **updates)
        with pytest.raises((TypeError, ValueError)):
            integration._validate_certificate(forged)


def test_zero_duration_has_no_proposals_evidence_or_randomness(zero_result):
    intensity, envelope, rng, result = zero_result
    parent = result.loop_result
    assert parent.initial_intensity is intensity
    assert parent.initial_envelope is envelope
    assert parent.proposal_count == result.proposal_count == 0
    assert result.route_evidences == result.route_evidence_sha256s == ()
    assert result.loop_entry_state.snapshot_sha256 == (
        result.loop_exit_state.snapshot_sha256
    )
    assert result.rng_state_before_sha256 == result.rng_state_after_sha256
    assert parent.terminal_waiting_draw.zero_duration is True
    assert parent.terminal_waiting_draw.raw_words_consumed == 0
    assert route_evidence._capture_philox_state(rng).snapshot_sha256 == (
        result.loop_exit_snapshot_sha256
    )


def test_active_terminal_hold_consumes_clock_bits_but_has_no_route_evidence(bundle):
    intensity, envelope = _parents(bundle)
    rng = _philox(37)
    result = _run(
        bundle,
        intensity,
        envelope,
        endpoint=math.nextafter(0.0, math.inf),
        budget=1,
        rng=rng,
    )
    assert result.proposal_count == 0
    assert result.route_evidences == ()
    assert result.loop_result.terminal_waiting_draw.raw_words_consumed > 0
    assert result.loop_result.right_endpoint_exhausted is True
    assert result.rng_state_before_sha256 != result.rng_state_after_sha256
    assert route_evidence._capture_philox_state(rng).snapshot_sha256 == (
        result.loop_exit_snapshot_sha256
    )


def test_rejected_continuous_birth_binds_full_stream_and_reuses_parents(
    bundle,
    rejection_result,
):
    intensity, envelope, rng, result = rejection_result
    parent = result.loop_result
    iteration = parent.iterations[0]
    evidence = result.route_evidences[0]
    assert result.proposal_count == result.rejected_count == 1
    assert result.accepted_count == 0
    assert result.continuous_destination_proposal_count == 1
    assert result.continuous_destination_accepted_count == 0
    assert evidence.edit_kind == "birth"
    assert evidence.continuous_destination is True
    assert evidence.positive_dimensional_birth is True
    assert evidence.destination_event_dimension == 3
    assert iteration.proposal_time == _REJECTED_BIRTH_TIME
    assert iteration.accepted is False
    assert iteration.pre_intensity is iteration.post_intensity is intensity
    assert iteration.pre_envelope is iteration.post_envelope is envelope
    assert evidence.route_draw is not iteration.route_draw
    assert evidence.route_draw_sha256 == iteration.route_draw_sha256
    assert evidence.route_draw.candidate_sha256 == iteration.route_draw.candidate_sha256
    assert evidence.pre_route_state.state_sha256 == (
        iteration.waiting_draw.rng_state_after_sha256
    )
    assert evidence.post_route_state.state_sha256 == (
        iteration.decision.rng_state_before_sha256
    )
    assert parent.terminal_waiting_draw.rng_state_before_sha256 == (
        iteration.decision.rng_state_after_sha256
    )
    assert route_evidence._capture_philox_state(rng).snapshot_sha256 == (
        result.loop_exit_snapshot_sha256
    )
    caller_before = route_evidence._capture_philox_state(rng)
    assert (
        bundle["integration_owner"].validate_result(
            result,
            intensity,
            envelope,
            clock_start=0.0,
            right_endpoint=math.nextafter(_REJECTED_BIRTH_TIME, math.inf),
            proposal_budget=2,
            base_context=_BASE_CONTEXT,
            residual_context=_RESIDUAL_CONTEXT,
        )
        is result
    )
    caller_after = route_evidence._capture_philox_state(rng)
    assert route_evidence._snapshot_values(caller_after) == (
        route_evidence._snapshot_values(caller_before)
    )


def test_accepted_birth_then_unequal_replacement_refreshes_every_parent(
    tight_bundle,
    accepted_result,
):
    initial_intensity, initial_envelope, rng, result = accepted_result
    parent = result.loop_result
    first, second = parent.iterations
    birth, replacement = result.route_evidences
    assert result.proposal_count == result.accepted_count == 2
    assert result.rejected_count == 0
    assert (first.proposal_time, second.proposal_time) == (
        _TIGHT_FIRST_TIME,
        _TIGHT_SECOND_TIME,
    )
    assert (birth.edit_kind, replacement.edit_kind) == ("birth", "replacement")
    assert birth.positive_dimensional_birth is True
    assert birth.destination_event_dimension == 2
    assert replacement.positive_dimensional_replacement is True
    assert replacement.unequal_positive_dimensional_replacement is True
    assert replacement.source_event_dimension == 2
    assert replacement.destination_event_dimension == 3
    assert result.continuous_destination_proposal_count == 2
    assert result.continuous_destination_accepted_count == 2
    assert result.positive_dimensional_birth_proposal_count == 1
    assert result.positive_dimensional_replacement_proposal_count == 1
    assert result.unequal_positive_dimensional_replacement_proposal_count == 1
    assert result.unequal_positive_dimensional_replacement_accepted_count == 1
    assert first.pre_intensity is initial_intensity
    assert first.pre_envelope is initial_envelope
    assert first.post_intensity is second.pre_intensity
    assert first.post_envelope is second.pre_envelope
    assert first.post_intensity is not initial_intensity
    assert first.post_envelope is not initial_envelope
    assert second.post_intensity is not first.post_intensity
    assert second.post_envelope is not first.post_envelope
    assert len(parent.final_configuration[0].coordinates) == 3
    for iteration, evidence in zip(parent.iterations, result.route_evidences):
        assert evidence.route_draw is not iteration.route_draw
        assert evidence.route_draw_sha256 == iteration.route_draw_sha256
        assert evidence.pre_route_state.state_sha256 == (
            iteration.waiting_draw.rng_state_after_sha256
        )
        assert evidence.post_route_state.state_sha256 == (
            iteration.decision.rng_state_before_sha256
        )
    assert route_evidence._capture_philox_state(rng).snapshot_sha256 == (
        result.loop_exit_snapshot_sha256
    )
    caller_before = route_evidence._capture_philox_state(rng)
    assert (
        tight_bundle["integration_owner"].validate_result(
            result,
            initial_intensity,
            initial_envelope,
            clock_start=0.0,
            right_endpoint=math.nextafter(_TIGHT_SECOND_TIME, math.inf),
            proposal_budget=4,
            base_context=_BASE_CONTEXT,
            residual_context=_RESIDUAL_CONTEXT,
        )
        is result
    )
    caller_after = route_evidence._capture_philox_state(rng)
    assert route_evidence._snapshot_values(caller_after) == (
        route_evidence._snapshot_values(caller_before)
    )


@pytest.mark.parametrize("attack", ["reorder", "duplicate", "omit", "append"])
def test_evidence_reorder_duplication_omission_and_append_are_refused(
    accepted_result,
    attack,
):
    result = accepted_result[-1]
    first, second = result.route_evidences
    if attack == "reorder":
        evidences = (second, first)
    elif attack == "duplicate":
        evidences = (first, first)
    elif attack == "omit":
        evidences = (first,)
    else:
        evidences = (first, second, first)
    with pytest.raises((TypeError, ValueError)):
        _reconstruct_result(
            result,
            route_evidences=evidences,
            route_evidence_sha256s=tuple(
                evidence.evidence_sha256 for evidence in evidences
            ),
        )


def test_cross_transcript_route_and_parent_result_splices_are_refused(
    rejection_result,
    accepted_result,
):
    rejected = rejection_result[-1]
    accepted = accepted_result[-1]
    with pytest.raises((TypeError, ValueError)):
        _reconstruct_result(
            accepted,
            route_evidences=(rejected.route_evidences[0], accepted.route_evidences[1]),
            route_evidence_sha256s=(
                rejected.route_evidences[0].evidence_sha256,
                accepted.route_evidences[1].evidence_sha256,
            ),
        )
    with pytest.raises((TypeError, ValueError)):
        _reconstruct_result(
            accepted,
            loop_result=rejected.loop_result,
            loop_result_sha256=rejected.loop_result_sha256,
        )


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("proposal_count", False),
        ("accepted_count", 1),
        ("continuous_destination_proposal_count", 0),
        ("unequal_positive_dimensional_replacement_accepted_count", 0),
        ("every_completed_proposal_has_route_evidence", 1),
        ("same_runtime_full_loop_rng_replay_completed", False),
        ("terminal_waiting_prefix_replayed", False),
        ("original_route_python_object_identity_certified", True),
        ("live_snapshot_capture_at_original_route_call_certified", True),
        ("rng_state_after_sha256", "f" * 64),
    ],
)
def test_redigested_counts_flags_aliases_and_rng_tampering_are_refused(
    accepted_result,
    field,
    replacement,
):
    result = accepted_result[-1]
    with pytest.raises((TypeError, ValueError)):
        _reconstruct_result(result, **{field: replacement})


def test_entry_exit_snapshot_and_digest_splices_are_refused(accepted_result):
    result = accepted_result[-1]
    unrelated_entry = route_evidence._capture_philox_state(_philox(91))
    unrelated_exit = route_evidence._capture_philox_state(_philox(92))
    attacks = (
        {
            "loop_entry_state": unrelated_entry,
            "loop_entry_snapshot_sha256": unrelated_entry.snapshot_sha256,
            "rng_state_before_sha256": unrelated_entry.state_sha256,
        },
        {
            "loop_exit_state": unrelated_exit,
            "loop_exit_snapshot_sha256": unrelated_exit.snapshot_sha256,
            "rng_state_after_sha256": unrelated_exit.state_sha256,
        },
        {"route_evidence_sha256s": tuple(reversed(result.route_evidence_sha256s))},
        {"loop_result_sha256": "f" * 64},
    )
    for updates in attacks:
        with pytest.raises((TypeError, ValueError)):
            _reconstruct_result(result, **updates)


def test_cross_owner_result_certificate_and_live_binding_attacks_are_refused(
    bundle,
    zero_result,
):
    intensity, envelope, _, result = zero_result
    other_route_owner = route_evidence.certify_plugin_bridge_continuous_route_evidence(
        bundle["thinning_owner"],
        evidence_policy=(route_evidence.PLUGIN_BRIDGE_CONTINUOUS_ROUTE_EVIDENCE_POLICY),
        evidence_role_sha256="8" * 64,
    )
    other = integration.certify_plugin_bridge_operational_thinning_loop_route_evidence(
        bundle["loop_owner"],
        other_route_owner,
        integration_policy=_INTEGRATION_POLICY,
        integration_role_sha256="7" * 64,
    )
    with pytest.raises(ValueError, match="another loop route-evidence owner"):
        other.validate_result(
            result,
            intensity,
            envelope,
            clock_start=0.0,
            right_endpoint=0.0,
            proposal_budget=0,
            base_context=_BASE_CONTEXT,
            residual_context=_RESIDUAL_CONTEXT,
        )

    forged_certificate = _redigested_certificate(
        result.certificate,
        full_sampler_admissible=True,
    )
    with pytest.raises(ValueError, match="negative flags"):
        _reconstruct_result(
            result,
            certificate=forged_certificate,
            certificate_sha256=forged_certificate.certificate_sha256,
        )

    owner = bundle["integration_owner"]
    replacement_loop = loop.certify_plugin_bridge_operational_thinning_loop(
        bundle["thinning_owner"],
        loop_policy=loop.PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_POLICY,
        loop_role_sha256="b" * 64,
    )
    original_loop = owner._loop_owner
    object.__setattr__(owner, "_loop_owner", replacement_loop)
    try:
        with pytest.raises(ValueError, match="loop-owner binding changed"):
            owner._require_live_binding()
    finally:
        object.__setattr__(owner, "_loop_owner", original_loop)
    assert owner._require_live_binding() is owner.certificate


def test_active_budget_zero_and_invalid_budgets_are_pre_rng_failures(
    bundle,
    monkeypatch,
):
    intensity, envelope = _parents(bundle)

    def forbidden(*args, **kwargs):
        del args, kwargs
        raise AssertionError("a failed parent loop attempted route-evidence replay")

    monkeypatch.setattr(
        route_evidence.ContinuousRouteEvidenceOwner,
        "draw_reference_route_with_evidence",
        forbidden,
    )
    for budget in (0, -1, 65, True, 1.0, np.int64(1)):
        rng = _philox(41)
        before = thinning._rng_state_sha256(rng.bit_generator.state)
        with pytest.raises((TypeError, ValueError, ArithmeticError)):
            _run(
                bundle,
                intensity,
                envelope,
                endpoint=1.0,
                budget=budget,
                rng=rng,
            )
        assert thinning._rng_state_sha256(rng.bit_generator.state) == before


def test_active_cap_failure_keeps_bits_and_never_starts_shadow_replay(
    tight_bundle,
    accepted_result,
    monkeypatch,
):
    intensity, envelope = _parents(tight_bundle)
    expected_after = (
        accepted_result[-1].loop_result.iterations[0].rng_state_after_sha256
    )
    calls = {"count": 0}

    def forbidden(*args, **kwargs):
        del args, kwargs
        calls["count"] += 1
        raise AssertionError("failed checkpoint-20 call began shadow replay")

    monkeypatch.setattr(
        route_evidence.ContinuousRouteEvidenceOwner,
        "draw_reference_route_with_evidence",
        forbidden,
    )
    rng = _philox(7)
    before = thinning._rng_state_sha256(rng.bit_generator.state)
    with pytest.raises(loop.PluginBridgeOperationalThinningLoopError, match="budget"):
        _run(
            tight_bundle,
            intensity,
            envelope,
            endpoint=5.0,
            budget=1,
            rng=rng,
        )
    after = thinning._rng_state_sha256(rng.bit_generator.state)
    assert calls["count"] == 0
    assert after == expected_after
    assert after != before


def test_post_loop_replay_failure_is_fail_closed_but_nontransactional(
    bundle,
    rejection_result,
    monkeypatch,
):
    intensity, envelope = _parents(bundle)
    expected_exit = rejection_result[-1].loop_exit_state
    rng = _philox(0)
    entry = route_evidence._capture_philox_state(rng)
    calls = {"count": 0}

    def fail_replay(self, *args, **kwargs):
        del self, args, kwargs
        calls["count"] += 1
        raise RuntimeError("injected post-loop replay failure")

    monkeypatch.setattr(
        integration.BoundedOperationalThinningLoopRouteEvidence,
        "_replay_stream",
        fail_replay,
    )
    returned = None
    with pytest.raises(RuntimeError, match="injected post-loop replay failure"):
        returned = _run(
            bundle,
            intensity,
            envelope,
            endpoint=math.nextafter(_REJECTED_BIRTH_TIME, math.inf),
            budget=2,
            rng=rng,
        )
    exit_state = route_evidence._capture_philox_state(rng)
    assert calls["count"] == 1
    assert returned is None
    assert route_evidence._snapshot_values(exit_state) == (
        route_evidence._snapshot_values(expected_exit)
    )
    assert exit_state.state_sha256 != entry.state_sha256


def test_records_certificate_and_owner_are_sealed_nonpickle_objects(
    bundle,
    zero_result,
    rejection_result,
):
    owner = bundle["integration_owner"]
    result = zero_result[-1]
    evidence = rejection_result[-1].route_evidences[0]
    for record in (owner, owner.certificate, result):
        with pytest.raises(TypeError, match="pickle"):
            pickle.dumps(record)
    with pytest.raises(AttributeError, match="immutable"):
        owner._integration_role_sha256 = "0" * 64
    with pytest.raises(TypeError, match="module-created"):
        field_names = integration.OperationalLocalThinningRouteEvidence.__annotations__
        integration.OperationalLocalThinningRouteEvidence(
            **{name: getattr(result, name) for name in field_names},
            _construction_token=object(),
        )
    with pytest.raises(TypeError, match="certification"):
        integration.BoundedOperationalThinningLoopRouteEvidence(
            bundle["loop_owner"],
            bundle["route_owner"],
            "e" * 64,
            owner.certificate,
            _construction_token=object(),
        )
    with pytest.raises(TypeError, match="subclassed"):

        class BadResult(integration.OperationalLocalThinningRouteEvidence):
            pass

    with pytest.raises(TypeError, match="subclassed"):

        class BadOwner(integration.BoundedOperationalThinningLoopRouteEvidence):
            pass

    assert evidence.certificate is bundle["route_owner"].certificate


def test_public_surface_and_source_do_not_reimplement_any_route_law(bundle):
    expected = {
        "PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_ROUTE_EVIDENCE_POLICY",
        "PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_ROUTE_EVIDENCE_SCHEMA_VERSION",
        "PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_ROUTE_EVIDENCE_SCOPE",
        "BoundedOperationalThinningLoopRouteEvidence",
        "OperationalLocalThinningRouteEvidence",
        "OperationalThinningLoopRouteEvidenceCertificate",
        "PluginBridgeOperationalThinningLoopRouteEvidenceError",
        "certify_plugin_bridge_operational_thinning_loop_route_evidence",
        "require_matching_plugin_bridge_operational_thinning_loop_route_evidence",
        "validate_plugin_bridge_operational_thinning_loop_route_evidence_certificate",
    }
    assert set(integration.__all__) == expected
    owner = bundle["integration_owner"]
    for name in (
        "sample_path",
        "simulate_path",
        "integrate_drift",
        "initialize",
        "strang_step",
        "heun_step",
        "exact_controlled_total_exit",
        "sample_exact_gaussian",
        "sample_exact_categorical",
    ):
        assert not hasattr(owner, name)

    source = inspect.getsource(integration)
    tree = ast.parse(source)
    forbidden_calls = {
        "choice",
        "exponential",
        "integers",
        "normal",
        "random",
        "random_raw",
        "searchsorted",
        "standard_normal",
        "uniform",
    }
    called_attributes = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert called_attributes.isdisjoint(forbidden_calls)
    assert source.count(".draw_reference_route_with_evidence(") == 1
    assert ".sample_candidate_from_intensity(" not in source
    assert ".draw_reference_route(" not in source
    assert source.count("self.loop_owner.run(") == 1
    assert "same-runtime replay object" in source
    assert "not-exact-gaussian-law" in source
    assert "not-full-sampler" in source


def test_optional_torch_import_boundary_is_explicit():
    module_path = Path(integration.__file__).resolve()
    source_root = module_path.parents[3]
    script = """
import builtins

real_import = builtins.__import__
def guarded(name, *args, **kwargs):
    if name == 'torch' or name.startswith('torch.'):
        raise ModuleNotFoundError("No module named 'torch'", name='torch')
    return real_import(name, *args, **kwargs)
builtins.__import__ = guarded
try:
    import heterodiff.processes.plugin_bridge_operational_thinning_loop_route_evidence
except ModuleNotFoundError as error:
    text = str(error)
    assert "route-evidenced operational thinning loops require" in text
    assert "optional PyTorch" in text
else:
    raise AssertionError("optional PyTorch boundary did not refuse")
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=source_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
