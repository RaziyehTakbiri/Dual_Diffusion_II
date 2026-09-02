"""Independent contract tests for the provider-based initializer kernel v2."""

from fractions import Fraction
import builtins
import hashlib
import math
import os
from pathlib import Path
import pickle
import subprocess
import sys
from unittest import mock

import numpy as np
import pytest

from heterodiff.evaluation import exact_rational_quadratic_initial_tilt as exact_source
from heterodiff.processes import certified_initial_score_provider_v1 as score_provider
from heterodiff.processes import (
    plugin_bridge_mixed_support_initial_tilt_initializer_kernel_v2 as kernel_v2,
)
from heterodiff.theory.configuration_reference import (
    CappedPoissonConfigurationReference,
    TransformedEvent,
)


_ADAPTER_ROLE = hashlib.sha256(b"cp52-test-adapter").hexdigest()
_ADAPTER_ROLE_2 = hashlib.sha256(b"cp52-test-adapter-2").hexdigest()
_KERNEL_ROLE = hashlib.sha256(b"cp52-test-kernel").hexdigest()


def _forge(instance, **changes):
    forged = object.__new__(type(instance))
    for name in instance.__annotations__:
        object.__setattr__(
            forged,
            name,
            changes[name] if name in changes else getattr(instance, name),
        )
    return forged


class _TouchBomb:
    def __eq__(self, other):
        del other
        raise AssertionError("hostile equality was touched")

    def __ne__(self, other):
        del other
        raise AssertionError("hostile inequality was touched")


class _HostileMapping:
    def items(self):
        raise AssertionError("hostile mapping iteration was touched")


@pytest.fixture(scope="module")
def m1_provider():
    source = exact_source.build_t28_m1_q_exact_score_provider()
    return score_provider.adapt_exact_rational_quadratic_initial_tilt_score_provider_v1(
        source,
        adapter_role_sha256=_ADAPTER_ROLE,
    )


@pytest.fixture(scope="module")
def m2_provider():
    source = exact_source.build_t28_m2_q_exact_score_provider()
    return score_provider.adapt_exact_rational_quadratic_initial_tilt_score_provider_v1(
        source,
        adapter_role_sha256=_ADAPTER_ROLE,
    )


def _plan(provider, strategy, *, seed=None, budget=None):
    return kernel_v2.make_mixed_support_initial_tilt_initializer_plan_v2(
        provider,
        strategy=strategy,
        residual_context=(),
        initializer_role_sha256=_KERNEL_ROLE,
        seed=seed,
        budget=budget,
    )


def _kernel(provider, strategy, *, seed=None, budget=None):
    plan = _plan(provider, strategy, seed=seed, budget=budget)
    return kernel_v2.certify_mixed_support_initial_tilt_initializer_kernel_v2(
        provider,
        plan=plan,
    )


def test_import_is_torch_lazy():
    source_root = str(Path(__file__).resolve().parents[2] / "src")
    code = r"""
import builtins
import sys
real_import = builtins.__import__
def guarded(name, *args, **kwargs):
    if name == "torch" or name.startswith("torch."):
        raise AssertionError("torch crossed the exact kernel-v2 import boundary")
    return real_import(name, *args, **kwargs)
builtins.__import__ = guarded
import heterodiff.processes.plugin_bridge_mixed_support_initial_tilt_initializer_kernel_v2
assert "torch" not in sys.modules
"""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = source_root
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(Path(__file__).resolve().parents[2]),
        env=environment,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


def test_source_never_imports_cp50_v1_or_cp30_directly():
    source = Path(kernel_v2.__file__).read_text(encoding="utf-8")
    assert (
        "plugin_bridge_mixed_support_initial_tilt_initializer_kernel.py" not in source
    )
    assert "configuration_initial_tilt_composer_torch" not in source


def test_plan_requires_exact_provider_and_provider_fixed_context(m1_provider):
    with pytest.raises(TypeError):
        _plan(object(), "bounded-rejection", seed=1, budget=1)
    with pytest.raises(ValueError, match="context"):
        kernel_v2.make_mixed_support_initial_tilt_initializer_plan_v2(
            m1_provider,
            strategy="bounded-rejection",
            residual_context=(0.0,),
            initializer_role_sha256=_KERNEL_ROLE,
            seed=1,
            budget=1,
        )
    with pytest.raises(TypeError, match="exact integer"):
        kernel_v2.make_mixed_support_initial_tilt_initializer_plan_v2(
            m1_provider,
            strategy="finite-atomic-enumeration",
            residual_context=(),
            initializer_role_sha256=_KERNEL_ROLE,
            budget=False,
        )


@pytest.mark.parametrize(
    "strategy,seed,budget",
    [
        ("bounded-rejection", 11, 2),
        ("fixed-budget-sir", 12, 2),
    ],
)
def test_missing_global_lower_bound_is_admitted_but_never_fabricated(
    m2_provider, strategy, seed, budget
):
    owner = _kernel(m2_provider, strategy, seed=seed, budget=budget)
    certificate = owner.certificate
    assert certificate.exact_log_weight_upper_bound == Fraction(0)
    assert certificate.exact_log_weight_lower_bound is None
    assert certificate.exact_global_lower_bound_available is False
    assert certificate.lower_bound_required_by_strategy is False
    assert certificate.formal_test_28_closed is False
    assert certificate.operational_reference_sampling_law_verified is False
    assert certificate.iid_proposals_verified is False
    assert certificate.analytic_target_equality_verified is False
    assert certificate.certificate_digest_cross_process_stable is False
    assert certificate.runtime_portable is False
    assert certificate.cryptographic_authentication is False
    assert "operational-reference-sampling-interface-trace" in (
        certificate.executed_measure_policy
    )


def test_stream_roots_bind_provider_but_proposal_prefix_omits_budget():
    source_a = exact_source.build_t28_m1_q_exact_score_provider()
    source_b = exact_source.build_t28_m1_q_exact_score_provider()
    provider_a = (
        score_provider.adapt_exact_rational_quadratic_initial_tilt_score_provider_v1(
            source_a, adapter_role_sha256=_ADAPTER_ROLE
        )
    )
    provider_b = (
        score_provider.adapt_exact_rational_quadratic_initial_tilt_score_provider_v1(
            source_b, adapter_role_sha256=_ADAPTER_ROLE_2
        )
    )
    a2 = _kernel(provider_a, "bounded-rejection", seed=44, budget=2).certificate
    a3 = _kernel(provider_a, "bounded-rejection", seed=44, budget=3).certificate
    b2 = _kernel(provider_b, "bounded-rejection", seed=44, budget=2).certificate
    assert a2.proposal_seed == a3.proposal_seed
    assert a2.rejection_decision_seed == a3.rejection_decision_seed
    assert a2.proposal_seed != b2.proposal_seed
    assert a2.rejection_decision_seed != b2.rejection_decision_seed


def test_complete_stream_matrix_binds_strategy_role_and_only_sir_j(
    m1_provider,
    m2_provider,
):
    rejection_2 = _kernel(
        m2_provider, "bounded-rejection", seed=77, budget=2
    ).certificate
    rejection_4 = _kernel(
        m2_provider, "bounded-rejection", seed=77, budget=4
    ).certificate
    sir_2 = _kernel(m2_provider, "fixed-budget-sir", seed=77, budget=2).certificate
    sir_4 = _kernel(m2_provider, "fixed-budget-sir", seed=77, budget=4).certificate

    assert rejection_2.proposal_seed == rejection_4.proposal_seed
    assert rejection_2.rejection_decision_seed == rejection_4.rejection_decision_seed
    assert sir_2.proposal_seed == sir_4.proposal_seed
    assert sir_2.sir_resampling_seed != sir_4.sir_resampling_seed
    assert rejection_2.proposal_seed != sir_2.proposal_seed
    assert (
        len(
            {
                77,
                rejection_2.proposal_seed,
                rejection_2.rejection_decision_seed,
            }
        )
        == 3
    )
    assert len({77, sir_2.proposal_seed, sir_2.sir_resampling_seed}) == 3

    alternate_role = kernel_v2.make_mixed_support_initial_tilt_initializer_plan_v2(
        m2_provider,
        strategy="bounded-rejection",
        residual_context=(),
        initializer_role_sha256="e" * 64,
        seed=77,
        budget=2,
    )
    alternate = kernel_v2.certify_mixed_support_initial_tilt_initializer_kernel_v2(
        m2_provider, plan=alternate_role
    ).certificate
    assert alternate.proposal_seed != rejection_2.proposal_seed
    assert alternate.rejection_decision_seed != rejection_2.rejection_decision_seed
    same_adapter_role_different_spec = _kernel(
        m1_provider,
        "bounded-rejection",
        seed=77,
        budget=2,
    ).certificate
    assert same_adapter_role_different_spec.proposal_seed != rejection_2.proposal_seed


def test_aggregate_preflight_refuses_before_any_rng_or_reference_sample(m2_provider):
    plan = _plan(m2_provider, "bounded-rejection", seed=88, budget=2)
    reference_type = type(m2_provider.reference)
    with mock.patch.object(
        kernel_v2._reference,
        "MAX_REFERENCE_BATCH_OCCURRENCES",
        1,
    ), mock.patch.object(
        kernel_v2,
        "_new_philox",
        side_effect=AssertionError("Philox constructed before preflight"),
    ), mock.patch.object(
        reference_type,
        "sample_configuration",
        side_effect=AssertionError("reference sampled before preflight"),
    ):
        with pytest.raises(ValueError, match="resource limits"):
            kernel_v2.certify_mixed_support_initial_tilt_initializer_kernel_v2(
                m2_provider,
                plan=plan,
            )


def test_m2_exact_arbitrary_rational_rejection_gaps(m2_provider):
    owner = _kernel(m2_provider, "bounded-rejection", seed=21, budget=2)
    configurations = (
        (TransformedEvent(1, (1.0, 1.0)),),
        (
            TransformedEvent(0, (1.0,)),
            TransformedEvent(1, (1.0, 1.0)),
        ),
    )
    expected = (Fraction(-7, 24), Fraction(-19, 24))
    attempts = []
    for index, configuration in enumerate(configurations):
        evaluation = m2_provider.evaluate(configuration, residual_context=())
        scored = kernel_v2._make_scored(index, evaluation, owner.certificate)
        attempt = kernel_v2._make_attempt(scored, 0, owner.certificate)
        attempts.append(attempt)
    assert tuple(attempt.exact_delta for attempt in attempts) == expected
    assert all(
        Fraction(
            attempt.quota_certificate.delta_numerator,
            attempt.quota_certificate.delta_denominator,
        )
        == delta
        for attempt, delta in zip(attempts, expected)
    )
    assert all(
        attempt.quota_certificate.decision_denominator == 1 << 64
        for attempt in attempts
    )


def test_rejection_executes_full_budget_and_retains_valid_quota_certificates(
    m2_provider,
):
    owner = _kernel(m2_provider, "bounded-rejection", seed=314, budget=4)
    first = owner.execute()
    second = owner.execute()
    assert first.result_sha256 == second.result_sha256
    assert len(first.attempts) == 4
    assert tuple(attempt.scored.index for attempt in first.attempts) == tuple(range(4))
    assert first.status in ("selected", "exhausted")
    assert owner.validate_result(first) is first
    for attempt in first.attempts:
        assert attempt.exact_delta <= 0
        assert attempt.accepted == (
            attempt.decision_word < attempt.quota_certificate.quota
        )


def test_sir_without_lower_bound_is_deterministic_and_structurally_valid(m2_provider):
    owner = _kernel(m2_provider, "fixed-budget-sir", seed=2718, budget=4)
    first = owner.execute()
    second = owner.execute()
    assert first.result_sha256 == second.result_sha256
    assert first.status == "selected"
    assert len(first.particles) == 4
    assert math_fsum(first.normalized_weights) == pytest.approx(1.0)
    assert np.all(first.normalized_weights > 0.0)
    assert owner.validate_result(first) is first


def math_fsum(values):
    return sum(float(value) for value in values)


def test_structural_result_validation_never_replays_point_source_sampler_or_rng(
    m2_provider,
):
    owner = _kernel(m2_provider, "bounded-rejection", seed=99, budget=2)
    result = owner.execute()
    provider_type = type(m2_provider)
    reference_type = type(m2_provider.reference)
    source = m2_provider.backend_adapter.source
    with mock.patch.object(
        provider_type, "evaluate", side_effect=AssertionError("evaluate replayed")
    ), mock.patch.object(
        provider_type,
        "validate_evaluation",
        side_effect=AssertionError("source point replayed"),
    ), mock.patch.object(
        type(source),
        "validate_evaluation",
        side_effect=AssertionError("underlying source replayed"),
    ), mock.patch.object(
        kernel_v2._score,
        "_replay_source_evaluation",
        side_effect=AssertionError("source replay hook called"),
    ), mock.patch.object(
        reference_type,
        "sample_configuration",
        side_effect=AssertionError("sampler replayed"),
    ), mock.patch.object(
        kernel_v2, "_new_philox", side_effect=AssertionError("RNG replayed")
    ):
        assert owner.validate_result(result) is result


def test_fully_redigested_rejection_quota_and_certificate_tampering_is_rejected(
    m2_provider,
):
    owner = _kernel(m2_provider, "bounded-rejection", seed=808, budget=2)
    result = owner.execute()
    attempt = result.attempts[0]

    forged_attempt = _forge(attempt, accepted=not attempt.accepted)
    object.__setattr__(
        forged_attempt,
        "attempt_sha256",
        kernel_v2._digest(
            kernel_v2._attempt_payload(forged_attempt),
            domain=b"heterodiff-mixed-support-rejection-attempt-v2\x00",
        ),
    )
    forged_result = _forge(
        result,
        attempts=(forged_attempt,) + result.attempts[1:],
    )
    object.__setattr__(
        forged_result,
        "result_sha256",
        kernel_v2._digest(
            kernel_v2._rejection_payload(forged_result),
            domain=b"heterodiff-mixed-support-rejection-result-v2\x00",
        ),
    )
    with pytest.raises(ValueError, match="acceptance"):
        owner.validate_result(forged_result)

    wrong_delta = (
        Fraction(-1, 3) if attempt.exact_delta != Fraction(-1, 3) else Fraction(-1, 5)
    )
    wrong_quota = kernel_v2.certify_arbitrary_rational_uint64_exp_quota(wrong_delta)
    forged_attempt = _forge(
        attempt,
        quota_certificate=wrong_quota,
        quota_certificate_sha256=wrong_quota.certificate_sha256,
    )
    object.__setattr__(
        forged_attempt,
        "attempt_sha256",
        kernel_v2._digest(
            kernel_v2._attempt_payload(forged_attempt),
            domain=b"heterodiff-mixed-support-rejection-attempt-v2\x00",
        ),
    )
    with pytest.raises(ValueError, match="another delta"):
        kernel_v2._validate_attempt(forged_attempt, certificate=owner.certificate)

    forged_certificate = _forge(
        owner.certificate,
        exact_log_weight_lower_bound=Fraction(0),
        exact_global_lower_bound_available=True,
    )
    object.__setattr__(
        forged_certificate,
        "certificate_sha256",
        kernel_v2._digest(
            kernel_v2._certificate_payload(forged_certificate),
            domain=b"heterodiff-mixed-support-initializer-certificate-v2\x00",
        ),
    )
    with pytest.raises(ValueError, match="lower bound"):
        kernel_v2.validate_mixed_support_initial_tilt_initializer_certificate_v2(
            forged_certificate
        )

    forged_certificate = _forge(
        owner.certificate,
        explicit_rejection_exhaustion=1,
    )
    object.__setattr__(
        forged_certificate,
        "certificate_sha256",
        kernel_v2._digest(
            kernel_v2._certificate_payload(forged_certificate),
            domain=b"heterodiff-mixed-support-initializer-certificate-v2\x00",
        ),
    )
    with pytest.raises(TypeError, match="Boolean"):
        kernel_v2.validate_mixed_support_initial_tilt_initializer_certificate_v2(
            forged_certificate
        )


def test_fully_redigested_sir_weight_and_bool_selected_index_tampering_is_rejected(
    m2_provider,
):
    owner = _kernel(m2_provider, "fixed-budget-sir", seed=909, budget=2)
    result = owner.execute()
    forged = _forge(result, selected_index=False)
    object.__setattr__(
        forged,
        "result_sha256",
        kernel_v2._digest(
            kernel_v2._sir_payload(forged),
            domain=b"heterodiff-mixed-support-SIR-result-v2\x00",
        ),
    )
    with pytest.raises(TypeError, match="exact integer"):
        owner.validate_result(forged)

    altered = np.array(result.normalized_weights[::-1], dtype=np.float64, copy=True)
    altered.setflags(write=False)
    forged = _forge(result, normalized_weights=altered)
    object.__setattr__(
        forged,
        "result_sha256",
        kernel_v2._digest(
            kernel_v2._sir_payload(forged),
            domain=b"heterodiff-mixed-support-SIR-result-v2\x00",
        ),
    )
    with pytest.raises(ValueError, match="weights differ|particle index or weight"):
        owner.validate_result(forged)


def test_hostile_text_and_bool_aliases_fail_before_equality(m2_provider):
    owner = _kernel(m2_provider, "bounded-rejection", seed=123, budget=2)
    result = owner.execute()
    hostile = _forge(result, status=_TouchBomb())
    with pytest.raises(TypeError, match="exact text"):
        owner.validate_result(hostile)

    forged_plan = _forge(owner.plan, budget=False)
    object.__setattr__(
        forged_plan,
        "plan_sha256",
        kernel_v2._digest(
            kernel_v2._plan_payload(forged_plan),
            domain=b"heterodiff-mixed-support-initializer-plan-v2\x00",
        ),
    )
    with pytest.raises(TypeError, match="exact integer"):
        kernel_v2._validate_plan(forged_plan)


def test_digest_encoder_is_bounded_exact_and_does_not_iterate_hostile_mappings():
    with pytest.raises(TypeError, match="exact dict"):
        kernel_v2._digest(_HostileMapping(), domain=b"x")
    with pytest.raises(ValueError, match="bit limit"):
        kernel_v2._digest({"x": 1 << 20_000}, domain=b"x")
    with pytest.raises(ValueError, match="text"):
        kernel_v2._digest({"x": "a" * 65_537}, domain=b"x")
    nested = None
    for _ in range(40):
        nested = (nested,)
    with pytest.raises(ValueError, match="node/depth"):
        kernel_v2._digest({"x": nested}, domain=b"x")
    assert len(kernel_v2._digest({"x": Fraction(1 << 15_000, 3)}, domain=b"x")) == 64


def test_sir_normalization_fails_closed_on_realized_underflow():
    with pytest.raises(
        kernel_v2.MixedSupportInitialTiltInitializerV2Error, match="underflow"
    ):
        kernel_v2.normalize_mixed_support_sir_exact_log_weights_v2(
            (Fraction(0), Fraction(-10_000))
        )


def test_atomic_normalization_zero_and_constant_tilts_are_exact_invariants():
    near_unit = kernel_v2._make_array(
        [0.5000000000000001, 0.5000000000000001],
        name="near-unit base",
    )
    (
        zero_probabilities,
        zero_log_z,
    ) = kernel_v2.normalize_mixed_support_atomic_exact_log_weights_v2(
        near_unit,
        (Fraction(0), Fraction(0)),
    )
    assert zero_log_z == 0.0
    assert zero_probabilities.tolist() == [0.5, 0.5]

    constant = Fraction(3, 7)
    (
        constant_probabilities,
        constant_log_z,
    ) = kernel_v2.normalize_mixed_support_atomic_exact_log_weights_v2(
        near_unit,
        (constant, constant),
    )
    assert constant_log_z == float(constant)
    assert constant_probabilities.tolist() == [0.5, 0.5]

    reference = CappedPoissonConfigurationReference(
        {0: 0, 1: 0},
        {0: 0.4, 1: 0.6},
        activity=0.3,
        total_cap=3,
    )
    _, _, oracle_masses = reference.finite_atomic_oracle()
    assert math.fsum(float(value) for value in oracle_masses) != 1.0
    immutable = kernel_v2._make_array(oracle_masses, name="real oracle masses")
    (
        probabilities,
        log_z,
    ) = kernel_v2.normalize_mixed_support_atomic_exact_log_weights_v2(
        immutable,
        (Fraction(0),) * len(immutable),
    )
    assert log_z == 0.0
    assert math.fsum(float(value) for value in probabilities) == pytest.approx(1.0)


def test_public_records_and_owner_are_nonpickle_and_immutable(m2_provider):
    owner = _kernel(m2_provider, "bounded-rejection", seed=15, budget=1)
    result = owner.execute()
    records = (
        owner.plan,
        owner.certificate,
        result,
        result.attempts[0],
        result.attempts[0].scored,
        owner,
    )
    for record in records:
        with pytest.raises(TypeError, match="pickle"):
            pickle.dumps(record)
    with pytest.raises((AttributeError, TypeError)):
        owner._provider = m2_provider

    sir_owner = _kernel(m2_provider, "fixed-budget-sir", seed=16, budget=1)
    sir_result = sir_owner.execute()
    for record in (sir_result, sir_result.particles[0]):
        with pytest.raises(TypeError, match="pickle"):
            pickle.dumps(record)


@pytest.mark.parametrize(
    "record_type",
    (
        kernel_v2.MixedSupportInitialTiltScoredConfigurationV2,
        kernel_v2.MixedSupportInitialTiltRejectionAttemptV2,
        kernel_v2.MixedSupportInitialTiltSIRParticleV2,
        kernel_v2.MixedSupportInitialTiltEnumerationAtomV2,
        kernel_v2.MixedSupportInitialTiltRejectionResultV2,
        kernel_v2.MixedSupportInitialTiltSIRResultV2,
        kernel_v2.MixedSupportInitialTiltEnumerationResultV2,
    ),
)
def test_all_record_types_refuse_subclassing_and_public_construction(record_type):
    with pytest.raises(TypeError, match="subclass"):
        builtins.__build_class__(lambda: None, "HostileSubclass", record_type)
    with pytest.raises(TypeError):
        record_type()


@pytest.fixture(scope="module")
def atomic_composer_provider():
    pytest.importorskip("torch")
    from tests.unit import (
        test_configuration_initial_tilt_composer_torch as checkpoint30,
    )

    bundle = checkpoint30.bundle.__wrapped__()
    composer = bundle["initial_tilt"]
    provider = (
        score_provider.adapt_configuration_initial_tilt_composer_score_provider_v1(
            composer,
            adapter_role_sha256=_ADAPTER_ROLE,
        )
    )
    return provider


def test_atomic_enumeration_binds_every_count_state_to_its_scored_configuration(
    atomic_composer_provider,
):
    plan = kernel_v2.make_mixed_support_initial_tilt_initializer_plan_v2(
        atomic_composer_provider,
        strategy="finite-atomic-enumeration",
        residual_context=(-0.4,),
        initializer_role_sha256=_KERNEL_ROLE,
    )
    owner = kernel_v2.certify_mixed_support_initial_tilt_initializer_kernel_v2(
        atomic_composer_provider,
        plan=plan,
    )
    result = owner.execute()
    assert result.status == "enumerated"
    assert "finite-atomic-oracle-binary64" in owner.certificate.executed_measure_policy
    assert len(result.atoms) == owner.certificate.enumeration_state_count
    assert np.sum(result.normalized_probabilities) == pytest.approx(1.0)
    assert owner.validate_result(result) is result
    assert owner.certificate.exact_log_weight_lower_bound is not None

    composer = atomic_composer_provider.backend_adapter.source
    for atom in result.atoms:
        direct = composer.evaluate(
            atom.scored.configuration,
            residual_context=(-0.4,),
        )
        direct_exact = Fraction(
            direct.exact_initial_log_factor_numerator,
            direct.exact_initial_log_factor_denominator,
        )
        assert atom.scored.exact_log_weight == direct_exact

    from heterodiff.processes import (
        plugin_bridge_mixed_support_initial_tilt_initializer_kernel as kernel_v1,
    )

    v1_plan = kernel_v1.make_mixed_support_initial_tilt_initializer_plan(
        composer,
        strategy="finite-atomic-enumeration",
        residual_context=(-0.4,),
        initializer_role_sha256=_KERNEL_ROLE,
    )
    v1_owner = kernel_v1.certify_mixed_support_initial_tilt_initializer_kernel(
        composer,
        plan=v1_plan,
    )
    v1_result = v1_owner.execute()
    assert tuple(atom.count_state for atom in result.atoms) == tuple(
        atom.count_state for atom in v1_result.atoms
    )
    assert tuple(atom.scored.configuration for atom in result.atoms) == tuple(
        atom.scored.configuration for atom in v1_result.atoms
    )
    assert result.base_masses.tobytes() == v1_result.base_masses.tobytes()
    assert tuple(
        (
            atom.scored.exact_log_weight_numerator,
            atom.scored.exact_log_weight_denominator,
        )
        for atom in result.atoms
    ) == tuple(
        (
            atom.scored.exact_log_weight_numerator,
            atom.scored.exact_log_weight_denominator,
        )
        for atom in v1_result.atoms
    )
    assert (
        result.normalized_probabilities.tobytes()
        == v1_result.normalized_probabilities.tobytes()
    )
    assert (
        result.represented_log_normalizer_float64.hex()
        == v1_result.operational_log_normalizer.hex()
    )

    for record in (result, result.atoms[0]):
        with pytest.raises(TypeError, match="pickle"):
            pickle.dumps(record)

    alternate_context_plan = (
        kernel_v2.make_mixed_support_initial_tilt_initializer_plan_v2(
            atomic_composer_provider,
            strategy="bounded-rejection",
            residual_context=(0.1,),
            initializer_role_sha256=_KERNEL_ROLE,
            seed=4321,
            budget=1,
        )
    )
    original_context_plan = (
        kernel_v2.make_mixed_support_initial_tilt_initializer_plan_v2(
            atomic_composer_provider,
            strategy="bounded-rejection",
            residual_context=(-0.4,),
            initializer_role_sha256=_KERNEL_ROLE,
            seed=4321,
            budget=1,
        )
    )
    alternate_context_certificate = (
        kernel_v2.certify_mixed_support_initial_tilt_initializer_kernel_v2(
            atomic_composer_provider,
            plan=alternate_context_plan,
        ).certificate
    )
    original_context_certificate = (
        kernel_v2.certify_mixed_support_initial_tilt_initializer_kernel_v2(
            atomic_composer_provider,
            plan=original_context_plan,
        ).certificate
    )
    assert (
        alternate_context_certificate.proposal_seed
        != original_context_certificate.proposal_seed
    )
    assert (
        alternate_context_certificate.rejection_decision_seed
        != original_context_certificate.rejection_decision_seed
    )

    if len(result.atoms) >= 2:
        swapped = list(result.atoms)
        first = swapped[0]
        second = swapped[1]
        swapped[0] = _forge(first, scored=second.scored)
        object.__setattr__(
            swapped[0],
            "atom_sha256",
            kernel_v2._atom_sha(
                swapped[0].count_state,
                swapped[0].base_mass,
                swapped[0].scored.scored_configuration_sha256,
                swapped[0].normalized_probability,
            ),
        )
        forged = _forge(result, atoms=tuple(swapped))
        object.__setattr__(
            forged,
            "result_sha256",
            kernel_v2._digest(
                kernel_v2._enumeration_payload(forged),
                domain=b"heterodiff-mixed-support-enumeration-result-v2\x00",
            ),
        )
        with pytest.raises(ValueError, match="count state"):
            owner.validate_result(forged)


def test_exported_claim_boundaries_are_explicit():
    assert (
        kernel_v2.MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_V2_FORMAL_TEST_28_STATUS
        == "OPEN"
    )
    assert (
        "P_ref^{oracle,b64}"
        in kernel_v2.MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_V2_ENUMERATION_CAVEAT
    )
    assert "not" in kernel_v2.MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_V2_NONCLAIM
    assert "never-required" in kernel_v2.MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_V2_SCOPE
