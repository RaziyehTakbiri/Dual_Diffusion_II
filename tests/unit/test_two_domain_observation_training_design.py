"""Invented visible observations only; no data access, training run or GPU job."""
from dataclasses import FrozenInstanceError, replace
from fractions import Fraction
import inspect

import pytest
import torch

from heterodiff.events.observations import ObservationView, ObservedAnchor, ObservationPattern
from heterodiff.models import two_domain_observation_training_design as design


def schema(domain='online-retail-ii'):
    return design.VisibleObservationSchema(
        domain, (0, 1), (('x', (1.0,)), ('vector', (2.0, 3.0))),
        ('anchors', 'partial'), ('static_z',), (1.0,), 10.0)


def batch(spec=None):
    spec = spec or schema()
    views = (ObservationView((ObservedAnchor(event_time=0.0, event_type=0, marks={'x': (0.0,)}),), 1),
             ObservationView((ObservedAnchor(marks={'vector': (2.0, -3.0)}),), None))
    return design.tensorize_observations(views, ('anchors', 'partial'), ((0.0,), (1.0,)), spec)


def test_feature_shape_visible_masks_and_hidden_cardinality():
    spec = schema()
    raw = batch(spec)
    assert raw.validate(spec) == 2
    assert raw.anchor_features.shape == (2, 11)
    assert raw.global_features.shape == (2, 6)
    assert raw.anchor_features[0, :5].tolist() == [1, 0, 1, 1, 0]
    assert raw.anchor_features[0, 5:7].tolist() == [1, 0]  # observed x=0, not missing
    assert raw.anchor_features[1, :7].tolist() == [0] * 7
    assert raw.global_features[:, :3].tolist() == [[0.5, 1, 0.5], [0.5, 0, 0]]
    assert not raw.anchor_features.requires_grad
    assert raw.to('cpu').task_context_sha256s == raw.task_context_sha256s
    assert raw.to('cpu').anchor_features.data_ptr() != raw.anchor_features.data_ptr()


def test_hidden_empty_and_observed_zero_cardinality_distinct_without_target_alignment():
    spec = schema()
    raw = design.tensorize_observations((ObservationView((), None), ObservationView((), 0)),
                                       ('anchors',) * 2, ((0.0,),) * 2, spec)
    assert raw.anchor_features.shape == (0, spec.anchor_dimension)
    assert raw.global_features[:, :3].tolist() == [[0, 0, 0], [0, 1, 0]]
    encoded = design.ObservationConditionEncoderV1(spec)(raw)
    assert encoded.shape == (2, 64) and torch.isfinite(encoded).all()
    with pytest.raises(ValueError, match='ObservationView'):
        design.tensorize_observations((ObservationPattern(),), ('anchors',), ((0.0,),), spec)


def test_unknown_visible_fields_type_and_width_rejected():
    spec = schema()
    for anchor in (ObservedAnchor(marks={'hidden_target': (1.0,)}),
                   ObservedAnchor(event_type=2), ObservedAnchor(marks={'x': (1.0, 2.0)})):
        with pytest.raises(ValueError):
            design.tensorize_observations((ObservationView((anchor,)),), ('anchors',), ((0.0,),), spec)


def test_occurrences_preserved_and_encoder_is_permutation_invariant_to_tolerance():
    spec = schema()
    anchor = ObservedAnchor(event_time=1.0, marks={'x': (0.2,)})
    different = ObservedAnchor(event_type=1, marks={'x': (-0.7,)})
    raw = design.tensorize_observations((ObservationView((anchor, anchor, different)),),
                                       ('anchors',), ((0.0,),), spec)
    assert len(raw.anchor_features) == 3
    assert raw.global_features[0, 0].item() == 0.75
    permuted = replace(raw, anchor_features=raw.anchor_features.flip(0), batch_indices=raw.batch_indices.flip(0))
    model = design.ObservationConditionEncoderV1(spec)
    torch.testing.assert_close(model(raw), model(permuted), rtol=1e-6, atol=1e-6)
    once = design.tensorize_observations((ObservationView((anchor,)),), ('anchors',), ((0.0,),), spec)
    assert not torch.equal(model(raw), model(once))


@pytest.mark.parametrize('domain', ['physionet-challenge-2012', 'online-retail-ii'])
def test_trainable_encoders_bounded_outputs_independent_nuisance_and_exact_counts(domain):
    spec = schema(domain)
    raw = batch(spec)
    encoder = design.ObservationConditionEncoderV1(spec, initialization_seed=2**64 - 1)
    nuisance = design.ObservationOnlyNuisanceV1(spec, initialization_seed=4)
    output, scalar = encoder(raw), nuisance(raw)
    assert output.shape == (2, 64) and output.dtype == torch.float32
    assert output.requires_grad and bool((output.abs() <= 1).all())
    assert scalar.shape == (2,)
    encoder_grad = torch.autograd.grad(output.square().sum(), tuple(encoder.parameters()), retain_graph=True)
    assert all(value is not None for value in encoder_grad)
    assert any(value.abs().sum() > 0 for value in encoder_grad)
    assert all(value is None for value in torch.autograd.grad(scalar.sum(), tuple(encoder.parameters()), allow_unused=True))
    counts = design.training_design_parameter_counts(spec)
    assert counts['condition_encoder'] == encoder.parameter_count
    assert counts['nuisance_encoder'] == nuisance.encoder.parameter_count
    assert nuisance.parameter_count == counts['nuisance_encoder'] + counts['nuisance_head']
    assert counts['nuisance_head'] == 2113
    assert counts['additional_unique_trainable_parameters'] == encoder.parameter_count + nuisance.parameter_count
    assert not counts['b06_successor_adopted'] and not counts['production_schema_admitted']
    assert not ({value.data_ptr() for value in encoder.parameters()} & {value.data_ptr() for value in nuisance.parameters()})


def test_proposed_domain_count_formula_includes_both_new_encoders_without_double_counting():
    for domain, dimension, encoder_count, total in (
        ('physionet-challenge-2012', 112, 27392, 268099),
        ('online-retail-ii', 10, 14336, 215875)):
        spec = design.VisibleObservationSchema(domain, (0,),
            tuple(('coordinate_%03d' % i, (1.0,)) for i in range(dimension)),
            ('one_declared_task',), (), ())
        counts = design.training_design_parameter_counts(spec)
        assert counts['condition_encoder'] == encoder_count
        assert counts['proposed_total_unique_parameters'] == total
        with_z = replace(spec, static_context_names=('static_z',), static_context_scales=(1.0,))
        assert design.training_design_parameter_counts(with_z)['proposed_total_unique_parameters'] == total + 128


def test_clock_state_paths_and_wrong_schema_fail_closed():
    spec, raw = schema(), batch()
    assert 'latent' not in inspect.signature(design.tensorize_observations).parameters
    assert list(inspect.signature(design.ObservationOnlyNuisanceV1.forward).parameters) == ['self', 'batch']
    with pytest.raises(ValueError, match='aliases latent/time'):
        raw.validate(spec, forbidden_tensors=(raw.anchor_features,))
    with pytest.raises(ValueError, match='detached'):
        replace(raw, anchor_features=raw.anchor_features.clone().requires_grad_()).validate(spec)
    with pytest.raises(ValueError, match='schema binding'):
        raw.validate(replace(spec, physical_time_scale=2.0))
    with pytest.raises(ValueError, match='diffusion clock'):
        replace(spec, static_context_names=('reverse_time',))


def test_exact_context_identity_not_inferred_from_colliding_fp32_features():
    spec = schema()
    raw = design.tensorize_observations((ObservationView(),) * 2, ('anchors',) * 2,
                                       ((1e100,), (2e100,)), spec)
    assert torch.equal(raw.static_context_features[0], raw.static_context_features[1])
    assert raw.task_context_sha256s[0] != raw.task_context_sha256s[1]


def test_declared_models_and_law_do_not_change_global_random_state():
    before = torch.random.get_rng_state().clone()
    spec = schema()
    design.ObservationConditionEncoderV1(spec)
    design.ObservationOnlyNuisanceV1(spec)
    law = design.SyntheticTrainingLawV1(spec, ((0.0,), (1.0,)), Fraction(2))
    first = law.draw(16, generator=torch.Generator().manual_seed(99))
    second = law.draw(16, generator=torch.Generator().manual_seed(99))
    assert first == second
    assert torch.equal(before, torch.random.get_rng_state())
    assert all(0 < row.reverse_time < 2 and row.reverse_time + row.direct_time == 2 for row in first)


def test_uniform_q_proposal_full_open_support_is_not_finite_rng_claim():
    law = design.SyntheticTrainingLawV1(schema(), ((0.0,), (1.0,)), Fraction(2))
    for time in (Fraction(1, 10**20), Fraction(1), Fraction(2) - Fraction(1, 10**20)):
        assert law.proposed_continuous_time_density(time) == Fraction(1, 2)
    assert law.proposed_continuous_time_density(Fraction(0)) == 0
    assert law.proposed_continuous_time_density(Fraction(2)) == 0
    weights = law.equal_prior_weights(16)
    assert weights.joint == weights.product == (Fraction(1),) * 16
    assert weights.target_law_id == weights.proposal_law_id == law.law_id
    report = law.description()
    assert report['proposed_q_has_full_open_interval_support']
    assert not report['finite_midpoint_draws_exactly_sample_continuous_q']
    assert not report['continuous_to_discrete_rn_correction_claimed']
    assert report['synthetic_unit_weights_apply_only_to_declared_finite_law']
    assert not report['cross_context_batch_permutation_allowed']
    assert not report['initial_law_or_base_trajectories_generated_by_this_component']
    assert not report['production_law_or_design_adopted']
    with pytest.raises(FrozenInstanceError):
        law.horizon = Fraction(3)
    assert design.SyntheticTrainingLawV1(schema(), ((0.0,),), Fraction(2)).law_id != law.law_id


def test_explicit_resource_bounds_reject_instead_of_truncating(monkeypatch):
    spec = schema()
    monkeypatch.setattr(design, 'MAX_VISIBLE_ANCHORS', 1)
    view = ObservationView((ObservedAnchor(event_time=0.0),) * 2)
    with pytest.raises(ValueError, match='no truncation'):
        design.tensorize_observations((view,), ('anchors',), ((0.0,),), spec)
