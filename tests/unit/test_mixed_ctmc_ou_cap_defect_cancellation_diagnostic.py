from __future__ import annotations

import ast
import math
from pathlib import Path

import numpy as np
import pytest

from heterodiff.evaluation.mixed_ctmc_ou_cap_defect_cancellation_diagnostic import (
    DIAGNOSTIC_SCOPE,
    NUMERICAL_QUALIFICATION,
    build_mixed_ctmc_ou_cap_defect_cancellation_diagnostic,
)
from heterodiff.evaluation.mixed_ctmc_ou_path_kl_diagnostic import (
    TerminalMatchedResidual,
)


@pytest.fixture(scope="module")
def diagnostic():
    return build_mixed_ctmc_ou_cap_defect_cancellation_diagnostic()


def test_scope_is_finite_noninterval_and_nonpromotional(diagnostic) -> None:
    assert diagnostic.scope == DIAGNOSTIC_SCOPE
    assert diagnostic.numerical_qualification == NUMERICAL_QUALIFICATION
    boundary = diagnostic.boundary
    assert boundary.mathematical_shared_guide_cancellation_exact is True
    assert boundary.mathematical_blocked_birth_identity_exact is True
    assert boundary.fixture_cap_defect_cancellation_exercised is True
    assert boundary.floating_matrix_exponentials_interval_certified is False
    assert boundary.floating_quadrature_interval_certified is False
    assert boundary.adaptive_error_estimate_is_rigorous_bound is False
    assert boundary.cap_defect_used_as_path_kl_summand is False
    assert boundary.general_cap_stability_proved is False
    assert boundary.learned_estimator_exercised is False
    assert boundary.association_marginalization_exercised is False
    assert boundary.continuous_marks_attached_to_occurrences is False
    assert boundary.general_c17_theorem_proved is False
    assert boundary.r2_hybrid_completed is False
    assert boundary.claim_promotion_authorized is False
    assert boundary.confirmatory_execution_authorized is False
    assert boundary.production_execution_authorized is False


def test_source_does_not_import_learned_or_association_components() -> None:
    source_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "heterodiff"
        / "evaluation"
        / "mixed_ctmc_ou_cap_defect_cancellation_diagnostic.py"
    )
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_names.add(node.module)
    assert not any("configuration_residual" in name for name in imported_names)
    assert not any("association_preconditioner" in name for name in imported_names)
    assert not any("association_observation" in name for name in imported_names)


def test_auxiliary_cap3_space_restricts_to_the_cap2_state_order(diagnostic) -> None:
    assert diagnostic.auxiliary_cap == 3
    assert diagnostic.state_vectors == (
        (0, 0),
        (0, 1),
        (1, 0),
        (0, 2),
        (1, 1),
        (2, 0),
    )
    assert diagnostic.auxiliary_state_vectors == diagnostic.state_vectors + (
        (0, 3),
        (1, 2),
        (2, 1),
        (3, 0),
    )
    np.testing.assert_array_equal(
        diagnostic.evaluation_times,
        np.asarray((0.0, 0.2, 0.4, 0.6000000000000001, 0.8)),
    )
    np.testing.assert_array_equal(
        diagnostic.evaluation_coordinates,
        np.asarray((-1.0, 0.0, 1.0)),
    )
    for item in diagnostic.time_slices:
        np.testing.assert_array_equal(
            item.cap_mask,
            np.asarray((False, False, False, True, True, True)),
        )


def test_restricted_guide_defect_equals_only_blocked_birth_action(
    diagnostic,
) -> None:
    assert diagnostic.maximum_absolute_cap_defect == pytest.approx(
        0.5361111111111103,
        rel=0.0,
        abs=2.0e-15,
    )
    assert diagnostic.maximum_defect_identity_residual < 1.0e-14
    for item in diagnostic.time_slices:
        np.testing.assert_allclose(
            item.generator_harmonic_defect,
            item.blocked_birth_defect,
            rtol=0.0,
            atol=1.0e-14,
        )
        np.testing.assert_array_equal(
            item.generator_harmonic_defect[~item.cap_mask],
            np.zeros(3, dtype=np.float64),
        )
        assert np.all(item.generator_harmonic_defect[item.cap_mask] < 0.0)
        assert item.maximum_defect_identity_residual < 1.0e-14

    np.testing.assert_allclose(
        diagnostic.time_slices[-1].generator_harmonic_defect,
        np.asarray(
            (
                0.0,
                0.0,
                0.0,
                -0.5361111111111103,
                -0.38510638297872246,
                -0.3379999999999996,
            )
        ),
        rtol=0.0,
        atol=2.0e-14,
    )


def test_shared_guide_recovers_error_and_terminal_matching(diagnostic) -> None:
    assert diagnostic.maximum_error_recovery_residual < 1.0e-15
    assert diagnostic.maximum_target_log_reconstruction_residual < 1.0e-15
    assert diagnostic.maximum_plugin_log_reconstruction_residual < 1.0e-15
    assert diagnostic.terminal_exact_residual_zero is True
    assert diagnostic.terminal_plugin_residual_zero is True
    assert diagnostic.terminal_guide_matches_target_likelihood is True

    initial = diagnostic.time_slices[0]
    terminal = diagnostic.time_slices[-1]
    assert np.any(initial.exact_residual != 0.0)
    np.testing.assert_array_equal(
        terminal.exact_residual,
        np.zeros(len(diagnostic.state_vectors), dtype=np.float64),
    )
    np.testing.assert_array_equal(
        terminal.plugin_residual_at_zero_coordinate,
        np.zeros(len(diagnostic.state_vectors), dtype=np.float64),
    )
    np.testing.assert_array_equal(
        terminal.recovered_error_at_zero_coordinate,
        np.zeros(len(diagnostic.state_vectors), dtype=np.float64),
    )


def test_all_five_terms_match_existing_fork_b_diagnostic(diagnostic) -> None:
    shared = diagnostic.shared_guide_decomposition
    existing = diagnostic.existing_path_diagnostic.decomposition
    agreement = diagnostic.existing_diagnostic_agreement

    assert shared.initializer > 0.0
    assert shared.ou_continuous_gradient > 0.0
    assert shared.birth > 0.0
    assert shared.death > 0.0
    assert shared.replacement > 0.0
    assert shared.initializer == pytest.approx(
        existing.initializer.total_exact_to_plugin,
        rel=0.0,
        abs=1.0e-15,
    )
    assert shared.ou_continuous_gradient == pytest.approx(
        existing.ou_continuous_gradient,
        rel=0.0,
        abs=1.0e-15,
    )
    assert (shared.birth, shared.death, shared.replacement) == pytest.approx(
        (existing.jumps.birth, existing.jumps.death, existing.jumps.replacement),
        rel=0.0,
        abs=1.0e-14,
    )
    assert shared.total == pytest.approx(existing.total, rel=0.0, abs=1.0e-14)
    assert agreement.maximum_component_absolute_difference < 1.0e-14
    assert agreement.total_absolute_difference < 1.0e-14


def test_nonzero_cap_defect_is_excluded_from_path_total(diagnostic) -> None:
    shared = diagnostic.shared_guide_decomposition
    five_term_sum = math.fsum(
        (
            shared.initializer,
            shared.ou_continuous_gradient,
            shared.birth,
            shared.death,
            shared.replacement,
        )
    )
    assert diagnostic.maximum_absolute_cap_defect > 0.5
    assert diagnostic.path_total_excludes_cap_defect is True
    assert shared.total == pytest.approx(five_term_sum, rel=0.0, abs=2.0e-15)
    assert shared.total != pytest.approx(
        five_term_sum + diagnostic.maximum_absolute_cap_defect,
        rel=0.0,
        abs=1.0e-10,
    )
    assert shared.total == pytest.approx(
        0.22604807707806718,
        rel=0.0,
        abs=2.0e-14,
    )


def test_zero_path_error_stays_zero_while_guide_defect_remains_nonzero() -> None:
    zero = build_mixed_ctmc_ou_cap_defect_cancellation_diagnostic(
        residual=TerminalMatchedResidual(
            discrete_scale=0.0,
            continuous_slope=0.0,
            gauge_scale=0.0,
        )
    )
    shared = zero.shared_guide_decomposition
    assert zero.maximum_absolute_cap_defect > 0.5
    assert shared.initializer == pytest.approx(0.0, rel=0.0, abs=2.0e-16)
    assert shared.ou_continuous_gradient == 0.0
    assert shared.birth == 0.0
    assert shared.death == 0.0
    assert shared.replacement == 0.0
    assert shared.total == pytest.approx(0.0, rel=0.0, abs=2.0e-16)
    assert zero.existing_diagnostic_agreement.maximum_component_absolute_difference < (
        2.0e-16
    )
    assert zero.path_total_excludes_cap_defect is True


def test_public_arrays_are_read_only(diagnostic) -> None:
    arrays = [diagnostic.evaluation_times, diagnostic.evaluation_coordinates]
    for item in diagnostic.time_slices:
        arrays.extend(
            (
                item.exact_cap2_information,
                item.restricted_cap3_guide,
                item.exact_residual,
                item.plugin_residual_at_zero_coordinate,
                item.recovered_error_at_zero_coordinate,
                item.generator_harmonic_defect,
                item.blocked_birth_defect,
                item.cap_mask,
            )
        )
    for array in arrays:
        assert array.flags.writeable is False
        with pytest.raises(ValueError):
            array.flat[0] = array.flat[0]


def test_inputs_fail_closed() -> None:
    with pytest.raises(TypeError, match="TerminalMatchedResidual"):
        build_mixed_ctmc_ou_cap_defect_cancellation_diagnostic(
            residual=object()  # type: ignore[arg-type]
        )
    with pytest.raises(TypeError, match="non-boolean"):
        build_mixed_ctmc_ou_cap_defect_cancellation_diagnostic(
            quadrature_absolute_tolerance=True
        )
    with pytest.raises(ValueError, match="greater than zero"):
        build_mixed_ctmc_ou_cap_defect_cancellation_diagnostic(
            quadrature_relative_tolerance=0.0
        )
    with pytest.raises(TypeError, match="integer non-boolean"):
        build_mixed_ctmc_ou_cap_defect_cancellation_diagnostic(
            quadrature_subdivisions=False
        )
    with pytest.raises(ValueError, match="between"):
        build_mixed_ctmc_ou_cap_defect_cancellation_diagnostic(
            quadrature_subdivisions=10_001
        )
