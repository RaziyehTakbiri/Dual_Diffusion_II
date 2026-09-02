"""Tests for the mixed-support initial-tilt initializer kernel."""

from decimal import Decimal, localcontext
from fractions import Fraction
import ast
import inspect
import math
from pathlib import Path
import pickle
import random

import numpy as np
import pytest


torch = pytest.importorskip(
    "torch", reason="mixed-support initializer tests require PyTorch"
)

from heterodiff.processes import (  # noqa: E402
    plugin_bridge_mixed_support_initial_tilt_initializer_kernel as initializer,
)
from heterodiff.theory.configuration_reference import (  # noqa: E402
    CappedPoissonConfigurationReference,
    TransformedEvent,
)
from tests.unit import (  # noqa: E402
    test_configuration_initial_tilt_composer_torch as checkpoint30,
)


ROLE = "5" * 64
CONTEXT = (-0.4,)
D = 1 << 64
SOURCE = Path(initializer.__file__)


def _plan(composer, strategy, *, seed=None, budget=None, ess=None):
    return initializer.make_mixed_support_initial_tilt_initializer_plan(
        composer,
        strategy=strategy,
        residual_context=CONTEXT,
        initializer_role_sha256=ROLE,
        seed=seed,
        budget=budget,
        ess_warning_fraction=ess,
    )


def _owner(composer, strategy, *, seed=None, budget=None, ess=None):
    plan = _plan(
        composer,
        strategy,
        seed=seed,
        budget=budget,
        ess=ess,
    )
    owner = initializer.certify_mixed_support_initial_tilt_initializer_kernel(
        composer,
        plan=plan,
    )
    return plan, owner


def _forge(record, **updates):
    forged = object.__new__(type(record))
    for name in type(record).__annotations__:
        object.__setattr__(
            forged,
            name,
            updates.get(name, getattr(record, name)),
        )
    return forged


def _fully_redigested_enumeration_configuration_tamper(result, source_indices):
    """Rebind scored configurations, then consistently rebuild every digest."""

    assert len(source_indices) == len(result.atoms)
    scored_records = []
    for index, source_index in enumerate(source_indices):
        source = result.atoms[source_index].scored
        scored = _forge(source, index=index)
        object.__setattr__(
            scored,
            "scored_configuration_sha256",
            initializer._semantic_digest(
                initializer._scored_payload(scored),
                domain=b"heterodiff-mixed-support-scored-configuration-v1\x00",
            ),
        )
        scored_records.append(scored)

    exact_q = tuple(
        Fraction(
            scored.exact_log_weight_numerator,
            scored.exact_log_weight_denominator,
        )
        for scored in scored_records
    )
    (
        probabilities,
        log_normalizer,
    ) = initializer.normalize_mixed_support_atomic_exact_log_weights(
        result.base_masses,
        exact_q,
    )
    atoms = []
    for index, (original, scored) in enumerate(zip(result.atoms, scored_records)):
        probability = float(probabilities[index])
        atom = _forge(
            original,
            scored=scored,
            normalized_probability=probability,
        )
        object.__setattr__(
            atom,
            "atom_sha256",
            initializer._atom_digest(
                atom.count_state,
                atom.base_mass,
                scored.scored_configuration_sha256,
                probability,
            ),
        )
        atoms.append(atom)

    forged = _forge(
        result,
        atoms=tuple(atoms),
        normalized_probabilities=probabilities,
        operational_log_normalizer=log_normalizer,
    )
    object.__setattr__(
        forged,
        "result_sha256",
        initializer._semantic_digest(
            initializer._enumeration_result_payload(forged),
            domain=b"heterodiff-mixed-support-enumeration-result-v1\x00",
        ),
    )
    return forged


def _rng_snapshot():
    numpy_state = np.random.get_state()
    return (
        random.getstate(),
        (
            numpy_state[0],
            numpy_state[1].tobytes(),
            numpy_state[2],
            numpy_state[3],
            numpy_state[4],
        ),
        torch.random.get_rng_state().clone(),
    )


def _mixed_bundle():
    """Construct one genuine atomic-plus-one-dimensional CP30 owner."""

    type_dimensions = {0: 0, 1: 1}
    reference = checkpoint30.CappedPoissonConfigurationReference(
        type_dimensions,
        {0: 0.4, 1: 0.6},
        activity=1.2,
        total_cap=2,
    )
    schedule = checkpoint30.PiecewiseConstantHybridSchedule(
        (0.0, 0.25, 1.0),
        (0.0, 0.8),
        (0.0, 0.6),
        clean_hold=0.25,
    )
    rates = checkpoint30.ReversibleHybridRates(
        reference,
        per_particle_death_rate=0.7,
    )
    process = checkpoint30.ReversibleHybridReference(reference, schedule, rates)
    observation_reference = checkpoint30.CollapsedPoissonObservationReference(
        {10: 0, 11: 1},
        {10: 0.5, 11: 0.5},
        retained_cap=2,
    )
    channel = checkpoint30.TypedAffineGaussianObservationChannel(
        type_dimensions,
        observation_reference,
        ((0.8, 0.2), (0.2, 0.8)),
        fiber_channels={
            (0, 11): checkpoint30.AffineGaussianFiberChannel(
                np.zeros((1, 0), dtype=np.float64),
                [0.1],
                [[0.8]],
            ),
            (1, 11): checkpoint30.AffineGaussianFiberChannel(
                [[1.4]],
                [0.2],
                [[0.6]],
            ),
        },
    )
    clutter = checkpoint30.TypedGaussianClutterIntensity(
        observation_reference,
        0.3,
        (0.5, 0.5),
        fiber_channels={
            11: checkpoint30.AffineGaussianFiberChannel(
                np.zeros((1, 0), dtype=np.float64),
                [-0.1],
                [[1.2]],
            )
        },
    )
    preconditioner = checkpoint30.AnalyticAssociationPreconditioner(
        process,
        observation_reference,
        channel,
        clutter,
        {0: 0.7, 1: 0.3},
        contamination_probability=0.08,
        context_key=("checkpoint-50-mixed",),
    )
    outcome = (TransformedEvent(10),)
    analytic = preconditioner.certify_guide_range(outcome)
    range_gate = checkpoint30.certify_range_gated_association_guide(
        preconditioner,
        analytic,
        observation=outcome,
    )
    guide = checkpoint30.certify_totalized_association_jump_guide(
        preconditioner,
        range_gate,
        analytic,
        observation=outcome,
    )
    architecture = checkpoint30.ConfigurationEnergyArchitecture.from_process(
        process,
        coordinate_scales_by_type={0: (), 1: (1.5,)},
        context_dimension=1,
        context_scales=(1.0,),
        context_schema_sha256="f" * 64,
        event_hidden_width=3,
        event_embedding_width=2,
        context_hidden_width=3,
        context_embedding_width=2,
        readout_hidden_width=4,
        value_bound=1.5,
        spectral_ceilings=checkpoint30.SpectralNormCeilings(*(100.0,) * 7),
        bias_ceiling=100.0,
        first_derivative_ceiling=1_000_000.0,
        second_derivative_ceiling=1_000_000.0,
    )
    model = checkpoint30._model(architecture, 5001)
    provenance = checkpoint30.residual.ConditionalResidualProvenance(
        method_freeze_sha256="1" * 64,
        training_run_sha256="2" * 64,
        data_manifest_sha256="3" * 64,
        selection_rule_sha256="4" * 64,
        observation_schema_sha256="a" * 64,
        task_schema_sha256="b" * 64,
        conditioning_adapter_sha256="d" * 64,
        residual_role_sha256="e" * 64,
    )
    contract = checkpoint30.residual.make_conditional_residual_contract(
        architecture,
        observation_schema_sha256="a" * 64,
        task_schema_sha256="b" * 64,
        conditioning_adapter_sha256="d" * 64,
        residual_role_sha256="e" * 64,
    )
    checkpoint = checkpoint30.residual.certify_conditional_residual(
        model,
        contract,
        provenance=provenance,
    )
    residual_owner = (
        checkpoint30.totalized_residual.certify_totalized_conditional_jump_residual(
            model,
            checkpoint,
            expected_provenance=provenance,
        )
    )
    result = {
        "process": process,
        "reference_composer": checkpoint30.ProcessValidReferenceJumpComposer(process),
        "totalized_guide": guide,
        "totalized_residual": residual_owner,
        "residual_model": model,
    }
    result["initial_tilt"] = checkpoint30._certify(result)
    return result


@pytest.fixture(scope="module")
def atomic_bundle():
    return checkpoint30.bundle.__wrapped__()


@pytest.fixture(scope="module")
def continuous_bundle():
    return checkpoint30._continuous_bundle()


@pytest.fixture(scope="module")
def mixed_bundle():
    return _mixed_bundle()


@pytest.fixture(scope="module")
def enumeration_case(atomic_bundle):
    plan, owner = _owner(
        atomic_bundle["initial_tilt"],
        "finite-atomic-enumeration",
    )
    return plan, owner, owner.execute()


@pytest.fixture(scope="module")
def continuous_sir_case(continuous_bundle):
    plan, owner = _owner(
        continuous_bundle["initial_tilt"],
        "fixed-budget-sir",
        seed=50_001,
        budget=1,
    )
    return plan, owner, owner.execute()


def test_public_quota_terminal_branches_and_independent_decimal_oracle():
    unity = initializer.certify_mixed_support_rejection_quota(Fraction(0))
    zero = initializer.certify_mixed_support_rejection_quota(Fraction(-64))
    tiny = initializer.certify_mixed_support_rejection_quota(Fraction(-1, 1 << 1_074))
    adaptive = initializer.certify_mixed_support_rejection_quota(Fraction(-1))

    assert (unity.branch, unity.quota, unity.precision) == ("unity", D, 0)
    assert (zero.branch, zero.quota, zero.precision) == (
        "below_uint64_resolution",
        0,
        0,
    )
    assert tiny.branch == "below_one_uint64_cell"
    assert tiny.quota == D - 1
    with localcontext() as context:
        context.prec = 500
        oracle = int(Decimal(-1).exp() * Decimal(D))
    assert adaptive.branch == "adaptive_decimal"
    assert adaptive.quota == oracle
    assert Fraction(adaptive.quota, D) <= adaptive.ideal_lower
    assert adaptive.ideal_upper <= Fraction(adaptive.quota + 1, D)


@pytest.mark.parametrize("bad", (0, -1, 1.0, Decimal("-1"), True, None))
def test_public_quota_requires_an_exact_fraction(bad):
    with pytest.raises(TypeError):
        initializer.certify_mixed_support_rejection_quota(bad)


def test_public_quota_refuses_positive_and_nondyadic_gaps():
    with pytest.raises(ValueError, match="nonpositive"):
        initializer.certify_mixed_support_rejection_quota(Fraction(1, 2))
    with pytest.raises(
        initializer.MixedSupportInitialTiltInitializerError,
        match="dyadic",
    ):
        initializer.certify_mixed_support_rejection_quota(Fraction(-1, 3))


def test_public_quota_refuses_hostile_dyadic_before_decimal_allocation(monkeypatch):
    delta = Fraction(-1, 1 << initializer._QUOTA_MAX_EXACT_INTEGER_BITS)

    def bomb(*args, **kwargs):
        del args, kwargs
        raise AssertionError("oversized dyadic reached decimal allocation")

    monkeypatch.setattr(initializer, "_exact_dyadic_decimal", bomb)
    with pytest.raises(
        initializer.MixedSupportInitialTiltInitializerError,
        match="exact-dyadic work limit",
    ):
        initializer.certify_mixed_support_rejection_quota(delta)


def test_public_sir_normalization_and_half_open_selection_are_exactly_frozen():
    equal = initializer.normalize_mixed_support_sir_exact_log_weights(
        (Fraction(7, 4), Fraction(7, 4))
    )
    assert equal.flags.writeable is False
    assert equal.tobytes() == np.asarray([0.5, 0.5], dtype=np.float64).tobytes()
    assert initializer.select_mixed_support_sir_index(equal, 0) == 0
    assert initializer.select_mixed_support_sir_index(equal, 1 << 63) == 1
    assert initializer.select_mixed_support_sir_index(equal, D - 1) == 1

    singleton = initializer.normalize_mixed_support_sir_exact_log_weights(
        (Fraction(10**6, 3),)
    )
    assert singleton.tolist() == [1.0]
    assert initializer.select_mixed_support_sir_index(singleton, D - 1) == 0


def test_public_atomic_normalization_uses_base_mass_and_exact_fraction_inputs():
    masses = np.asarray([0.2, 0.3, 0.5], dtype=np.float64)
    (
        probabilities,
        log_normalizer,
    ) = initializer.normalize_mixed_support_atomic_exact_log_weights(
        masses,
        (Fraction(3, 2),) * 3,
    )
    assert probabilities.flags.writeable is False
    np.testing.assert_allclose(probabilities, masses, rtol=4.0e-16, atol=0.0)
    assert log_normalizer == pytest.approx(1.5, rel=0.0, abs=4.0e-16)

    with pytest.raises(TypeError, match="Fraction"):
        initializer.normalize_mixed_support_sir_exact_log_weights((0.0,))
    with pytest.raises(ValueError, match="sum to one"):
        initializer.normalize_mixed_support_atomic_exact_log_weights(
            [0.4, 0.4],
            (Fraction(0), Fraction(0)),
        )


def test_public_atomic_normalization_refuses_positive_mass_underflow():
    with pytest.raises(
        initializer.MixedSupportInitialTiltInitializerError,
        match="underflow|erased a positive",
    ):
        initializer.normalize_mixed_support_atomic_exact_log_weights(
            np.asarray([0.5, 0.25, 0.25], dtype=np.float64),
            (Fraction(-745), Fraction(0), Fraction(0)),
        )


def test_aggregate_resource_preflight_boundaries_precede_rng_and_model_calls(
    monkeypatch,
):
    def bomb(*args, **kwargs):
        del args, kwargs
        raise AssertionError("resource preflight crossed an operational boundary")

    monkeypatch.setattr(initializer, "_new_philox", bomb)
    monkeypatch.setattr(initializer, "_COMPOSER_EVALUATE", bomb)
    monkeypatch.setattr(
        CappedPoissonConfigurationReference,
        "sample_configuration",
        bomb,
    )

    occurrence_limit = initializer._reference.MAX_REFERENCE_BATCH_OCCURRENCES
    coordinate_limit = initializer._reference.MAX_REFERENCE_BATCH_COORDINATES
    budget = 4_000
    assert occurrence_limit % budget == 0
    assert coordinate_limit % budget == 0

    occurrence_cap = occurrence_limit // budget
    occurrence_boundary = CappedPoissonConfigurationReference(
        {0: 0},
        {0: 1.0},
        activity=1.0,
        total_cap=occurrence_cap,
    )
    preflight = initializer._preflight_reference_resources(
        occurrence_boundary,
        strategy="bounded-rejection",
        budget=budget,
    )
    assert preflight[-2:] == (occurrence_limit, 0)

    occurrence_over = CappedPoissonConfigurationReference(
        {0: 0},
        {0: 1.0},
        activity=1.0,
        total_cap=occurrence_cap + 1,
    )
    with pytest.raises(ValueError, match="MAX_REFERENCE_BATCH_OCCURRENCES"):
        initializer._preflight_reference_resources(
            occurrence_over,
            strategy="fixed-budget-sir",
            budget=budget,
        )

    coordinate_dimension = coordinate_limit // budget
    coordinate_boundary = CappedPoissonConfigurationReference(
        {0: coordinate_dimension},
        {0: 1.0},
        activity=1.0,
        total_cap=1,
    )
    preflight = initializer._preflight_reference_resources(
        coordinate_boundary,
        strategy="fixed-budget-sir",
        budget=budget,
    )
    assert preflight[-2:] == (budget, coordinate_limit)

    coordinate_over = CappedPoissonConfigurationReference(
        {0: coordinate_dimension + 1},
        {0: 1.0},
        activity=1.0,
        total_cap=1,
    )
    with pytest.raises(ValueError, match="MAX_REFERENCE_BATCH_COORDINATES"):
        initializer._preflight_reference_resources(
            coordinate_over,
            strategy="bounded-rejection",
            budget=budget,
        )


def test_source_binds_reference_interface_and_exact_q_without_cp28_or_cp49_imports():
    source = SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
    assert not any(
        "counter_keyed_reference_initializer" in name
        or "full_source_law_admission" in name
        for name in imported
    )
    assert "self._reference.sample_configuration" in source

    exact_source = inspect.getsource(initializer._fraction_from_evaluation)
    assert "exact_initial_log_factor_numerator" in exact_source
    assert "exact_initial_log_factor_denominator" in exact_source
    assert ".initial_log_factor" not in exact_source
    for operation in (
        initializer.MixedSupportInitialTiltInitializerKernel._execute_sir,
        initializer.MixedSupportInitialTiltInitializerKernel._execute_enumeration,
    ):
        operation_source = inspect.getsource(operation)
        assert "_fraction_from_evaluation" in operation_source
        assert ".initial_log_factor" not in operation_source


def test_plan_factory_validates_complete_precommitted_strategy_surface(
    atomic_bundle,
    monkeypatch,
):
    composer = atomic_bundle["initial_tilt"]
    monkeypatch.setattr(initializer, "_COMPOSER_OWNER_SNAPSHOT", lambda owner: ())
    monkeypatch.setattr(
        initializer,
        "_COMPOSER_LIVE_COMPONENTS",
        lambda owner, snapshot: None,
    )

    enumeration = _plan(composer, "finite-atomic-enumeration")
    rejection = _plan(composer, "bounded-rejection", seed=1, budget=1)
    sir = _plan(composer, "fixed-budget-sir", seed=1, budget=1)
    assert enumeration.seed is None and enumeration.budget == 0
    assert rejection.ess_warning_fraction is None
    assert sir.ess_warning_fraction == (
        initializer.MIXED_SUPPORT_INITIALIZER_DEFAULT_ESS_WARNING_FRACTION
    )
    assert all(
        plan.adaptive_fallback_permitted is False
        for plan in (enumeration, rejection, sir)
    )

    def bomb(*args, **kwargs):
        del args, kwargs
        raise AssertionError("invalid plan reached live composer ancestry")

    monkeypatch.setattr(initializer, "_COMPOSER_OWNER_SNAPSHOT", bomb)
    monkeypatch.setattr(initializer, "_COMPOSER_LIVE_COMPONENTS", bomb)

    invalid_calls = (
        ({"strategy": "auto", "seed": 1, "budget": 1}, ValueError),
        ({"strategy": b"bounded-rejection", "seed": 1, "budget": 1}, ValueError),
        ({"strategy": "bounded-rejection", "seed": True, "budget": 1}, TypeError),
        ({"strategy": "bounded-rejection", "seed": -1, "budget": 1}, ValueError),
        ({"strategy": "bounded-rejection", "seed": 1, "budget": 0}, ValueError),
        (
            {
                "strategy": "bounded-rejection",
                "seed": 1,
                "budget": initializer.MAX_MIXED_SUPPORT_INITIALIZER_BUDGET + 1,
            },
            ValueError,
        ),
        ({"strategy": "finite-atomic-enumeration", "seed": 1}, ValueError),
        ({"strategy": "finite-atomic-enumeration", "budget": 1}, ValueError),
        (
            {
                "strategy": "bounded-rejection",
                "seed": 1,
                "budget": 1,
                "ess_warning_fraction": 0.5,
            },
            ValueError,
        ),
        (
            {
                "strategy": "fixed-budget-sir",
                "seed": 1,
                "budget": 1,
                "ess_warning_fraction": 0,
            },
            TypeError,
        ),
        (
            {
                "strategy": "fixed-budget-sir",
                "seed": 1,
                "budget": 1,
                "ess_warning_fraction": 0.0,
            },
            ValueError,
        ),
    )
    for supplied, error_type in invalid_calls:
        with pytest.raises(error_type):
            initializer.make_mixed_support_initial_tilt_initializer_plan(
                composer,
                residual_context=CONTEXT,
                initializer_role_sha256=ROLE,
                **supplied,
            )

    with pytest.raises(ValueError, match="initializer_role_sha256"):
        initializer.make_mixed_support_initial_tilt_initializer_plan(
            composer,
            strategy="bounded-rejection",
            residual_context=CONTEXT,
            initializer_role_sha256="not-a-sha256",
            seed=1,
            budget=1,
        )


def test_all_atomic_enumeration_has_complete_factorial_mass_and_normalization(
    enumeration_case,
):
    plan, owner, result = enumeration_case
    reference = owner.reference
    assert plan.strategy == "finite-atomic-enumeration"
    assert result.status == "enumerated"
    assert len(result.atoms) == math.comb(
        reference.total_cap + len(reference.type_ids),
        len(reference.type_ids),
    )
    assert result.normalized_probabilities.flags.writeable is False
    assert result.base_masses.flags.writeable is False

    states = tuple(atom.count_state for atom in result.atoms)
    assert states == ((0, 0), (0, 1), (1, 0), (0, 2), (1, 1), (2, 0))
    theta = reference.activity
    weights = tuple(reference.type_weights[type_id] for type_id in reference.type_ids)
    raw = []
    for state in states:
        coefficient = theta ** sum(state)
        for count, weight in zip(state, weights):
            coefficient *= weight**count / math.factorial(count)
        raw.append(coefficient)
    normalizer = math.fsum(raw)
    expected_base = np.asarray([value / normalizer for value in raw])
    np.testing.assert_allclose(
        result.base_masses,
        expected_base,
        rtol=2.0e-15,
        atol=0.0,
    )
    assert math.fsum(float(value) for value in result.base_masses) == pytest.approx(
        1.0,
        rel=0.0,
        abs=2.0e-15,
    )

    mass = {atom.count_state: atom.base_mass for atom in result.atoms}
    assert 2.0 * mass[(2, 0)] * mass[(0, 0)] == pytest.approx(
        mass[(1, 0)] ** 2,
        rel=2.0e-15,
    )
    assert mass[(1, 1)] * mass[(0, 0)] == pytest.approx(
        mass[(1, 0)] * mass[(0, 1)],
        rel=2.0e-15,
    )

    exact_q = tuple(
        Fraction(
            atom.scored.evaluation.exact_initial_log_factor_numerator,
            atom.scored.evaluation.exact_initial_log_factor_denominator,
        )
        for atom in result.atoms
    )
    (
        expected_probabilities,
        expected_log_normalizer,
    ) = initializer.normalize_mixed_support_atomic_exact_log_weights(
        result.base_masses,
        exact_q,
    )
    assert result.normalized_probabilities.tobytes() == expected_probabilities.tobytes()
    assert result.operational_log_normalizer.hex() == expected_log_normalizer.hex()
    assert math.fsum(
        float(value) for value in result.normalized_probabilities
    ) == pytest.approx(1.0, rel=0.0, abs=2.0e-15)
    for atom, q in zip(result.atoms, exact_q):
        assert (
            Fraction(
                atom.scored.exact_log_weight_numerator,
                atom.scored.exact_log_weight_denominator,
            )
            == q
        )
        assert atom.scored.configuration == tuple(
            TransformedEvent(type_id)
            for type_id, count in zip(reference.type_ids, atom.count_state)
            for _ in range(count)
        )


@pytest.mark.parametrize(
    "source_indices",
    (
        (0, 0, 2, 3, 4, 5),
        (0, 2, 1, 3, 4, 5),
    ),
    ids=("duplicate-configuration", "swapped-configurations"),
)
def test_enumeration_binds_each_count_state_to_its_exact_configuration_after_redigest(
    enumeration_case,
    source_indices,
):
    _, owner, result = enumeration_case
    forged = _fully_redigested_enumeration_configuration_tamper(
        result,
        source_indices,
    )
    with pytest.raises(
        ValueError,
        match="configuration differs from its count state",
    ):
        owner.validate_result(forged)


def test_continuous_enumeration_refuses_before_rng_or_model_evaluation(
    continuous_bundle,
    monkeypatch,
):
    composer = continuous_bundle["initial_tilt"]
    plan = _plan(composer, "finite-atomic-enumeration")

    def bomb(*args, **kwargs):
        del args, kwargs
        raise AssertionError("continuous enumeration crossed the refusal boundary")

    monkeypatch.setattr(initializer, "_new_philox", bomb)
    monkeypatch.setattr(initializer, "_COMPOSER_EVALUATE", bomb)
    monkeypatch.setattr(
        CappedPoissonConfigurationReference, "sample_configuration", bomb
    )
    with pytest.raises(ValueError, match="continuous fiber"):
        initializer.certify_mixed_support_initial_tilt_initializer_kernel(
            composer,
            plan=plan,
        )


def test_public_certification_refuses_aggregate_work_before_rng_or_model(
    continuous_bundle,
    monkeypatch,
):
    composer = continuous_bundle["initial_tilt"]
    reference = composer.reference_composer.process.reference
    plan = _plan(composer, "fixed-budget-sir", seed=50_009, budget=1)

    def bomb(*args, **kwargs):
        del args, kwargs
        raise AssertionError("aggregate refusal crossed an operational boundary")

    monkeypatch.setattr(initializer, "_new_philox", bomb)
    monkeypatch.setattr(initializer, "_COMPOSER_EVALUATE", bomb)
    monkeypatch.setattr(
        CappedPoissonConfigurationReference,
        "sample_configuration",
        bomb,
    )
    monkeypatch.setattr(
        initializer._reference,
        "MAX_REFERENCE_BATCH_OCCURRENCES",
        reference.total_cap - 1,
    )
    with pytest.raises(ValueError, match="MAX_REFERENCE_BATCH_OCCURRENCES"):
        initializer.certify_mixed_support_initial_tilt_initializer_kernel(
            composer,
            plan=plan,
        )


def test_rejection_selected_and_exhausted_are_fixed_work_without_fallback(
    continuous_bundle,
    monkeypatch,
):
    composer = continuous_bundle["initial_tilt"]
    _, owner = _owner(
        composer,
        "bounded-rejection",
        seed=50_010,
        budget=2,
    )
    original_sample = CappedPoissonConfigurationReference.sample_configuration
    original_evaluate = initializer._COMPOSER_EVALUATE
    counts = {"sample": 0, "evaluate": 0}

    def counted_sample(reference, rng):
        counts["sample"] += 1
        return original_sample(reference, rng)

    def counted_evaluate(bound_composer, configuration, *, residual_context):
        counts["evaluate"] += 1
        return original_evaluate(
            bound_composer,
            configuration,
            residual_context=residual_context,
        )

    def forbidden_fallback(*args, **kwargs):
        del args, kwargs
        raise AssertionError("preselected rejection attempted a fallback")

    monkeypatch.setattr(
        CappedPoissonConfigurationReference,
        "sample_configuration",
        counted_sample,
    )
    monkeypatch.setattr(initializer, "_COMPOSER_EVALUATE", counted_evaluate)
    monkeypatch.setattr(
        initializer.MixedSupportInitialTiltInitializerKernel,
        "_execute_sir",
        forbidden_fallback,
    )
    monkeypatch.setattr(
        initializer.MixedSupportInitialTiltInitializerKernel,
        "_execute_enumeration",
        forbidden_fallback,
    )

    def forced_quota(quota):
        def certify(delta):
            assert type(delta) is Fraction and delta <= 0
            return initializer.MixedSupportInitialTiltRejectionQuota(
                "test-forced",
                0,
                Fraction(0),
                Fraction(1),
                True,
                quota,
            )

        return certify

    monkeypatch.setattr(
        initializer,
        "certify_mixed_support_rejection_quota",
        forced_quota(D),
    )
    selected = owner.execute()
    assert selected.status == "selected"
    assert selected.selected_index == 0
    assert len(selected.attempts) == owner.plan.budget
    assert all(attempt.accepted for attempt in selected.attempts)
    assert selected.selected_configuration == selected.attempts[0].scored.configuration

    forged_attempt = _forge(selected.attempts[0], quota_precision=False)
    object.__setattr__(
        forged_attempt,
        "attempt_sha256",
        initializer._semantic_digest(
            initializer._attempt_payload(forged_attempt),
            domain=b"heterodiff-mixed-support-rejection-attempt-v1\x00",
        ),
    )
    forged_attempt_result = _forge(
        selected,
        attempts=(forged_attempt,) + selected.attempts[1:],
    )
    object.__setattr__(
        forged_attempt_result,
        "result_sha256",
        initializer._semantic_digest(
            initializer._rejection_result_payload(forged_attempt_result),
            domain=b"heterodiff-mixed-support-rejection-result-v1\x00",
        ),
    )
    with pytest.raises(TypeError, match=r"quota_precision.*exact integer"):
        owner.validate_result(forged_attempt_result)

    forged_index_result = _forge(selected, selected_index=False)
    object.__setattr__(
        forged_index_result,
        "result_sha256",
        initializer._semantic_digest(
            initializer._rejection_result_payload(forged_index_result),
            domain=b"heterodiff-mixed-support-rejection-result-v1\x00",
        ),
    )
    with pytest.raises(TypeError, match=r"selected_index.*exact integer"):
        owner.validate_result(forged_index_result)

    monkeypatch.setattr(
        initializer,
        "certify_mixed_support_rejection_quota",
        forced_quota(0),
    )
    exhausted = owner.execute()
    assert exhausted.status == "exhausted"
    assert exhausted.selected_index is None
    assert exhausted.selected_configuration is None
    assert len(exhausted.attempts) == owner.plan.budget
    assert not any(attempt.accepted for attempt in exhausted.attempts)
    assert counts == {"sample": 4, "evaluate": 4}
    assert selected.proposal_stream_initial_state_sha256 == (
        exhausted.proposal_stream_initial_state_sha256
    )
    assert selected.decision_stream_initial_state_sha256 == (
        exhausted.decision_stream_initial_state_sha256
    )
    assert selected.proposal_stream_initial_state_sha256 != (
        selected.decision_stream_initial_state_sha256
    )


def test_sir_j_one_is_its_proposal_and_seeded_execution_replays(
    continuous_sir_case,
):
    plan, owner, first = continuous_sir_case
    assert plan.budget == 1
    assert len(first.particles) == 1
    assert first.normalized_weights.tolist() == [1.0]
    assert first.selected_index == 0
    assert first.selected_configuration == first.particles[0].scored.configuration
    assert first.effective_sample_size == 1.0
    assert first.maximum_normalized_weight == 1.0
    assert first.ess_warning is False

    before = _rng_snapshot()
    second = owner.execute()
    after = _rng_snapshot()
    assert before[0] == after[0]
    assert before[1] == after[1]
    assert torch.equal(before[2], after[2])
    assert first.result_sha256 == second.result_sha256
    assert first.selected_configuration == second.selected_configuration
    assert first.particles[0].scored.evaluation_sha256 == (
        second.particles[0].scored.evaluation_sha256
    )
    assert owner.validate_result(second) is second


def test_stream_contract_preserves_work_prefixes_and_binds_sir_budget(
    continuous_bundle,
):
    composer = continuous_bundle["initial_tilt"]
    seed = 50_015

    _, rejection_one = _owner(
        composer,
        "bounded-rejection",
        seed=seed,
        budget=1,
    )
    _, rejection_two = _owner(
        composer,
        "bounded-rejection",
        seed=seed,
        budget=2,
    )
    assert rejection_one.certificate.proposal_seed == (
        rejection_two.certificate.proposal_seed
    )
    assert rejection_one.certificate.rejection_decision_seed == (
        rejection_two.certificate.rejection_decision_seed
    )
    first_rejection = rejection_one.execute()
    second_rejection = rejection_two.execute()
    assert first_rejection.attempts[0].scored.configuration == (
        second_rejection.attempts[0].scored.configuration
    )
    assert first_rejection.attempts[0].decision_word == (
        second_rejection.attempts[0].decision_word
    )

    _, sir_one = _owner(
        composer,
        "fixed-budget-sir",
        seed=seed,
        budget=1,
    )
    _, sir_two = _owner(
        composer,
        "fixed-budget-sir",
        seed=seed,
        budget=2,
    )
    assert sir_one.certificate.proposal_seed == sir_two.certificate.proposal_seed
    assert sir_one.certificate.proposal_seed != (
        rejection_one.certificate.proposal_seed
    )
    assert sir_one.certificate.resampling_seed != sir_two.certificate.resampling_seed
    first_sir = sir_one.execute()
    second_sir = sir_two.execute()
    assert first_sir.particles[0].scored.configuration == (
        second_sir.particles[0].scored.configuration
    )


def _seed_covering_both_mixed_strata(reference, context_sha256, *, budget):
    for seed in range(1_000):
        proposal_seed = initializer._derive_stream_seed(
            seed,
            "proposal",
            ROLE,
            context_sha256,
            strategy="fixed-budget-sir",
        )
        rng = initializer._new_philox(proposal_seed)
        configurations = tuple(
            reference.sample_configuration(rng) for _ in range(budget)
        )
        event_types = {
            event.event_type
            for configuration in configurations
            for event in configuration
        }
        if event_types == set(reference.type_ids):
            return seed, configurations
    raise AssertionError("no bounded seed covered both mixed-support strata")


def test_fixed_j_retains_mixed_reference_interface_particles_and_disjoint_streams(
    mixed_bundle,
    monkeypatch,
):
    composer = mixed_bundle["initial_tilt"]
    reference = mixed_bundle["process"].reference
    context_sha256 = initializer._CONTEXT_SHA256(CONTEXT)
    seed, expected_configurations = _seed_covering_both_mixed_strata(
        reference,
        context_sha256,
        budget=4,
    )
    plan, owner = _owner(
        composer,
        "fixed-budget-sir",
        seed=seed,
        budget=4,
    )
    original_sample = CappedPoissonConfigurationReference.sample_configuration
    observed = []

    def traced_sample(bound_reference, rng):
        assert bound_reference is reference
        assert isinstance(rng, np.random.Generator)
        configuration = original_sample(bound_reference, rng)
        observed.append(configuration)
        return configuration

    monkeypatch.setattr(
        CappedPoissonConfigurationReference,
        "sample_configuration",
        traced_sample,
    )
    result = owner.execute()
    assert len(observed) == plan.budget
    assert tuple(observed) == expected_configurations
    assert len(result.particles) == plan.budget
    assert (
        tuple(particle.scored.configuration for particle in result.particles)
        == expected_configurations
    )
    event_types = {
        event.event_type
        for particle in result.particles
        for event in particle.scored.configuration
    }
    assert event_types == {0, 1}
    for particle in result.particles:
        configuration = particle.scored.configuration
        assert reference.canonicalize(configuration) == configuration
        for event in configuration:
            assert len(event.coordinates) == reference.type_dimensions[event.event_type]

    exact_q = tuple(
        Fraction(
            particle.scored.evaluation.exact_initial_log_factor_numerator,
            particle.scored.evaluation.exact_initial_log_factor_denominator,
        )
        for particle in result.particles
    )
    expected_weights = initializer.normalize_mixed_support_sir_exact_log_weights(
        exact_q
    )
    assert result.normalized_weights.tobytes() == expected_weights.tobytes()
    assert result.selected_configuration == (
        result.particles[result.selected_index].scored.configuration
    )
    assert owner.certificate.proposal_seed != owner.certificate.resampling_seed
    assert owner.certificate.proposal_seed != plan.seed
    assert owner.certificate.resampling_seed != plan.seed
    assert result.proposal_stream_initial_state_sha256 != (
        result.resampling_stream_initial_state_sha256
    )


def test_structural_result_validation_calls_no_model_rng_or_live_replay(
    continuous_sir_case,
    monkeypatch,
):
    _, owner, result = continuous_sir_case

    def bomb(*args, **kwargs):
        del args, kwargs
        raise AssertionError("structural validation replayed an operational entrypoint")

    monkeypatch.setattr(initializer, "_COMPOSER_EVALUATE", bomb)
    monkeypatch.setattr(initializer, "_COMPOSER_OWNER_SNAPSHOT", bomb)
    monkeypatch.setattr(initializer, "_COMPOSER_LIVE_COMPONENTS", bomb)
    monkeypatch.setattr(initializer, "_new_philox", bomb)
    monkeypatch.setattr(initializer, "_runtime_sha256", bomb)
    monkeypatch.setattr(
        CappedPoissonConfigurationReference, "sample_configuration", bomb
    )
    monkeypatch.setattr(
        initializer.MixedSupportInitialTiltInitializerKernel,
        "execute",
        bomb,
    )
    monkeypatch.setattr(
        initializer.MixedSupportInitialTiltInitializerKernel,
        "revalidate_live_components",
        bomb,
    )
    assert owner.validate_result(result) is result


def test_redigested_result_tampering_and_direct_construction_are_refused(
    continuous_sir_case,
):
    _, owner, result = continuous_sir_case
    forged = _forge(result, status="forged-selected")
    redigest = initializer._semantic_digest(
        initializer._sir_result_payload(forged),
        domain=b"heterodiff-mixed-support-SIR-result-v1\x00",
    )
    object.__setattr__(forged, "result_sha256", redigest)
    with pytest.raises(ValueError, match="strategy or status"):
        owner.validate_result(forged)
    with pytest.raises(TypeError, match="kernel-created"):
        initializer.MixedSupportInitialTiltSIRResult(_construction_token=None)
    with pytest.raises(ValueError):
        result.normalized_weights[0] = 0.5
    with pytest.raises(TypeError, match="pickle"):
        pickle.dumps(result)


def test_certificate_freezes_explicit_nonclaims_and_formal_test_28_open(
    continuous_sir_case,
):
    plan, owner, _ = continuous_sir_case
    certificate = owner.certificate
    assert certificate.process_owned_reference_object_bound is True
    assert certificate.process_owned_reference_sampling_interface_used is True
    assert certificate.represented_exact_rational_q_point_score_bound is True
    assert certificate.strategy_preselected is True
    assert certificate.aggregate_resource_preflight_passed is True
    assert certificate.reference_per_configuration_sampling_gates_preserved is True
    assert certificate.finite_atomic_oracle_limits_preserved is True
    assert certificate.certificate_structural_contract_passed is True
    assert certificate.adaptive_fallback_permitted is False
    assert certificate.structural_validation_replays_model_or_rng is False
    assert certificate.live_philox_law_verified is False
    assert certificate.operational_reference_sampling_law_verified is False
    assert certificate.iid_sequence_law_verified is False
    assert certificate.exact_operational_rejection_bernoulli is False
    assert certificate.finite_j_sir_equals_target is False
    assert certificate.analytic_pi_n_proposal_law_verified is False
    assert certificate.ideal_real_fiber_q_extension_verified is False
    assert certificate.analytic_h_equality_verified is False
    assert certificate.continuous_empirical_tv_kl_valid is False
    assert certificate.path_or_sampler_admitted is False
    assert certificate.formal_test_28_closed is False
    assert certificate.resource_preflight_mode == "stochastic-worst-case"
    assert certificate.planned_worst_case_occurrences == (
        plan.budget * owner.reference.total_cap
    )
    assert certificate.planned_worst_case_coordinates == (
        certificate.planned_worst_case_occurrences
        * max(owner.reference.type_dimensions.values())
    )
    assert initializer.MIXED_SUPPORT_INITIAL_TILT_FORMAL_TEST_28_STATUS == "OPEN"
    assert "P_ref^op=unspecified-finite-precision-law" in certificate.target_policy
    assert "no-exact-live-proposal-or-target-law-certified" in (
        certificate.target_policy
    )
    assert "identity-custody-only" in (
        certificate.process_owned_reference_object_bound_scope
    )
    assert "does-not-certify-the-analytic-Pi_N-law" in (
        certificate.process_owned_reference_object_bound_scope
    )
    assert "external-proof-supplies" in certificate.ideal_rejection_theorem
    assert "iid-analytic-Pi_N" in certificate.ideal_rejection_theorem
    assert "real-fiber-extension-qbar" in certificate.ideal_rejection_theorem
    assert "not-model-quality-generality" in (
        initializer.MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_SCOPE
    )
    assert "not-analytic-Pi_N-live-proposal-law-or-real-fiber-q-extension" in (
        initializer.MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_SCOPE
    )
    assert "exact-operational-rejection-Bernoulli" in (
        initializer.MIXED_SUPPORT_INITIAL_TILT_INITIALIZER_SCOPE
    )
    assert "floor(2^64*exp(q_repr-U))" in (
        initializer.MIXED_SUPPORT_INITIAL_TILT_DYADIC_REJECTION_CAVEAT
    )
    assert "identical-represented-proposal-and-score-batch-fixed" in (
        initializer.MIXED_SUPPORT_INITIAL_TILT_DYADIC_REJECTION_CAVEAT
    )
