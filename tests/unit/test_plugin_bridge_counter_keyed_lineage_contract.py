"""Hostile tests for checkpoint-23 counter-key and lineage contracts."""

import ast
import copy
import inspect
import math
from pathlib import Path
import pickle
import subprocess
import sys
from types import MappingProxyType

import numpy as np
import pytest


torch = pytest.importorskip(
    "torch", reason="counter-keyed lineage contracts require the PyTorch stack"
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
    plugin_bridge_counter_keyed_lineage_contract as contract,
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


TYPE_DIMENSIONS = {0: 0, 1: 0}
TYPE_WEIGHTS = {0: 0.4, 1: 0.6}
TYPE_SCALES = {0: (), 1: ()}
BASE_CONTEXT = (0.25,)
RESIDUAL_CONTEXT = (-0.4,)
TIGHT_ENDPOINT = 2.13292024


def _process(*, total_cap=2):
    reference = CappedPoissonConfigurationReference(
        TYPE_DIMENSIONS,
        TYPE_WEIGHTS,
        activity=1.4,
        total_cap=total_cap,
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
        context_key=(("checkpoint-23-tight",) if tight else ("checkpoint-23",)),
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


def _bundle(*, tight=False, total_cap=2):
    process = _process(total_cap=total_cap)
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
    base_model = _model(base_architecture, 2301)
    residual_model = _model(residual_architecture, 2302)
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
        evidence_policy=(route_evidence.PLUGIN_BRIDGE_CONTINUOUS_ROUTE_EVIDENCE_POLICY),
        evidence_role_sha256="d" * 64,
    )
    certify_integration = (
        integration.certify_plugin_bridge_operational_thinning_loop_route_evidence
    )
    integration_owner = certify_integration(
        loop_owner,
        route_owner,
        integration_policy=(
            integration.PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_ROUTE_EVIDENCE_POLICY
        ),
        integration_role_sha256="e" * 64,
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


def _philox(seed):
    return np.random.Generator(np.random.Philox(seed))


def _parents(bundle, state=(TransformedEvent(0),)):
    intensity = bundle["reference_composer"].preflight_candidate_intensity(
        state,
        reverse_time=0.4,
    )
    envelope = bundle["rate_owner"].preflight_envelope(intensity)
    return intensity, envelope


def _run_parent(bundle, intensity, envelope, *, endpoint, budget, seed):
    return bundle["integration_owner"].run(
        intensity,
        envelope,
        clock_start=0.0,
        right_endpoint=endpoint,
        proposal_budget=budget,
        base_context=BASE_CONTEXT,
        residual_context=RESIDUAL_CONTEXT,
        rng=_philox(seed),
    )


def _forged_record(record, **updates):
    forged = object.__new__(type(record))
    for name in type(record).__annotations__:
        object.__setattr__(forged, name, updates.get(name, getattr(record, name)))
    return forged


def _address_values(address, **updates):
    values = {
        name: updates.get(name, getattr(address, name))
        for name in contract.CounterKeyedPhiloxAddress.__annotations__
    }
    values["address_sha256"] = "0" * 64
    values["address_sha256"] = thinning._semantic_digest(
        contract._without(values, "address_sha256")
    )
    return values


def _advanced_snapshot(snapshot):
    values = {
        name: getattr(snapshot, name)
        for name in route_evidence.PhiloxRouteStateSnapshot.__annotations__
    }
    values["buffer"] = (1, 0, 0, 0)
    values["buffer_pos"] = 0
    values["state_sha256"] = thinning._rng_state_sha256(
        route_evidence._philox_state_mapping(values)
    )
    values["snapshot_sha256"] = "0" * 64
    values["snapshot_sha256"] = thinning._semantic_digest(
        route_evidence._snapshot_payload(values)
    )
    return route_evidence.PhiloxRouteStateSnapshot(
        **values,
        _construction_token=route_evidence._SNAPSHOT_TOKEN,
    )


def _stream_values(stream, **updates):
    values = {
        name: updates.get(name, getattr(stream, name))
        for name in contract.CounterKeyedPhiloxStream.__annotations__
    }
    values["stream_sha256"] = "0" * 64
    values["stream_sha256"] = thinning._semantic_digest(
        contract._without(
            values,
            "certificate",
            "address",
            "initial_state",
            "stream_sha256",
        )
    )
    return values


def _identifier_values(identifier, **updates):
    values = {
        name: updates.get(name, getattr(identifier, name))
        for name in contract.OperationalLineageIdentifier.__annotations__
    }
    values["identifier_sha256"] = "0" * 64
    values["identifier_sha256"] = thinning._semantic_digest(
        contract._without(values, "identifier_sha256")
    )
    return values


def _occurrence_values(occurrence, **updates):
    values = {
        name: updates.get(name, getattr(occurrence, name))
        for name in contract.OperationalLineagedOccurrence.__annotations__
    }
    values["occurrence_sha256"] = "0" * 64
    values["occurrence_sha256"] = thinning._semantic_digest(
        contract._without(
            values,
            "identifier",
            "event",
            "occurrence_sha256",
        )
    )
    return values


def _state_values(state, **updates):
    values = {
        name: updates.get(name, getattr(state, name))
        for name in contract.OperationalLineageState.__annotations__
    }
    values["state_sha256"] = "0" * 64
    values["state_sha256"] = thinning._semantic_digest(
        contract._without(
            values,
            "occurrences",
            "retired_identifiers",
            "model_configuration",
            "state_sha256",
        )
    )
    return values


def _transition_values(transition, **updates):
    values = {
        name: updates.get(name, getattr(transition, name))
        for name in contract.OperationalLineageTransition.__annotations__
    }
    values["transition_sha256"] = "0" * 64
    values["transition_sha256"] = thinning._semantic_digest(
        contract._without(
            values,
            "certificate",
            "parent_iteration",
            "parent_route_evidence",
            "selected_source_identifier",
            "destroyed_identifier",
            "created_occurrence",
            "pre_state",
            "post_state",
            "transition_sha256",
        )
    )
    return values


def _result_values(result, **updates):
    values = {
        name: updates.get(name, getattr(result, name))
        for name in contract.OperationalLocalThinningLineageResult.__annotations__
    }
    values["result_sha256"] = "0" * 64
    values["result_sha256"] = thinning._semantic_digest(
        contract._without(
            values,
            "certificate",
            "parent_result",
            "initial_state",
            "transitions",
            "final_state",
            "result_sha256",
        )
    )
    return values


def _forged_iteration(iteration, **updates):
    values = {
        name: updates.get(name, getattr(iteration, name))
        for name in loop.OperationalProposalIteration.__annotations__
    }
    values["iteration_sha256"] = "0" * 64
    values["iteration_sha256"] = thinning._semantic_digest(
        loop._iteration_payload(values)
    )
    forged = object.__new__(loop.OperationalProposalIteration)
    for name, value in values.items():
        object.__setattr__(forged, name, value)
    return forged


def _certify_owner(bundle, *, role="f" * 64):
    return contract.certify_plugin_bridge_counter_keyed_lineage_contract(
        bundle["integration_owner"],
        contract_policy=contract.PLUGIN_BRIDGE_COUNTER_KEYED_LINEAGE_POLICY,
        contract_role_sha256=role,
    )


@pytest.fixture(scope="module")
def tight_bundle():
    bundle = _bundle(tight=True)
    bundle["contract_owner"] = _certify_owner(bundle)
    return bundle


@pytest.fixture(scope="module")
def regular_bundle():
    bundle = _bundle(tight=False)
    bundle["contract_owner"] = _certify_owner(bundle)
    return bundle


def _stream_limb(stream):
    return stream.initial_state.key, stream.initial_state.counter


def _domain_streams(owner, *, run_id, step_index):
    return (
        owner.make_jump_proposal_stream(run_id, step_index, 7),
        owner.make_terminal_wait_stream(run_id, step_index, 7),
        owner.make_initializer_stream(run_id, step_index, 11),
        owner.make_brownian_left_stream(run_id, step_index, 11),
        owner.make_brownian_right_stream(run_id, step_index, 11),
    )


def test_certificate_scope_is_explicit_and_parent_execution_remains_unkeyed(
    tight_bundle,
):
    owner = tight_bundle["contract_owner"]
    certificate = owner.certificate
    for name in (
        "exact_parent_owner_binding_certified",
        "parent_result_revalidation_before_annotation_certified",
        "direct_unhashed_address_components_certified",
        "injective_fixed_domain_address_layout_certified",
        "exact_checkpoint21_initial_snapshot_certified",
        "same_runtime_stream_reconstruction_certified",
        "immutable_stream_receipt_certified",
        "sealed_lineage_sidecar_certified",
        "positional_initial_duplicate_lift_certified",
        "stable_model_key_only_edit_order_certified",
        "accepted_fresh_monotone_lineage_certified",
        "accepted_exact_index_destruction_certified",
        "rejection_exact_state_reuse_certified",
        "terminal_exact_state_preservation_certified",
        "retired_serial_no_reuse_ledger_certified",
        "bounded_lineage_ledger_certified",
        "identifier_excluded_from_model_projection_certified",
        "bounded_live_coordinate_preflight_certified",
        "passed",
    ):
        assert getattr(certificate, name) is True
    for name in (
        "checkpoint22_proposal_keyed_execution_certified",
        "checkpoint22_stream_consumption_certified",
        "occurrence_stream_consumption_certified",
        "initializer_stream_consumption_certified",
        "brownian_stream_consumption_certified",
        "brownian_additive_coupling_certified",
        "global_run_id_uniqueness_certified",
        "duplicate_address_use_prevention_certified",
        "lineage_fork_prevention_certified",
        "statistical_independence_certified",
        "physical_randomness_certified",
        "exact_categorical_law_certified",
        "exact_integer_law_certified",
        "exact_gaussian_law_certified",
        "analytic_output_law_certified",
        "analytic_target_preserved",
        "rounded_stationarity_certified",
        "sampler_liveness_certified",
        "initializer_admissible",
        "unconditional_local_completion_certified",
        "unconditional_exact_frozen_jump_law_certified",
        "exact_real_time_poisson_or_ctmc_path",
        "conditional_posterior_or_doob_target",
        "continuous_drift_admissible",
        "path_admissible",
        "strang_sampler_admissible",
        "full_sampler_admissible",
        "runtime_portable",
        "cryptographic_authentication",
    ):
        assert getattr(certificate, name) is False
    assert certificate.parent_certificate_sha256 == (
        tight_bundle["integration_owner"].certificate.certificate_sha256
    )
    assert certificate.maximum_live_coordinates == 4_000_000
    assert "not-checkpoint22-proposal-keyed-execution" in (
        certificate.certificate_scope
    )


def test_direct_address_limbs_and_exact_empty_initial_state(tight_bundle):
    owner = tight_bundle["contract_owner"]
    run_id = 0x0123456789ABCDEF
    step_index = 0x1020304050607080
    streams = _domain_streams(owner, run_id=run_id, step_index=step_index)
    expected = (
        (
            contract.COUNTER_KEY_DOMAIN_JUMP_PROPOSAL,
            contract.COUNTER_KEY_DOMAIN_TAG_JUMP_PROPOSAL,
            0,
            7,
        ),
        (
            contract.COUNTER_KEY_DOMAIN_TERMINAL_WAIT,
            contract.COUNTER_KEY_DOMAIN_TAG_TERMINAL_WAIT,
            0,
            7,
        ),
        (
            contract.COUNTER_KEY_DOMAIN_INITIALIZER,
            contract.COUNTER_KEY_DOMAIN_TAG_INITIALIZER,
            11,
            0,
        ),
        (
            contract.COUNTER_KEY_DOMAIN_BROWNIAN_LEFT,
            contract.COUNTER_KEY_DOMAIN_TAG_BROWNIAN_LEFT,
            11,
            0,
        ),
        (
            contract.COUNTER_KEY_DOMAIN_BROWNIAN_RIGHT,
            contract.COUNTER_KEY_DOMAIN_TAG_BROWNIAN_RIGHT,
            11,
            0,
        ),
    )
    for stream, (domain, tag, occurrence, proposal) in zip(streams, expected):
        address = stream.address
        snapshot = stream.initial_state
        assert address.domain == domain
        assert address.domain_tag == tag
        assert address.philox_key == snapshot.key == (run_id, tag)
        assert (
            address.philox_counter
            == snapshot.counter
            == (
                0,
                step_index,
                occurrence,
                proposal,
            )
        )
        assert snapshot.buffer == (0, 0, 0, 0)
        assert snapshot.buffer_pos == 4
        assert snapshot.has_uint32 == snapshot.uinteger == 0
        assert stream.buffer_is_zero is True
        assert stream.uint32_cache_is_zero is True
        assert stream.parent_execution_used_this_stream is False
        assert stream.same_runtime_only is True
        assert owner.validate_stream(stream) is stream


def test_address_layout_is_injective_on_a_bounded_cartesian_product(tight_bundle):
    certificate = tight_bundle["contract_owner"].certificate
    addresses = []
    for run_id in (0, 1, contract.MAX_UINT64):
        for step_index in (0, 2, contract.MAX_UINT64):
            for proposal_index in (0, 1, 63):
                addresses.extend(
                    (
                        contract._make_address(
                            certificate,
                            domain=contract.COUNTER_KEY_DOMAIN_JUMP_PROPOSAL,
                            run_id=run_id,
                            step_index=step_index,
                            occurrence_serial=0,
                            proposal_index=proposal_index,
                        ),
                        contract._make_address(
                            certificate,
                            domain=contract.COUNTER_KEY_DOMAIN_TERMINAL_WAIT,
                            run_id=run_id,
                            step_index=step_index,
                            occurrence_serial=0,
                            proposal_index=proposal_index,
                        ),
                    )
                )
            addresses.append(
                contract._make_address(
                    certificate,
                    domain=contract.COUNTER_KEY_DOMAIN_TERMINAL_WAIT,
                    run_id=run_id,
                    step_index=step_index,
                    occurrence_serial=0,
                    proposal_index=64,
                )
            )
            for occurrence_serial in (1, 9, contract.MAX_UINT64):
                for domain in (
                    contract.COUNTER_KEY_DOMAIN_INITIALIZER,
                    contract.COUNTER_KEY_DOMAIN_BROWNIAN_LEFT,
                    contract.COUNTER_KEY_DOMAIN_BROWNIAN_RIGHT,
                ):
                    addresses.append(
                        contract._make_address(
                            certificate,
                            domain=domain,
                            run_id=run_id,
                            step_index=step_index,
                            occurrence_serial=occurrence_serial,
                            proposal_index=0,
                        )
                    )
    limbs = tuple((address.philox_key, address.philox_counter) for address in addresses)
    assert len(limbs) == len(set(limbs))
    assert len({address.address_sha256 for address in addresses}) == len(addresses)


def test_same_address_replays_and_creation_order_is_irrelevant(tight_bundle):
    owner = tight_bundle["contract_owner"]
    assert owner.certificate.duplicate_address_use_prevention_certified is False
    assert owner.certificate.global_run_id_uniqueness_certified is False
    requests = (
        (owner.make_jump_proposal_stream, (17, 23, 5)),
        (owner.make_terminal_wait_stream, (17, 23, 5)),
        (owner.make_initializer_stream, (17, 23, 31)),
        (owner.make_brownian_left_stream, (17, 23, 31)),
        (owner.make_brownian_right_stream, (17, 23, 31)),
    )
    forward = tuple(factory(*arguments) for factory, arguments in requests)
    reverse = tuple(
        reversed(
            tuple(factory(*arguments) for factory, arguments in reversed(requests))
        )
    )
    assert tuple(item.stream_sha256 for item in forward) == tuple(
        item.stream_sha256 for item in reverse
    )
    for first, second in zip(forward, reverse):
        assert first is not second
        assert _stream_limb(first) == _stream_limb(second)
        first_rng = owner.reconstruct_stream(first)
        second_rng = owner.reconstruct_stream(second)
        assert np.array_equal(
            first_rng.bit_generator.random_raw(32),
            second_rng.bit_generator.random_raw(32),
        )
        assert owner.validate_stream(first) is first


def test_each_address_component_or_domain_change_changes_the_stream(tight_bundle):
    owner = tight_bundle["contract_owner"]
    baseline = owner.make_jump_proposal_stream(41, 43, 47)
    variants = (
        owner.make_jump_proposal_stream(42, 43, 47),
        owner.make_jump_proposal_stream(41, 44, 47),
        owner.make_jump_proposal_stream(41, 43, 48),
        owner.make_terminal_wait_stream(41, 43, 47),
    )
    assert all(_stream_limb(item) != _stream_limb(baseline) for item in variants)
    assert (
        len({baseline.stream_sha256, *(item.stream_sha256 for item in variants)}) == 5
    )


@pytest.mark.parametrize(
    "invalid",
    [True, False, np.int64(1), 1.0, -1, contract.MAX_UINT64 + 1],
)
def test_all_address_coordinates_require_exact_uint64(tight_bundle, invalid):
    owner = tight_bundle["contract_owner"]
    calls = (
        lambda: owner.make_jump_proposal_stream(invalid, 2, 3),
        lambda: owner.make_jump_proposal_stream(1, invalid, 3),
        lambda: owner.make_jump_proposal_stream(1, 2, invalid),
        lambda: owner.make_initializer_stream(invalid, 2, 3),
        lambda: owner.make_initializer_stream(1, invalid, 3),
        lambda: owner.make_initializer_stream(1, 2, invalid),
    )
    for call in calls:
        with pytest.raises((TypeError, ValueError)):
            call()

    if invalid == contract.MAX_UINT64 + 1:
        with pytest.raises((TypeError, ValueError)):
            owner.make_terminal_wait_stream(1, 2, invalid)


def test_domain_specific_subject_bounds_are_fail_closed(tight_bundle):
    owner = tight_bundle["contract_owner"]
    with pytest.raises((TypeError, ValueError)):
        owner.make_jump_proposal_stream(1, 2, 64)
    with pytest.raises((TypeError, ValueError)):
        owner.make_terminal_wait_stream(1, 2, 65)
    for factory in (
        owner.make_initializer_stream,
        owner.make_brownian_left_stream,
        owner.make_brownian_right_stream,
    ):
        with pytest.raises((TypeError, ValueError)):
            factory(1, 2, 0)


def test_unknown_domains_and_zero_sentinel_aliases_are_refused(tight_bundle):
    certificate = tight_bundle["contract_owner"].certificate
    with pytest.raises((TypeError, ValueError)):
        contract._make_address(
            certificate,
            domain="unknown",
            run_id=1,
            step_index=2,
            occurrence_serial=0,
            proposal_index=3,
        )
    illegal = (
        (contract.COUNTER_KEY_DOMAIN_JUMP_PROPOSAL, 1, 3),
        (contract.COUNTER_KEY_DOMAIN_TERMINAL_WAIT, 1, 3),
        (contract.COUNTER_KEY_DOMAIN_INITIALIZER, 1, 3),
        (contract.COUNTER_KEY_DOMAIN_BROWNIAN_LEFT, 0, 0),
        (contract.COUNTER_KEY_DOMAIN_BROWNIAN_RIGHT, 0, 0),
    )
    for domain, occurrence, proposal in illegal:
        with pytest.raises((TypeError, ValueError)):
            contract._make_address(
                certificate,
                domain=domain,
                run_id=1,
                step_index=2,
                occurrence_serial=occurrence,
                proposal_index=proposal,
            )


def test_stream_factories_do_not_accept_or_advance_external_rng(tight_bundle):
    owner = tight_bundle["contract_owner"]
    for name in (
        "make_jump_proposal_stream",
        "make_terminal_wait_stream",
        "make_initializer_stream",
        "make_brownian_left_stream",
        "make_brownian_right_stream",
        "validate_stream",
        "reconstruct_stream",
    ):
        assert "rng" not in inspect.signature(getattr(owner, name)).parameters
    original = np.random.get_state()
    try:
        np.random.seed(2307)
        before = np.random.get_state()
        _domain_streams(owner, run_id=3, step_index=5)
        after = np.random.get_state()
        assert before[0] == after[0]
        assert np.array_equal(before[1], after[1])
        assert before[2:] == after[2:]
    finally:
        np.random.set_state(original)


def test_redigested_address_snapshot_and_stream_forgeries_are_refused(
    tight_bundle,
):
    owner = tight_bundle["contract_owner"]
    stream = owner.make_jump_proposal_stream(3, 5, 7)
    address = stream.address
    attacks = (
        {"run_id": 4},
        {"domain_tag": contract.COUNTER_KEY_DOMAIN_TAG_TERMINAL_WAIT},
        {"occurrence_serial": 1},
        {"philox_key": (4, address.domain_tag)},
        {"philox_counter": (1, 5, 0, 7)},
    )
    for updates in attacks:
        values = _address_values(address, **updates)
        with pytest.raises((TypeError, ValueError)):
            contract.CounterKeyedPhiloxAddress(
                **values,
                _construction_token=contract._ADDRESS_TOKEN,
            )

    advanced = _advanced_snapshot(stream.initial_state)
    values = _stream_values(
        stream,
        initial_state=advanced,
        initial_snapshot_sha256=advanced.snapshot_sha256,
        initial_state_sha256=advanced.state_sha256,
    )
    with pytest.raises((TypeError, ValueError)):
        contract.CounterKeyedPhiloxStream(
            **values,
            _construction_token=contract._STREAM_TOKEN,
        )
    for updates in (
        {"parent_execution_used_this_stream": True},
        {"buffer_is_zero": 1},
        {"same_runtime_only": False},
        {"address_sha256": "0" * 64},
    ):
        values = _stream_values(stream, **updates)
        with pytest.raises((TypeError, ValueError)):
            contract.CounterKeyedPhiloxStream(
                **values,
                _construction_token=contract._STREAM_TOKEN,
            )


def test_stream_address_certificate_and_owner_are_sealed(tight_bundle):
    owner = tight_bundle["contract_owner"]
    records = (
        owner,
        owner.certificate,
        owner.make_jump_proposal_stream(1, 2, 3),
        owner.make_jump_proposal_stream(1, 2, 3).address,
    )
    for record in records:
        with pytest.raises(TypeError, match="pickle"):
            pickle.dumps(record)
    with pytest.raises(AttributeError, match="immutable"):
        owner._contract_role_sha256 = "0" * 64
    with pytest.raises(TypeError, match="subclassed"):

        class BadAddress(contract.CounterKeyedPhiloxAddress):
            pass

    with pytest.raises(TypeError, match="subclassed"):

        class BadStream(contract.CounterKeyedPhiloxStream):
            pass


def test_runtime_domain_and_origin_rebinding_refuses_before_issue(
    tight_bundle,
    monkeypatch,
):
    owner = tight_bundle["contract_owner"]
    original_tags = contract.COUNTER_KEY_DOMAIN_TAGS
    monkeypatch.setattr(
        contract,
        "COUNTER_KEY_DOMAIN_TAGS",
        MappingProxyType({domain: 1 for domain in original_tags}),
    )
    with pytest.raises(ValueError):
        owner.make_jump_proposal_stream(1, 2, 3)
    monkeypatch.setattr(contract, "COUNTER_KEY_DOMAIN_TAGS", original_tags)
    monkeypatch.setattr(contract, "_BIRTH_ORIGIN", "counterfeit-birth")
    with pytest.raises(ValueError):
        owner.make_jump_proposal_stream(1, 2, 3)


def test_duplicate_bootstrap_is_positional_canonical_and_model_clean(tight_bundle):
    owner = tight_bundle["contract_owner"]
    duplicate = TransformedEvent(0)
    intensity, _ = _parents(tight_bundle, (duplicate, duplicate))
    state = owner.bootstrap_lineage(
        intensity,
        run_id=101,
        initialization_index=103,
    )
    assert state.model_configuration == intensity.source_configuration
    assert state.model_configuration == (duplicate, duplicate)
    assert state.identifiers_absent_from_model_projection is True
    assert state.retired_identifiers == state.retired_identifier_sha256s == ()
    assert state.next_serial == 3
    identifiers = tuple(item.identifier for item in state.occurrences)
    assert tuple(item.serial for item in identifiers) == (1, 2)
    assert tuple(item.origin_kind for item in identifiers) == ("initial", "initial")
    assert tuple(item.origin_initial_position for item in identifiers) == (0, 1)
    assert all(item.origin_initialization_index == 103 for item in identifiers)
    assert identifiers[0].identifier_sha256 != identifiers[1].identifier_sha256
    assert all(type(event) is TransformedEvent for event in state.model_configuration)
    again = owner.bootstrap_lineage(
        intensity,
        run_id=101,
        initialization_index=103,
    )
    assert again is not state
    assert again.state_sha256 == state.state_sha256


def test_redigested_identifier_occurrence_and_live_retired_collision_refuse(
    tight_bundle,
):
    owner = tight_bundle["contract_owner"]
    intensity, _ = _parents(tight_bundle)
    state = owner.bootstrap_lineage(
        intensity,
        run_id=107,
        initialization_index=109,
    )
    occurrence = state.occurrences[0]
    identifier = occurrence.identifier

    identifier_values = _identifier_values(
        identifier,
        origin_kind="birth",
    )
    with pytest.raises(ValueError, match="initial fields"):
        contract.OperationalLineageIdentifier(
            **identifier_values,
            _construction_token=contract._IDENTIFIER_TOKEN,
        )

    occurrence_values = _occurrence_values(
        occurrence,
        event_model_key=("counterfeit",),
    )
    with pytest.raises(ValueError, match="model key"):
        contract.OperationalLineagedOccurrence(
            **occurrence_values,
            _construction_token=contract._OCCURRENCE_TOKEN,
        )

    state_values = _state_values(
        state,
        retired_identifiers=(identifier,),
        retired_identifier_sha256s=(identifier.identifier_sha256,),
    )
    with pytest.raises(ValueError, match="live and retired lineage serials"):
        contract.OperationalLineageState(
            **state_values,
            _construction_token=contract._STATE_TOKEN,
        )


@pytest.mark.parametrize(
    "invalid",
    [True, np.int64(1), 1.0, -1, contract.MAX_UINT64 + 1],
)
def test_bootstrap_coordinates_require_exact_uint64(tight_bundle, invalid):
    owner = tight_bundle["contract_owner"]
    intensity, _ = _parents(tight_bundle)
    for kwargs in (
        {"run_id": invalid, "initialization_index": 0},
        {"run_id": 0, "initialization_index": invalid},
    ):
        with pytest.raises((TypeError, ValueError)):
            owner.bootstrap_lineage(intensity, **kwargs)


def _single_iteration_case(
    bundle,
    state,
    *,
    edit_kind,
    accepted,
    seed,
    run_id,
    step_index,
    source_index=None,
):
    intensity, envelope = _parents(bundle, state)
    probe = _philox(seed)
    raw_word = int(probe.bit_generator.random_raw())
    trace = thinning._waiting_trace(
        envelope.controlled_total_exit_upper_bound,
        0.0,
        64.0,
        (raw_word,),
    )
    assert trace is not None and trace["candidate_due"] is True
    rng = _philox(seed)
    waiting = bundle["thinning_owner"].draw_waiting_time(
        intensity,
        envelope,
        clock_start=0.0,
        right_endpoint=math.nextafter(trace["proposal_time"], math.inf),
        rng=rng,
    )
    evidence = bundle["route_owner"].draw_reference_route_with_evidence(
        waiting,
        intensity,
        envelope,
        rng=rng,
    )
    route = evidence.route_draw
    proposal = route.candidate.proposal
    assert proposal.kind.value == edit_kind
    assert proposal.source_occurrence_index == source_index
    potential_evaluation = bundle["potential_composer"].evaluate(
        route.candidate,
        base_context=BASE_CONTEXT,
        residual_context=RESIDUAL_CONTEXT,
    )
    rate_evaluation = bundle["rate_owner"].evaluate_candidate(
        route.candidate,
        potential_evaluation,
        envelope=envelope,
    )
    decision = bundle["thinning_owner"].decide_acceptance(
        route,
        waiting,
        intensity,
        envelope,
        potential_evaluation,
        rate_evaluation,
        rng=rng,
    )
    assert decision.accepted is accepted
    if accepted:
        post_intensity = bundle["reference_composer"].preflight_candidate_intensity(
            decision.result_configuration,
            reverse_time=intensity.reverse_time,
        )
        post_envelope = bundle["rate_owner"].preflight_envelope(post_intensity)
    else:
        post_intensity = intensity
        post_envelope = envelope
    iteration = bundle["loop_owner"]._make_iteration(
        proposal_index=0,
        pre_intensity=intensity,
        pre_envelope=envelope,
        waiting_draw=waiting,
        route_draw=route,
        potential_evaluation=potential_evaluation,
        rate_evaluation=rate_evaluation,
        decision=decision,
        post_intensity=post_intensity,
        post_envelope=post_envelope,
    )
    assert (
        bundle["loop_owner"].validate_iteration(
            iteration,
            intensity,
            envelope,
            base_context=BASE_CONTEXT,
            residual_context=RESIDUAL_CONTEXT,
        )
        is iteration
    )
    assert (
        bundle["route_owner"].validate_reference_route_evidence(
            evidence,
            waiting,
            intensity,
            envelope,
        )
        is evidence
    )
    owner = bundle["contract_owner"]
    initial_state = owner.bootstrap_lineage(
        intensity,
        run_id=run_id,
        initialization_index=0,
    )
    transition = contract._make_transition(
        owner.certificate,
        iteration,
        evidence,
        initial_state,
        run_id=run_id,
        step_index=step_index,
    )
    return evidence, initial_state, transition


@pytest.fixture(scope="module")
def transition_matrix(tight_bundle, regular_bundle):
    event = TransformedEvent(0)
    duplicate_state = (event, event)
    requests = {
        "accepted_birth": (tight_bundle, (event,), "birth", True, 1, None),
        "accepted_death": (tight_bundle, duplicate_state, "death", True, 0, 0),
        "accepted_replacement": (
            tight_bundle,
            duplicate_state,
            "replacement",
            True,
            2,
            1,
        ),
        "rejected_birth": (regular_bundle, (event,), "birth", False, 0, None),
        "rejected_death": (
            regular_bundle,
            duplicate_state,
            "death",
            False,
            3,
            1,
        ),
        "rejected_replacement": (
            regular_bundle,
            duplicate_state,
            "replacement",
            False,
            5,
            0,
        ),
    }
    cases = {}
    for case_index, (name, request) in enumerate(requests.items()):
        bundle, state, kind, accepted, seed, source_index = request
        evidence, initial_state, transition = _single_iteration_case(
            bundle,
            state,
            edit_kind=kind,
            accepted=accepted,
            seed=seed,
            source_index=source_index,
            run_id=2300 + case_index,
            step_index=case_index,
        )
        cases[name] = (bundle, evidence, initial_state, transition)
    return cases


@pytest.fixture(scope="module")
def end_to_end_case(tight_bundle):
    intensity, envelope = _parents(tight_bundle)
    parent = _run_parent(
        tight_bundle,
        intensity,
        envelope,
        endpoint=TIGHT_ENDPOINT,
        budget=4,
        seed=7,
    )
    assert tuple(item.accepted for item in parent.loop_result.iterations) == (
        True,
        True,
    )
    assert tuple(
        item.route_draw.candidate.proposal.kind.value
        for item in parent.loop_result.iterations
    ) == ("birth", "death")
    owner = tight_bundle["contract_owner"]
    initial = owner.bootstrap_lineage(
        intensity,
        run_id=2499,
        initialization_index=0,
    )
    result = owner.annotate_result(
        parent,
        initial,
        run_id=2499,
        step_index=29,
    )
    return tight_bundle, parent, initial, result


@pytest.fixture(scope="module")
def zero_end_to_end_case(tight_bundle):
    intensity, envelope = _parents(tight_bundle)
    parent = _run_parent(
        tight_bundle,
        intensity,
        envelope,
        endpoint=0.0,
        budget=0,
        seed=99,
    )
    owner = tight_bundle["contract_owner"]
    initial = owner.bootstrap_lineage(
        intensity,
        run_id=2411,
        initialization_index=0,
    )
    result = owner.annotate_result(
        parent,
        initial,
        run_id=2411,
        step_index=23,
    )
    return tight_bundle, parent, initial, result


def _case_transition(transition_matrix, name):
    _, _, initial_state, transition = transition_matrix[name]
    return initial_state, transition


def test_accepted_birth_death_and_replacement_have_exact_lineage_algebra(
    transition_matrix,
):
    initial, birth = _case_transition(transition_matrix, "accepted_birth")
    assert birth.edit_kind == "birth"
    assert birth.accepted is True
    assert birth.selected_source_identifier is None
    assert birth.destroyed_identifier is None
    assert birth.created_occurrence is not None
    assert birth.created_occurrence.identifier.serial == initial.next_serial
    assert birth.created_occurrence.identifier.origin_kind == "birth"
    assert birth.created_occurrence.identifier.origin_step_index == birth.step_index
    assert birth.created_occurrence.identifier.origin_proposal_index == 0
    assert birth.accepted_allocated_fresh_serial is True
    assert birth.accepted_destroyed_exact_index is False

    initial, death = _case_transition(transition_matrix, "accepted_death")
    assert death.edit_kind == "death"
    assert death.accepted is True
    assert death.source_occurrence_index == 0
    assert death.selected_source_identifier is initial.occurrences[0].identifier
    assert death.destroyed_identifier is initial.occurrences[0].identifier
    assert death.created_occurrence is None
    assert tuple(item.identifier.serial for item in death.post_state.occurrences) == (
        initial.occurrences[1].identifier.serial,
    )
    assert death.post_state.retired_identifiers[-1] is death.destroyed_identifier
    assert death.accepted_allocated_fresh_serial is False
    assert death.accepted_destroyed_exact_index is True

    initial, replacement = _case_transition(transition_matrix, "accepted_replacement")
    assert replacement.edit_kind == "replacement"
    assert replacement.accepted is True
    assert replacement.source_occurrence_index == 1
    assert replacement.selected_source_identifier is (initial.occurrences[1].identifier)
    assert replacement.destroyed_identifier is initial.occurrences[1].identifier
    assert replacement.created_occurrence is not None
    assert replacement.created_occurrence.identifier.serial == initial.next_serial
    assert replacement.created_occurrence.identifier is not (
        replacement.destroyed_identifier
    )
    assert replacement.created_occurrence.identifier.origin_kind == "replacement"
    assert replacement.accepted_allocated_fresh_serial is True
    assert replacement.accepted_destroyed_exact_index is True


def test_duplicate_source_index_and_stable_model_key_reordering_are_exact(
    transition_matrix,
):
    initial, death = _case_transition(transition_matrix, "accepted_death")
    assert initial.occurrences[0].event == initial.occurrences[1].event
    assert death.source_occurrence_index == 0
    assert death.destroyed_identifier is initial.occurrences[0].identifier
    assert death.post_state.occurrences[0].identifier is (
        initial.occurrences[1].identifier
    )

    initial, replacement = _case_transition(transition_matrix, "accepted_replacement")
    assert replacement.source_occurrence_index == 1
    assert replacement.destroyed_identifier is initial.occurrences[1].identifier
    assert tuple(
        item.event.model_key() for item in replacement.post_state.occurrences
    ) == (
        tuple(
            sorted(
                (item.event for item in replacement.post_state.occurrences),
                key=TransformedEvent.model_key,
            )
        )[0].model_key(),
        tuple(
            sorted(
                (item.event for item in replacement.post_state.occurrences),
                key=TransformedEvent.model_key,
            )
        )[1].model_key(),
    )
    surviving = tuple(
        item
        for item in replacement.post_state.occurrences
        if item.identifier is initial.occurrences[0].identifier
    )
    assert len(surviving) == 1
    assert replacement.stable_model_key_sort_only is True


def test_all_rejections_reuse_the_exact_state_without_phantom_lineage(
    transition_matrix,
):
    for name in ("rejected_birth", "rejected_death", "rejected_replacement"):
        initial, transition = _case_transition(transition_matrix, name)
        assert transition.accepted is False
        assert transition.pre_state is initial
        assert transition.post_state is initial
        assert transition.created_occurrence is None
        assert transition.destroyed_identifier is None
        assert transition.rejection_reused_exact_state is True
        if transition.edit_kind == "birth":
            assert transition.selected_source_identifier is None
        else:
            selected = initial.occurrences[transition.source_occurrence_index]
            assert transition.selected_source_identifier is selected.identifier


def test_end_to_end_parent_projection_terminal_and_offline_validation(
    end_to_end_case,
):
    bundle, parent, initial, result = end_to_end_case
    assert result.parent_result is parent
    assert result.initial_state is initial
    assert result.initial_state.model_configuration == (
        parent.loop_result.initial_intensity.source_configuration
    )
    assert result.final_state.model_configuration == (
        parent.loop_result.final_configuration
    )
    assert result.terminal_waiting_draw_sha256 == (
        parent.loop_result.terminal_waiting_draw_sha256
    )
    assert result.terminal_reused_exact_lineage_state is True
    assert result.checkpoint22_execution_was_proposal_keyed is False
    assert result.checkpoint22_execution_used_contract_streams is False
    assert result.identifiers_absent_from_model_projection is True
    assert result.proposal_count == 2
    assert result.created_lineage_count == result.destroyed_lineage_count == 1
    assert not any(
        isinstance(value, contract.CounterKeyedPhiloxAddress)
        for value in result.__dict__.values()
    )
    assert (
        bundle["contract_owner"].validate_lineage_result(
            result,
            initial,
            run_id=result.run_id,
            step_index=result.step_index,
        )
        is result
    )


def test_a_to_b_to_a_and_identical_rebirth_never_resurrect_lineage(
    transition_matrix,
):
    bundle, _, initial, death = transition_matrix["accepted_death"]
    birth_template = transition_matrix["accepted_birth"][3]
    birth = contract._make_transition(
        bundle["contract_owner"].certificate,
        birth_template.parent_iteration,
        birth_template.parent_route_evidence,
        death.post_state,
        run_id=death.run_id,
        step_index=17,
    )
    assert initial.model_configuration == birth.post_state.model_configuration
    original = initial.occurrences[0].identifier
    recreated = birth.created_occurrence.identifier
    assert death.destroyed_identifier is original
    assert any(
        occurrence.identifier is recreated
        for occurrence in birth.post_state.occurrences
    )
    assert recreated.serial > original.serial
    assert recreated.identifier_sha256 != original.identifier_sha256
    assert recreated.origin_kind == "birth"
    assert birth.post_state.retired_identifiers == (original,)
    assert birth.post_state.next_serial == recreated.serial + 1


def test_zero_proposal_terminal_reuses_bootstrap_exactly(zero_end_to_end_case):
    _, _, initial, result = zero_end_to_end_case
    assert result.transitions == result.transition_sha256s == ()
    assert result.final_state is initial
    assert result.proposal_count == result.accepted_count == 0
    assert result.terminal_reused_exact_lineage_state is True


def test_lineage_metadata_never_enters_parent_model_records(transition_matrix):
    lineage_types = (
        contract.OperationalLineageIdentifier,
        contract.OperationalLineagedOccurrence,
        contract.OperationalLineageState,
        contract.CounterKeyedPhiloxAddress,
        contract.CounterKeyedPhiloxStream,
    )
    for _, _, initial, transition in transition_matrix.values():
        iteration = transition.parent_iteration
        assert not any(
            isinstance(value, lineage_types) for value in iteration.__dict__.values()
        )
        configurations = (
            iteration.pre_intensity.source_configuration,
            iteration.post_intensity.source_configuration,
            iteration.route_draw.candidate.source_configuration,
            iteration.route_draw.candidate.destination_configuration,
            iteration.decision.result_configuration,
        )
        assert all(
            all(type(event) is TransformedEvent for event in configuration)
            for configuration in configurations
        )
        assert initial.model_configuration == configurations[0]


def test_equal_duplicate_identifier_swap_is_not_the_certified_chain(
    transition_matrix,
):
    _, _, initial, transition = transition_matrix["accepted_death"]
    first, second = initial.occurrences
    swapped_occurrences = (
        contract._make_occurrence(
            transition.certificate,
            second.identifier,
            first.event,
        ),
        contract._make_occurrence(
            transition.certificate,
            first.identifier,
            second.event,
        ),
    )
    swapped = contract._make_state(
        transition.certificate,
        run_id=initial.run_id,
        initialization_index=initial.initialization_index,
        occurrences=swapped_occurrences,
        retired_identifiers=(),
        next_serial=initial.next_serial,
    )
    assert swapped.model_configuration == initial.model_configuration
    assert swapped.state_sha256 != initial.state_sha256
    values = _transition_values(
        transition,
        pre_state=swapped,
        pre_state_sha256=swapped.state_sha256,
    )
    with pytest.raises((TypeError, ValueError)):
        contract.OperationalLineageTransition(
            **values,
            _construction_token=contract._TRANSITION_TOKEN,
        )


def test_serial_ordered_origins_and_replacement_custody_are_enforced(
    tight_bundle,
):
    certificate = tight_bundle["contract_owner"].certificate
    initial = contract._make_identifier(
        certificate,
        run_id=71,
        serial=1,
        origin_kind="initial",
        origin_initialization_index=0,
        origin_initial_position=0,
    )
    later = contract._make_identifier(
        certificate,
        run_id=71,
        serial=2,
        origin_kind="birth",
        origin_step_index=9,
        origin_proposal_index=0,
    )
    earlier = contract._make_identifier(
        certificate,
        run_id=71,
        serial=3,
        origin_kind="birth",
        origin_step_index=8,
        origin_proposal_index=0,
    )
    event = TransformedEvent(0)
    occurrences = tuple(
        contract._make_occurrence(certificate, identifier, event)
        for identifier in (initial, later, earlier)
    )
    with pytest.raises(ValueError, match="serial order"):
        contract._make_state(
            certificate,
            run_id=71,
            initialization_index=0,
            occurrences=occurrences,
            retired_identifiers=(),
            next_serial=4,
        )

    replacement = contract._make_identifier(
        certificate,
        run_id=73,
        serial=2,
        origin_kind="replacement",
        origin_step_index=1,
        origin_proposal_index=0,
    )
    initial_other = contract._make_identifier(
        certificate,
        run_id=73,
        serial=1,
        origin_kind="initial",
        origin_initialization_index=0,
        origin_initial_position=0,
    )
    with pytest.raises(ValueError, match="retired source"):
        contract._make_state(
            certificate,
            run_id=73,
            initialization_index=0,
            occurrences=(
                contract._make_occurrence(certificate, initial_other, event),
                contract._make_occurrence(certificate, replacement, event),
            ),
            retired_identifiers=(),
            next_serial=3,
        )


def test_identifier_serial_bounds_invalid_events_and_state_resources_refuse(
    tight_bundle,
):
    certificate = tight_bundle["contract_owner"].certificate
    for serial in (0, contract.MAX_UINT64 + 1, True, np.int64(1)):
        with pytest.raises((TypeError, ValueError)):
            contract._make_identifier(
                certificate,
                run_id=1,
                serial=serial,
                origin_kind="initial",
                origin_initialization_index=0,
                origin_initial_position=0,
            )

    valid = contract._make_identifier(
        certificate,
        run_id=1,
        serial=1,
        origin_kind="initial",
        origin_initialization_index=0,
        origin_initial_position=0,
    )
    malformed_event = object.__new__(TransformedEvent)
    object.__setattr__(malformed_event, "event_type", True)
    object.__setattr__(malformed_event, "coordinates", ())
    with pytest.raises((TypeError, ValueError)):
        contract._make_occurrence(certificate, valid, malformed_event)

    occurrence = contract._make_occurrence(
        certificate,
        valid,
        TransformedEvent(0),
    )
    with pytest.raises((TypeError, ValueError)):
        contract._make_state(
            certificate,
            run_id=1,
            initialization_index=0,
            occurrences=(occurrence,),
            retired_identifiers=(),
            next_serial=contract.MAX_LINEAGE_NEXT_SERIAL,
        )
    oversized_count = contract.MAX_CONFIGURATION_CARDINALITY + 1
    values = _state_values(
        contract._make_state(
            certificate,
            run_id=1,
            initialization_index=0,
            occurrences=(occurrence,),
            retired_identifiers=(),
            next_serial=2,
        ),
        occurrences=(occurrence,) * oversized_count,
        occurrence_sha256s=(occurrence.occurrence_sha256,) * oversized_count,
    )
    with pytest.raises(ValueError, match="exceeds"):
        contract.OperationalLineageState(
            **values,
            _construction_token=contract._STATE_TOKEN,
        )


def test_aggregate_live_coordinate_bound_preflights_before_nested_validation(
    tight_bundle,
    monkeypatch,
):
    certificate = tight_bundle["contract_owner"].certificate
    identifier = contract._make_identifier(
        certificate,
        run_id=79,
        serial=1,
        origin_kind="initial",
        origin_initialization_index=0,
        origin_initial_position=0,
    )
    small = contract._make_occurrence(
        certificate,
        identifier,
        TransformedEvent(0),
    )
    base = contract._make_state(
        certificate,
        run_id=79,
        initialization_index=0,
        occurrences=(small,),
        retired_identifiers=(),
        next_serial=2,
    )
    wide = contract._make_occurrence(
        certificate,
        identifier,
        TransformedEvent(0, (0.0,) * 65_536),
    )
    repeated = (wide,) * 62
    values = _state_values(
        base,
        occurrences=repeated,
        occurrence_sha256s=(wide.occurrence_sha256,) * len(repeated),
    )

    def forbidden(*args, **kwargs):
        del args, kwargs
        raise AssertionError("coordinate preflight traversed nested occurrences")

    monkeypatch.setattr(contract, "_validate_occurrence", forbidden)
    with pytest.raises(ValueError, match="live coordinates exceed"):
        contract.OperationalLineageState(
            **values,
            _construction_token=contract._STATE_TOKEN,
        )


def test_transition_reconstructs_parent_iteration_and_route_evidence(
    transition_matrix,
):
    bundle, evidence, initial, transition = transition_matrix["accepted_death"]
    iteration = transition.parent_iteration
    assert transition.parent_route_evidence is evidence
    forged_iteration = _forged_iteration(
        iteration,
        accepted=False,
        rejection_parents_reused=True,
        accepted_parents_refreshed=False,
    )
    with pytest.raises((TypeError, ValueError)):
        contract._make_transition(
            transition.certificate,
            forged_iteration,
            evidence,
            initial,
            run_id=transition.run_id,
            step_index=transition.step_index,
        )

    alien_evidence = transition_matrix["accepted_replacement"][1]
    with pytest.raises((TypeError, ValueError)):
        contract._make_transition(
            transition.certificate,
            iteration,
            alien_evidence,
            initial,
            run_id=transition.run_id,
            step_index=transition.step_index,
        )

    alien_certificate = transition_matrix["rejected_death"][3].certificate
    with pytest.raises((TypeError, ValueError)):
        contract._make_transition(
            alien_certificate,
            iteration,
            evidence,
            initial,
            run_id=transition.run_id,
            step_index=transition.step_index,
        )
    assert bundle["contract_owner"].certificate is transition.certificate


def test_redigested_transition_flags_splices_and_digests_are_refused(
    transition_matrix,
):
    transition = transition_matrix["accepted_replacement"][3]
    other = transition_matrix["accepted_death"][3]
    attacks = (
        {"accepted": False},
        {"source_occurrence_index": 0},
        {"selected_source_identifier": other.selected_source_identifier},
        {"destroyed_identifier": other.destroyed_identifier},
        {"created_occurrence": None, "created_occurrence_sha256": None},
        {"post_state": transition.pre_state},
        {"rejection_reused_exact_state": True},
        {"accepted_allocated_fresh_serial": 1},
        {"stable_model_key_sort_only": False},
        {"identifiers_absent_from_model_projection": False},
        {"parent_route_evidence": other.parent_route_evidence},
        {"parent_route_evidence_sha256": "0" * 64},
    )
    for updates in attacks:
        values = _transition_values(transition, **updates)
        with pytest.raises((TypeError, ValueError)):
            contract.OperationalLineageTransition(
                **values,
                _construction_token=contract._TRANSITION_TOKEN,
            )


def test_result_transition_omission_duplication_reorder_and_parent_splice_refuse(
    end_to_end_case,
    zero_end_to_end_case,
    transition_matrix,
):
    _, _, _, result = end_to_end_case
    first, second = result.transitions
    other_transition = transition_matrix["accepted_death"][3]
    zero_result = zero_end_to_end_case[3]
    attacks = (
        {"transitions": (), "transition_sha256s": ()},
        {
            "transitions": (first, first),
            "transition_sha256s": (
                first.transition_sha256,
                first.transition_sha256,
            ),
        },
        {
            "transitions": (second, first),
            "transition_sha256s": (
                second.transition_sha256,
                first.transition_sha256,
            ),
        },
        {
            "transitions": (first, other_transition),
            "transition_sha256s": (
                first.transition_sha256,
                other_transition.transition_sha256,
            ),
        },
        {
            "parent_result": zero_result.parent_result,
            "parent_result_sha256": zero_result.parent_result_sha256,
        },
    )
    for updates in attacks:
        values = _result_values(result, **updates)
        with pytest.raises((TypeError, ValueError)):
            contract.OperationalLocalThinningLineageResult(
                **values,
                _construction_token=contract._RESULT_TOKEN,
            )


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("proposal_count", 0),
        ("accepted_count", 0),
        ("rejected_count", 1),
        ("created_lineage_count", 0),
        ("destroyed_lineage_count", 0),
        ("parent_result_revalidated", False),
        ("terminal_reused_exact_lineage_state", 1),
        ("checkpoint22_execution_was_proposal_keyed", True),
        ("checkpoint22_execution_used_contract_streams", True),
        ("identifiers_absent_from_model_projection", False),
        ("final_state_sha256", "0" * 64),
    ],
)
def test_redigested_result_counts_flags_and_hashes_refuse(
    end_to_end_case,
    field,
    replacement,
):
    result = end_to_end_case[3]
    values = _result_values(result, **{field: replacement})
    with pytest.raises((TypeError, ValueError)):
        contract.OperationalLocalThinningLineageResult(
            **values,
            _construction_token=contract._RESULT_TOKEN,
        )


def test_wrong_initial_object_run_step_and_distinct_owner_refuse(
    end_to_end_case,
):
    bundle, _, initial, result = end_to_end_case
    owner = bundle["contract_owner"]
    clone = contract._make_state(
        result.certificate,
        run_id=initial.run_id,
        initialization_index=initial.initialization_index,
        occurrences=initial.occurrences,
        retired_identifiers=initial.retired_identifiers,
        next_serial=initial.next_serial,
    )
    assert clone is not initial and clone.state_sha256 == initial.state_sha256
    calls = (
        lambda: owner.validate_lineage_result(
            result,
            clone,
            run_id=result.run_id,
            step_index=result.step_index,
        ),
        lambda: owner.validate_lineage_result(
            result,
            initial,
            run_id=result.run_id + 1,
            step_index=result.step_index,
        ),
        lambda: owner.validate_lineage_result(
            result,
            initial,
            run_id=result.run_id,
            step_index=result.step_index + 1,
        ),
    )
    for call in calls:
        with pytest.raises((TypeError, ValueError)):
            call()

    alien_owner = _certify_owner(bundle, role="1" * 64)
    with pytest.raises((TypeError, ValueError)):
        alien_owner.validate_lineage_result(
            result,
            initial,
            run_id=result.run_id,
            step_index=result.step_index,
        )


def test_factory_require_validator_and_parent_binding(tight_bundle):
    owner = tight_bundle["contract_owner"]
    parent = tight_bundle["integration_owner"]
    assert (
        contract.require_matching_plugin_bridge_counter_keyed_lineage_contract(
            parent,
            owner,
            contract_policy=contract.PLUGIN_BRIDGE_COUNTER_KEYED_LINEAGE_POLICY,
            contract_role_sha256="f" * 64,
        )
        is owner
    )
    assert (
        contract.validate_plugin_bridge_counter_keyed_lineage_certificate(
            parent,
            owner,
            contract_policy=contract.PLUGIN_BRIDGE_COUNTER_KEYED_LINEAGE_POLICY,
            contract_role_sha256="f" * 64,
        )
        is owner.certificate
    )
    for updates in (
        {"contract_policy": "unsupported"},
        {"contract_role_sha256": "1" * 64},
    ):
        arguments = {
            "contract_policy": contract.PLUGIN_BRIDGE_COUNTER_KEYED_LINEAGE_POLICY,
            "contract_role_sha256": "f" * 64,
        }
        arguments.update(updates)
        with pytest.raises((TypeError, ValueError)):
            contract.require_matching_plugin_bridge_counter_keyed_lineage_contract(
                parent,
                owner,
                **arguments,
            )


def test_every_new_record_is_nonpickle_noncopy_and_nonsubclassable(
    tight_bundle,
    end_to_end_case,
):
    owner = tight_bundle["contract_owner"]
    _, _, _, result = end_to_end_case
    transition = result.transitions[0]
    stream = owner.make_jump_proposal_stream(1, 2, 3)
    records = (
        owner,
        owner.certificate,
        stream.address,
        stream,
        result.initial_state.occurrences[0].identifier,
        result.initial_state.occurrences[0],
        result.initial_state,
        transition,
        result,
    )
    for record in records:
        for operation in (pickle.dumps, copy.copy, copy.deepcopy):
            with pytest.raises(TypeError):
                operation(record)
    for record_type in (
        contract.CounterKeyedLineageCertificate,
        contract.CounterKeyedPhiloxAddress,
        contract.CounterKeyedPhiloxStream,
        contract.OperationalLineageIdentifier,
        contract.OperationalLineagedOccurrence,
        contract.OperationalLineageState,
        contract.OperationalLineageTransition,
        contract.OperationalLocalThinningLineageResult,
        contract.CounterKeyedLineageContractOwner,
    ):
        with pytest.raises(TypeError, match="subclassed"):
            type("ForbiddenSubclass", (record_type,), {})


def test_public_surface_keeps_stream_namespace_and_parent_annotation_separate(
    tight_bundle,
):
    expected = {
        "PLUGIN_BRIDGE_COUNTER_KEYED_LINEAGE_POLICY",
        "PLUGIN_BRIDGE_COUNTER_KEYED_LINEAGE_SCHEMA_VERSION",
        "PLUGIN_BRIDGE_COUNTER_KEYED_LINEAGE_SCOPE",
        "COUNTER_KEYED_PHILOX_ADDRESS_LAYOUT",
        "COUNTER_KEY_DOMAIN_JUMP_PROPOSAL",
        "COUNTER_KEY_DOMAIN_TERMINAL_WAIT",
        "COUNTER_KEY_DOMAIN_INITIALIZER",
        "COUNTER_KEY_DOMAIN_BROWNIAN_LEFT",
        "COUNTER_KEY_DOMAIN_BROWNIAN_RIGHT",
        "COUNTER_KEY_DOMAIN_TAG_JUMP_PROPOSAL",
        "COUNTER_KEY_DOMAIN_TAG_TERMINAL_WAIT",
        "COUNTER_KEY_DOMAIN_TAG_INITIALIZER",
        "COUNTER_KEY_DOMAIN_TAG_BROWNIAN_LEFT",
        "COUNTER_KEY_DOMAIN_TAG_BROWNIAN_RIGHT",
        "COUNTER_KEY_DOMAIN_TAGS",
        "MAX_UINT64",
        "MAX_LINEAGE_NEXT_SERIAL",
        "MAX_OPERATIONAL_LINEAGE_IDENTIFIERS",
        "CounterKeyedLineageCertificate",
        "CounterKeyedLineageContractOwner",
        "CounterKeyedPhiloxAddress",
        "CounterKeyedPhiloxStream",
        "OperationalLineageIdentifier",
        "OperationalLineagedOccurrence",
        "OperationalLineageState",
        "OperationalLineageTransition",
        "OperationalLocalThinningLineageResult",
        "PluginBridgeCounterKeyedLineageContractError",
        "certify_plugin_bridge_counter_keyed_lineage_contract",
        "require_matching_plugin_bridge_counter_keyed_lineage_contract",
        "validate_plugin_bridge_counter_keyed_lineage_certificate",
    }
    assert set(contract.__all__) == expected
    result_fields = contract.OperationalLocalThinningLineageResult.__annotations__
    transition_fields = contract.OperationalLineageTransition.__annotations__
    negative_execution_flag = "checkpoint22_execution_used_contract_streams"
    assert result_fields[negative_execution_flag] == "bool"
    assert not any(
        "stream" in name or "address" in name
        for name in result_fields
        if name != negative_execution_flag
    )
    assert not any("stream" in name or "address" in name for name in transition_fields)
    owner = tight_bundle["contract_owner"]
    annotate_source = inspect.getsource(owner.annotate_result)
    assert "rng" not in inspect.signature(owner.annotate_result).parameters
    assert "make_jump_proposal_stream" not in annotate_source
    assert "make_terminal_wait_stream" not in annotate_source
    assert ".run(" not in annotate_source
    source = inspect.getsource(contract)
    tree = ast.parse(source)
    assert "not-checkpoint22-proposal-keyed-execution" in source
    assert "independent-bootstrap-or-fork-requires-fresh-run-id" in source
    assert "statistical_independence_certified" in source
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "hash" not in called_names
    state_source = inspect.getsource(contract.OperationalLineageState.__init__)
    assert "bisect_left(retired_serials, replacement.serial)" in state_source
    assert "sum(identifier.serial < replacement.serial" not in state_source


def test_optional_torch_import_boundary_is_explicit():
    module_path = Path(contract.__file__).resolve()
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
    import heterodiff.processes.plugin_bridge_counter_keyed_lineage_contract
except ModuleNotFoundError as error:
    text = str(error)
    assert "counter-keyed lineage contracts require" in text
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
