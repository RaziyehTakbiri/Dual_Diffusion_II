"""Small CPU cross-module smoke, not a complete loss or trajectory integration.

All records, TRAIN labels, prior parameters, and contexts here are invented.
Only continuous native magnitudes are lifted/smoothed. No clinical/data/compute
admission, full hybrid sampler, or analytic-guide derivative is claimed.
"""

from fractions import Fraction
import math

import numpy as np
import pytest
import torch

from heterodiff.data.two_domain_factorized_state import (
    FactoredEvent, FactorizedMetadataReference, PhysioStateKey, RetailStateKey,
    TrainInformedMetadataReference,
)
from heterodiff.data.two_domain_generative_chart_proposal import decode_metric_event
from heterodiff.evaluation import two_domain_count_normalized_event_cks as cks
from heterodiff.models.factorized_configuration_energy_torch import (
    BoundedFactorizedConfigurationEnergy, FactorizedConfigurationBatch,
    FactorizedEnergyArchitecture, FactorizedEnergyLimits,
)
from heterodiff.theory.factorized_smooth_amendment import (
    AmendmentParameters, FactorizedSmoothOracle, OracleLimits,
)


def supplied_state(domain):
    if domain == cks.PHYSIONET_DOMAIN_ID:
        return (FactoredEvent(PhysioStateKey(42, "GCS", "ATOMIC", Fraction(7, 2))),
                FactoredEvent(PhysioStateKey(42, "MechVent", "ATOMIC", Fraction(1))),
                FactoredEvent(PhysioStateKey(42, "HR", "POSITIVE"), 0.25))
    def key(branch):
        return RetailStateKey("C000042", "art-Ω", "", -3,
                              (2010, 2, 3, 4, 5, 6, 7), None, branch)
    return (FactoredEvent(key("ZERO")), FactoredEvent(key("NEGATIVE"), 0.25))


def oracle_for(domain, source, use_train_mixture):
    reference = FactorizedMetadataReference(domain)
    if use_train_mixture:
        reference = TrainInformedMetadataReference(reference, source, beta=Fraction(1, 5))
    parameters = AmendmentParameters(
        reference_count_mean=0.25, reference_cap=8, observation_cap=8,
        death_rate=1.0, target_contamination=0.1, target_log_value_sd=0.25,
        observation_contamination=0.1, observation_log_value_sd=0.25)
    return FactorizedSmoothOracle(reference, parameters, limits=OracleLimits(maximum_events=16))


def energy_batch(domain, events):
    spec = FactorizedEnergyArchitecture(
        metadata_schema_id="LOCAL_SYNTHETIC_FACTORIZED_V1:" + domain,
        total_cap=8, horizon=1.0, value_bound=2.0, coordinate_scale=1.0,
        context_scale=1.0, limits=FactorizedEnergyLimits(1, 8, 2048, 8192))
    model = BoundedFactorizedConfigurationEnergy(spec, initialization_seed=2718)
    coordinates = tuple(torch.tensor([] if event.coordinate is None else [event.coordinate],
                                     dtype=torch.float32, device="cpu", requires_grad=True)
                        for event in events)
    batch = FactorizedConfigurationBatch(
        spec.architecture_sha256,
        tuple(event.key.canonical_bytes() for event in events),
        tuple(event.key.dimension for event in events), coordinates, (0,) * len(events),
        torch.tensor([0.5], dtype=torch.float32), torch.full((1, 64), 0.125, dtype=torch.float32))
    return model, batch


@pytest.mark.parametrize("domain", [cks.PHYSIONET_DOMAIN_ID, cks.RETAIL_DOMAIN_ID])
@pytest.mark.parametrize("use_train_mixture", [False, True])
def test_actual_keys_reference_oracle_lift_and_energy_cpu_gradient(domain, use_train_mixture):
    source = supplied_state(domain)
    oracle = oracle_for(domain, source, use_train_mixture)
    # The first seeded Bernoulli falls in the source-lift branch, not reference
    # contamination. This is a supplied fixture, not a source-selection policy.
    lifted = oracle.sample_training_target((source,), np.random.default_rng(0))
    assert tuple(item.key for item in lifted) == tuple(item.key for item in source)
    assert math.isfinite(oracle.lift_log_density(source, lifted))
    assert math.isfinite(oracle.target_log_density((source,), lifted))
    assert oracle.target_log_density((source,), ()) == pytest.approx(math.log(0.1))
    for before, after in zip(source, lifted):
        if before.key.dimension:
            assert before.coordinate != after.coordinate
        else:
            assert after is before and after.coordinate is None
            assert after.to_metric_event() == before.to_metric_event()
    model, batch = energy_batch(domain, lifted)
    keys_before = batch.metadata_keys
    energy = model(batch)
    assert energy.shape == (1,) and bool(torch.isfinite(energy).all())
    energy.sum().backward()  # Derivative of energy only; not an invented training objective.
    for event, coordinate in zip(lifted, batch.coordinates):
        if event.key.dimension:
            assert coordinate.grad is not None and bool(torch.isfinite(coordinate.grad).all())
            assert bool((coordinate.grad != 0).any())
        else:
            assert coordinate.shape == (0,) and coordinate.grad is None
    for name in ("metadata_encoder.recurrent_weight", "event_hidden.weight", "readout_output.weight"):
        gradient = dict(model.named_parameters())[name].grad
        assert gradient is not None and bool(torch.isfinite(gradient).all())
    assert batch.metadata_keys == keys_before
    assert model.workload(batch)["metadata_bytes_consumed"] == sum(map(len, keys_before))
    assert model.description()["production_domain_schema_or_rates_adopted"] is False


@pytest.mark.parametrize("domain", [cks.PHYSIONET_DOMAIN_ID, cks.RETAIL_DOMAIN_ID])
def test_observation_smoothing_changes_only_ordinary_scalar_f105_slots(domain):
    source = supplied_state(domain)
    oracle = oracle_for(domain, source, False)
    observed = oracle.sample_observation(source, np.random.default_rng(0))
    assert observed is not None and len(observed) == len(source)
    assert math.isfinite(oracle.observation_log_density(source, observed))
    propagated = oracle.observation_log_density(source, observed, jump_clock=0.5, continuous_clock=0.5)
    assert math.isfinite(propagated)
    assert math.isfinite(oracle.observation_log_density(source, None))
    for before, after in zip(source, observed):
        assert before.key == after.key
        old, new = before.to_metric_event(), after.to_metric_event()
        changed = {i for i, (left, right) in enumerate(zip(old.coordinates, new.coordinates)) if left != right}
        if not before.key.dimension:
            assert changed == set() and after is before
        elif domain == cks.PHYSIONET_DOMAIN_ID:
            assert changed == {75 + cks.PHYSIONET_PARAMETERS.index("HR")}
            assert decode_metric_event(new).parameter == "HR"
        else:
            assert changed == {7}
            semantic = decode_metric_event(new)
            assert semantic.invoice_no == "C000042" and semantic.quantity == -3
            assert semantic.description == "" and semantic.country is None
            assert new.coordinates[1] == 1


def test_tiny_retail_reference_key_probability_stays_in_log_space_in_actual_oracle():
    key = RetailStateKey("c000000", "x", "x" * 512, -2**2000,
                         (2009, 12, 1, 0, 0, 0, 0), "", "ZERO")
    event = FactoredEvent(key)
    oracle = oracle_for(cks.RETAIL_DOMAIN_ID, (event,), False)
    assert oracle.reference.log_prob(key) < -1000
    assert math.exp(oracle.reference.log_prob(key)) == 0.0
    log_signal = oracle.clean_observation_log_density((event,), (event,))
    assert math.isfinite(log_signal) and log_signal > 1000
    assert math.isfinite(oracle.observation_log_density((event,), (event,)))
    assert math.isfinite(oracle.target_log_density(((event,),), (event,)))


@pytest.mark.parametrize("domain", [cks.PHYSIONET_DOMAIN_ID, cks.RETAIL_DOMAIN_ID])
def test_train_mixture_oracle_keeps_positive_unseen_complete_key_support(domain):
    source = supplied_state(domain)
    oracle = oracle_for(domain, source, True)
    if domain == cks.PHYSIONET_DOMAIN_ID:
        unseen = FactoredEvent(PhysioStateKey(43, "GCS", "ATOMIC", Fraction(1, 3)))
    else:
        unseen = FactoredEvent(RetailStateKey("000043", "unseen", None, 0,
                              (2010, 2, 3, 4, 5, 6, 7), None, "ZERO"))
    assert unseen.key not in oracle.reference.train_keys
    assert oracle.reference.log_prob(unseen.key) == pytest.approx(
        math.log(0.2) + oracle.reference.universal.log_prob(unseen.key))
    assert math.isfinite(oracle.target_log_density((source,), (unseen,)))
    model, batch = energy_batch(domain, (unseen,))
    assert bool(torch.isfinite(model(batch)).all())
    assert oracle.reference.diagnostics()["train_split_or_no_leakage_independently_verified"] is False
