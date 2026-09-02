"""Hostile tests for checkpoint-37 finite-resolution rejection decisions."""

import ast
from decimal import Decimal, localcontext
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
    "torch", reason="counter-keyed rejection decisions require PyTorch"
)

from heterodiff.processes import (  # noqa: E402
    plugin_bridge_counter_keyed_initial_tilt_rejection_decision as decision,
)
from tests.unit import (  # noqa: E402
    test_plugin_bridge_counter_keyed_initial_tilt_rejection_preparation as checkpoint36,
)


DECISION_POLICY = (
    decision.PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_DECISION_POLICY
)
DECISION_ROLE = "8" * 64
D = 1 << 64
_CERTIFY = getattr(
    decision,
    "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_decision",
)
_MATCHING = getattr(
    decision,
    "require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_decision",
)
_VALIDATE_CERTIFICATE = getattr(
    decision,
    "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_decision_certificate",
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


def _record(cls, values):
    record = object.__new__(cls)
    for name in cls.__annotations__:
        object.__setattr__(record, name, values[name])
    return record


def _certificate_values(certificate, **updates):
    values = {
        name: updates.get(name, getattr(certificate, name))
        for name in decision._certificate_fields()
    }
    values["certificate_sha256"] = "0" * 64
    values["certificate_sha256"] = decision._semantic_digest(
        decision._certificate_payload(values)
    )
    return values


def _threshold_values(threshold, **updates):
    values = {
        name: updates.get(name, getattr(threshold, name))
        for name in decision._threshold_fields()
    }
    values["threshold_sha256"] = "0" * 64
    values["threshold_sha256"] = decision._semantic_digest(
        decision._threshold_payload(values)
    )
    return values


def _decision_values(attempt_decision, **updates):
    values = {
        name: updates.get(name, getattr(attempt_decision, name))
        for name in decision._decision_fields()
    }
    values["decision_sha256"] = "0" * 64
    values["decision_sha256"] = decision._semantic_digest(
        decision._decision_payload(values)
    )
    return values


def _result_values(result, **updates):
    values = {
        name: updates.get(name, getattr(result, name))
        for name in decision._result_fields()
    }
    if "thresholds" in updates and "threshold_sha256s" not in updates:
        values["threshold_sha256s"] = tuple(
            item.threshold_sha256 for item in values["thresholds"]
        )
    if "decisions" in updates and "decision_sha256s" not in updates:
        values["decision_sha256s"] = tuple(
            item.decision_sha256 for item in values["decisions"]
        )
        values["evaluated_attempt_count"] = len(values["decisions"])
    values["result_sha256"] = "0" * 64
    values["result_sha256"] = decision._semantic_digest(
        decision._result_payload(values)
    )
    return values


def _attempt_with(base, *, index, delta, word):
    assert isinstance(delta, Fraction) and delta <= 0
    return _forged(
        base,
        attempt_index=index,
        q_minus_upper_bound_numerator=delta.numerator,
        q_minus_upper_bound_denominator=delta.denominator,
        reserved_decision_raw64_word=word,
    )


def _threshold_for(certificate, attempt):
    delta = Fraction(
        attempt.q_minus_upper_bound_numerator,
        attempt.q_minus_upper_bound_denominator,
    )
    data = decision._floor_exp_uint64_quota(delta)
    probability = Fraction(data.quota, D)
    values = {
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "preparation_attempt": attempt,
        "preparation_attempt_sha256": attempt.attempt_sha256,
        "attempt_index": attempt.attempt_index,
        "delta_numerator": delta.numerator,
        "delta_denominator": delta.denominator,
        "threshold_branch": data.branch,
        "decimal_precision_used": data.precision,
        "ideal_probability_lower_numerator": data.ideal_lower.numerator,
        "ideal_probability_lower_denominator": data.ideal_lower.denominator,
        "ideal_probability_upper_numerator": data.ideal_upper.numerator,
        "ideal_probability_upper_denominator": data.ideal_upper.denominator,
        "ideal_probability_upper_strict": data.ideal_upper_strict,
        "acceptance_quota": data.quota,
        "quota_probability_numerator": probability.numerator,
        "quota_probability_denominator": probability.denominator,
        "ideal_minus_quota_error_strict_upper_numerator": 1,
        "ideal_minus_quota_error_strict_upper_denominator": D,
        "quota_certified_before_word_interpretation": True,
        "exact_ideal_probability_materialized": False,
        "threshold_sha256": "0" * 64,
    }
    values["threshold_sha256"] = decision._semantic_digest(
        decision._threshold_payload(values)
    )
    return _record(decision.CounterKeyedInitialTiltRejectionThreshold, values)


def _attempt_decision_for(threshold):
    attempt = threshold.preparation_attempt
    accepted = attempt.reserved_decision_raw64_word < threshold.acceptance_quota
    values = {
        "certificate": threshold.certificate,
        "certificate_sha256": threshold.certificate_sha256,
        "threshold": threshold,
        "threshold_sha256": threshold.threshold_sha256,
        "preparation_attempt": attempt,
        "preparation_attempt_sha256": attempt.attempt_sha256,
        "attempt_index": attempt.attempt_index,
        "decision_word": attempt.reserved_decision_raw64_word,
        "acceptance_quota": threshold.acceptance_quota,
        "word_below_quota": accepted,
        "accepted": accepted,
        "inherited_reserved_word_interpreted": True,
        "exact_half_open_comparison": True,
        "extra_word_consumed": False,
        "ideal_exponential_bernoulli_claimed": False,
        "decision_sha256": "0" * 64,
    }
    values["decision_sha256"] = decision._semantic_digest(
        decision._decision_payload(values)
    )
    return _record(decision.CounterKeyedInitialTiltRejectionAttemptDecision, values)


def _synthetic_case(live_result, specs):
    parent = live_result.preparation_result
    certificate = live_result.certificate
    attempts = tuple(
        _attempt_with(
            parent.attempts[min(index, len(parent.attempts) - 1)],
            index=index,
            delta=delta,
            word=word,
        )
        for index, (delta, word) in enumerate(specs)
    )
    synthetic_parent = _forged(parent, attempts=attempts)
    thresholds = tuple(_threshold_for(certificate, attempt) for attempt in attempts)
    all_decisions = tuple(_attempt_decision_for(item) for item in thresholds)
    stop = next(
        (index + 1 for index, item in enumerate(all_decisions) if item.accepted),
        len(all_decisions),
    )
    decisions = all_decisions[:stop]
    selected = decisions[-1].accepted
    selected_index = len(decisions) - 1 if selected else None
    selected_attempt = attempts[selected_index] if selected else None
    probability = decision._conditional_probability(thresholds, selected_index)
    values = {
        "schema_version": (
            getattr(
                decision,
                (
                    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_"
                    "DECISION_SCHEMA_VERSION"
                ),
            )
        ),
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "preparation_result": synthetic_parent,
        "preparation_result_sha256": synthetic_parent.result_sha256,
        "run_id": synthetic_parent.run_id,
        "initialization_index": synthetic_parent.initialization_index,
        "attempt_budget": synthetic_parent.attempt_budget,
        "thresholds": thresholds,
        "threshold_sha256s": tuple(item.threshold_sha256 for item in thresholds),
        "decisions": decisions,
        "decision_sha256s": tuple(item.decision_sha256 for item in decisions),
        "evaluated_attempt_count": len(decisions),
        "outcome": "selected" if selected else "exhausted",
        "selected_attempt_index": selected_index,
        "selected_preparation_attempt": selected_attempt,
        "selected_preparation_attempt_sha256": (
            None if selected_attempt is None else selected_attempt.attempt_sha256
        ),
        "selected_configuration": (
            None
            if selected_attempt is None
            else selected_attempt.canonical_configuration
        ),
        "selected_configuration_sha256": (
            None
            if selected_attempt is None
            else selected_attempt.canonical_configuration_sha256
        ),
        "succeeded": selected,
        "budget_exhausted": not selected,
        "all_thresholds_certified_before_first_decision": True,
        "prior_attempts_rejected": True,
        "selected_attempt_is_first_accepted": selected,
        "suffix_decision_words_uninterpreted": (
            selected and len(decisions) < len(thresholds)
        ),
        "complete_preparation_prefix_retained": True,
        "conditional_outcome_probability_numerator": probability.numerator,
        "conditional_outcome_probability_denominator": probability.denominator,
        "operational_failure_returned_as_exhaustion": False,
        "retry_fallback_or_rollback_claimed": False,
        "initializer_output_admitted": False,
        "deterministic_fixed_address_replay_only": True,
        "result_sha256": "0" * 64,
    }
    values["result_sha256"] = decision._semantic_digest(
        decision._result_payload(values)
    )
    return _record(decision.CounterKeyedInitialTiltRejectionDecisionResult, values)


@pytest.fixture(scope="module")
def live_bundle():
    bundle = checkpoint36.certified_bundle.__wrapped__()
    owner = _CERTIFY(
        bundle["owner"],
        decision_policy=DECISION_POLICY,
        decision_role_sha256=DECISION_ROLE,
    )
    events = []
    originals = {
        "prepare_global": decision._PREP_PREPARE,
        "threshold_global": decision._make_threshold,
        "decision_global": decision._make_decision,
        "prepare_owner": owner._preparation_prepare,
        "threshold_owner": owner._threshold_builder,
        "decision_owner": owner._decision_builder,
    }

    def traced_prepare(parent_owner, run_id, initialization_index):
        events.append(("prepare", run_id, initialization_index))
        return originals["prepare_global"](parent_owner, run_id, initialization_index)

    def traced_threshold(certificate, attempt):
        events.append(("threshold", attempt.attempt_index))
        return originals["threshold_global"](certificate, attempt)

    def traced_decision(threshold):
        events.append(("decision", threshold.attempt_index))
        assert sum(kind == "threshold" for kind, *_ in events) == (
            owner.certificate.attempt_budget
        )
        return originals["decision_global"](threshold)

    decision._PREP_PREPARE = traced_prepare
    decision._make_threshold = traced_threshold
    decision._make_decision = traced_decision
    object.__setattr__(owner, "_preparation_prepare", traced_prepare)
    object.__setattr__(owner, "_threshold_builder", traced_threshold)
    object.__setattr__(owner, "_decision_builder", traced_decision)
    before = _rng_snapshot()
    try:
        result = owner.decide(37_000, 0)
    finally:
        decision._PREP_PREPARE = originals["prepare_global"]
        decision._make_threshold = originals["threshold_global"]
        decision._make_decision = originals["decision_global"]
        object.__setattr__(owner, "_preparation_prepare", originals["prepare_owner"])
        object.__setattr__(owner, "_threshold_builder", originals["threshold_owner"])
        object.__setattr__(owner, "_decision_builder", originals["decision_owner"])
    _assert_rng_unchanged(before)
    bundle.update(owner=owner, result=result, chronology=tuple(events))
    return bundle


@pytest.fixture(scope="module")
def synthetic_cases(live_bundle):
    adaptive_quota = decision._floor_exp_uint64_quota(Fraction(-1)).quota
    return {
        "first": _synthetic_case(
            live_bundle["result"],
            ((Fraction(0), D - 1), (Fraction(0), D - 1)),
        ),
        "later": _synthetic_case(
            live_bundle["result"],
            ((Fraction(-1), adaptive_quota), (Fraction(0), 0)),
        ),
        "exhausted": _synthetic_case(
            live_bundle["result"],
            ((Fraction(-1), adaptive_quota), (Fraction(-64), 0)),
        ),
    }


def test_frozen_constants_public_exports_and_owner_signatures_are_exact(live_bundle):
    expected_exports = {
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_DECISION_SCHEMA_VERSION",
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_DECISION_POLICY",
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_DECISION_ALGORITHM",
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_DECISION_SCOPE",
        "INITIAL_TILT_REJECTION_DECISION_DYADIC_DENOMINATOR",
        "INITIAL_TILT_REJECTION_DECISION_RAW_WORD_BITS",
        "INITIAL_TILT_REJECTION_DECISION_PRIMARY_PRECISION",
        "INITIAL_TILT_REJECTION_DECISION_AUDIT_PRECISION",
        "INITIAL_TILT_REJECTION_DECISION_MAX_PRECISION",
        "INITIAL_TILT_REJECTION_DECISION_ZERO_QUOTA_LOG_CUTOFF",
        "INITIAL_TILT_REJECTION_DECISION_MAX_DECIMAL_COEFFICIENT_DIGITS",
        "INITIAL_TILT_REJECTION_DECISION_MAX_ATTEMPTS",
        "INITIAL_TILT_REJECTION_DECISION_OUTCOMES",
        "INITIAL_TILT_REJECTION_DECISION_CONDITIONAL_THEOREM",
        "INITIAL_TILT_REJECTION_DECISION_APPROXIMATION_THEOREM",
        "CounterKeyedInitialTiltRejectionDecisionCertificate",
        "CounterKeyedInitialTiltRejectionThreshold",
        "CounterKeyedInitialTiltRejectionAttemptDecision",
        "CounterKeyedInitialTiltRejectionDecisionResult",
        "CounterKeyedInitialTiltRejectionDecisionOwner",
        "PluginBridgeCounterKeyedInitialTiltRejectionDecisionError",
        "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_decision",
        (
            "require_matching_plugin_bridge_counter_keyed_initial_tilt_"
            "rejection_decision"
        ),
        (
            "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_"
            "decision_certificate"
        ),
    }
    assert set(decision.__all__) == expected_exports
    assert len(decision.__all__) == len(expected_exports)
    assert decision.INITIAL_TILT_REJECTION_DECISION_DYADIC_DENOMINATOR == D
    assert decision.INITIAL_TILT_REJECTION_DECISION_RAW_WORD_BITS == 64
    assert decision.INITIAL_TILT_REJECTION_DECISION_PRIMARY_PRECISION == 192
    assert decision.INITIAL_TILT_REJECTION_DECISION_AUDIT_PRECISION == 384
    assert decision.INITIAL_TILT_REJECTION_DECISION_MAX_PRECISION == 3_072
    assert decision.INITIAL_TILT_REJECTION_DECISION_ZERO_QUOTA_LOG_CUTOFF == -64
    assert (
        decision.INITIAL_TILT_REJECTION_DECISION_MAX_DECIMAL_COEFFICIENT_DIGITS
        == 16_384
    )
    assert decision.INITIAL_TILT_REJECTION_DECISION_MAX_ATTEMPTS == 64
    assert decision.INITIAL_TILT_REJECTION_DECISION_OUTCOMES == (
        "selected",
        "exhausted",
    )
    owner_type = decision.CounterKeyedInitialTiltRejectionDecisionOwner
    assert str(inspect.signature(owner_type.decide)) == (
        "(self, run_id: 'object', initialization_index: 'object') -> "
        "'CounterKeyedInitialTiltRejectionDecisionResult'"
    )
    assert str(inspect.signature(owner_type.validate_result)) == (
        "(self, result: 'object', run_id: 'object', "
        "initialization_index: 'object') -> "
        "'CounterKeyedInitialTiltRejectionDecisionResult'"
    )
    assert str(inspect.signature(_CERTIFY)) == (
        "(preparation_owner: 'object', *, decision_policy: 'object', "
        "decision_role_sha256: 'object') -> "
        "'CounterKeyedInitialTiltRejectionDecisionOwner'"
    )
    assert (
        live_bundle["owner"].preparation_owner
        is live_bundle["owner"]._preparation_owner
    )


def test_certificate_truth_matrix_and_scope_are_exhaustive(live_bundle):
    certificate = live_bundle["owner"].certificate
    for name in decision._CERTIFICATE_POSITIVE_FLAGS:
        assert getattr(certificate, name) is True
    for name in decision._CERTIFICATE_NEGATIVE_FLAGS:
        assert getattr(certificate, name) is False
    assert set(decision._CERTIFICATE_POSITIVE_FLAGS).isdisjoint(
        decision._CERTIFICATE_NEGATIVE_FLAGS
    )
    assert (
        set(decision._CERTIFICATE_POSITIVE_FLAGS)
        | set(decision._CERTIFICATE_NEGATIVE_FLAGS)
    ) == {
        name
        for name in decision._certificate_fields()
        if name.endswith("certified")
        or name.endswith("admissible")
        or name
        in {
            "passed",
            "test28_closed",
            "runtime_portable",
            "cryptographic_authentication",
        }
    }
    assert certificate.attempt_budget == 2
    assert certificate.maximum_decimal_coefficient_digits == 16_384
    assert certificate.preparation_owner_runtime_identity == id(
        live_bundle["owner"].preparation_owner
    )
    assert (
        certificate.preparation_certificate
        is live_bundle["owner"].preparation_owner.certificate
    )
    assert "not-exact-exp-bernoulli" in certificate.certificate_scope
    assert (
        "not-live-uniformity-independence-randomness" in certificate.certificate_scope
    )


@pytest.mark.parametrize(
    "delta, branch, quota, precision, upper_strict",
    (
        (Fraction(0), "unity", D, 0, False),
        (Fraction(-64), "below_uint64_resolution", 0, 0, True),
        (Fraction(-65), "below_uint64_resolution", 0, 0, True),
    ),
)
def test_exact_quota_terminal_branches(delta, branch, quota, precision, upper_strict):
    data = decision._floor_exp_uint64_quota(delta)
    assert data.branch == branch
    assert data.quota == quota
    assert data.precision == precision
    assert data.ideal_upper_strict is upper_strict
    assert Fraction(data.quota, D) <= data.ideal_lower <= data.ideal_upper
    assert data.ideal_upper - Fraction(data.quota, D) <= Fraction(1, D)


@pytest.mark.parametrize(
    "delta",
    (
        Fraction(-1),
        Fraction(-1, 2),
        Fraction(-63),
        Fraction(-1, 1 << 40),
        Fraction(-63 * (1 << 31) - 1, 1 << 31),
    ),
)
def test_adaptive_quota_matches_independent_high_precision_decimal_oracle(delta):
    data = decision._floor_exp_uint64_quota(delta)
    with localcontext() as context:
        context.prec = 500
        scaled = (
            Decimal(delta.numerator) / Decimal(delta.denominator)
        ).exp() * Decimal(D)
        oracle = int(scaled)
    assert data.branch == "adaptive_decimal"
    assert data.quota == oracle
    assert data.precision in decision._precision_schedule()
    assert Fraction(data.quota, D) <= data.ideal_lower
    quota_ceiling = Fraction(data.quota + 1, D)
    assert data.ideal_upper < quota_ceiling or (
        data.ideal_upper_strict and data.ideal_upper == quota_ceiling
    )


def test_seeded_dyadic_fuzz_matches_independent_mpmath_oracle_384_cases():
    mpmath = pytest.importorskip("mpmath")
    generator = random.Random(37_064)
    cases = []
    for _ in range(384):
        exponent = generator.randrange(1, 81)
        denominator = 1 << exponent
        numerator = generator.randrange(1, 64 * denominator)
        delta = Fraction(-numerator, denominator)
        if delta <= -64:
            delta = Fraction(-63 * denominator - 1, denominator)
        cases.append(delta)
    with mpmath.workprec(1_000):
        for delta in cases:
            oracle = int(
                mpmath.floor(
                    mpmath.exp(mpmath.mpf(delta.numerator) / delta.denominator)
                    * mpmath.power(2, 64)
                )
            )
            data = decision._floor_exp_uint64_quota(delta)
            assert data.branch == "adaptive_decimal"
            assert data.quota == oracle


@pytest.mark.parametrize("bad", (0, -1, 1.0, Decimal("-1"), True, None))
def test_quota_requires_an_exact_fraction(bad):
    with pytest.raises(TypeError):
        decision._floor_exp_uint64_quota(bad)


def test_quota_refuses_positive_and_nondyadic_gaps():
    with pytest.raises(ValueError, match="nonpositive"):
        decision._floor_exp_uint64_quota(Fraction(1, 2))
    with pytest.raises(
        decision.PluginBridgeCounterKeyedInitialTiltRejectionDecisionError,
        match="dyadic",
    ):
        decision._floor_exp_uint64_quota(Fraction(-1, 3))


def test_tiny_negative_gap_and_large_integer_decimal_conversion_boundaries():
    tiny = decision._floor_exp_uint64_quota(Fraction(-1, 1 << 1_074))
    assert tiny.branch == "below_one_uint64_cell"
    assert tiny.quota == D - 1
    assert tiny.ideal_upper == 1
    assert tiny.ideal_upper_strict is True

    value = 1 << 8_191
    digits = decision._nonnegative_integer_decimal_digits(value, name="boundary")
    reconstructed = 0
    for digit in digits:
        assert 0 <= digit <= 9
        reconstructed = 10 * reconstructed + digit
    assert reconstructed == value

    cap = decision.INITIAL_TILT_REJECTION_DECISION_MAX_DECIMAL_COEFFICIENT_DIGITS
    capped_digits = decision._nonnegative_integer_decimal_digits(
        10 ** (cap - 1), name="at cap"
    )
    assert len(capped_digits) == cap
    with pytest.raises(
        decision.PluginBridgeCounterKeyedInitialTiltRejectionDecisionError,
        match="coefficient exceeds",
    ):
        decision._nonnegative_integer_decimal_digits(10**cap, name="above cap")


def test_live_decide_certifies_every_threshold_before_first_word(live_bundle):
    chronology = live_bundle["chronology"]
    kinds = tuple(item[0] for item in chronology)
    assert kinds.count("prepare") == 1
    assert kinds.count("threshold") == live_bundle["owner"].certificate.attempt_budget
    assert kinds.index("decision") > max(
        index for index, kind in enumerate(kinds) if kind == "threshold"
    )
    result = live_bundle["result"]
    assert result.all_thresholds_certified_before_first_decision is True
    assert len(result.thresholds) == result.attempt_budget
    assert 1 <= len(result.decisions) <= result.attempt_budget


def test_half_open_boundary_words_cover_zero_quota_minus_one_quota_and_domain_end(
    live_bundle,
):
    certificate = live_bundle["owner"].certificate
    base = live_bundle["result"].preparation_result.attempts[0]
    quota = decision._floor_exp_uint64_quota(Fraction(-1)).quota
    cases = (
        (Fraction(0), 0, D, True),
        (Fraction(0), D - 1, D, True),
        (Fraction(-1), quota - 1, quota, True),
        (Fraction(-1), quota, quota, False),
        (Fraction(-1), D - 1, quota, False),
        (Fraction(-64), 0, 0, False),
        (Fraction(-64), D - 1, 0, False),
    )
    for index, (delta, word, expected_quota, accepted) in enumerate(cases):
        attempt = _attempt_with(base, index=index % 2, delta=delta, word=word)
        threshold = _threshold_for(certificate, attempt)
        item = _attempt_decision_for(threshold)
        assert threshold.acceptance_quota == expected_quota
        assert item.decision_word == word
        assert item.word_below_quota is accepted
        assert item.accepted is accepted
        assert item.extra_word_consumed is False


def test_first_success_prefix_and_bounded_exhaustion_truth_matrices(synthetic_cases):
    first = synthetic_cases["first"]
    assert first.outcome == "selected"
    assert first.evaluated_attempt_count == 1
    assert first.selected_attempt_index == 0
    assert first.succeeded is True
    assert first.budget_exhausted is False
    assert first.suffix_decision_words_uninterpreted is True
    later = synthetic_cases["later"]
    assert tuple(item.accepted for item in later.decisions) == (False, True)
    assert later.outcome == "selected"
    assert later.selected_attempt_index == 1
    assert later.selected_preparation_attempt is later.preparation_result.attempts[1]
    assert (
        later.selected_configuration
        is later.selected_preparation_attempt.canonical_configuration
    )
    assert later.suffix_decision_words_uninterpreted is False
    exhausted = synthetic_cases["exhausted"]
    assert tuple(item.accepted for item in exhausted.decisions) == (False, False)
    assert exhausted.outcome == "exhausted"
    assert exhausted.selected_attempt_index is None
    assert exhausted.selected_preparation_attempt is None
    assert exhausted.selected_configuration is None
    assert exhausted.succeeded is False
    assert exhausted.budget_exhausted is True


def test_conditional_product_probabilities_are_exact_reduced_fractions(synthetic_cases):
    first = synthetic_cases["first"]
    assert (
        Fraction(
            first.conditional_outcome_probability_numerator,
            first.conditional_outcome_probability_denominator,
        )
        == 1
    )
    quota = decision._floor_exp_uint64_quota(Fraction(-1)).quota
    later = synthetic_cases["later"]
    assert Fraction(
        later.conditional_outcome_probability_numerator,
        later.conditional_outcome_probability_denominator,
    ) == Fraction(D - quota, D)
    exhausted = synthetic_cases["exhausted"]
    assert Fraction(
        exhausted.conditional_outcome_probability_numerator,
        exhausted.conditional_outcome_probability_denominator,
    ) == Fraction(D - quota, D)
    assert decision._conditional_probability(later.thresholds, 1) == Fraction(
        D - quota, D
    )
    assert decision._conditional_probability(exhausted.thresholds, None) == Fraction(
        D - quota, D
    )


def test_live_result_replay_validation_uses_no_prepare_and_no_rng(live_bundle):
    owner = live_bundle["owner"]
    result = live_bundle["result"]
    counts = {"prepare": 0, "validate": 0}
    old_prepare_global = decision._PREP_PREPARE
    old_validate_global = decision._PREP_VALIDATE_RESULT
    old_prepare_owner = owner._preparation_prepare
    old_validate_owner = owner._preparation_validate_result

    def forbidden_prepare(*args, **kwargs):
        del args, kwargs
        counts["prepare"] += 1
        raise AssertionError("result validation must not prepare another CP36 batch")

    def counted_validate(parent_owner, parent, run_id, initialization_index):
        counts["validate"] += 1
        return old_validate_global(parent_owner, parent, run_id, initialization_index)

    decision._PREP_PREPARE = forbidden_prepare
    decision._PREP_VALIDATE_RESULT = counted_validate
    object.__setattr__(owner, "_preparation_prepare", forbidden_prepare)
    object.__setattr__(owner, "_preparation_validate_result", counted_validate)
    before = _rng_snapshot()
    try:
        checked = owner.validate_result(
            result, result.run_id, result.initialization_index
        )
    finally:
        decision._PREP_PREPARE = old_prepare_global
        decision._PREP_VALIDATE_RESULT = old_validate_global
        object.__setattr__(owner, "_preparation_prepare", old_prepare_owner)
        object.__setattr__(owner, "_preparation_validate_result", old_validate_owner)
    _assert_rng_unchanged(before)
    assert checked is result
    assert counts == {"prepare": 0, "validate": 1}


def test_matching_and_certificate_helpers_bind_exact_parent_policy_role(live_bundle):
    owner = live_bundle["owner"]
    parent = owner.preparation_owner
    assert (
        _MATCHING(
            parent,
            owner,
            decision_policy=DECISION_POLICY,
            decision_role_sha256=DECISION_ROLE,
        )
        is owner
    )
    assert (
        _VALIDATE_CERTIFICATE(
            parent,
            owner,
            decision_policy=DECISION_POLICY,
            decision_role_sha256=DECISION_ROLE,
        )
        is owner.certificate
    )
    with pytest.raises(ValueError, match="policy"):
        _MATCHING(
            parent,
            owner,
            decision_policy=DECISION_POLICY + "x",
            decision_role_sha256=DECISION_ROLE,
        )
    with pytest.raises(ValueError, match="role"):
        _MATCHING(
            parent,
            owner,
            decision_policy=DECISION_POLICY,
            decision_role_sha256="9" * 64,
        )


def test_certificate_parent_owner_runtime_identity_is_required(
    live_bundle, monkeypatch
):
    owner = live_bundle["owner"]
    certificate = owner.certificate
    monkeypatch.setattr(
        decision, "_validate_preparation_certificate", lambda value: value
    )
    values = _certificate_values(
        certificate,
        preparation_owner_runtime_identity=(
            certificate.preparation_owner_runtime_identity + 1
        ),
    )
    alien_certificate = _record(
        decision.CounterKeyedInitialTiltRejectionDecisionCertificate, values
    )
    alien_owner = _forge_owner(
        owner,
        _certificate=alien_certificate,
        _certificate_identity=alien_certificate,
        _certificate_snapshot=tuple(
            getattr(alien_certificate, name) for name in decision._certificate_fields()
        ),
    )
    object.__setattr__(
        alien_owner,
        "_certificate_snapshot_identity",
        alien_owner._certificate_snapshot,
    )
    monkeypatch.setattr(decision, "_validate_certificate", lambda value: value)
    with pytest.raises(ValueError, match="runtime identity"):
        alien_owner._live_certificate(alien_owner._owner_snapshot())


@pytest.mark.parametrize("value", (True, -1, 1 << 64, 1.0, "0", None))
def test_decide_request_preflight_rejects_before_preparation(live_bundle, value):
    with pytest.raises((TypeError, ValueError)):
        live_bundle["owner"].decide(value, 0)


def test_record_validators_refuse_boolean_integer_digest_order_and_identity_forgeries(
    live_bundle, synthetic_cases, monkeypatch
):
    certificate = live_bundle["owner"].certificate
    threshold = synthetic_cases["later"].thresholds[0]
    item = synthetic_cases["later"].decisions[0]
    result = synthetic_cases["later"]

    monkeypatch.setattr(
        decision, "_validate_preparation_certificate", lambda value: value
    )
    with pytest.raises(TypeError, match="exact Boolean"):
        decision._validate_certificate_values(
            _certificate_values(certificate, passed=1)
        )

    monkeypatch.setattr(decision, "_validate_certificate", lambda value: value)
    with pytest.raises(TypeError, match="exact integer"):
        values = _threshold_values(threshold, acceptance_quota=True)
        decision._validate_threshold_values(values)
    with pytest.raises(ValueError, match="digest"):
        values = _threshold_values(threshold)
        values["threshold_sha256"] = "f" * 64
        decision._validate_threshold_values(values)

    monkeypatch.setattr(
        decision, "_validate_threshold_values", lambda values, **kwargs: None
    )
    with pytest.raises(ValueError, match="identity"):
        alien_threshold = synthetic_cases["first"].thresholds[0]
        decision._validate_decision_values(
            _decision_values(
                item,
                threshold=alien_threshold,
                threshold_sha256=alien_threshold.threshold_sha256,
            )
        )
    with pytest.raises(TypeError, match="exact Boolean"):
        decision._validate_decision_values(_decision_values(item, accepted=1))

    monkeypatch.setattr(
        decision, "_preflight_preparation_result", lambda value, certificate: value
    )
    monkeypatch.setattr(
        decision, "_validate_decision_values", lambda values, **kwargs: None
    )
    with pytest.raises(ValueError, match="order"):
        wrong_order_thresholds = (
            _forged(result.thresholds[0], attempt_index=1),
            result.thresholds[1],
        )
        decision._validate_result_values(
            _result_values(result, thresholds=wrong_order_thresholds)
        )
    with pytest.raises(ValueError, match="identity"):
        alien = synthetic_cases["first"].decisions[0]
        decision._validate_result_values(
            _result_values(result, decisions=(alien, result.decisions[-1]))
        )


def test_resource_and_type_preflights_fail_closed_before_hostile_work(live_bundle):
    certificate = live_bundle["owner"].certificate
    attempt = live_bundle["result"].preparation_result.attempts[0]
    with pytest.raises(TypeError, match="exact integer"):
        decision._preflight_preparation_attempt(
            _forged(attempt, reserved_decision_raw64_word=True), name="attempt"
        )
    with pytest.raises(ValueError, match="frozen range"):
        decision._preflight_preparation_attempt(
            _forged(attempt, reserved_decision_raw64_word=D), name="attempt"
        )
    with pytest.raises(TypeError, match="SHA-256"):
        decision._preflight_preparation_attempt(
            _forged(attempt, attempt_sha256="short"), name="attempt"
        )
    with pytest.raises(ValueError, match="text resource"):
        decision._require_text("x" * 16_385, "", name="oversized")
    with pytest.raises(ValueError, match="tuple resource"):
        decision._exact_tuple((None,) * 3, name="oversized", maximum=2)
    with pytest.raises(TypeError, match="wrong exact CP36"):
        decision._preflight_preparation_result(object(), certificate=certificate)


def test_owner_callback_identity_seal_and_snapshot_custody_fail_closed(live_bundle):
    owner = live_bundle["owner"]
    with pytest.raises(ValueError, match="seal"):
        _forge_owner(owner, _sealed=False)._owner_snapshot()
    with pytest.raises(ValueError, match="cached callback"):
        _forge_owner(owner, _threshold_builder=lambda *args: None)._owner_snapshot()
    distinct_equal_role = DECISION_ROLE.encode("ascii").decode("ascii")
    assert (
        distinct_equal_role == DECISION_ROLE
        and distinct_equal_role is not DECISION_ROLE
    )
    with pytest.raises(ValueError, match="identity"):
        _forge_owner(owner, _decision_role_sha256=distinct_equal_role)._owner_snapshot()
    snapshot = owner._owner_snapshot()
    with pytest.raises(
        decision.PluginBridgeCounterKeyedInitialTiltRejectionDecisionError,
        match="changed during operation",
    ):
        owner._require_owner_snapshot(snapshot[:-1] + (object(),))


@pytest.mark.parametrize(
    "surface",
    ("certificate", "threshold", "decision", "result", "owner"),
)
def test_records_and_owner_are_sealed_nonpickle_and_nonsubclassable(
    live_bundle, surface
):
    values = {
        "certificate": live_bundle["owner"].certificate,
        "threshold": live_bundle["result"].thresholds[0],
        "decision": live_bundle["result"].decisions[0],
        "result": live_bundle["result"],
        "owner": live_bundle["owner"],
    }
    value = values[surface]
    with pytest.raises((AttributeError, TypeError)):
        value.passed = False
    with pytest.raises(TypeError, match="pickle"):
        pickle.dumps(value)
    with pytest.raises(TypeError):
        type("ForbiddenSubclass", (type(value),), {})


def test_public_constructors_are_token_sealed():
    for cls in (
        decision.CounterKeyedInitialTiltRejectionDecisionCertificate,
        decision.CounterKeyedInitialTiltRejectionThreshold,
        decision.CounterKeyedInitialTiltRejectionAttemptDecision,
        decision.CounterKeyedInitialTiltRejectionDecisionResult,
    ):
        with pytest.raises(TypeError, match="module-created"):
            cls(_construction_token=object())


def test_source_ast_enforces_two_phase_chronology_and_prohibits_extra_draws():
    source_path = Path(decision.__file__)
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                calls.append((node.func.value, node.func.attr))
            elif isinstance(node.func, ast.Name):
                calls.append((None, node.func.id))
    forbidden_attributes = {
        "random",
        "rand",
        "randint",
        "randrange",
        "uniform",
        "manual_seed",
        "seed",
    }
    assert not any(attribute in forbidden_attributes for _, attribute in calls)
    assert not any(
        isinstance(owner, ast.Name) and owner.id == "math" and attribute == "exp"
        for owner, attribute in calls
    )
    assert not any(
        name
        in {
            "draw_word",
            "draw_words",
            "allocate_words",
            "next_word",
            "getrandbits",
        }
        for owner, name in calls
        if owner is None
    )
    owner_class = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "CounterKeyedInitialTiltRejectionDecisionOwner"
    )
    decide_node = next(
        node
        for node in owner_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "decide"
    )
    prepare_calls = [
        node
        for node in ast.walk(decide_node)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "_preparation_prepare"
    ]
    assert len(prepare_calls) == 1
    threshold_loop = next(
        node
        for node in decide_node.body
        if isinstance(node, ast.For)
        and any(
            isinstance(item, ast.Call)
            and isinstance(item.func, ast.Attribute)
            and item.func.attr == "_threshold_builder"
            for item in ast.walk(node)
        )
    )
    decision_loop = next(
        node
        for node in decide_node.body
        if isinstance(node, ast.For)
        and any(
            isinstance(item, ast.Call)
            and isinstance(item.func, ast.Attribute)
            and item.func.attr == "_decision_builder"
            for item in ast.walk(node)
        )
    )
    assert threshold_loop.lineno < decision_loop.lineno


def test_module_is_not_reexported_from_dependency_light_process_package():
    import heterodiff.processes as processes

    assert not hasattr(
        processes,
        "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_decision",
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
                "rejection_decision"
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
