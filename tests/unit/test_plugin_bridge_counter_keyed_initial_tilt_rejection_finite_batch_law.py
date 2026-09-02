"""Hostile tests for checkpoint-38 exact finite-batch rejection laws."""

import ast
from fractions import Fraction
import inspect
from pathlib import Path
import pickle
import random
import subprocess
import sys
import textwrap

import numpy as np
import pytest


torch = pytest.importorskip(
    "torch", reason="counter-keyed rejection finite-batch laws require PyTorch"
)

from heterodiff.processes import (  # noqa: E402
    plugin_bridge_counter_keyed_initial_tilt_rejection_finite_batch_law as law,
)
from heterodiff.theory.configuration_reference import TransformedEvent  # noqa: E402
from tests.unit import (  # noqa: E402
    test_plugin_bridge_counter_keyed_initial_tilt_rejection_decision as checkpoint37,
)
from tests.unit import (  # noqa: E402
    test_plugin_bridge_counter_keyed_initial_tilt_rejection_preparation as checkpoint36,
)


LAW_POLICY = (
    law.PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_POLICY
)
LAW_ROLE = "c" * 64
DECISION_ROLE = "b" * 64
PREPARATION_ROLE = "a" * 64
D = 1 << 64
_DECLARE = law.declare_fixed_batch_iid_uint64_decision_word_hypothesis
_VALIDATE_HYPOTHESIS = law.validate_fixed_batch_iid_uint64_decision_word_hypothesis
_CERTIFY = (
    law.certify_plugin_bridge_counter_keyed_initial_tilt_rejection_finite_batch_law
)
_MATCHING = law.require_matching_counter_keyed_initial_tilt_rejection_finite_batch_law
_VALIDATE_CERTIFICATE = (
    law.validate_counter_keyed_initial_tilt_rejection_finite_batch_law_certificate
)


def _rng_snapshot():
    numpy_state = np.random.get_state()
    return (
        random.getstate(),
        (numpy_state[0], numpy_state[1].copy(), *numpy_state[2:]),
        torch.random.get_rng_state().clone(),
    )


def _assert_rng_unchanged(before):
    python_before, numpy_before, torch_before = before
    numpy_after = np.random.get_state()
    assert random.getstate() == python_before
    assert numpy_after[0] == numpy_before[0]
    assert np.array_equal(numpy_after[1], numpy_before[1])
    assert numpy_after[2:] == numpy_before[2:]
    assert torch.equal(torch.random.get_rng_state(), torch_before)


def _forged(value, **updates):
    forged = object.__new__(type(value))
    for name in type(value).__annotations__:
        object.__setattr__(forged, name, updates.get(name, getattr(value, name)))
    return forged


def _forge_owner(owner, **updates):
    forged = object.__new__(type(owner))
    for name in type(owner).__slots__:
        object.__setattr__(forged, name, updates.get(name, getattr(owner, name)))
    return forged


def _values(record, fields, payload, digest_name, **updates):
    values = {name: updates.get(name, getattr(record, name)) for name in fields()}
    values[digest_name] = "0" * 64
    values[digest_name] = law._semantic_digest(payload(values))
    return values


def _fraction(record, numerator_name, denominator_name):
    return Fraction(getattr(record, numerator_name), getattr(record, denominator_name))


@pytest.fixture(scope="module")
def live_bundle():
    """Build one three-attempt ancestry and call CP38 exactly once."""

    bundle = checkpoint36.certified_bundle.__wrapped__()
    preparation_hypothesis, preparation_owner = checkpoint36._certify(
        bundle,
        attempt_budget=3,
        role=PREPARATION_ROLE,
    )
    decision_owner = checkpoint37._CERTIFY(
        preparation_owner,
        decision_policy=checkpoint37.DECISION_POLICY,
        decision_role_sha256=DECISION_ROLE,
    )
    word_hypothesis = _DECLARE(
        hypothesis_scope=law.FIXED_BATCH_IID_UINT64_DECISION_WORD_HYPOTHESIS_SCOPE,
        word_source_premise=law.FIXED_BATCH_IID_UINT64_DECISION_WORD_PREMISE,
    )

    # Instrument the exact frozen CP37 method before CP38 captures it.  Restore
    # both module/class surfaces and the owner's cached callback after the call.
    original_decide = law._DEC_DECIDE
    calls = {"decide": 0}

    def counted_decide(parent_owner, run_id, initialization_index):
        calls["decide"] += 1
        return original_decide(parent_owner, run_id, initialization_index)

    law._DEC_OWNER_TYPE.decide = counted_decide
    law._DEC_DECIDE = counted_decide
    owner = None
    before = _rng_snapshot()
    try:
        owner = _CERTIFY(
            decision_owner,
            word_hypothesis,
            law_policy=LAW_POLICY,
            law_role_sha256=LAW_ROLE,
        )
        result = owner.resolve(37_000, 0)
    finally:
        law._DEC_OWNER_TYPE.decide = original_decide
        law._DEC_DECIDE = original_decide
        if owner is not None:
            object.__setattr__(owner, "_parent_decide", original_decide)
    _assert_rng_unchanged(before)
    assert calls == {"decide": 1}
    return {
        **bundle,
        "preparation_hypothesis": preparation_hypothesis,
        "preparation_owner": preparation_owner,
        "decision_owner": decision_owner,
        "word_hypothesis": word_hypothesis,
        "owner": owner,
        "result": result,
        "parent_decide_calls": calls["decide"],
    }


@pytest.fixture(scope="module")
def synthetic_parents(live_bundle):
    parent = live_bundle["result"].parent_decision_result
    quota = checkpoint37.decision._floor_exp_uint64_quota(Fraction(-1)).quota
    return {
        "all_zero": checkpoint37._synthetic_case(
            parent,
            (
                (Fraction(-64), 0),
                (Fraction(-64), D - 1),
                (Fraction(-65), 1),
            ),
        ),
        "quota_d": checkpoint37._synthetic_case(
            parent,
            (
                (Fraction(0), D - 1),
                (Fraction(-1), quota),
                (Fraction(-64), 0),
            ),
        ),
        "mixed": checkpoint37._synthetic_case(
            parent,
            (
                (Fraction(-1), quota),
                (Fraction(-2), 0),
                (Fraction(0), D - 1),
            ),
        ),
        "exhausted": checkpoint37._synthetic_case(
            parent,
            (
                (Fraction(-1), quota),
                (Fraction(-2), D - 1),
                (Fraction(-64), 0),
            ),
        ),
        "projection_selected": checkpoint37._synthetic_case(
            parent,
            (
                (Fraction(-1), 0),
                (Fraction(-2), 0),
                (Fraction(-64), 0),
            ),
        ),
        "projection_exhausted": checkpoint37._synthetic_case(
            parent,
            (
                (Fraction(-1), quota),
                (Fraction(-2), D - 1),
                (Fraction(-64), D - 1),
            ),
        ),
    }


@pytest.mark.parametrize(
    "quotas, expected_first, expected_exhaustion",
    (
        ((0, 0, 0), (Fraction(0),) * 3, Fraction(1)),
        ((D, 0, D), (Fraction(1), Fraction(0), Fraction(0)), Fraction(0)),
        (
            (D // 2, D // 4, D),
            (Fraction(1, 2), Fraction(1, 8), Fraction(3, 8)),
            Fraction(0),
        ),
        (
            (D // 2, D // 4, 0),
            (Fraction(1, 2), Fraction(1, 8), Fraction(0)),
            Fraction(3, 8),
        ),
    ),
)
def test_pure_first_success_partition_exact_branches(
    quotas, expected_first, expected_exhaustion
):
    (
        survival_befores,
        first_masses,
        exhaustion,
        selection,
    ) = law._first_success_partition(quotas)
    assert first_masses == expected_first
    assert exhaustion == expected_exhaustion
    assert selection == sum(expected_first, Fraction(0))
    assert selection + exhaustion == 1
    assert survival_befores[0] == 1
    for position in range(len(quotas) - 1):
        assert survival_befores[position + 1] == (
            survival_befores[position] * (1 - Fraction(quotas[position], D))
        )


def test_pure_stable_configuration_partition_aggregates_duplicates_in_order():
    key_a = ((1, (0.0,)),)
    key_b = ((2, (1.0,)),)
    representatives, contributors, mapping = law._stable_configuration_key_partition(
        (key_a, key_b, key_a, key_a, key_b)
    )
    assert representatives == (0, 1)
    assert contributors == ((0, 2, 3), (1, 4))
    assert mapping == (0, 1, 0, 0, 1)


@pytest.mark.parametrize("bad", ((), (True,), (-1,), (D + 1,), [0]))
def test_pure_partition_preflights_reject_malformed_quotas(bad):
    with pytest.raises((TypeError, ValueError)):
        law._first_success_partition(bad)


def test_public_exports_constants_and_signatures_are_frozen(live_bundle):
    expected_exports = {
        (
            "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FINITE_BATCH_"
            "LAW_SCHEMA_VERSION"
        ),
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_POLICY",
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_SCOPE",
        "INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_DYADIC_DENOMINATOR",
        "INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_MAX_ATTEMPTS",
        "INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_MAX_CONFIGURATION_EVENTS",
        "INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_MAX_COORDINATES_PER_EVENT",
        "INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_OUTCOMES",
        "INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_FIXED_BATCH_OUTCOME_THEOREM",
        "INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_FIXED_BATCH_CONFIGURATION_THEOREM",
        "INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_AUGMENTED_IDEAL_TV_THEOREM",
        "INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_OPERATIONAL_DEFINITION",
        "FIXED_BATCH_IID_UINT64_DECISION_WORD_HYPOTHESIS_SCHEMA_VERSION",
        "FIXED_BATCH_IID_UINT64_DECISION_WORD_HYPOTHESIS_SCOPE",
        "FIXED_BATCH_IID_UINT64_DECISION_WORD_PREMISE",
        "FixedBatchIidUint64DecisionWordHypothesis",
        "CounterKeyedInitialTiltRejectionFiniteBatchLawCertificate",
        "CounterKeyedInitialTiltRejectionAttemptMass",
        "CounterKeyedInitialTiltRejectionConfigurationMass",
        "CounterKeyedInitialTiltRejectionFiniteBatchLawResult",
        "CounterKeyedInitialTiltRejectionFiniteBatchLawOwner",
        "PluginBridgeCounterKeyedInitialTiltRejectionFiniteBatchLawError",
        "declare_fixed_batch_iid_uint64_decision_word_hypothesis",
        "validate_fixed_batch_iid_uint64_decision_word_hypothesis",
        "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_finite_batch_law",
        "require_matching_counter_keyed_initial_tilt_rejection_finite_batch_law",
        "validate_counter_keyed_initial_tilt_rejection_finite_batch_law_certificate",
    }
    assert set(law.__all__) == expected_exports
    assert len(law.__all__) == len(expected_exports)
    assert law.INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_DYADIC_DENOMINATOR == D
    assert law.INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_MAX_ATTEMPTS == 64
    assert law.INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_MAX_CONFIGURATION_EVENTS == 64
    assert (
        law.INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_MAX_COORDINATES_PER_EVENT == 65_536
    )
    assert law.INITIAL_TILT_REJECTION_FINITE_BATCH_LAW_OUTCOMES == (
        "selected",
        "exhausted",
    )
    owner_type = law.CounterKeyedInitialTiltRejectionFiniteBatchLawOwner
    assert str(inspect.signature(owner_type.resolve)) == (
        "(self, run_id: 'object', initialization_index: 'object') -> "
        "'CounterKeyedInitialTiltRejectionFiniteBatchLawResult'"
    )
    assert str(inspect.signature(owner_type.validate_result)) == (
        "(self, result: 'object', run_id: 'object', "
        "initialization_index: 'object') -> "
        "'CounterKeyedInitialTiltRejectionFiniteBatchLawResult'"
    )
    assert str(inspect.signature(_CERTIFY)) == (
        "(decision_owner: 'object', word_law_hypothesis: 'object', *, "
        "law_policy: 'object', law_role_sha256: 'object') -> "
        "'CounterKeyedInitialTiltRejectionFiniteBatchLawOwner'"
    )
    assert live_bundle["parent_decide_calls"] == 1


def test_word_hypothesis_truth_matrix_scope_and_digest_are_exact(live_bundle):
    hypothesis = live_bundle["word_hypothesis"]
    assert _VALIDATE_HYPOTHESIS(hypothesis) is hypothesis
    assert hypothesis.raw_word_domain_size == D
    for name in (
        "conditioning_projection_excludes_reserved_words",
        "conditioning_projection_excludes_decisions_and_outcome",
        "conditioning_projection_excludes_word_binding_parent_digests",
        "abstract_words_iid_uniform_uint64",
        "abstract_words_independent_of_projection",
    ):
        assert getattr(hypothesis, name) is True
    for name in (
        "live_philox_words_identified_with_abstract_words",
        "live_uniformity_certified",
        "live_independence_certified",
        "physical_randomness_certified",
    ):
        assert getattr(hypothesis, name) is False
    assert "not-live-philox-word-law" in hypothesis.hypothesis_scope
    assert "not-the-live-philox-words" in hypothesis.word_source_premise
    with pytest.raises(ValueError, match="digest"):
        _VALIDATE_HYPOTHESIS(_forged(hypothesis, hypothesis_sha256="f" * 64))


def test_certificate_truth_matrix_is_exhaustive_and_conservative(live_bundle):
    certificate = live_bundle["owner"].certificate
    for name in law._CERTIFICATE_POSITIVE_FLAGS:
        assert getattr(certificate, name) is True
    for name in law._CERTIFICATE_NEGATIVE_FLAGS:
        assert getattr(certificate, name) is False
    assert set(law._CERTIFICATE_POSITIVE_FLAGS).isdisjoint(
        law._CERTIFICATE_NEGATIVE_FLAGS
    )
    assert (
        set(law._CERTIFICATE_POSITIVE_FLAGS) | set(law._CERTIFICATE_NEGATIVE_FLAGS)
    ) == {
        name
        for name in law._certificate_fields()
        if name.endswith("certified")
        or name.endswith("admissible")
        or name.endswith("admitted")
        or name
        in {
            "passed",
            "test28_closed",
            "runtime_portable",
            "cryptographic_authentication",
        }
    }
    assert certificate.attempt_budget == 3
    assert certificate.decision_owner_runtime_identity == id(
        live_bundle["decision_owner"]
    )
    assert certificate.word_law_hypothesis is live_bundle["word_hypothesis"]
    assert certificate.augmented_configuration_ideal_tv_comparison_certified is True
    assert certificate.success_conditioned_ideal_tv_comparison_certified is False
    assert certificate.initializer_admissible is False
    assert certificate.live_initializer_distribution_admitted is False
    assert certificate.test28_closed is False
    assert certificate.result_promotion_admissible is False


def test_live_result_binds_parent_and_materializes_complete_exact_partition(
    live_bundle,
):
    owner = live_bundle["owner"]
    result = live_bundle["result"]
    parent = result.parent_decision_result
    assert result.certificate is owner.certificate
    assert parent.certificate is owner.certificate.decision_certificate
    assert result.parent_decision_result_sha256 == parent.result_sha256
    assert result.run_id == parent.run_id == 37_000
    assert result.initialization_index == parent.initialization_index == 0
    assert result.attempt_budget == 3
    assert len(result.attempt_masses) == 3
    assert len(result.attempt_mass_sha256s) == 3
    assert 1 <= result.unique_configuration_count <= 3
    assert len(result.configuration_masses) == result.unique_configuration_count

    exhaustion = _fraction(
        result,
        "fixed_batch_exhaustion_probability_numerator",
        "fixed_batch_exhaustion_probability_denominator",
    )
    selection = _fraction(
        result,
        "fixed_batch_selection_probability_numerator",
        "fixed_batch_selection_probability_denominator",
    )
    assert exhaustion + selection == 1
    assert (
        _fraction(
            result,
            "augmented_law_normalization_numerator",
            "augmented_law_normalization_denominator",
        )
        == 1
    )
    assert (
        _fraction(
            result,
            "grouped_selection_mass_numerator",
            "grouped_selection_mass_denominator",
        )
        == selection
    )
    assert (
        sum(
            (
                _fraction(
                    row,
                    "fixed_batch_first_selection_probability_numerator",
                    "fixed_batch_first_selection_probability_denominator",
                )
                for row in result.attempt_masses
            ),
            Fraction(0),
        )
        == selection
    )
    assert (
        sum(
            (
                _fraction(
                    row,
                    "fixed_batch_selection_probability_numerator",
                    "fixed_batch_selection_probability_denominator",
                )
                for row in result.configuration_masses
            ),
            Fraction(0),
        )
        == selection
    )
    assert result.outcome == parent.outcome
    assert _fraction(
        result,
        "counterfactual_mass_of_realized_outcome_numerator",
        "counterfactual_mass_of_realized_outcome_denominator",
    ) == Fraction(
        parent.conditional_outcome_probability_numerator,
        parent.conditional_outcome_probability_denominator,
    )
    assert result.reported_counterfactual_masses_require_abstract_iid_premise is True
    assert result.actual_outcome_is_counterfactual_draw is False
    assert result.deterministic_fixed_address_replay_only is True
    assert result.operational_failure_returned_as_exhaustion is False
    assert result.initializer_output_admitted is False
    assert result.initializer_admissible is False
    assert result.lineage_attached is False
    assert result.tag3_payload_attached is False
    assert _fraction(
        result,
        "augmented_configuration_ideal_tv_strict_upper_numerator",
        "augmented_configuration_ideal_tv_strict_upper_denominator",
    ) == Fraction(3, D)
    assert result.augmented_configuration_ideal_tv_upper_is_strict is True
    assert result.ideal_comparison_uses_separate_common_uniform_coupling is True
    assert result.success_conditioned_ideal_tv_bound_claimed is False
    if result.outcome == "selected":
        assert result.selected_configuration is parent.selected_configuration
        assert result.selected_configuration_structurally_valid_as_initial_state is True
        assert result.bounded_exhaustion_is_valid_no_state_outcome is False
        row = result.configuration_masses[result.selected_configuration_ordinal]
        assert _fraction(
            result,
            "counterfactual_aggregate_mass_of_realized_configuration_numerator",
            "counterfactual_aggregate_mass_of_realized_configuration_denominator",
        ) == _fraction(
            row,
            "fixed_batch_selection_probability_numerator",
            "fixed_batch_selection_probability_denominator",
        )
        assert _fraction(
            result,
            ("counterfactual_conditioned_mass_of_realized_" "configuration_numerator"),
            (
                "counterfactual_conditioned_mass_of_realized_"
                "configuration_denominator"
            ),
        ) == _fraction(
            row,
            "selected_conditioned_probability_numerator",
            "selected_conditioned_probability_denominator",
        )
    else:
        assert result.selected_configuration is None
        assert (
            result.selected_configuration_structurally_valid_as_initial_state is False
        )
        assert result.bounded_exhaustion_is_valid_no_state_outcome is True
        for name in (
            "counterfactual_aggregate_mass_of_realized_configuration_numerator",
            "counterfactual_aggregate_mass_of_realized_configuration_denominator",
            ("counterfactual_conditioned_mass_of_realized_" "configuration_numerator"),
            (
                "counterfactual_conditioned_mass_of_realized_"
                "configuration_denominator"
            ),
        ):
            assert getattr(result, name) is None


def test_exact_product_formula_and_telescoping_for_every_attempt(
    live_bundle, synthetic_parents
):
    data = law._materialize_law(
        live_bundle["owner"].certificate,
        synthetic_parents["mixed"],
    )
    survival = Fraction(1)
    expected_first = []
    for threshold, row in zip(
        synthetic_parents["mixed"].thresholds, data.attempt_masses
    ):
        acceptance = Fraction(threshold.acceptance_quota, D)
        first = survival * acceptance
        after = survival * (1 - acceptance)
        assert (
            _fraction(
                row,
                "acceptance_probability_numerator",
                "acceptance_probability_denominator",
            )
            == acceptance
        )
        assert (
            _fraction(
                row,
                "survival_before_numerator",
                "survival_before_denominator",
            )
            == survival
        )
        assert (
            _fraction(
                row,
                "fixed_batch_first_selection_probability_numerator",
                "fixed_batch_first_selection_probability_denominator",
            )
            == first
        )
        assert (
            _fraction(
                row,
                "survival_after_numerator",
                "survival_after_denominator",
            )
            == after
        )
        expected_first.append(first)
        survival = after
    assert data.exhaustion_probability == survival
    assert data.selection_probability == sum(expected_first, Fraction(0))
    assert data.selection_probability + data.exhaustion_probability == 1
    assert data.selection_probability == 1  # terminal quota-D attempt
    assert all(
        row.selected_conditioned_probability_defined for row in data.attempt_masses
    )
    assert (
        sum(
            (
                _fraction(
                    row,
                    "selected_conditioned_probability_numerator",
                    "selected_conditioned_probability_denominator",
                )
                for row in data.attempt_masses
            ),
            Fraction(0),
        )
        == 1
    )


def test_all_zero_and_quota_d_terminal_laws_are_total(live_bundle, synthetic_parents):
    zero = law._materialize_law(
        live_bundle["owner"].certificate,
        synthetic_parents["all_zero"],
    )
    assert zero.exhaustion_probability == 1
    assert zero.selection_probability == 0
    for row in zero.attempt_masses:
        assert row.acceptance_quota == 0
        assert (
            _fraction(
                row,
                "fixed_batch_first_selection_probability_numerator",
                "fixed_batch_first_selection_probability_denominator",
            )
            == 0
        )
        assert row.selected_conditioned_probability_defined is False
        assert row.selected_conditioned_probability_numerator is None
        assert row.selected_conditioned_probability_denominator is None
    for row in zero.configuration_masses:
        assert row.selected_conditioned_probability_defined is False
        assert row.selected_conditioned_probability_numerator is None
        assert row.selected_conditioned_probability_denominator is None

    unity = law._materialize_law(
        live_bundle["owner"].certificate,
        synthetic_parents["quota_d"],
    )
    assert unity.attempt_masses[0].acceptance_quota == D
    assert (
        _fraction(
            unity.attempt_masses[0],
            "fixed_batch_first_selection_probability_numerator",
            "fixed_batch_first_selection_probability_denominator",
        )
        == 1
    )
    assert all(
        _fraction(
            row,
            "fixed_batch_first_selection_probability_numerator",
            "fixed_batch_first_selection_probability_denominator",
        )
        == (1 if position == 0 else 0)
        for position, row in enumerate(unity.attempt_masses)
    )
    assert unity.selection_probability == 1
    assert unity.exhaustion_probability == 0


def test_live_exhaustion_is_not_confused_with_failure_and_has_exact_mass(
    live_bundle, synthetic_parents
):
    parent = synthetic_parents["exhausted"]
    assert parent.outcome == "exhausted"
    data = law._materialize_law(live_bundle["owner"].certificate, parent)
    expected = Fraction(1)
    for threshold in parent.thresholds:
        expected *= 1 - Fraction(threshold.acceptance_quota, D)
    assert data.exhaustion_probability == expected
    assert expected > 0
    assert parent.operational_failure_returned_as_exhaustion is False


def test_duplicate_configurations_are_aggregated_by_exact_structure(
    live_bundle, synthetic_parents
):
    parent = synthetic_parents["mixed"]
    first_attempt = parent.thresholds[0].preparation_attempt
    attempts = []
    thresholds = []
    for threshold in parent.thresholds:
        attempt = _forged(
            threshold.preparation_attempt,
            canonical_configuration=first_attempt.canonical_configuration,
            canonical_configuration_sha256=(
                first_attempt.canonical_configuration_sha256
            ),
        )
        attempts.append(attempt)
        thresholds.append(checkpoint37._threshold_for(parent.certificate, attempt))
    duplicate_preparation = _forged(
        parent.preparation_result,
        attempts=tuple(attempts),
    )
    duplicate_parent = _forged(
        parent,
        preparation_result=duplicate_preparation,
        thresholds=tuple(thresholds),
    )
    data = law._materialize_law(
        live_bundle["owner"].certificate,
        duplicate_parent,
    )
    assert data.attempt_to_configuration_ordinal == (0, 0, 0)
    assert len(data.configuration_masses) == 1
    grouped = data.configuration_masses[0]
    assert grouped.attempt_indices == (0, 1, 2)
    assert grouped.duplicate_attempt_count == 3
    assert grouped.configuration is first_attempt.canonical_configuration
    assert (
        _fraction(
            grouped,
            "fixed_batch_selection_probability_numerator",
            "fixed_batch_selection_probability_denominator",
        )
        == data.selection_probability
    )
    assert (
        _fraction(
            grouped,
            "selected_conditioned_probability_numerator",
            "selected_conditioned_probability_denominator",
        )
        == 1
    )


def test_conditioning_projection_is_invariant_to_words_decisions_outcome_and_digests(
    live_bundle, synthetic_parents
):
    selected = synthetic_parents["projection_selected"]
    exhausted = synthetic_parents["projection_exhausted"]
    assert selected.outcome == "selected"
    assert exhausted.outcome == "exhausted"
    assert selected.result_sha256 != exhausted.result_sha256
    selected_projection = law._conditioning_projection_sha256(selected)
    exhausted_projection = law._conditioning_projection_sha256(exhausted)
    assert selected_projection == exhausted_projection
    selected_law = law._materialize_law(live_bundle["owner"].certificate, selected)
    exhausted_law = law._materialize_law(live_bundle["owner"].certificate, exhausted)
    assert (
        selected_law.conditioning_projection_sha256
        == exhausted_law.conditioning_projection_sha256
    )
    assert selected_law.selection_probability == exhausted_law.selection_probability
    assert selected_law.exhaustion_probability == exhausted_law.exhaustion_probability
    assert tuple(
        _fraction(
            row,
            "fixed_batch_first_selection_probability_numerator",
            "fixed_batch_first_selection_probability_denominator",
        )
        for row in selected_law.attempt_masses
    ) == tuple(
        _fraction(
            row,
            "fixed_batch_first_selection_probability_numerator",
            "fixed_batch_first_selection_probability_denominator",
        )
        for row in exhausted_law.attempt_masses
    )


def test_conditioning_projection_accepts_more_than_4096_coordinates(live_bundle):
    parent = live_bundle["result"].parent_decision_result
    wide_configuration = (TransformedEvent(7, (0.25,) * 4_097),)
    first_threshold = parent.thresholds[0]
    wide_attempt = _forged(
        first_threshold.preparation_attempt,
        canonical_configuration=wide_configuration,
    )
    wide_threshold = _forged(
        first_threshold,
        preparation_attempt=wide_attempt,
    )
    wide_parent = _forged(
        parent,
        thresholds=(wide_threshold,) + parent.thresholds[1:],
    )
    projection = law._conditioning_projection_sha256(wide_parent)
    assert isinstance(projection, str)
    assert len(projection) == 64
    assert projection != law._conditioning_projection_sha256(parent)


def test_parent_preflight_rejects_bad_decision_and_preparation_before_snapshot(
    live_bundle,
):
    certificate = live_bundle["owner"].certificate
    parent = live_bundle["result"].parent_decision_result
    with pytest.raises(TypeError, match=r"decisions\[0\].*wrong exact type"):
        law._preflight_decision_result(
            _forged(parent, decisions=(object(),)),
            certificate=certificate,
        )
    with pytest.raises(TypeError, match="wrong exact CP36 preparation"):
        law._preflight_decision_result(
            _forged(parent, preparation_result=object()),
            certificate=certificate,
        )


def test_oversized_configuration_row_fails_before_parent_validation(live_bundle):
    owner = live_bundle["owner"]
    result = live_bundle["result"]
    row = result.configuration_masses[0]
    base_event = row.configuration[0]
    oversized_row = _forged(row, configuration=(base_event,) * 65)
    oversized_result = _forged(
        result,
        configuration_masses=(oversized_row,) + result.configuration_masses[1:],
    )
    original_validate = law._DEC_VALIDATE_RESULT
    calls = {"validate": 0}

    def forbidden_validate(*args, **kwargs):
        del args, kwargs
        calls["validate"] += 1
        raise AssertionError("malformed CP38 row reached CP37 validation")

    law._DEC_OWNER_TYPE.validate_result = forbidden_validate
    law._DEC_VALIDATE_RESULT = forbidden_validate
    object.__setattr__(owner, "_parent_validate_result", forbidden_validate)
    try:
        with pytest.raises(ValueError, match="tuple resource limit"):
            owner.validate_result(
                oversized_result,
                result.run_id,
                result.initialization_index,
            )
    finally:
        law._DEC_OWNER_TYPE.validate_result = original_validate
        law._DEC_VALIDATE_RESULT = original_validate
        object.__setattr__(owner, "_parent_validate_result", original_validate)
    assert calls == {"validate": 0}


def test_oversized_top_level_tuple_fails_before_parent_preflight(
    live_bundle, monkeypatch
):
    result = live_bundle["result"]
    oversized = _forged(
        result,
        attempt_masses=result.attempt_masses + (result.attempt_masses[0],),
    )
    calls = {"parent_preflight": 0}

    def forbidden_parent_preflight(*args, **kwargs):
        del args, kwargs
        calls["parent_preflight"] += 1
        raise AssertionError("oversized CP38 tuple reached parent preflight")

    monkeypatch.setattr(law, "_preflight_decision_result", forbidden_parent_preflight)
    with pytest.raises(ValueError, match="tuple resource limit"):
        law._preflight_result_record(
            oversized,
            certificate=live_bundle["owner"].certificate,
        )
    assert calls == {"parent_preflight": 0}


def test_validate_result_replays_without_parent_decide_prepare_or_rng(
    live_bundle,
):
    owner = live_bundle["owner"]
    result = live_bundle["result"]
    original_decide = law._DEC_DECIDE
    original_validate = law._DEC_VALIDATE_RESULT
    calls = {"decide": 0, "validate": 0}

    def forbidden_decide(*args, **kwargs):
        del args, kwargs
        calls["decide"] += 1
        raise AssertionError("validation must not call CP37 decide")

    def counted_validate(parent_owner, parent, run_id, initialization_index):
        calls["validate"] += 1
        return original_validate(parent_owner, parent, run_id, initialization_index)

    law._DEC_OWNER_TYPE.decide = forbidden_decide
    law._DEC_DECIDE = forbidden_decide
    law._DEC_OWNER_TYPE.validate_result = counted_validate
    law._DEC_VALIDATE_RESULT = counted_validate
    object.__setattr__(owner, "_parent_decide", forbidden_decide)
    object.__setattr__(owner, "_parent_validate_result", counted_validate)
    before = _rng_snapshot()
    try:
        checked = owner.validate_result(
            result, result.run_id, result.initialization_index
        )
    finally:
        law._DEC_OWNER_TYPE.decide = original_decide
        law._DEC_DECIDE = original_decide
        law._DEC_OWNER_TYPE.validate_result = original_validate
        law._DEC_VALIDATE_RESULT = original_validate
        object.__setattr__(owner, "_parent_decide", original_decide)
        object.__setattr__(owner, "_parent_validate_result", original_validate)
    _assert_rng_unchanged(before)
    assert checked is result
    assert calls == {"decide": 0, "validate": 1}


def test_matching_helpers_bind_exact_parent_hypothesis_policy_and_role(live_bundle):
    owner = live_bundle["owner"]
    parent = live_bundle["decision_owner"]
    hypothesis = live_bundle["word_hypothesis"]
    assert (
        _MATCHING(
            parent,
            hypothesis,
            owner,
            law_policy=LAW_POLICY,
            law_role_sha256=LAW_ROLE,
        )
        is owner
    )
    assert (
        _VALIDATE_CERTIFICATE(
            parent,
            hypothesis,
            owner,
            law_policy=LAW_POLICY,
            law_role_sha256=LAW_ROLE,
        )
        is owner.certificate
    )
    alien_hypothesis = _DECLARE(
        hypothesis_scope=law.FIXED_BATCH_IID_UINT64_DECISION_WORD_HYPOTHESIS_SCOPE,
        word_source_premise=law.FIXED_BATCH_IID_UINT64_DECISION_WORD_PREMISE,
    )
    with pytest.raises(ValueError, match="hypothesis"):
        _MATCHING(
            parent,
            alien_hypothesis,
            owner,
            law_policy=LAW_POLICY,
            law_role_sha256=LAW_ROLE,
        )
    with pytest.raises(ValueError, match="policy"):
        _MATCHING(
            parent,
            hypothesis,
            owner,
            law_policy=LAW_POLICY + "x",
            law_role_sha256=LAW_ROLE,
        )
    with pytest.raises(ValueError, match="role"):
        _MATCHING(
            parent,
            hypothesis,
            owner,
            law_policy=LAW_POLICY,
            law_role_sha256="d" * 64,
        )


@pytest.mark.parametrize("bad", (True, -1, 1 << 64, 1.0, "0", None))
def test_request_preflight_rejects_before_parent_decide(live_bundle, bad):
    owner = live_bundle["owner"]
    original = owner._parent_decide

    def forbidden(*args, **kwargs):
        del args, kwargs
        raise AssertionError("bad coordinates reached CP37")

    object.__setattr__(owner, "_parent_decide", forbidden)
    object.__setattr__(law, "_DEC_DECIDE", forbidden)
    law._DEC_OWNER_TYPE.decide = forbidden
    try:
        with pytest.raises((TypeError, ValueError)):
            owner.resolve(bad, 0)
    finally:
        object.__setattr__(owner, "_parent_decide", original)
        object.__setattr__(law, "_DEC_DECIDE", original)
        law._DEC_OWNER_TYPE.decide = original


def test_record_validators_reject_boolean_fraction_digest_and_mapping_tampering(
    live_bundle,
):
    certificate = live_bundle["owner"].certificate
    result = live_bundle["result"]
    attempt = result.attempt_masses[0]
    configuration = result.configuration_masses[0]

    certificate_values = _values(
        certificate,
        law._certificate_fields,
        law._certificate_payload,
        "certificate_sha256",
        passed=1,
    )
    with pytest.raises(TypeError, match="exact Boolean"):
        law._validate_certificate_values(certificate_values)

    attempt_values = _values(
        attempt,
        law._attempt_mass_fields,
        law._attempt_mass_payload,
        "mass_sha256",
        acceptance_probability_numerator=True,
    )
    with pytest.raises(TypeError, match="exact Python integer"):
        law._validate_attempt_mass_values(attempt_values)
    attempt_values = _values(
        attempt,
        law._attempt_mass_fields,
        law._attempt_mass_payload,
        "mass_sha256",
    )
    attempt_values["mass_sha256"] = "f" * 64
    with pytest.raises(ValueError, match="digest"):
        law._validate_attempt_mass_values(attempt_values)

    configuration_values = _values(
        configuration,
        law._configuration_mass_fields,
        law._configuration_mass_payload,
        "mass_sha256",
        attempt_indices=(0, 0),
    )
    with pytest.raises(ValueError, match="increase uniquely"):
        law._validate_configuration_mass_values(configuration_values)

    result_values = _values(
        result,
        law._result_fields,
        law._result_payload,
        "result_sha256",
        attempt_to_configuration_ordinal=(0,) * result.attempt_budget,
    )
    with pytest.raises(ValueError, match="surjective|mapping differs"):
        law._validate_result_values(result_values)


def test_result_request_binding_and_tree_tampering_fail_closed(live_bundle):
    owner = live_bundle["owner"]
    result = live_bundle["result"]
    with pytest.raises(ValueError, match="request coordinates"):
        owner.validate_result(result, result.run_id + 1, result.initialization_index)
    with pytest.raises(ValueError, match="result digest|replay digest|differs"):
        owner.validate_result(
            _forged(result, result_sha256="f" * 64),
            result.run_id,
            result.initialization_index,
        )
    with pytest.raises(ValueError, match="digest"):
        owner.validate_result(
            _forged(
                result,
                attempt_mass_sha256s=("f" * 64,) + result.attempt_mass_sha256s[1:],
            ),
            result.run_id,
            result.initialization_index,
        )


def test_resource_type_and_configuration_preflights_are_bounded(live_bundle):
    certificate = live_bundle["owner"].certificate
    result = live_bundle["result"]
    with pytest.raises(ValueError, match="text resource"):
        law._require_text("x" * 16_385, "", name="oversized")
    with pytest.raises(ValueError, match="tuple resource"):
        law._exact_tuple((None,) * 4, name="oversized", maximum=3)
    with pytest.raises(ValueError, match="integer-bit resource"):
        law._signed_integer(1 << 131_072, name="oversized")
    with pytest.raises(TypeError, match="wrong exact CP37"):
        law._preflight_decision_result(object(), certificate=certificate)
    bad_configuration = (
        _forged(
            result.parent_decision_result.thresholds[
                0
            ].preparation_attempt.canonical_configuration[0],
            coordinates=(float("nan"),),
        ),
    )
    with pytest.raises(ValueError, match="finite binary64"):
        law._configuration_key(bad_configuration, name="bad")


def test_owner_identity_callback_surface_and_snapshot_custody_are_sealed(
    live_bundle, monkeypatch
):
    owner = live_bundle["owner"]
    with pytest.raises(ValueError, match="seal"):
        _forge_owner(owner, _sealed=False)._owner_snapshot()
    with pytest.raises(ValueError, match="cached callback"):
        _forge_owner(owner, _law_builder=lambda *args: None)._owner_snapshot()
    distinct_equal_role = LAW_ROLE.encode("ascii").decode("ascii")
    assert distinct_equal_role == LAW_ROLE and distinct_equal_role is not LAW_ROLE
    with pytest.raises(ValueError, match="identity"):
        _forge_owner(owner, _law_role_sha256=distinct_equal_role)._owner_snapshot()
    snapshot = owner._owner_snapshot()
    with pytest.raises(
        law.PluginBridgeCounterKeyedInitialTiltRejectionFiniteBatchLawError,
        match="changed during operation",
    ):
        owner._require_owner_snapshot(snapshot[:-1] + (object(),))
    monkeypatch.setattr(law._DEC_OWNER_TYPE, "decide", lambda *args: None)
    with pytest.raises(ValueError, match="dependency surface"):
        owner._live_certificate(snapshot)


@pytest.mark.parametrize(
    "surface",
    ("hypothesis", "certificate", "attempt", "configuration", "result", "owner"),
)
def test_records_and_owner_are_immutable_nonpickle_and_nonsubclassable(
    live_bundle, surface
):
    result = live_bundle["result"]
    values = {
        "hypothesis": live_bundle["word_hypothesis"],
        "certificate": live_bundle["owner"].certificate,
        "attempt": result.attempt_masses[0],
        "configuration": result.configuration_masses[0],
        "result": result,
        "owner": live_bundle["owner"],
    }
    value = values[surface]
    with pytest.raises((AttributeError, TypeError)):
        value.passed = False
    with pytest.raises(TypeError, match="pickle"):
        pickle.dumps(value)
    with pytest.raises(TypeError):
        type("ForbiddenSubclass", (type(value),), {})


def test_public_record_constructors_are_token_sealed():
    for cls in (
        law.FixedBatchIidUint64DecisionWordHypothesis,
        law.CounterKeyedInitialTiltRejectionFiniteBatchLawCertificate,
        law.CounterKeyedInitialTiltRejectionAttemptMass,
        law.CounterKeyedInitialTiltRejectionConfigurationMass,
        law.CounterKeyedInitialTiltRejectionFiniteBatchLawResult,
    ):
        with pytest.raises(TypeError, match="module-created"):
            cls(_construction_token=object())


def test_source_ast_has_one_parent_decide_and_no_rng_lineage_or_tag3_dependencies():
    source_path = Path(law.__file__)
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported_roots = set()
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                calls.append(node.func.attr)
            elif isinstance(node.func, ast.Name):
                calls.append(node.func.id)
    assert {"random", "numpy", "torch"}.isdisjoint(imported_roots)
    assert not any(
        name
        in {"random", "rand", "randint", "randrange", "uniform", "seed", "manual_seed"}
        for name in calls
    )
    assert not any(
        "lineage" in name.lower() or "tag3" in name.lower() for name in imported_roots
    )
    owner_class = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "CounterKeyedInitialTiltRejectionFiniteBatchLawOwner"
    )
    resolve = next(
        node
        for node in owner_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "resolve"
    )
    parent_decides = [
        node
        for node in ast.walk(resolve)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "_parent_decide"
    ]
    assert len(parent_decides) == 1
    assert not any(
        isinstance(parent, (ast.For, ast.While))
        and any(call in set(ast.walk(parent)) for call in parent_decides)
        for parent in ast.walk(resolve)
    )


def test_module_is_not_reexported_from_dependency_light_process_package():
    import heterodiff.processes as processes

    assert not hasattr(
        processes,
        "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_finite_batch_law",
    )


def test_optional_torch_boundary_translates_dependency_failure():
    source = textwrap.dedent(
        """
        import builtins
        original_import = builtins.__import__
        def guarded_import(name, *args, **kwargs):
            if name == 'torch' or name.startswith('torch.'):
                raise ModuleNotFoundError("No module named 'torch'", name='torch')
            return original_import(name, *args, **kwargs)
        builtins.__import__ = guarded_import
        try:
            __import__(
                "heterodiff.processes.plugin_bridge_counter_keyed_initial_tilt_"
                "rejection_finite_batch_law"
            )
        except ModuleNotFoundError as error:
            assert "optional PyTorch reference dependency" in str(error)
            assert error.name is None
        else:
            raise AssertionError("missing optional dependency was not translated")
        """
    )
    completed = subprocess.run(
        [sys.executable, "-c", source],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
