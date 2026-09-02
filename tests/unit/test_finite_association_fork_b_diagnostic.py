from dataclasses import FrozenInstanceError, fields, replace
import math
from types import SimpleNamespace

import numpy as np
import pytest

import heterodiff.evaluation.finite_association_fork_b_diagnostic as fork_b_module
from heterodiff.evaluation.finite_association_fork_b_diagnostic import (
    FINITE_ASSOCIATION_FORK_B_CONTINUOUS_COMPONENT_DISPOSITION,
    FINITE_ASSOCIATION_FORK_B_ORIENTATION,
    FINITE_ASSOCIATION_FORK_B_SCOPE,
    FINITE_ASSOCIATION_FORK_B_STATUS,
    FiniteAssociationForkBComponentDiagnostic,
    FiniteAssociationForkBDiagnostic,
    FiniteAssociationForkBObservationDiagnostic,
    evaluate_finite_association_fork_b_diagnostic,
)
from heterodiff.evaluation.finite_association_residual_evaluator import (
    bind_test_only_finite_association_logit_evaluator,
)
from heterodiff.experiments.finite_association_guided_residual_pilot import (
    build_frozen_association_residual_fixture,
    frozen_association_fixture_content_digests,
    frozen_association_fixture_sha256,
)
from heterodiff.theory.finite_bridge_family_path_control import (
    FINITE_BRIDGE_JUMP_FAMILY_ORDER,
    tilted_path_kl_by_edge_family,
)
from heterodiff.theory.finite_bridge_path_control import tilted_path_kl
from heterodiff.theory.finite_bridge_path_control import (
    potential_tilted_generator,
)


def _test_certificate(fixture):
    maximum = 0.1
    return SimpleNamespace(
        passed=True,
        parameter_sha256="1" * 64,
        frozen_fixture_sha256=frozen_association_fixture_sha256(
            frozen_association_fixture_content_digests(fixture)
        ),
        feature_sha256="2" * 64,
        input_features=21,
        hidden_width=32,
        grid_intervals=4096,
        grid_points=4097,
        time_chunk_size=128,
        pair_count=420,
        evaluated_output_count=4097 * 420,
        layer_outward_row_sums=(1.0, 1.0, 1.0),
        input_time_lipschitz=1.0,
        network_time_lipschitz=1.0,
        maximum_grid_absolute_correction=maximum,
        outward_grid_maximum=math.nextafter(maximum, math.inf),
        half_cell_allowance=0.01,
        certified_maximum_absolute_correction=0.11,
        correction_limit=20.0,
        certificate_sha256="3" * 64,
    )


@pytest.fixture(scope="module")
def finite_diagnostic():
    fixture = build_frozen_association_residual_fixture()
    state_residual = np.linspace(-1.0, 1.0, 20)[:, None]
    observation_density = np.asarray(
        fixture.population.observation_marginal_density, dtype=np.float64
    )[None, :]

    def evaluate_logits(times):
        return np.stack(
            [
                np.log(fixture.guide.density_grid(float(direct_time)))
                + (1.0 - float(direct_time)) * 0.05 * state_residual
                - np.log(observation_density)
                for direct_time in times
            ],
            axis=0,
        )

    evaluator = bind_test_only_finite_association_logit_evaluator(
        evaluate_logits, _test_certificate(fixture)
    )
    return (
        fixture,
        evaluator,
        evaluate_finite_association_fork_b_diagnostic(
            evaluator, fixture, test_only=True
        ),
    )


def test_family_helper_exactly_partitions_existing_target_first_total():
    generator = np.asarray(((-3.0, 1.0, 2.0), (1.0, -2.0, 1.0), (1.0, 1.0, -2.0)))
    initial = np.asarray((0.2, 0.3, 0.5))
    family_indices = np.asarray(((-1, 0, 1), (0, -1, 2), (1, 2, -1)), dtype=np.int64)

    def reference(time):
        return np.exp(np.asarray((0.1 * time, -0.2 * time, 0.05 * time)))

    def candidate(time):
        return np.exp(np.asarray((0.2 * time, -0.1 * time, -0.05 * time)))

    split = tilted_path_kl_by_edge_family(
        initial, generator, reference, candidate, 1.0, family_indices
    )
    existing = tilted_path_kl(initial, generator, reference, candidate, 1.0)
    assert split.orientation == "KL(P_REFERENCE_H || P_CANDIDATE_H_HAT)"
    assert split.family_names == FINITE_BRIDGE_JUMP_FAMILY_ORDER
    assert split.active_edge_counts == (2, 2, 2)
    assert split.dynamic == pytest.approx(
        split.birth_dynamic + split.death_dynamic + split.replacement_dynamic,
        rel=2.0e-12,
        abs=2.0e-14,
    )
    assert split.total == pytest.approx(existing.total, rel=2.0e-11, abs=2.0e-13)
    assert split.aggregate_state_transition_rates_used is True
    assert split.interval_enclosure_provided is False
    assert split.ode_discretization_error_enclosed is False


def test_manual_target_first_k0_and_qh_phi_family_oracle():
    generator = np.asarray(((-3.0, 1.0, 2.0), (1.0, -2.0, 1.0), (1.0, 1.0, -2.0)))
    reference_values = np.asarray((1.4, 0.8, 1.1))
    error = np.asarray((0.25, -0.15, 0.05))
    candidate_values = reference_values * np.exp(error)
    family_indices = np.asarray(((-1, 0, 1), (0, -1, 2), (1, 2, -1)), dtype=np.int64)

    def reference(_time):
        return reference_values

    def candidate(_time):
        return candidate_values

    reference_generator = potential_tilted_generator(generator, reference, 0.0)
    system = np.vstack((reference_generator.T[:-1], np.ones(3)))
    right = np.asarray((0.0, 0.0, 1.0))
    target_mass = np.linalg.solve(system, right)
    base_initial = target_mass / reference_values
    base_initial /= base_initial.sum()
    duration = 0.7
    split = tilted_path_kl_by_edge_family(
        base_initial,
        generator,
        reference,
        candidate,
        duration,
        family_indices,
        reference_marginal=lambda _time: target_mass,
    )
    candidate_initial = base_initial * candidate_values
    candidate_initial /= candidate_initial.sum()
    manual_k0 = float(target_mass @ (np.log(target_mass) - np.log(candidate_initial)))
    reverse_k0 = float(
        candidate_initial @ (np.log(candidate_initial) - np.log(target_mass))
    )
    manual_family = np.zeros(3)
    for source in range(3):
        for destination in range(3):
            family = family_indices[source, destination]
            if family < 0:
                continue
            delta_error = error[destination] - error[source]
            phi = math.exp(delta_error) - 1.0 - delta_error
            manual_family[family] += (
                duration
                * target_mass[source]
                * reference_generator[source, destination]
                * phi
            )
    assert split.initial == pytest.approx(manual_k0, rel=2.0e-12, abs=2.0e-14)
    assert split.initial != pytest.approx(reverse_k0, rel=1.0e-4, abs=1.0e-8)
    assert np.asarray(
        (split.birth_dynamic, split.death_dynamic, split.replacement_dynamic)
    ) == pytest.approx(manual_family, rel=2.0e-11, abs=2.0e-13)


def test_exact_and_constant_gauge_candidates_have_zero_path_error():
    generator = np.asarray(((-3.0, 1.0, 2.0), (1.0, -2.0, 1.0), (1.0, 1.0, -2.0)))
    base_initial = np.asarray((0.2, 0.3, 0.5))
    families = np.asarray(((-1, 0, 1), (0, -1, 2), (1, 2, -1)), dtype=np.int64)

    def reference(time):
        return np.exp(np.asarray((0.1 * time, -0.2 * time, 0.05 * time)))

    exact = tilted_path_kl_by_edge_family(
        base_initial, generator, reference, reference, 1.0, families
    )
    gauged = tilted_path_kl_by_edge_family(
        base_initial,
        generator,
        reference,
        lambda time: 3.7 * reference(time),
        1.0,
        families,
    )
    assert exact.total < 1.0e-24
    assert gauged.total < 1.0e-24


def test_family_helper_rejects_unassigned_or_fabricated_edge_families():
    generator = np.asarray(((-3.0, 1.0, 2.0), (1.0, -2.0, 1.0), (1.0, 1.0, -2.0)))
    initial = np.asarray((0.2, 0.3, 0.5))

    def potential(_time):
        return np.ones(3)

    missing = np.asarray(((-1, -1, 1), (0, -1, 2), (1, 2, -1)), dtype=np.int64)
    with pytest.raises(ValueError, match="every positive aggregate edge"):
        tilted_path_kl_by_edge_family(
            initial, generator, potential, potential, 1.0, missing
        )
    fabricated = np.asarray(((0, 0, 1), (0, -1, 2), (1, 2, -1)), dtype=np.int64)
    with pytest.raises(ValueError, match="structural-zero"):
        tilted_path_kl_by_edge_family(
            initial, generator, potential, potential, 1.0, fabricated
        )
    with pytest.raises(TypeError, match="must not contain booleans"):
        tilted_path_kl_by_edge_family(
            initial,
            generator,
            potential,
            potential,
            1.0,
            np.zeros((3, 3), dtype=np.bool_),
        )
    with pytest.raises(ValueError, match="must have shape"):
        tilted_path_kl_by_edge_family(
            initial,
            generator,
            potential,
            potential,
            1.0,
            np.full((2, 2), -1, dtype=np.int64),
        )
    with pytest.raises(ValueError, match="finite"):
        tilted_path_kl_by_edge_family(
            initial,
            generator,
            potential,
            lambda _time: np.asarray((1.0, np.inf, 1.0)),
            1.0,
            np.asarray(((-1, 0, 1), (0, -1, 2), (1, 2, -1)), dtype=np.int64),
        )


def test_public_record_field_inventories_are_exact_and_duplicate_free():
    assert tuple(
        field.name for field in fields(FiniteAssociationForkBComponentDiagnostic)
    ) == (
        "component_id",
        "applicability",
        "target_measure",
        "integration_method",
        "primary_solver_settings",
        "refined_solver_settings",
        "value",
        "refined_value",
        "primary_refined_absolute_difference",
        "primary_numerical_error_estimate",
        "refined_numerical_error_estimate",
        "numerical_error_estimate_disposition",
        "interval_certified",
        "active_aggregate_edge_count",
        "entered_issued_total",
    )
    assert tuple(
        field.name for field in fields(FiniteAssociationForkBObservationDiagnostic)
    ) == (
        "observation_index",
        "observation_mass",
        "components",
        "primary_initial",
        "primary_birth",
        "primary_death",
        "primary_replacement",
        "primary_dynamic",
        "primary_total",
        "refined_initial",
        "refined_birth",
        "refined_death",
        "refined_replacement",
        "refined_dynamic",
        "refined_total",
        "separately_computed_aggregate_total",
        "family_aggregate_crosscheck_absolute_difference",
        "initial_refinement_change",
        "birth_refinement_change",
        "death_refinement_change",
        "replacement_refinement_change",
        "total_refinement_change",
        "target_marginal_maximum_absolute_error",
        "terminal_log_potential_maximum_absolute_error",
        "primary_quadrature_error_estimate",
        "refined_quadrature_error_estimate",
        "primary_potential_evaluations",
        "refined_potential_evaluations",
        "numerical_failures",
    )
    assert tuple(field.name for field in fields(FiniteAssociationForkBDiagnostic)) == (
        "schema_version",
        "scope",
        "status",
        "orientation",
        "continuous_component_disposition",
        "local_compatibility_fixture_sha256",
        "preregistered_production_fixture_sha256",
        "fixture_content_sha256",
        "edge_family_partition_sha256",
        "evaluator_parameter_sha256",
        "evaluator_feature_sha256",
        "evaluator_certificate_sha256",
        "classifier_sha256",
        "execution_receipt_sha256",
        "campaign_sha256",
        "evaluator_production_bound",
        "test_only_evaluator_used",
        "test_only_callback_determinism_checked",
        "determinism_unique_input_count",
        "production_checkpoint_evaluation_supported",
        "runtime",
        "primary_solver_settings",
        "refined_solver_settings",
        "family_names",
        "active_edge_counts",
        "observations",
        "observation_mass",
        "observation_weighted_initial",
        "observation_weighted_birth",
        "observation_weighted_death",
        "observation_weighted_replacement",
        "observation_weighted_dynamic",
        "observation_weighted_total",
        "maximum_primary_refined_total_change",
        "maximum_target_marginal_absolute_error",
        "maximum_terminal_log_potential_absolute_error",
        "maximum_family_aggregate_crosscheck_absolute_difference",
        "numerical_failures",
        "all_21_observations_evaluated",
        "exact_finite_target_semigroup_marginal_used",
        "association_marginalized_likelihood_used",
        "aggregate_transition_family_partition_used",
        "occurrence_attached_mark_fibers_exercised",
        "continuous_coordinate_energy_exercised",
        "cap_reference_defect_cancellation_certified",
        "interval_enclosure_provided",
        "simultaneous_coverage_proved",
        "rigorous_numerical_enclosure_present",
        "ode_or_quadrature_error_rigorously_enclosed",
        "full_fork_b_certificate_complete",
        "c17_theorem_proved",
        "r1_a1_status",
        "r1_a1_result_slot_qualified",
        "r2_hybrid_status",
        "r2_result_slot_qualified",
        "manuscript_claim_promoted",
        "execution_authorized",
    )


def test_all_21_partial_diagnostic_has_family_custody_and_no_broader_effect(
    finite_diagnostic,
):
    fixture, evaluator, result = finite_diagnostic
    assert result.scope == FINITE_ASSOCIATION_FORK_B_SCOPE
    assert result.status == FINITE_ASSOCIATION_FORK_B_STATUS
    assert result.orientation == FINITE_ASSOCIATION_FORK_B_ORIENTATION
    assert result.continuous_component_disposition == (
        FINITE_ASSOCIATION_FORK_B_CONTINUOUS_COMPONENT_DISPOSITION
    )
    assert result.test_only_evaluator_used is True
    assert result.evaluator_production_bound is False
    assert result.production_checkpoint_evaluation_supported is False
    assert result.test_only_callback_determinism_checked is True
    assert result.determinism_unique_input_count >= 4
    assert result.local_compatibility_fixture_sha256 == (
        "b96901980055f5ecfda653373ed935010040698985e274e0ebd3f04822f3e75d"
    )
    assert result.preregistered_production_fixture_sha256 == (
        "0121b487728b40356de6707a33ba4881100c3d1b587259b19723463a60cecdcc"
    )
    assert result.classifier_sha256 is None
    assert result.execution_receipt_sha256 is None
    assert result.campaign_sha256 is None
    assert result.evaluator_parameter_sha256 == evaluator.certification.parameter_sha256
    assert result.family_names == ("birth", "death", "replacement")
    assert result.active_edge_counts == (30, 30, 60)
    assert len(result.observations) == 21
    assert tuple(item.observation_index for item in result.observations) == tuple(
        range(21)
    )
    assert np.allclose(
        result.observation_mass,
        fixture.population.observation_marginal_mass,
        atol=0.0,
        rtol=0.0,
    )
    assert result.all_21_observations_evaluated is True
    assert result.exact_finite_target_semigroup_marginal_used is True
    assert result.association_marginalized_likelihood_used is True
    assert result.aggregate_transition_family_partition_used is True
    assert result.numerical_coherence_passed is True
    assert result.maximum_target_marginal_absolute_error < 1.0e-12
    assert result.maximum_terminal_log_potential_absolute_error < 1.0e-12
    assert result.maximum_primary_refined_total_change < 1.0e-10
    assert result.maximum_family_aggregate_crosscheck_absolute_difference < 1.0e-8
    assert all(
        item.family_aggregate_crosscheck_absolute_difference < 1.0e-8
        for item in result.observations
    )
    assert result.observation_weighted_initial > 0.0
    assert result.observation_weighted_birth > 0.0
    assert result.observation_weighted_death > 0.0
    assert result.observation_weighted_replacement > 0.0
    assert result.observation_weighted_total == pytest.approx(
        result.observation_weighted_initial
        + result.observation_weighted_birth
        + result.observation_weighted_death
        + result.observation_weighted_replacement,
        rel=2.0e-12,
        abs=2.0e-14,
    )
    for item in result.observations:
        assert tuple(component.component_id for component in item.components) == (
            "K0_NORMALIZED_INITIALIZER",
            "KC_CONTINUOUS_COORDINATES",
            "K_PLUS_BIRTH",
            "K_MINUS_DEATH",
            "K_R_REPLACEMENT",
        )
        assert item.components[0].target_measure == (
            "EXACT_CONDITIONED_TARGET_INITIAL_LAW"
        )
        assert item.components[1].target_measure == (
            "NOT_APPLICABLE_NO_CONTINUOUS_COORDINATES"
        )
        assert all(
            component.target_measure == "EXACT_CONDITIONED_TARGET_OCCUPATION"
            for component in item.components[2:]
        )
        assert all(
            component.interval_certified is False for component in item.components
        )
        assert item.components[0].active_aggregate_edge_count == 0
        assert item.components[0].entered_issued_total is True
        assert item.components[1].applicability == (
            "NOT_APPLICABLE_NO_CONTINUOUS_COORDINATES"
        )
        assert item.components[1].value is None
        assert item.components[1].entered_issued_total is False
        assert tuple(
            component.active_aggregate_edge_count for component in item.components[2:]
        ) == (30, 30, 60)
        assert all(
            component.numerical_error_estimate_disposition
            == "SHARED_VECTOR_ADAPTIVE_ESTIMATE_NOT_AN_ENCLOSURE"
            for component in item.components[2:]
        )
    for field in (
        "occurrence_attached_mark_fibers_exercised",
        "continuous_coordinate_energy_exercised",
        "cap_reference_defect_cancellation_certified",
        "interval_enclosure_provided",
        "simultaneous_coverage_proved",
        "rigorous_numerical_enclosure_present",
        "ode_or_quadrature_error_rigorously_enclosed",
        "full_fork_b_certificate_complete",
        "c17_theorem_proved",
        "r1_a1_result_slot_qualified",
        "r2_result_slot_qualified",
        "manuscript_claim_promoted",
        "execution_authorized",
    ):
        assert getattr(result, field) is False
    assert result.r1_a1_status == "NOT_RUN"
    assert result.r2_hybrid_status == "NOT_RUN"


def test_partial_record_rejects_c17_or_execution_promotion(finite_diagnostic):
    _fixture, _evaluator, result = finite_diagnostic
    with pytest.raises(ValueError, match="c17_theorem_proved must remain false"):
        replace(result, c17_theorem_proved=True)
    with pytest.raises(ValueError, match="execution_authorized must remain false"):
        replace(result, execution_authorized=True)


def test_family_partition_is_independently_pinned_to_count_vector_deltas(
    finite_diagnostic,
):
    fixture, _evaluator, result = finite_diagnostic
    matrix, counts, digest = fork_b_module._edge_family_partition(fixture)
    assert counts == (30, 30, 60)
    assert digest == result.edge_family_partition_sha256
    states = fixture.latent_space.states
    generator = fixture.oracle.generator
    for source, source_counts in enumerate(states):
        for destination, destination_counts in enumerate(states):
            if source == destination or generator[source, destination] <= 0.0:
                assert matrix[source, destination] == -1
                continue
            delta = tuple(
                destination_counts[index] - source_counts[index]
                for index in range(len(source_counts))
            )
            positive = tuple(value for value in delta if value > 0)
            negative = tuple(value for value in delta if value < 0)
            if sum(delta) == 1 and positive == (1,) and not negative:
                expected = 0
            elif sum(delta) == -1 and negative == (-1,) and not positive:
                expected = 1
            elif sum(delta) == 0 and positive == (1,) and negative == (-1,):
                expected = 2
            else:
                pytest.fail("positive generator edge has an invalid count delta")
            assert matrix[source, destination] == expected


def test_opposing_family_refinement_drift_cannot_cancel_in_total(
    finite_diagnostic,
):
    _fixture, _evaluator, result = finite_diagnostic
    record = result.observations[0]
    shift = 2.0e-8
    shifted_birth = record.refined_birth + shift
    shifted_death = record.refined_death - shift
    assert shifted_death >= 0.0
    birth_component = replace(
        record.components[2],
        refined_value=shifted_birth,
        primary_refined_absolute_difference=abs(record.primary_birth - shifted_birth),
    )
    death_component = replace(
        record.components[3],
        refined_value=shifted_death,
        primary_refined_absolute_difference=abs(record.primary_death - shifted_death),
    )
    components = (
        record.components[:2]
        + (birth_component, death_component)
        + record.components[4:]
    )
    with pytest.raises(
        ValueError, match="failed observation record cannot issue component totals"
    ):
        replace(
            record,
            components=components,
            refined_birth=shifted_birth,
            refined_death=shifted_death,
            birth_refinement_change=abs(record.primary_birth - shifted_birth),
            death_refinement_change=abs(record.primary_death - shifted_death),
        )


def test_test_only_evaluator_cannot_enter_production_lane(finite_diagnostic):
    fixture, evaluator, _result = finite_diagnostic
    with pytest.raises(ValueError, match="requires test_only=True"):
        evaluate_finite_association_fork_b_diagnostic(
            evaluator, fixture, test_only=False
        )


def test_crosscheck_drift_refuses_atomically_before_any_summary(
    finite_diagnostic, monkeypatch
):
    fixture, evaluator, _result = finite_diagnostic
    original = fork_b_module.tilted_path_kl

    def drifted_aggregate(*args, **kwargs):
        result = original(*args, **kwargs)
        return SimpleNamespace(total=result.total + 1.0)

    monkeypatch.setattr(fork_b_module, "tilted_path_kl", drifted_aggregate)
    with pytest.raises(
        ArithmeticError,
        match="refused before issuing totals: .*crosscheck exceeds",
    ):
        evaluate_finite_association_fork_b_diagnostic(
            evaluator, fixture, test_only=True
        )


def test_terminal_mismatch_refuses_before_path_totals():
    fixture = build_frozen_association_residual_fixture()
    observation_density = np.asarray(
        fixture.population.observation_marginal_density, dtype=np.float64
    )[None, :]

    def terminal_mismatch(times):
        return np.stack(
            [
                np.log(fixture.guide.density_grid(float(time)))
                - np.log(observation_density)
                + 0.01
                for time in times
            ],
            axis=0,
        )

    evaluator = bind_test_only_finite_association_logit_evaluator(
        terminal_mismatch, _test_certificate(fixture)
    )
    with pytest.raises(ValueError, match="terminal boundary"):
        evaluate_finite_association_fork_b_diagnostic(
            evaluator, fixture, test_only=True
        )


def test_candidate_occupancy_substitution_refuses_atomically(
    finite_diagnostic, monkeypatch
):
    fixture, evaluator, _result = finite_diagnostic
    original = fork_b_module._ExactTargetMarginal.__call__

    def substituted(self, direct_time):
        result = np.array(original(self, direct_time), copy=True)
        if float(direct_time) > 0.0:
            transfer = min(1.0e-4, 0.25 * float(result[1]))
            result[0] += transfer
            result[1] -= transfer
        return result

    monkeypatch.setattr(fork_b_module._ExactTargetMarginal, "__call__", substituted)
    with pytest.raises(ArithmeticError, match="refused before issuing totals"):
        evaluate_finite_association_fork_b_diagnostic(
            evaluator, fixture, test_only=True
        )


def test_self_signed_reordered_fixture_is_not_canonical():
    fixture = build_frozen_association_residual_fixture()
    observations = list(fixture.observation.observations)
    observations[0], observations[1] = observations[1], observations[0]
    object.__setattr__(fixture.observation, "_observations", tuple(observations))
    evaluator = bind_test_only_finite_association_logit_evaluator(
        lambda times: np.zeros((len(times), 20, 21)),
        _test_certificate(fixture),
    )
    with pytest.raises(ValueError, match="observations are not in canonical order"):
        evaluate_finite_association_fork_b_diagnostic(
            evaluator, fixture, test_only=True
        )


def test_reordered_latent_state_subject_is_not_canonical():
    fixture = build_frozen_association_residual_fixture()
    certificate = _test_certificate(fixture)
    states = list(fixture.latent_space.states)
    states[0], states[1] = states[1], states[0]
    object.__setattr__(fixture.latent_space, "states", tuple(states))
    evaluator = bind_test_only_finite_association_logit_evaluator(
        lambda times: np.zeros((len(times), 20, 21)),
        certificate,
    )
    with pytest.raises(ValueError, match="latent states are not in canonical order"):
        evaluate_finite_association_fork_b_diagnostic(
            evaluator, fixture, test_only=True
        )


def test_clean_law_cannot_replace_contaminated_overflow_subject():
    fixture = build_frozen_association_residual_fixture()
    assert fixture.observation.overflow_index == 20
    assert not np.array_equal(
        fixture.observation.kernel_mass,
        fixture.observation.clean_kernel_mass,
    )
    object.__setattr__(
        fixture.observation,
        "_kernel_mass",
        fixture.observation.clean_kernel_mass,
    )
    evaluator = bind_test_only_finite_association_logit_evaluator(
        lambda times: np.zeros((len(times), 20, 21)),
        _test_certificate(fixture),
    )
    with pytest.raises(ValueError, match="contaminated observation law"):
        evaluate_finite_association_fork_b_diagnostic(
            evaluator, fixture, test_only=True
        )


def test_fixture_certification_mismatch_fails_before_evaluation():
    fixture = build_frozen_association_residual_fixture()
    certificate = _test_certificate(fixture)
    certificate.frozen_fixture_sha256 = "f" * 64
    evaluator = bind_test_only_finite_association_logit_evaluator(
        lambda times: np.zeros((len(times), 20, 21)), certificate
    )
    with pytest.raises(ValueError, match="does not bind the frozen fixture"):
        evaluate_finite_association_fork_b_diagnostic(
            evaluator, fixture, test_only=True
        )


def test_cap_extra_term_and_component_duplication_cannot_enter_total(
    finite_diagnostic,
):
    _fixture, _evaluator, result = finite_diagnostic
    record = result.observations[0]
    with pytest.raises(ValueError, match="exact five-term order"):
        replace(
            record,
            components=record.components + (record.components[4],),
        )
    with pytest.raises(ValueError, match="observation_weighted_total is inconsistent"):
        replace(
            result,
            observation_weighted_total=result.observation_weighted_total + 0.1,
        )


def test_raw_value_or_nce_callable_cannot_substitute_for_certified_evaluator():
    fixture = build_frozen_association_residual_fixture()
    with pytest.raises(TypeError, match="evaluator must be certificate-bound"):
        evaluate_finite_association_fork_b_diagnostic(  # type: ignore[arg-type]
            lambda _times: np.zeros((1, 20, 21)),
            fixture,
            test_only=True,
        )


def test_nonfinite_potential_and_resource_failure_leave_no_partial_summary(
    finite_diagnostic, monkeypatch
):
    generator = np.asarray(((-3.0, 1.0, 2.0), (1.0, -2.0, 1.0), (1.0, 1.0, -2.0)))
    families = np.asarray(((-1, 0, 1), (0, -1, 2), (1, 2, -1)), dtype=np.int64)
    with pytest.raises(ValueError, match="finite"):
        tilted_path_kl_by_edge_family(
            np.asarray((0.2, 0.3, 0.5)),
            generator,
            lambda _time: np.ones(3),
            lambda _time: np.asarray((1.0, np.nan, 1.0)),
            1.0,
            families,
        )
    fixture, evaluator, _result = finite_diagnostic

    def exhausted(*_args, **_kwargs):
        raise MemoryError("injected resource failure")

    monkeypatch.setattr(fork_b_module, "tilted_path_kl_by_edge_family", exhausted)
    with pytest.raises(MemoryError, match="injected resource failure"):
        evaluate_finite_association_fork_b_diagnostic(
            evaluator, fixture, test_only=True
        )


def test_issued_records_are_frozen_and_arrays_are_read_only(finite_diagnostic):
    _fixture, _evaluator, result = finite_diagnostic
    with pytest.raises(FrozenInstanceError):
        result.observations[0].components[0].value = 9.0
    with pytest.raises(ValueError):
        result.observation_mass[0] = 0.0


def test_stateful_test_callback_is_refused_by_double_evaluation():
    fixture = build_frozen_association_residual_fixture()
    calls = {"count": 0}

    def stateful(times):
        calls["count"] += 1
        return np.full(
            (len(times), 20, 21),
            float(calls["count"]) * 1.0e-6,
            dtype=np.float64,
        )

    evaluator = bind_test_only_finite_association_logit_evaluator(
        stateful, _test_certificate(fixture)
    )
    with pytest.raises(ValueError, match="not deterministic"):
        evaluate_finite_association_fork_b_diagnostic(
            evaluator, fixture, test_only=True
        )


def test_production_bound_object_is_refused_by_local_compatibility_lane():
    fixture = build_frozen_association_residual_fixture()
    evaluator = bind_test_only_finite_association_logit_evaluator(
        lambda times: np.zeros((len(times), 20, 21)),
        _test_certificate(fixture),
    )
    object.__setattr__(evaluator, "_production_bound", True)
    with pytest.raises(
        ValueError, match="production checkpoint evaluation is not supported"
    ):
        evaluate_finite_association_fork_b_diagnostic(
            evaluator, fixture, test_only=False
        )


def test_aggregate_rejects_forged_per_component_edge_count(finite_diagnostic):
    _fixture, _evaluator, result = finite_diagnostic
    record = result.observations[0]
    forged_birth = replace(record.components[2], active_aggregate_edge_count=31)
    forged_record = replace(
        record,
        components=(record.components[:2] + (forged_birth,) + record.components[3:]),
    )
    with pytest.raises(ValueError, match="edge counts disagree"):
        replace(
            result,
            observations=(forged_record,) + result.observations[1:],
        )
