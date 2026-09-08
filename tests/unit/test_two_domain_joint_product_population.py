"""Finite synthetic population oracles; not production trajectory qualification."""

import numpy as np
import pytest

from heterodiff.experiments.two_domain_joint_product_population import (
    ConditionalContext, FiniteCandidateBasePopulation, PopulationConstructionError,
    TimeConditionedFinitePopulation, candidate_generator_from_energy,
)


def population(context_id=b"context-a", *, domain="physionet-challenge-2012"):
    q0 = np.array([[-0.8, 0.8], [0.4, -0.4]])
    return FiniteCandidateBasePopulation(
        context=ConditionalContext(domain, b"mask-task", context_id),
        generator=candidate_generator_from_energy(q0, [-0.3, 0.2]),
        initial_law=np.array([1/3, 2/3]),
        observation_kernel=np.array([[0.85, 0.15], [0.2, 0.8]]),
        horizon=1.0, declaration_id="SYNTHETIC_FINITE_ENERGY_TILT_NOT_DOMAIN_GENERATOR",
    )


def test_energy_tilt_is_candidate_not_reference_and_never_clipped():
    q0 = np.array([[-0.8, 0.8], [0.4, -0.4]])
    q = candidate_generator_from_energy(q0, [-0.3, 0.2])
    assert q[0, 1] == pytest.approx(0.8 * np.exp(0.5))
    assert q[1, 0] == pytest.approx(0.4 * np.exp(-0.5))
    assert not np.array_equal(q, q0)
    np.testing.assert_allclose(q.sum(axis=1), 0, atol=1e-15)
    with pytest.raises((FloatingPointError, PopulationConstructionError)):
        candidate_generator_from_energy(q0, [-1000, 1000])


def test_joint_product_tables_have_correct_same_context_population():
    fixed = population().at_time(0.35)
    tables = fixed.joint_product_tables()
    joint, product = tables["joint_mass"], tables["product_mass"]
    assert joint.sum() == pytest.approx(1)
    assert product.sum() == pytest.approx(1)
    np.testing.assert_allclose(joint.sum(axis=1), product.sum(axis=1))
    np.testing.assert_allclose(joint.sum(axis=0), product.sum(axis=0))
    assert not np.allclose(joint, product)
    # Direct enumeration of the two independent terminal-observation branches.
    p = fixed.population
    enumerated_product = np.zeros_like(product)
    for initial1 in range(2):
        for latent1 in range(2):
            for initial2 in range(2):
                for latent2 in range(2):
                    for terminal2 in range(2):
                        for obs2 in range(2):
                            enumerated_product[latent1, obs2] += (
                                p.initial_law[initial1] * fixed.initial_to_u[initial1, latent1]
                                * p.initial_law[initial2] * fixed.initial_to_u[initial2, latent2]
                                * fixed.u_to_terminal[latent2, terminal2]
                                * p.observation_kernel[terminal2, obs2])
    np.testing.assert_allclose(enumerated_product, product, atol=1e-15)
    np.testing.assert_allclose(tables["optimal_logit"], np.log(joint / product))


def test_replay_role_separation_and_no_requirement_for_unequal_realizations():
    fixed = population().at_time(0.5)
    sample = fixed.sample(run_seed=2**64-1, record_id=b"record-01")
    assert sample == fixed.sample(run_seed=2**64-1, record_id=b"record-01")
    assert sample.joint_pair[0] == sample.product_pair[0]
    assert sample.joint_pair[1] == sample.branch_one.observation
    assert sample.product_pair[1] == sample.branch_two.observation
    assert sample.model_direct_time == 0.5
    addresses = sample.branch_one.stream_addresses + sample.branch_two.stream_addresses
    assert len(set(addresses)) == 8
    other = fixed.sample(run_seed=2**64-1, record_id=b"record-01", draw_ordinal=1)
    assert set(addresses).isdisjoint(other.branch_one.stream_addresses + other.branch_two.stream_addresses)


def test_context_and_domain_are_stream_keys_without_batch_permutation():
    one = population().at_time(0.5).sample(run_seed=1, record_id=b"same-record")
    two = population(b"different-context").at_time(0.5).sample(run_seed=1, record_id=b"same-record")
    three = population(domain="online-retail-ii").at_time(0.5).sample(run_seed=1, record_id=b"same-record")
    assert one.context != two.context != three.context
    assert len({one.population_sha256, two.population_sha256, three.population_sha256}) == 3
    assert one.branch_one.stream_addresses != two.branch_one.stream_addresses


def test_empirical_pairs_follow_predeclared_finite_tables():
    fixed = population().at_time(0.35)
    joint = np.zeros((2, 2))
    product = np.zeros((2, 2))
    # Fixed seed/count and 0.025 absolute tolerance declared before the sample.
    for ordinal in range(4096):
        sample = fixed.sample(run_seed=8726, record_id=b"population-check", draw_ordinal=ordinal)
        joint[sample.joint_pair] += 1
        product[sample.product_pair] += 1
    tables = fixed.joint_product_tables()
    np.testing.assert_allclose(joint / 4096, tables["joint_mass"], atol=0.025, rtol=0)
    np.testing.assert_allclose(product / 4096, tables["product_mass"], atol=0.025, rtol=0)


@pytest.mark.parametrize("u", [0.0, 1.0, -0.1, float("nan"), True, 1])
def test_time_must_be_explicit_and_interior(u):
    with pytest.raises(PopulationConstructionError):
        population().at_time(u)


@pytest.mark.parametrize("seed", [-1, 2**64, True])
def test_seed_is_explicit_uint64(seed):
    with pytest.raises(PopulationConstructionError):
        population().at_time(0.5).sample(run_seed=seed, record_id=b"r")


def test_owned_arrays_are_immutable_and_summary_does_not_admit_real_laws():
    p = population()
    for array in (p.generator, p.initial_law, p.observation_kernel):
        with pytest.raises(ValueError):
            array.flat[0] = 0
    summary = p.summary()
    for key in ("general_learned_hybrid_sampler_implemented", "continuous_observation_sampler_implemented",
                "full_open_interval_time_support_verified", "scientific_execution_authorized"):
        assert summary[key] is False


def test_nonpositive_observation_law_and_bad_initial_support_are_rejected():
    p = population()
    kwargs = dict(context=p.context, generator=p.generator, initial_law=p.initial_law,
                  observation_kernel=p.observation_kernel, horizon=1.0, declaration_id="synthetic")
    with pytest.raises(PopulationConstructionError, match="common positive"):
        FiniteCandidateBasePopulation(**{**kwargs, "observation_kernel": np.eye(2)})
    with pytest.raises(PopulationConstructionError, match="full support"):
        FiniteCandidateBasePopulation(**{**kwargs, "initial_law": np.array([1.0, 0.0])})


def test_law_bindings_and_cached_transitions_cannot_be_reassigned():
    p = population()
    fixed = p.at_time(0.5)
    for target, field, value in ((p, "horizon", 2.0), (p, "initial_law", np.array([1.0, 0.0])),
                                  (fixed, "reverse_time", 0.8), (fixed, "population", population(b"other"))):
        with pytest.raises(AttributeError, match="immutable"):
            setattr(target, field, value)
    with pytest.raises(AttributeError):
        del p.generator


def test_time_conditioned_public_constructor_also_checks_its_inputs():
    with pytest.raises(PopulationConstructionError):
        TimeConditionedFinitePopulation(population(), 0.0)
    with pytest.raises(PopulationConstructionError):
        TimeConditionedFinitePopulation(object(), 0.5)
