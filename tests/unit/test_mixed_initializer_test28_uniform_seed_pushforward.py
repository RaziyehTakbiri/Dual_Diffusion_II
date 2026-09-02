"""Independent hostile tests for the CP60 whole-seed pushforward precursor."""

from __future__ import annotations

import ast
from collections import Counter
from dataclasses import FrozenInstanceError, fields, make_dataclass
from fractions import Fraction
import hashlib
import inspect
from itertools import product
from pathlib import Path
import pickle
import subprocess
import sys

import pytest

from heterodiff.evaluation import (
    mixed_initializer_test28_uniform_seed_pushforward as pushforward,
)


_D64 = 1 << 64
_ZERO_SHA256 = "0" * 64
_FIXTURES = ("T28-M1-Q", "T28-M2-Q")
_REJECTION_BUDGETS = (1, 4, 16, 64)
_SIR_BUDGETS = (8, 32, 128, 512)
_OUTCOMES = (
    "returned-rejection-selected",
    "returned-rejection-exhausted",
    "returned-sir-selected",
    "preexecution-refusal",
    "execution-failure",
    "nonreturn",
)


class _IntSubclass(int):
    pass


class _StrSubclass(str):
    pass


class _ProtocolBomb:
    def __len__(self):
        raise AssertionError("hostile __len__ was invoked")

    def __iter__(self):
        raise AssertionError("hostile __iter__ was invoked")

    def __eq__(self, other):
        del other
        raise AssertionError("hostile __eq__ was invoked")


def _sha(label: str) -> str:
    return hashlib.sha256(label.encode("ascii")).hexdigest()


def _uniform(domain):
    return dict.fromkeys(domain, Fraction(1, len(domain)))


def _push(law, mapping):
    result = {}
    for source, probability in law.items():
        image = mapping[source]
        result[image] = result.get(image, Fraction(0)) + probability
    return result


def _total_variation(left, right, domain):
    return (
        sum(
            (
                abs(left.get(value, Fraction(0)) - right.get(value, Fraction(0)))
                for value in domain
            ),
            Fraction(0),
        )
        / 2
    )


def _fiber_counts(mapping):
    return Counter(mapping.values())


def _forge(instance, **changes):
    field_names = {item.name for item in fields(type(instance))}
    unknown = set(changes).difference(field_names)
    assert not unknown, "hostile forge names nonexistent fields: " + repr(unknown)
    forged = object.__new__(type(instance))
    for item in fields(type(instance)):
        object.__setattr__(
            forged,
            item.name,
            changes.get(item.name, getattr(instance, item.name)),
        )
    return forged


def _redigest(instance, domain: str, **changes):
    forged = _forge(instance, **changes, record_sha256=_ZERO_SHA256)
    values = {item.name: getattr(forged, item.name) for item in fields(type(forged))}
    return _forge(forged, record_sha256=pushforward._digest(domain, values))


@pytest.fixture
def assumption():
    return pushforward.declare_cp60_uniform_plan_seed_assumption(
        request_template_sha256=_sha("cp60 hostile request"),
        assumption_role_sha256=_sha("cp60 hostile assumption role"),
        one_exact_uint64_seed_almost_surely_supplied_assumed=True,
        unconditional_uniform_plan_seed_assumed=True,
    )


@pytest.fixture
def alphabet():
    return pushforward.cp60_whole_seed_outcome_alphabet()


@pytest.fixture
def definition():
    request = pushforward._request_template_sha256("T28-M1-Q", "bounded-rejection", 4)
    bound_assumption = pushforward.declare_cp60_uniform_plan_seed_assumption(
        request_template_sha256=request,
        assumption_role_sha256=pushforward._assumption_role_sha256(request),
        one_exact_uint64_seed_almost_surely_supplied_assumed=True,
        unconditional_uniform_plan_seed_assumed=True,
    )
    return pushforward.define_cp60_whole_seed_pushforward(
        fixture_id="T28-M1-Q",
        strategy="bounded-rejection",
        budget=4,
        request_template_sha256=request,
        seed_assumption=bound_assumption,
        kernel_v2_source_sha256=pushforward.CP60_TEST28_KERNEL_V2_SOURCE_SHA256,
        reference_source_sha256=pushforward.CP60_TEST28_REFERENCE_SOURCE_SHA256,
        provider_source_sha256=pushforward.CP60_TEST28_PROVIDER_SOURCE_SHA256,
        exact_score_source_sha256=(pushforward.CP60_TEST28_EXACT_SCORE_SOURCE_SHA256),
        quota_source_sha256=pushforward.CP60_TEST28_QUOTA_SOURCE_SHA256,
        dependency_lock_sha256=_sha("cp60 hostile dependency lock"),
        runtime_record_sha256=_sha("cp60 hostile runtime record"),
    )


@pytest.fixture
def bundle():
    return pushforward.cp60_whole_seed_pushforward_bundle()


def test_whole_seed_fiber_count_law_and_six_way_partition_are_exact() -> None:
    seeds = tuple(range(16))
    mapping = {
        0: ("returned-rejection-selected", "a", 0),
        1: ("returned-rejection-selected", "a", 0),
        2: ("returned-rejection-selected", "b", 1),
        3: ("returned-rejection-exhausted", None, None),
        4: ("returned-sir-selected", "a", None),
        5: ("returned-sir-selected", "b", None),
        6: ("preexecution-refusal", "bad-request", None),
        7: ("preexecution-refusal", "bad-request", None),
        8: ("execution-failure", "proposal", None),
        9: ("execution-failure", "score", None),
        10: ("execution-failure", "normalization", None),
        11: ("nonreturn", "diverged", None),
        12: ("returned-rejection-exhausted", None, None),
        13: ("returned-rejection-selected", "b", 1),
        14: ("returned-sir-selected", "b", None),
        15: ("execution-failure", "quota", None),
    }
    counts = _fiber_counts(mapping)
    law = {outcome: Fraction(count, len(seeds)) for outcome, count in counts.items()}
    assert sum(law.values(), Fraction(0)) == 1

    status_counts = Counter(outcome[0] for outcome in mapping.values())
    assert set(status_counts) == set(_OUTCOMES)
    assert sum(Fraction(status_counts[name], len(seeds)) for name in _OUTCOMES) == 1
    assert law[("returned-rejection-selected", "a", 0)] == Fraction(1, 8)
    assert law[("returned-rejection-selected", "b", 1)] == Fraction(1, 8)
    assert law[("nonreturn", "diverged", None)] == Fraction(1, 16)


def test_valid_empty_configuration_is_not_refusal_exhaustion_or_nonreturn() -> None:
    selected_empty = ("returned-rejection-selected", (), 0)
    outcomes = (
        selected_empty,
        ("returned-rejection-exhausted", None, None),
        ("preexecution-refusal", "reason", None),
        ("execution-failure", "reason", None),
        ("nonreturn", "reason", None),
    )
    assert len(set(outcomes)) == len(outcomes)
    assert selected_empty[1] == ()


def test_first_accept_and_selected_conditioning_are_fiber_ratios_only() -> None:
    seeds = tuple(range(8))
    mapping = {
        0: ("selected", 0, "a"),
        1: ("selected", 0, "b"),
        2: ("selected", 1, "a"),
        3: ("selected", 2, "a"),
        4: ("exhausted", None, None),
        5: ("refusal", None, None),
        6: ("failure", None, None),
        7: ("nonreturn", None, None),
    }
    counts = _fiber_counts(mapping)
    assert Fraction(sum(value[0] == "selected" for value in mapping.values()), 8) == (
        Fraction(1, 2)
    )
    for attempt, expected in (
        (0, Fraction(1, 4)),
        (1, Fraction(1, 8)),
        (2, Fraction(1, 8)),
    ):
        fiber = sum(
            value[0] == "selected" and value[1] == attempt for value in mapping.values()
        )
        assert Fraction(fiber, len(seeds)) == expected
    selected_count = sum(value[0] == "selected" for value in mapping.values())
    selected_a = sum(
        value[0] == "selected" and value[2] == "a" for value in mapping.values()
    )
    assert Fraction(selected_a, selected_count) == Fraction(3, 4)
    assert counts[("exhausted", None, None)] == 1

    no_selection = dict.fromkeys(seeds, ("exhausted", None, None))
    denominator = sum(value[0] == "selected" for value in no_selection.values())
    assert denominator == 0
    with pytest.raises(ZeroDivisionError):
        Fraction(0, denominator)


def test_fixed_seed_replay_does_not_identify_the_uniform_seed_law() -> None:
    seeds = tuple(range(4))
    mapping = {0: "a", 1: "a", 2: "b", 3: "failure"}
    uniform_pushforward = _push(_uniform(seeds), mapping)
    assert uniform_pushforward == {
        "a": Fraction(1, 2),
        "b": Fraction(1, 4),
        "failure": Fraction(1, 4),
    }
    for seed in seeds:
        replay_law = {mapping[seed]: Fraction(1)}
        assert replay_law != uniform_pushforward

    constant_mapping = dict.fromkeys(seeds, "same")
    constant_pushforward = _push(_uniform(seeds), constant_mapping)
    assert constant_pushforward == {"same": Fraction(1)}
    for seed in seeds:
        assert {constant_mapping[seed]: Fraction(1)} == constant_pushforward


def test_uniform_root_cannot_supply_product_uniform_full_width_roles() -> None:
    roots = tuple(range(4))
    pair_domain = tuple(product(roots, repeat=2))
    product_uniform = _uniform(pair_domain)
    role_pair = {root: (root, root) for root in roots}
    pushed = _push(_uniform(roots), role_pair)
    assert _total_variation(pushed, product_uniform, pair_domain) == Fraction(3, 4)
    for coordinate in (0, 1):
        marginal = {
            value: sum(
                probability
                for pair, probability in pushed.items()
                if pair[coordinate] == value
            )
            for value in roots
        }
        assert marginal == _uniform(roots)


def test_per_role_uniform_marginals_do_not_give_rejection_product_formula() -> None:
    # V and W are each uniform bits but are the same root bit.  With quotas
    # K(0)=1 and K(1)=2 on the two-point decision domain, independence would
    # give acceptance 3/4; the correlated whole-seed law gives acceptance 1.
    joint = {(0, 0): Fraction(1, 2), (1, 1): Fraction(1, 2)}
    quotas = {0: 1, 1: 2}
    actual = sum(
        probability
        for (proposal, decision), probability in joint.items()
        if decision < quotas[proposal]
    )
    independent = sum(
        Fraction(1, 2) * Fraction(quotas[proposal], 2) for proposal in (0, 1)
    )
    assert actual == 1
    assert independent == Fraction(3, 4)


def test_per_attempt_uniformity_does_not_give_iid_first_acceptance() -> None:
    # Reusing one bit makes both decision marginals uniform.  Under the actual
    # joint law first acceptance is (1/2, 0) and exhaustion is 1/2, not the
    # independent values (1/2, 1/4, 1/4).
    roots = (0, 1)
    decisions = {root: (root, root) for root in roots}
    first = Counter()
    for root in roots:
        accepted = tuple(word == 0 for word in decisions[root])
        if any(accepted):
            first[accepted.index(True)] += 1
        else:
            first["exhausted"] += 1
    assert {key: Fraction(value, 2) for key, value in first.items()} == {
        0: Fraction(1, 2),
        "exhausted": Fraction(1, 2),
    }
    assert Fraction(first.get(1, 0), 2) != Fraction(1, 4)


def test_request_specific_maps_need_not_share_a_common_proposal_law() -> None:
    seeds = tuple(range(4))
    first_request = {seed: seed % 2 for seed in seeds}
    second_request = dict.fromkeys(seeds, 0)
    first_law = _push(_uniform(seeds), first_request)
    second_law = _push(_uniform(seeds), second_request)
    assert first_law == {0: Fraction(1, 2), 1: Fraction(1, 2)}
    assert second_law == {0: Fraction(1)}
    assert first_law != second_law


def test_totalized_failure_and_nonreturn_must_not_be_dropped_by_conditioning() -> None:
    source = tuple(range(4))
    total_map = {
        0: ("returned", "a"),
        1: ("returned", "a"),
        2: ("execution-failure", None),
        3: ("nonreturn", None),
    }
    full_law = _push(_uniform(source), total_map)
    assert sum(full_law.values(), Fraction(0)) == 1
    assert full_law[("execution-failure", None)] == Fraction(1, 4)
    assert full_law[("nonreturn", None)] == Fraction(1, 4)

    returned_mass = sum(
        probability
        for outcome, probability in full_law.items()
        if outcome[0] == "returned"
    )
    assert returned_mass == Fraction(1, 2)
    assert returned_mass != 1


def test_unobserved_fibers_are_unknown_not_zero() -> None:
    # Two maps agree on the inspected seeds and disagree elsewhere.  A finite
    # replay therefore cannot certify that a refusal or nonreturn fiber is
    # empty over the full seed domain.
    inspected = (0, 1, 2)
    map_a = {0: "selected", 1: "selected", 2: "selected", 3: "selected"}
    map_b = {0: "selected", 1: "selected", 2: "selected", 3: "nonreturn"}
    assert tuple(map_a[seed] for seed in inspected) == tuple(
        map_b[seed] for seed in inspected
    )
    assert _fiber_counts(map_a).get("nonreturn", 0) == 0
    assert _fiber_counts(map_b)["nonreturn"] == 1


def test_source_tv_obstruction_has_no_output_tv_lower_bound_converse() -> None:
    roots = tuple(range(4))
    pairs = tuple(product(roots, repeat=2))
    correlated = _push(_uniform(roots), {root: (root, root) for root in roots})
    product_uniform = _uniform(pairs)
    assert _total_variation(correlated, product_uniform, pairs) == Fraction(3, 4)
    constant = dict.fromkeys(pairs, "same")
    assert _push(correlated, constant) == _push(product_uniform, constant)


def test_current_numpy_standard_normal_consumes_a_variable_number_of_words() -> None:
    # This is a narrow regression witness for why a NumPy version string and a
    # one-word-per-normal story cannot complete the runtime map.  It is not a
    # distributional test or an attestation of NumPy's source law.
    import numpy as np

    generator = np.random.Generator(np.random.Philox(0))

    def consumed_words() -> int:
        state = generator.bit_generator.state
        counter = tuple(int(value) for value in state["state"]["counter"])
        assert counter[1:] == (0, 0, 0)
        buffer_position = int(state["buffer_pos"])
        return 0 if counter[0] == 0 else 4 * (counter[0] - 1) + buffer_position

    previous = consumed_words()
    for _ in range(205):
        generator.standard_normal()
        current = consumed_words()
        assert current - previous == 1
        previous = current
    generator.standard_normal()
    assert consumed_words() - previous == 3
    assert consumed_words() == 208


def test_uniform_seed_assumption_is_exact_and_never_self_attesting(
    assumption,
) -> None:
    assert (
        pushforward.validate_cp60_uniform_plan_seed_assumption(assumption) is assumption
    )
    assert assumption.seed_bits == 64
    assert assumption.seed_domain_minimum == 0
    assert assumption.seed_domain_maximum == _D64 - 1
    assert assumption.seed_domain_size == _D64
    assert assumption.uniform_seed_singleton_mass == Fraction(1, _D64)
    for name in (
        "one_exact_uint64_seed_almost_surely_supplied_assumed",
        "unconditional_uniform_plan_seed_assumed",
        "pointwise_one_future_fully_fixed_request_only",
        "assumption_only",
    ):
        assert getattr(assumption, name) is True
    for name in (
        "current_fixed_hash_seed_plan_matches",
        "operational_seed_source_verified",
        "backend_totality_verified",
        "seed_sequence_iid_assumed",
        "cross_request_iid_assumed",
        "derived_philox_word_uniformity_assumed",
        "derived_philox_product_law_assumed",
        "role_stream_independence_assumed",
        "proposal_iid_assumed",
        "os_entropy_law_verified",
        "physical_entropy_or_cryptographic_quality_verified",
    ):
        assert getattr(assumption, name) is False


@pytest.mark.parametrize(
    ("field", "value", "error"),
    (
        ("request_template_sha256", _StrSubclass("0" * 64), TypeError),
        ("assumption_role_sha256", _StrSubclass("0" * 64), TypeError),
        (
            "one_exact_uint64_seed_almost_surely_supplied_assumed",
            1,
            TypeError,
        ),
        ("unconditional_uniform_plan_seed_assumed", 1, TypeError),
        ("one_exact_uint64_seed_almost_surely_supplied_assumed", False, ValueError),
        ("unconditional_uniform_plan_seed_assumed", False, ValueError),
    ),
)
def test_uniform_seed_declaration_rejects_hostile_or_false_premises(
    field, value, error
) -> None:
    arguments = {
        "request_template_sha256": _sha("cp60 hostile request"),
        "assumption_role_sha256": _sha("cp60 hostile role"),
        "one_exact_uint64_seed_almost_surely_supplied_assumed": True,
        "unconditional_uniform_plan_seed_assumed": True,
    }
    arguments[field] = value
    with pytest.raises(error):
        pushforward.declare_cp60_uniform_plan_seed_assumption(**arguments)


def test_outcome_alphabet_is_exact_disjoint_and_total_only_mathematically(
    alphabet,
) -> None:
    assert pushforward.validate_cp60_whole_seed_outcome_alphabet(alphabet) is alphabet
    assert alphabet.statuses == _OUTCOMES
    assert len(alphabet.statuses) == len(set(alphabet.statuses)) == 6
    assert alphabet.preexecution_refusal_classes
    assert alphabet.execution_failure_classes
    assert alphabet.returned_trace_retains_configuration_values_not_digest_only
    assert alphabet.selected_empty_configuration_distinct_from_nonreturn
    assert alphabet.outcome_tags_pairwise_disjoint
    assert alphabet.outcome_tags_mathematically_exhaustive
    assert alphabet.nonreturn_is_explicit
    assert alphabet.failure_versus_nonreturn_mechanically_observable is False
    assert alphabet.python_exception_catching_proves_nonreturn_mass_zero is False
    assert "configuration-values-not-digest-only" in alphabet.rejection_trace_payload
    assert "selected-empty-configuration" in alphabet.rejection_trace_payload


def test_definition_binds_only_symbolic_correlated_whole_request_law(
    definition,
) -> None:
    assert pushforward.validate_cp60_whole_seed_pushforward(definition) is definition
    assert definition.fixture_id == "T28-M1-Q"
    assert definition.strategy == "bounded-rejection"
    assert definition.budget == 4
    assert definition.seed_assumption_sha256 == definition.seed_assumption.record_sha256
    assert definition.outcome_alphabet.statuses == _OUTCOMES
    assert (
        definition.symbolic_pushforward_formula_defined_for_future_fixed_request_under_assumption
    )
    assert definition.mathematical_totalization_formula_defined_for_future_fixed_request
    assert definition.correlated_whole_request_model_required
    assert definition.joint_realized_proposal_trace_sublaw_symbolically_defined
    assert definition.slotwise_proposal_marginals_symbolically_defined
    assert definition.fixed_seed_point_mass_theorem_recorded
    assert definition.future_validated_mc_requirements_recorded
    assert definition.source_file_digests_are_unverified_custody_labels
    assert definition.optional_runtime_digests_are_unverified_custody_labels
    assert definition.dependency_lock_sha256 == _sha("cp60 hostile dependency lock")
    assert definition.runtime_record_sha256 == _sha("cp60 hostile runtime record")

    for name in (
        "request_parameters_fully_bound",
        "fixed_request_map_instantiated",
        "fixed_seed_replay_establishes_or_samples_uniform_seed_law",
        "runtime_dependency_map_complete",
        "compiled_dependency_abi_libm_map_complete",
        "current_kernel_runtime_sha256_sufficient",
        "runtime_map_executed",
        "seed_domain_exhaustively_enumerated",
        "numeric_fiber_counts_computed",
        "nonreturn_mass_proved_zero",
        "common_mu_fp_identified",
        "proposal_iid_verified",
        "cross_request_iid_verified",
        "derived_word_uniformity_verified",
        "role_stream_independence_verified",
        "alpha64_product_formula_permitted",
        "rho64_product_formula_permitted",
        "operational_alpha64_derived",
        "operational_rho64_derived",
        "operational_refusal_probability_derived",
        "operational_exhaustion_probability_derived",
        "unconditional_finite_j_sir_law_derived",
        "future_mc_seed_source_verified",
        "future_mc_map_and_runtime_fully_fixed",
        "future_mc_failures_and_nonreturn_retained",
        "future_mc_no_retry_drop_or_seed_selection_verified",
        "future_mc_uncertainty_method_prespecified",
        "future_mc_multiplicity_method_prespecified",
        "future_mc_positive_selected_count_rule_prespecified",
        "future_mc_nonreturn_observability_mechanism_fixed",
        "validated_mc_executed",
        "validated_mc_sample_recorded",
        "validated_mc_intervals_computed",
        "current_deterministic_seed_plan_is_validated_mc",
        "operational_prediction",
        "production_observed",
        "confirmatory_evidence",
        "manuscript_claim_promoted",
        "formal_test_28_closed",
    ):
        assert getattr(definition, name) is False
    assert definition.formal_test_28_status == "OPEN"
    assert "no-common-alpha" in definition.rejection_fiber_formula
    assert "no-product-mu-fp" in definition.sir_fiber_formula


def test_symbolic_formula_and_future_validation_text_is_exact(definition) -> None:
    expected_text = {
        "total_map_definition": (
            "for-fixed-seed-free-request-R-and-fixed-runtime-E;K_R,E(s)-is-current-"
            "kernel-v2-after-inserting-exact-uint64-plan-seed-s;F_R,E(s)-is-the-"
            "corresponding-complete-validated-returned-trace-or-preexecution-refusal-or-"
            "execution-failure-or-nonreturn;these-disjoint-tags-mathematically-totalize-"
            "every-s-in-[0,2^64);failure-versus-nonreturn-need-not-be-mechanically-"
            "observable-by-a-returned-Python-record"
        ),
        "fiber_count_formula": (
            "N_E=cardinality({s-in-[0,2^64):F_R,E(s)-in-E});"
            "P(F_R,E(S)-in-E)=N_E/2^64-for-assumed-S-uniform-on-[0,2^64)"
        ),
        "singleton_formula": (
            "N_y=cardinality({s-in-[0,2^64):F_R,E(s)=y});" "P(F_R,E(S)=y)=N_y/2^64"
        ),
        "normalization_formula": (
            "the-disjoint-complete-outcome-fibers-partition-[0,2^64);"
            "sum_y-N_y=2^64-and-sum_y-N_y/2^64=1"
        ),
        "rejection_fiber_formula": (
            "for-one-based-t-in-{1,...,A};N_first,t-counts-returned-selected-traces-"
            "with-zero-based-selected-index=t-1;P(first=t)=N_first,t/2^64;"
            "P(exhausted)=N_exhausted/2^64;P(preexecution-refusal)=N_refusal/2^64;"
            "P(selected-value=c)=N_select,c/"
            "2^64;P(selected-value=c|selected)=N_select,c/N_selected-only-if-"
            "N_selected>0;N_accept,t-counts-complete-validated-returned-rejection-"
            "traces-with-recorded-slot-t-accepted;P(slot-t-accepted-and-complete-"
            "validated-return)=N_accept,t/2^64;this-is-an-unconditional-subprobability-"
            "and-execution-failure-or-nonreturn-is-not-conditioned-away;no-common-"
            "alpha-or-(1-alpha)^A-formula-follows"
        ),
        "sir_fiber_formula": (
            "P(finite-J-selected-value=c)=N_sir-select,c/2^64;arbitrary-cloud-weight-"
            "cell-and-selection-events-are-counted-by-the-same-whole-trace-fiber-"
            "formula;no-product-mu-fp^J-integral-follows"
        ),
        "proposal_marginal_formula": (
            "on-each-explicitly-defined-reached-and-recorded-proposal-slot-t;the-"
            "slotwise-sublaw-is-the-corresponding-trace-projection-of-the-uniform-seed-"
            "pushforward;the-joint-realized-proposal-trace-sublaw-is-a-single-whole-"
            "seed-pushforward;neither-object-identifies-one-common-mu-fp-or-an-iid-"
            "product-law"
        ),
        "no_returned_output_formula": (
            "P(no-validated-returned-output)=(N_preexecution_refusal+"
            "N_execution_failure+N_nonreturn)/2^64;these-three-fibers-are-distinct-"
            "and-N_refusal-never-denotes-their-aggregate"
        ),
        "fixed_seed_point_mass_theorem": (
            "for-any-future-fully-fixed-R,E-and-one-fixed-s0-in-[0,2^64);"
            "Law(F_R,E(s0))=delta_{F_R,E(s0)};one-fixed-seed-replay-does-not-by-"
            "itself-establish-or-sample-the-uniform-seed-pushforward;the-two-laws-"
            "coincide-only-if-the-uniform-seed-pushforward-is-that-same-point-mass"
        ),
    }
    for field, expected in expected_text.items():
        assert getattr(definition, field) == expected
        assert getattr(pushforward, "CP60_TEST28_" + field.upper()) == expected

    expected_mc_requirements = (
        "fully-bound-request-and-totalized-runtime-map-before-sampling",
        "independently-verified-iid-uniform-uint64-plan-seeds-with-replacement",
        "or-separately-frozen-without-replacement-hypergeometric-design",
        "retain-every-refusal-execution-failure-and-nonreturn-outcome",
        (
            "before-sampling-proved-termination-classifier-or-frozen-bounded-external-"
            "supervisor-with-timeout-censoring-retained-distinct-from-and-never-"
            "identified-with-semantic-nonreturn"
        ),
        "no-retry-drop-replacement-or-data-dependent-seed-selection",
        "prespecified-exact-binomial-multinomial-or-finite-population-uncertainty",
        "prespecified-familywise-multiplicity-control",
        "selected-law-claims-require-prespecified-positive-selected-count-rule",
        "seed-source-map-runtime-sample-and-interval-custody",
    )
    assert definition.future_validated_mc_requirements == expected_mc_requirements
    assert pushforward.CP60_TEST28_FUTURE_VALIDATED_MC_REQUIREMENTS == (
        expected_mc_requirements
    )


def test_runtime_binding_requirements_name_the_missing_variable_consumption_map(
    definition,
) -> None:
    requirements = definition.runtime_binding_requirements
    assert requirements == pushforward.CP60_TEST28_RUNTIME_BINDING_REQUIREMENTS
    assert len(requirements) == len(set(requirements))
    assert any("standard-normal-ziggurat" in value for value in requirements)
    assert any("variable-consumption" in value for value in requirements)
    assert any("compiled-abi" in value for value in requirements)
    assert any("libm" in value for value in requirements)
    assert definition.runtime_dependency_map_complete is False
    assert definition.compiled_dependency_abi_libm_map_complete is False


def test_frozen_source_custody_hashes_match_current_files(definition) -> None:
    source_root = Path(__file__).resolve().parents[2] / "src"
    paths = {
        "kernel_v2_source_sha256": source_root
        / "heterodiff/processes/plugin_bridge_mixed_support_initial_tilt_initializer_kernel_v2.py",
        "reference_source_sha256": source_root
        / "heterodiff/theory/configuration_reference.py",
        "provider_source_sha256": source_root
        / "heterodiff/processes/certified_initial_score_provider_v1.py",
        "exact_score_source_sha256": source_root
        / "heterodiff/evaluation/exact_rational_quadratic_initial_tilt.py",
        "quota_source_sha256": source_root
        / "heterodiff/processes/arbitrary_rational_uint64_exp_quota.py",
        "cp59_source_sha256": source_root
        / "heterodiff/evaluation/mixed_initializer_test28_runtime_conditional_predictions.py",
        "cp49_precedent_source_sha256": source_root
        / "heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_admission.py",
    }
    for field, path in paths.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == getattr(
            definition, field
        )
    assert definition.cp59_conditional_arithmetic_precursor_only
    assert definition.cp49_assumption_gate_semantic_precedent_only
    assert definition.cp49_artifact_ancestry_claimed is False


def test_optional_runtime_labels_never_promote_runtime_completeness(
    definition,
) -> None:
    assert definition.dependency_lock_sha256 is not None
    assert definition.runtime_record_sha256 is not None
    assert definition.optional_runtime_digests_are_unverified_custody_labels
    assert definition.runtime_dependency_map_complete is False
    assert definition.runtime_map_executed is False
    assert definition.operational_prediction is False


def test_bundle_contains_exact_sixteen_template_grid_in_frozen_order(bundle) -> None:
    assert pushforward.validate_cp60_whole_seed_pushforward_bundle(bundle) is bundle
    assert bundle.fixture_ids == _FIXTURES
    assert bundle.rejection_budget_grid == _REJECTION_BUDGETS
    assert bundle.sir_budget_grid == _SIR_BUDGETS
    assert len(bundle.rejection_definitions) == 8
    assert len(bundle.sir_definitions) == 8
    assert tuple(
        (child.fixture_id, child.strategy, child.budget)
        for child in bundle.rejection_definitions
    ) == tuple(
        (fixture, "bounded-rejection", budget)
        for fixture in _FIXTURES
        for budget in _REJECTION_BUDGETS
    )
    assert tuple(
        (child.fixture_id, child.strategy, child.budget)
        for child in bundle.sir_definitions
    ) == tuple(
        (fixture, "fixed-budget-sir", budget)
        for fixture in _FIXTURES
        for budget in _SIR_BUDGETS
    )
    assert bundle.all_grid_templates_predeclared
    assert bundle.definition_only
    assert bundle.future_validated_mc_requirements_recorded
    for name in (
        "kernel_numpy_scipy_provider_or_rng_imported_or_executed",
        "runtime_dependency_map_complete",
        "seed_domain_exhaustively_enumerated",
        "numeric_fiber_counts_computed",
        "request_parameters_fully_bound",
        "fixed_request_maps_instantiated",
        "validated_mc_executed",
        "common_mu_fp_identified",
        "operational_prediction",
        "unconditional_operational_predictions_blocker_closed",
        "production_observed",
        "confirmatory_evidence",
        "manuscript_claim_promoted",
        "formal_test_28_closed",
    ):
        assert getattr(bundle, name) is False
    assert bundle.formal_test_28_status == "OPEN"


def test_no_template_contains_a_numeric_fiber_count_or_probability(bundle) -> None:
    absent_fields = (
        "outcome_status_fiber_counts",
        "rejection_first_acceptance_fiber_counts",
        "rejection_selected_value_fiber_counts",
        "sir_selected_value_fiber_counts",
        "refusal_fiber_count",
        "exhaustion_fiber_count",
        "execution_failure_fiber_count",
        "nonreturn_fiber_count",
    )
    for definition in bundle.rejection_definitions + bundle.sir_definitions:
        assert all(getattr(definition, name) is None for name in absent_fields)
        assert definition.numeric_fiber_counts_computed is False
        assert definition.seed_domain_exhaustively_enumerated is False
        assert definition.execution_totality_proved is False


@pytest.mark.parametrize(
    ("field", "value", "error"),
    (
        ("fixture_id", "invented", ValueError),
        ("fixture_id", _StrSubclass("T28-M1-Q"), TypeError),
        ("strategy", "finite-atomic-enumeration", ValueError),
        ("strategy", _StrSubclass("bounded-rejection"), TypeError),
        ("budget", True, TypeError),
        ("budget", _IntSubclass(4), TypeError),
        ("budget", 0, ValueError),
        ("budget", 4097, ValueError),
    ),
)
def test_definition_rejects_hostile_fixture_strategy_and_budget(
    assumption, field, value, error
) -> None:
    arguments = {
        "fixture_id": "T28-M1-Q",
        "strategy": "bounded-rejection",
        "budget": 4,
        "request_template_sha256": assumption.request_template_sha256,
        "seed_assumption": assumption,
        "kernel_v2_source_sha256": pushforward.CP60_TEST28_KERNEL_V2_SOURCE_SHA256,
        "reference_source_sha256": pushforward.CP60_TEST28_REFERENCE_SOURCE_SHA256,
        "provider_source_sha256": pushforward.CP60_TEST28_PROVIDER_SOURCE_SHA256,
        "exact_score_source_sha256": pushforward.CP60_TEST28_EXACT_SCORE_SOURCE_SHA256,
        "quota_source_sha256": pushforward.CP60_TEST28_QUOTA_SOURCE_SHA256,
    }
    arguments[field] = value
    with pytest.raises(error):
        pushforward.define_cp60_whole_seed_pushforward(**arguments)


def test_definition_rejects_an_assumption_for_another_request(assumption) -> None:
    request = pushforward._request_template_sha256("T28-M1-Q", "bounded-rejection", 4)
    with pytest.raises(ValueError, match="another request"):
        pushforward.define_cp60_whole_seed_pushforward(
            fixture_id="T28-M1-Q",
            strategy="bounded-rejection",
            budget=4,
            request_template_sha256=request,
            seed_assumption=assumption,
            kernel_v2_source_sha256=(pushforward.CP60_TEST28_KERNEL_V2_SOURCE_SHA256),
            reference_source_sha256=pushforward.CP60_TEST28_REFERENCE_SOURCE_SHA256,
            provider_source_sha256=pushforward.CP60_TEST28_PROVIDER_SOURCE_SHA256,
            exact_score_source_sha256=(
                pushforward.CP60_TEST28_EXACT_SCORE_SOURCE_SHA256
            ),
            quota_source_sha256=pushforward.CP60_TEST28_QUOTA_SOURCE_SHA256,
        )


def test_absent_numeric_fibers_cannot_be_promoted_even_after_redigest(
    definition,
) -> None:
    for name in (
        "outcome_status_fiber_counts",
        "rejection_first_acceptance_fiber_counts",
        "rejection_selected_value_fiber_counts",
        "sir_selected_value_fiber_counts",
        "refusal_fiber_count",
        "exhaustion_fiber_count",
        "execution_failure_fiber_count",
        "nonreturn_fiber_count",
    ):
        assert getattr(definition, name) is None
        forged = _redigest(definition, "whole-seed-definition", **{name: 0})
        with pytest.raises((TypeError, ValueError)):
            pushforward.validate_cp60_whole_seed_pushforward(forged)


def test_redigested_assumption_claim_promotion_refuses(assumption) -> None:
    for changes in (
        {"operational_seed_source_verified": True},
        {"seed_sequence_iid_assumed": True},
        {"derived_philox_product_law_assumed": True},
        {"role_stream_independence_assumed": True},
        {"proposal_iid_assumed": True},
        {"current_fixed_hash_seed_plan_matches": True},
    ):
        forged = _redigest(assumption, "uniform-seed-assumption", **changes)
        with pytest.raises((TypeError, ValueError)):
            pushforward.validate_cp60_uniform_plan_seed_assumption(forged)


def test_redigested_alphabet_promotion_and_status_change_refuse(alphabet) -> None:
    changes = (
        {"statuses": tuple(reversed(alphabet.statuses))},
        {"failure_versus_nonreturn_mechanically_observable": True},
        {"python_exception_catching_proves_nonreturn_mass_zero": True},
        {"nonreturn_is_explicit": False},
    )
    for change in changes:
        forged = _redigest(alphabet, "outcome-alphabet", **change)
        with pytest.raises((TypeError, ValueError)):
            pushforward.validate_cp60_whole_seed_outcome_alphabet(forged)


def test_redigested_definition_claim_source_and_request_tamper_refuse(
    definition,
) -> None:
    changes = (
        {"request_parameters_fully_bound": True},
        {"fixed_request_map_instantiated": True},
        {"mathematical_totalization_formula_defined_for_future_fixed_request": False},
        {"fixed_seed_point_mass_theorem_recorded": False},
        {"future_validated_mc_requirements_recorded": False},
        {"execution_totality_proved": True},
        {"runtime_dependency_map_complete": True},
        {"seed_domain_exhaustively_enumerated": True},
        {"numeric_fiber_counts_computed": True},
        {"nonreturn_mass_proved_zero": True},
        {"common_mu_fp_identified": True},
        {"proposal_iid_verified": True},
        {"role_stream_independence_verified": True},
        {"alpha64_product_formula_permitted": True},
        {"operational_refusal_probability_derived": True},
        {"fixed_seed_replay_establishes_or_samples_uniform_seed_law": True},
        {"future_mc_seed_source_verified": True},
        {"future_mc_map_and_runtime_fully_fixed": True},
        {"future_mc_failures_and_nonreturn_retained": True},
        {"future_mc_no_retry_drop_or_seed_selection_verified": True},
        {"future_mc_uncertainty_method_prespecified": True},
        {"future_mc_multiplicity_method_prespecified": True},
        {"future_mc_positive_selected_count_rule_prespecified": True},
        {"future_mc_nonreturn_observability_mechanism_fixed": True},
        {"validated_mc_executed": True},
        {"validated_mc_sample_recorded": True},
        {"validated_mc_intervals_computed": True},
        {"current_deterministic_seed_plan_is_validated_mc": True},
        {"operational_prediction": True},
        {"manuscript_claim_promoted": True},
        {"formal_test_28_closed": True},
        {"kernel_v2_source_sha256": _sha("forged kernel source")},
        {"cp49_artifact_ancestry_claimed": True},
        {"no_returned_output_formula": "forged-no-output-formula"},
        {"fixed_seed_point_mass_theorem": "forged-fixed-seed-theorem"},
        {
            "future_validated_mc_requirements": tuple(
                reversed(definition.future_validated_mc_requirements)
            )
        },
    )
    for change in changes:
        forged = _redigest(definition, "whole-seed-definition", **change)
        with pytest.raises((TypeError, ValueError)):
            pushforward.validate_cp60_whole_seed_pushforward(forged)


def test_bundle_order_projection_and_claim_tamper_refuse(bundle) -> None:
    expected_order = tuple(
        (fixture, strategy, budget)
        for fixture in _FIXTURES
        for strategy, budgets in (
            ("bounded-rejection", _REJECTION_BUDGETS),
            ("fixed-budget-sir", _SIR_BUDGETS),
        )
        for budget in budgets
    )
    assert (
        tuple(
            (child.fixture_id, child.strategy, child.budget)
            for child in bundle.ordered_definitions
        )
        == expected_order
    )
    assert bundle.rejection_definitions == tuple(
        child
        for child in bundle.ordered_definitions
        if child.strategy == "bounded-rejection"
    )
    assert bundle.sir_definitions == tuple(
        child
        for child in bundle.ordered_definitions
        if child.strategy == "fixed-budget-sir"
    )

    for change in (
        {"ordered_definitions": tuple(reversed(bundle.ordered_definitions))},
        {"ordered_definitions": bundle.ordered_definitions[:-1]},
        {"rejection_definitions": tuple(reversed(bundle.rejection_definitions))},
        {"request_parameters_fully_bound": True},
        {"fixed_request_maps_instantiated": True},
        {"future_validated_mc_requirements_recorded": False},
        {"validated_mc_executed": True},
        {"numeric_fiber_counts_computed": True},
        {"operational_prediction": True},
        {"unconditional_operational_predictions_blocker_closed": True},
        {"manuscript_claim_promoted": True},
        {"formal_test_28_closed": True},
    ):
        forged = _redigest(bundle, "whole-seed-bundle", **change)
        with pytest.raises((TypeError, ValueError)):
            pushforward.validate_cp60_whole_seed_pushforward_bundle(forged)


def test_bundle_rejects_a_redigested_but_noncanonical_child(bundle) -> None:
    child = bundle.rejection_definitions[0]
    changed_child = _redigest(
        child,
        "whole-seed-definition",
        dependency_lock_sha256=_sha("spliced optional lock"),
    )
    changed_rejection = (changed_child,) + bundle.rejection_definitions[1:]
    changed_order = tuple(
        changed_child if item is child else item for item in bundle.ordered_definitions
    )
    forged = _redigest(
        bundle,
        "whole-seed-bundle",
        ordered_definitions=changed_order,
        rejection_definitions=changed_rejection,
    )
    with pytest.raises((TypeError, ValueError)):
        pushforward.validate_cp60_whole_seed_pushforward_bundle(forged)


def test_nested_exact_type_checks_precede_hostile_protocols(definition, bundle) -> None:
    bomb = _ProtocolBomb()
    with pytest.raises(TypeError):
        pushforward.validate_cp60_whole_seed_pushforward(
            _redigest(
                definition,
                "whole-seed-definition",
                seed_assumption=bomb,
            )
        )
    assert bomb.__dict__ == {}

    forged = _forge(bundle, ordered_definitions=bomb)
    with pytest.raises(TypeError):
        pushforward.validate_cp60_whole_seed_pushforward_bundle(forged)
    assert bomb.__dict__ == {}


def test_tuple_element_type_preflight_never_invokes_hostile_equality(alphabet) -> None:
    bomb = _ProtocolBomb()
    forged = _forge(
        alphabet,
        statuses=(bomb,) + alphabet.statuses[1:],
    )
    with pytest.raises(TypeError):
        pushforward.validate_cp60_whole_seed_outcome_alphabet(forged)
    assert bomb.__dict__ == {}


def test_record_types_are_slot_only_sealed_and_nonpickleable(
    assumption, alphabet, definition, bundle
) -> None:
    records = (
        assumption,
        alphabet,
        definition,
        bundle,
    ) + bundle.ordered_definitions
    for record in records:
        assert not hasattr(record, "__dict__")
        with pytest.raises(TypeError, match="module-created"):
            type(record)()
        with pytest.raises((TypeError, pickle.PicklingError)):
            pickle.dumps(record)
        with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
            record.hostile_attribute = True
        with pytest.raises(TypeError, match="cannot be subclassed"):
            type("HostileCP60Subclass", (type(record),), {})
    with pytest.raises(TypeError, match="cannot be subclassed"):
        make_dataclass(
            "HostileCP60Alien",
            (("record_sha256", str),),
            bases=(pushforward._SealedRecord,),
            frozen=True,
            init=False,
            slots=True,
        )


def test_canonical_encoder_is_exact_record_only_and_type_tagged(
    assumption, alphabet, definition, bundle
) -> None:
    encodings = tuple(
        pushforward.cp60_canonical_json_bytes(value)
        for value in (assumption, alphabet, definition, bundle)
    )
    assert len(set(encodings)) == 4
    assert all(type(value) is bytes and value for value in encodings)
    assert b"uniform-plan-seed-assumption-v1" in encodings[0]
    assert b"whole-seed-outcome-alphabet-v1" in encodings[1]
    assert b"whole-seed-pushforward-definition-v1" in encodings[2]
    assert b"whole-seed-pushforward-bundle-v1" in encodings[3]
    for malformed in (
        None,
        True,
        1,
        Fraction(1, 2),
        {},
        (),
        _ProtocolBomb(),
    ):
        with pytest.raises(TypeError):
            pushforward.cp60_canonical_json_bytes(malformed)


def test_canonical_aggregate_text_limit_is_enforced_before_json_materialization(
    monkeypatch,
) -> None:
    monkeypatch.setattr(pushforward, "_MAX_CANONICAL_TEXT_BYTES", 64)
    with pytest.raises(ValueError, match="aggregate|text"):
        pushforward._canonical_bytes(("x" * 40, "y" * 40))


def test_canonical_resource_preflights_cover_shape_depth_integer_and_fraction(
    monkeypatch,
) -> None:
    monkeypatch.setattr(pushforward, "_MAX_CANONICAL_NODES", 4)
    with pytest.raises(ValueError, match="tuple|resource"):
        pushforward._canonical_bytes((None,) * 5)

    monkeypatch.setattr(pushforward, "_MAX_CANONICAL_NODES", 64)
    monkeypatch.setattr(pushforward, "_MAX_CANONICAL_DEPTH", 1)
    with pytest.raises(ValueError, match="node/depth"):
        pushforward._canonical_bytes(((None,),))

    monkeypatch.setattr(pushforward, "_MAX_INTEGER_BITS", 8)
    for hostile in (1 << 8, Fraction(1 << 8, 3), Fraction(3, (1 << 8) + 1)):
        with pytest.raises(ValueError, match="bit limit"):
            pushforward._canonical_bytes(hostile)

    monkeypatch.setattr(pushforward, "_MAX_TEXT_BYTES", 4)
    with pytest.raises(ValueError, match="per-field"):
        pushforward._canonical_bytes("abcde")

    monkeypatch.setattr(pushforward, "_MAX_CANONICAL_OUTPUT_BYTES", 4)
    with pytest.raises(ValueError, match="output"):
        pushforward._canonical_bytes(None)


def test_source_is_definition_only_and_has_no_rng_or_operational_route() -> None:
    source_path = Path(pushforward.__file__).resolve()
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    }
    assert not any(
        name == forbidden or name.startswith(forbidden + ".")
        for name in imports
        for forbidden in (
            "numpy",
            "scipy",
            "random",
            "secrets",
            "os",
            "heterodiff.processes",
        )
    )
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    called_attributes = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert not called_names.intersection(
        {"range", "iter", "next", "list", "Generator", "Philox"}
    )
    assert not called_attributes.intersection(
        {
            "execute",
            "sample_configuration",
            "evaluate",
            "random",
            "random_raw",
            "standard_normal",
        }
    )
    assert not any(isinstance(node, ast.Pow) for node in ast.walk(tree))
    assert "PLAN_SEED_DOMAIN_SIZE" in source


def test_clean_import_bundle_hash_is_stable_and_loads_no_operational_dependencies(
    bundle,
) -> None:
    source_root = str(Path(__file__).resolve().parents[2] / "src")
    code = r"""
import builtins
import hashlib
import sys
real_import = builtins.__import__
forbidden = ("numpy", "scipy", "torch", "heterodiff.processes")
def guarded(name, *args, **kwargs):
    if any(name == item or name.startswith(item + ".") for item in forbidden):
        raise AssertionError("operational dependency crossed CP60 import boundary: " + name)
    return real_import(name, *args, **kwargs)
builtins.__import__ = guarded
from heterodiff.evaluation import mixed_initializer_test28_uniform_seed_pushforward as module
bundle = module.cp60_whole_seed_pushforward_bundle()
assert len(bundle.ordered_definitions) == 16
assert not any(name == item or name.startswith(item + ".") for name in sys.modules for item in forbidden)
print(bundle.record_sha256)
print(hashlib.sha256(module.cp60_canonical_json_bytes(bundle)).hexdigest())
"""
    expected = (
        bundle.record_sha256,
        hashlib.sha256(pushforward.cp60_canonical_json_bytes(bundle)).hexdigest(),
    )
    for _ in range(2):
        completed = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(Path(__file__).resolve().parents[2]),
            env={"PYTHONPATH": source_root},
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        assert tuple(completed.stdout.splitlines()) == expected


def test_public_export_surface_and_signatures_are_exact() -> None:
    expected = {
        "CP60_TEST28_WHOLE_SEED_SCHEMA_VERSION",
        "CP60_TEST28_WHOLE_SEED_SCOPE",
        "CP60_TEST28_UNIFORM_SEED_ASSUMPTION_MODE",
        "CP60_TEST28_UNIFORM_SEED_ASSUMPTION_SCOPE",
        "CP60_TEST28_OUTCOME_STATUSES",
        "CP60_TEST28_PREEXECUTION_REFUSAL_CLASSES",
        "CP60_TEST28_EXECUTION_FAILURE_CLASSES",
        "CP60_TEST28_REJECTION_TRACE_PAYLOAD",
        "CP60_TEST28_SIR_TRACE_PAYLOAD",
        "CP60_TEST28_TOTAL_MAP_DEFINITION",
        "CP60_TEST28_FIBER_COUNT_FORMULA",
        "CP60_TEST28_SINGLETON_FORMULA",
        "CP60_TEST28_NORMALIZATION_FORMULA",
        "CP60_TEST28_REJECTION_FIBER_FORMULA",
        "CP60_TEST28_SIR_FIBER_FORMULA",
        "CP60_TEST28_PROPOSAL_MARGINAL_FORMULA",
        "CP60_TEST28_NO_RETURNED_OUTPUT_FORMULA",
        "CP60_TEST28_FIXED_SEED_POINT_MASS_THEOREM",
        "CP60_TEST28_FUTURE_VALIDATED_MC_REQUIREMENTS",
        "CP60_TEST28_RUNTIME_BINDING_REQUIREMENTS",
        "CP60_TEST28_FORMAL_TEST_28_STATUS",
        "CP60_TEST28_FIXTURE_IDS",
        "CP60_TEST28_STRATEGIES",
        "CP60_TEST28_REJECTION_BUDGET_GRID",
        "CP60_TEST28_SIR_BUDGET_GRID",
        "CP60_TEST28_MAX_BUDGET",
        "CP60_TEST28_PLAN_SEED_BITS",
        "CP60_TEST28_PLAN_SEED_DOMAIN_SIZE",
        "CP60_TEST28_KERNEL_V2_SOURCE_SHA256",
        "CP60_TEST28_REFERENCE_SOURCE_SHA256",
        "CP60_TEST28_PROVIDER_SOURCE_SHA256",
        "CP60_TEST28_EXACT_SCORE_SOURCE_SHA256",
        "CP60_TEST28_QUOTA_SOURCE_SHA256",
        "CP60_TEST28_CP59_SOURCE_SHA256",
        "CP60_TEST28_CP49_PRECEDENT_SOURCE_SHA256",
        "UniformPlanSeedAssumptionV1",
        "WholeSeedOutcomeAlphabetV1",
        "WholeSeedPushforwardDefinitionV1",
        "CP60WholeSeedPushforwardBundleV1",
        "declare_cp60_uniform_plan_seed_assumption",
        "cp60_whole_seed_outcome_alphabet",
        "define_cp60_whole_seed_pushforward",
        "cp60_whole_seed_pushforward_bundle",
        "validate_cp60_uniform_plan_seed_assumption",
        "validate_cp60_whole_seed_outcome_alphabet",
        "validate_cp60_whole_seed_pushforward",
        "validate_cp60_whole_seed_pushforward_bundle",
        "cp60_canonical_json_bytes",
    }
    assert set(pushforward.__all__) == expected
    assert len(pushforward.__all__) == len(set(pushforward.__all__)) == 48

    declaration = inspect.signature(
        pushforward.declare_cp60_uniform_plan_seed_assumption
    ).parameters
    assert tuple(declaration) == (
        "request_template_sha256",
        "assumption_role_sha256",
        "one_exact_uint64_seed_almost_surely_supplied_assumed",
        "unconditional_uniform_plan_seed_assumed",
    )
    assert all(
        item.kind is inspect.Parameter.KEYWORD_ONLY for item in declaration.values()
    )
    definition = inspect.signature(
        pushforward.define_cp60_whole_seed_pushforward
    ).parameters
    assert tuple(definition) == (
        "fixture_id",
        "strategy",
        "budget",
        "request_template_sha256",
        "seed_assumption",
        "kernel_v2_source_sha256",
        "reference_source_sha256",
        "provider_source_sha256",
        "exact_score_source_sha256",
        "quota_source_sha256",
        "dependency_lock_sha256",
        "runtime_record_sha256",
    )
    assert all(
        item.kind is inspect.Parameter.KEYWORD_ONLY for item in definition.values()
    )
    assert (
        tuple(
            inspect.signature(pushforward.cp60_whole_seed_outcome_alphabet).parameters
        )
        == ()
    )
    assert (
        tuple(
            inspect.signature(pushforward.cp60_whole_seed_pushforward_bundle).parameters
        )
        == ()
    )
    for validator in (
        pushforward.validate_cp60_uniform_plan_seed_assumption,
        pushforward.validate_cp60_whole_seed_outcome_alphabet,
        pushforward.validate_cp60_whole_seed_pushforward,
        pushforward.validate_cp60_whole_seed_pushforward_bundle,
        pushforward.cp60_canonical_json_bytes,
    ):
        assert tuple(inspect.signature(validator).parameters) == ("value",)


def test_strategy_specific_grid_and_request_role_binding_are_fail_closed() -> None:
    for fixture, strategy, budget in (
        ("T28-M1-Q", "bounded-rejection", 8),
        ("T28-M2-Q", "fixed-budget-sir", 4),
    ):
        request = pushforward._request_template_sha256(fixture, strategy, budget)
        premise = pushforward.declare_cp60_uniform_plan_seed_assumption(
            request_template_sha256=request,
            assumption_role_sha256=pushforward._assumption_role_sha256(request),
            one_exact_uint64_seed_almost_surely_supplied_assumed=True,
            unconditional_uniform_plan_seed_assumed=True,
        )
        with pytest.raises(ValueError, match="strategy-specific"):
            pushforward.define_cp60_whole_seed_pushforward(
                fixture_id=fixture,
                strategy=strategy,
                budget=budget,
                request_template_sha256=request,
                seed_assumption=premise,
                kernel_v2_source_sha256=(
                    pushforward.CP60_TEST28_KERNEL_V2_SOURCE_SHA256
                ),
                reference_source_sha256=(
                    pushforward.CP60_TEST28_REFERENCE_SOURCE_SHA256
                ),
                provider_source_sha256=(pushforward.CP60_TEST28_PROVIDER_SOURCE_SHA256),
                exact_score_source_sha256=(
                    pushforward.CP60_TEST28_EXACT_SCORE_SOURCE_SHA256
                ),
                quota_source_sha256=pushforward.CP60_TEST28_QUOTA_SOURCE_SHA256,
            )

    request = pushforward._request_template_sha256("T28-M1-Q", "bounded-rejection", 4)
    wrong_role = pushforward.declare_cp60_uniform_plan_seed_assumption(
        request_template_sha256=request,
        assumption_role_sha256=_sha("wrong bound role"),
        one_exact_uint64_seed_almost_surely_supplied_assumed=True,
        unconditional_uniform_plan_seed_assumed=True,
    )
    with pytest.raises(ValueError, match="role differs"):
        pushforward.define_cp60_whole_seed_pushforward(
            fixture_id="T28-M1-Q",
            strategy="bounded-rejection",
            budget=4,
            request_template_sha256=request,
            seed_assumption=wrong_role,
            kernel_v2_source_sha256=(pushforward.CP60_TEST28_KERNEL_V2_SOURCE_SHA256),
            reference_source_sha256=pushforward.CP60_TEST28_REFERENCE_SOURCE_SHA256,
            provider_source_sha256=pushforward.CP60_TEST28_PROVIDER_SOURCE_SHA256,
            exact_score_source_sha256=(
                pushforward.CP60_TEST28_EXACT_SCORE_SOURCE_SHA256
            ),
            quota_source_sha256=pushforward.CP60_TEST28_QUOTA_SOURCE_SHA256,
        )
