"""Hostile tests for checkpoint-42 staged predecision factorization."""

import ast
import importlib
import inspect
import os
from pathlib import Path
import pickle
import random
import subprocess
import sys

import numpy as np
import pytest


torch = pytest.importorskip(
    "torch", reason="staged predecision factorization requires PyTorch"
)

factorization = importlib.import_module(  # noqa: E402
    "heterodiff.processes.plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "predecision_factorization"
)
checkpoint41 = importlib.import_module(  # noqa: E402
    "tests.unit.test_plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "failure_aware_source_law"
)


ROLE = "2" * 64
MAX_UINT64 = (1 << 64) - 1
POLICY = getattr(
    factorization,
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_PREDECISION_"
    "FACTORIZATION_POLICY",
)
_CERTIFY = getattr(
    factorization,
    "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "predecision_factorization",
)
_MATCHING = getattr(
    factorization,
    "require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "predecision_factorization",
)
_VALIDATE_CERTIFICATE = getattr(
    factorization,
    "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "predecision_factorization_certificate",
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


def _forged(record, **updates):
    forged = object.__new__(type(record))
    for name in type(record).__annotations__:
        object.__setattr__(forged, name, updates.get(name, getattr(record, name)))
    return forged


def _forge_owner(owner, **updates):
    forged = object.__new__(type(owner))
    for name in type(owner).__slots__:
        object.__setattr__(forged, name, updates.get(name, getattr(owner, name)))
    return forged


def _redigested(record, fields, payload, digest_name, **updates):
    values = {name: updates.get(name, getattr(record, name)) for name in fields()}
    values[digest_name] = "0" * 64
    values[digest_name] = factorization._semantic_digest(payload(values))
    return _forged(record, **values)


class _TouchBomb:
    def __init__(self):
        self.calls = 0

    def _touched(self, operation):
        self.calls += 1
        raise AssertionError("hostile object was touched by " + operation)

    def __iter__(self):
        return self._touched("iteration")

    def __len__(self):
        return self._touched("length")

    def __eq__(self, other):
        del other
        return self._touched("equality")

    def __ne__(self, other):
        del other
        return self._touched("inequality")

    def __lt__(self, other):
        del other
        return self._touched("ordering")

    def __float__(self):
        return self._touched("float conversion")

    def __index__(self):
        return self._touched("index conversion")

    def model_key(self):
        return self._touched("model-key lookup")


def _certify(parent_bundle, *, role=ROLE):
    return _CERTIFY(
        parent_bundle["source_law_owner"],
        factorization_policy=POLICY,
        factorization_role_sha256=role,
    )


def _one_attempt_parent():
    bundle = checkpoint41._certification_only_lineage()
    admission_owner = bundle["admission_owner"]
    hypothesis = checkpoint41._DECLARE(
        admission_owner,
        hypothesis_scope=getattr(
            checkpoint41.source_law,
            "INITIAL_TILT_REJECTION_PREDECISION_FACTORIZATION_" "HYPOTHESIS_SCOPE",
        ),
        factorization_premise=getattr(
            checkpoint41.source_law,
            "INITIAL_TILT_REJECTION_FAILURE_AWARE_FACTORIZATION_PREMISE",
        ),
    )
    owner = checkpoint41._CERTIFY(
        admission_owner,
        hypothesis,
        source_law_policy=checkpoint41.SOURCE_POLICY,
        source_law_role_sha256=checkpoint41.SOURCE_ROLE,
    )
    return {
        **bundle,
        "factorization_hypothesis": hypothesis,
        "source_law_owner": owner,
        "specification": owner.describe(),
    }


def _two_attempt_parent(one_attempt):
    checkpoint40 = checkpoint41.checkpoint40
    checkpoint39 = checkpoint40.checkpoint39
    checkpoint38 = checkpoint39.checkpoint38
    checkpoint37 = checkpoint38.checkpoint37
    checkpoint36 = checkpoint38.checkpoint36
    _, preparation_owner = checkpoint36._certify(
        one_attempt,
        attempt_budget=2,
        role="b" * 64,
    )
    decision_owner = checkpoint37._CERTIFY(
        preparation_owner,
        decision_policy=checkpoint37.DECISION_POLICY,
        decision_role_sha256="c" * 64,
    )
    word_hypothesis = checkpoint38._DECLARE(
        hypothesis_scope=getattr(
            checkpoint38.law,
            "FIXED_BATCH_IID_UINT64_DECISION_WORD_HYPOTHESIS_SCOPE",
        ),
        word_source_premise=(
            checkpoint38.law.FIXED_BATCH_IID_UINT64_DECISION_WORD_PREMISE
        ),
    )
    finite_batch_owner = checkpoint38._CERTIFY(
        decision_owner,
        word_hypothesis,
        law_policy=checkpoint38.LAW_POLICY,
        law_role_sha256="d" * 64,
    )
    coordination_owner = checkpoint39._CERTIFY(
        finite_batch_owner,
        coordination_policy=checkpoint39.COORDINATION_POLICY,
        coordination_role_sha256="e" * 64,
    )
    admission_owner = checkpoint40._CERTIFY(
        coordination_owner,
        admission_policy=checkpoint40.ADMISSION_POLICY,
        admission_role_sha256="f" * 64,
    )
    factorization_hypothesis = checkpoint41._DECLARE(
        admission_owner,
        hypothesis_scope=getattr(
            checkpoint41.source_law,
            "INITIAL_TILT_REJECTION_PREDECISION_FACTORIZATION_" "HYPOTHESIS_SCOPE",
        ),
        factorization_premise=getattr(
            checkpoint41.source_law,
            "INITIAL_TILT_REJECTION_FAILURE_AWARE_FACTORIZATION_PREMISE",
        ),
    )
    source_law_owner = checkpoint41._CERTIFY(
        admission_owner,
        factorization_hypothesis,
        source_law_policy=checkpoint41.SOURCE_POLICY,
        source_law_role_sha256="1" * 64,
    )
    return {
        "preparation_owner": preparation_owner,
        "decision_owner": decision_owner,
        "finite_batch_owner": finite_batch_owner,
        "coordination_owner": coordination_owner,
        "admission_owner": admission_owner,
        "factorization_hypothesis": factorization_hypothesis,
        "source_law_owner": source_law_owner,
        "specification": source_law_owner.describe(),
    }


@pytest.fixture(scope="module")
def one_attempt_bundle():
    before = _rng_snapshot()
    parent = _one_attempt_parent()
    owner = _certify(parent)
    _assert_rng_unchanged(before)
    return {**parent, "factorization_owner": owner}


@pytest.fixture(scope="module")
def two_attempt_bundle(one_attempt_bundle):
    before = _rng_snapshot()
    parent = _two_attempt_parent(one_attempt_bundle)
    owner = _certify(parent, role="3" * 64)
    _assert_rng_unchanged(before)
    return {**parent, "factorization_owner": owner}


@pytest.fixture(scope="module")
def live_checkpoint37(one_attempt_bundle):
    decision_owner = one_attempt_bundle["decision_owner"]
    before = _rng_snapshot()
    live = decision_owner.decide(42_002, 9)
    preparation = live.preparation_result
    proposal_words = tuple(
        word
        for attempt in preparation.attempts
        for word in attempt.proposal_concatenated_raw64_words
    )
    decision_words = tuple(
        attempt.reserved_decision_raw64_word for attempt in preparation.attempts
    )
    _assert_rng_unchanged(before)
    return {
        "live": live,
        "proposal_words": proposal_words,
        "decision_words": decision_words,
    }


@pytest.fixture(scope="module")
def one_predecision_evidence(one_attempt_bundle, live_checkpoint37):
    owner = one_attempt_bundle["factorization_owner"]
    before = _rng_snapshot()

    def evaluate():
        return owner.evaluate_predecision(
            live_checkpoint37["live"].run_id,
            live_checkpoint37["live"].initialization_index,
            live_checkpoint37["proposal_words"],
        )

    result, calls = checkpoint41._profile_parent_operations(evaluate)
    _assert_rng_unchanged(before)
    return {"result": result, "profile_calls": calls}


@pytest.fixture(scope="module")
def one_predecision(one_predecision_evidence):
    return one_predecision_evidence["result"]


@pytest.fixture(scope="module")
def validated_predecision_evidence(one_attempt_bundle, one_predecision):
    owner = one_attempt_bundle["factorization_owner"]
    before = _rng_snapshot()
    checked, calls = checkpoint41._profile_parent_operations(
        lambda: owner.validate_predecision_result(one_predecision)
    )
    assert checked is one_predecision
    _assert_rng_unchanged(before)
    return {"result": checked, "profile_calls": calls}


@pytest.fixture(scope="module")
def validated_predecision(validated_predecision_evidence):
    return validated_predecision_evidence["result"]


@pytest.fixture(scope="module")
def two_predecision_evidence(two_attempt_bundle):
    owner = two_attempt_bundle["factorization_owner"]
    words = (0,) * owner.certificate.proposal_word_count
    before = _rng_snapshot()
    result, calls = checkpoint41._profile_parent_operations(
        lambda: owner.evaluate_predecision(42_001, 8, words)
    )
    _assert_rng_unchanged(before)
    return {"result": result, "profile_calls": calls}


@pytest.fixture(scope="module")
def two_predecision(two_predecision_evidence):
    return two_predecision_evidence["result"]


@pytest.fixture(scope="module")
def selected_applied_evidence(one_attempt_bundle, one_predecision):
    owner = one_attempt_bundle["factorization_owner"]
    quota = one_predecision.rows[0].acceptance_quota
    assert 0 < quota <= (1 << 64)
    words = (quota - 1,)
    before = _rng_snapshot()

    def apply_and_validate():
        result = owner.apply_decision_words(one_predecision, words)
        assert owner.validate_applied_decision(result) is result
        return result

    result, calls = checkpoint41._profile_parent_operations(apply_and_validate)
    assert result.status == "selected"
    assert result.selected_attempt_index == 0
    _assert_rng_unchanged(before)
    return {"result": result, "profile_calls": calls}


@pytest.fixture(scope="module")
def selected_applied(selected_applied_evidence):
    return selected_applied_evidence["result"]


@pytest.fixture(scope="module")
def live_parity(one_attempt_bundle, live_checkpoint37, one_predecision):
    owner = one_attempt_bundle["factorization_owner"]
    before = _rng_snapshot()
    live = live_checkpoint37["live"]
    decision_words = live_checkpoint37["decision_words"]
    applied = factorization._make_applied_decision(
        owner.certificate,
        one_predecision,
        decision_words,
    )
    assert (
        factorization._validate_applied_record(
            applied,
            trusted_certificate=owner.certificate,
        )
        is applied
    )

    def witness_and_validate():
        witness = owner.witness_successful_parity(one_predecision, live)
        assert owner.validate_successful_parity_witness(witness) is witness
        return witness

    witness, calls = checkpoint41._profile_parent_operations(witness_and_validate)
    _assert_rng_unchanged(before)
    return {
        "live": live,
        "proposal_words": live_checkpoint37["proposal_words"],
        "decision_words": decision_words,
        "predecision": one_predecision,
        "applied": applied,
        "witness": witness,
        "profile_calls": calls,
    }


def test_public_api_and_staged_signatures_exclude_decision_words_from_g(
    one_attempt_bundle,
    one_predecision,
    validated_predecision,
):
    owner = one_attempt_bundle["factorization_owner"]
    assert validated_predecision is one_predecision
    expected_classes = {
        "CounterKeyedInitialTiltRejectionPredecisionFactorizationCertificate",
        "CounterKeyedInitialTiltRejectionPredecisionRow",
        "CounterKeyedInitialTiltRejectionPredecisionResult",
        "CounterKeyedInitialTiltRejectionAppliedDecision",
        "CounterKeyedInitialTiltRejectionSuccessfulParityWitness",
        "CounterKeyedInitialTiltRejectionPredecisionFactorizationOwner",
    }
    expected_functions = {
        "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_"
        "predecision_factorization",
        "require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_"
        "predecision_factorization",
        "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_"
        "predecision_factorization_certificate",
    }
    assert expected_classes | expected_functions <= set(factorization.__all__)
    assert len(factorization.__all__) == len(set(factorization.__all__))
    assert all(hasattr(factorization, name) for name in factorization.__all__)
    assert _CERTIFY is getattr(
        factorization,
        "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_"
        "predecision_factorization",
    )
    assert _MATCHING is getattr(
        factorization,
        "require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_"
        "predecision_factorization",
    )
    assert _VALIDATE_CERTIFICATE is getattr(
        factorization,
        "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_"
        "predecision_factorization_certificate",
    )
    assert factorization.INITIAL_TILT_REJECTION_PREDECISION_STATUSES == (
        "preparation_failure",
        "quota_certification_failure",
        "ready",
    )
    assert factorization.INITIAL_TILT_REJECTION_APPLIED_DECISION_STATUSES == (
        "preparation_failure",
        "quota_certification_failure",
        "selected",
        "exhausted",
    )

    assert tuple(inspect.signature(owner.evaluate_predecision).parameters) == (
        "run_id",
        "initialization_index",
        "proposal_words",
    )
    assert (
        "decision_words" not in inspect.signature(owner.evaluate_predecision).parameters
    )
    assert tuple(inspect.signature(owner.validate_predecision_result).parameters) == (
        "result",
    )
    assert tuple(inspect.signature(owner.apply_decision_words).parameters) == (
        "predecision_result",
        "decision_words",
    )
    assert tuple(inspect.signature(owner.validate_applied_decision).parameters) == (
        "result",
    )
    assert tuple(inspect.signature(owner.witness_successful_parity).parameters) == (
        "predecision_result",
        "checkpoint37_result",
    )
    assert tuple(
        inspect.signature(owner.validate_successful_parity_witness).parameters
    ) == ("witness",)

    for function in (_CERTIFY, _MATCHING, _VALIDATE_CERTIFICATE):
        parameters = inspect.signature(function).parameters
        assert parameters["factorization_policy"].kind is (
            inspect.Parameter.KEYWORD_ONLY
        )
        assert parameters["factorization_role_sha256"].kind is (
            inspect.Parameter.KEYWORD_ONLY
        )
    assert (
        _MATCHING(
            one_attempt_bundle["source_law_owner"],
            owner,
            factorization_policy=POLICY,
            factorization_role_sha256=ROLE,
        )
        is owner
    )
    assert (
        _VALIDATE_CERTIFICATE(
            one_attempt_bundle["source_law_owner"],
            owner,
            factorization_policy=POLICY,
            factorization_role_sha256=ROLE,
        )
        is owner.certificate
    )


def test_a1_and_a2_certificates_bind_the_cp41_partition_and_interleaving(
    one_attempt_bundle,
    two_attempt_bundle,
):
    one = one_attempt_bundle["factorization_owner"].certificate
    one_parent = one_attempt_bundle["specification"]
    assert one.attempt_budget == 1
    assert one.proposal_words_per_attempt == 3
    assert one.proposal_word_count == 3
    assert one.decision_word_count == 1
    assert one.proposal_word_coordinates == one_parent.proposal_word_coordinates
    assert one.decision_word_coordinates == one_parent.decision_word_coordinates
    assert one_parent.full_logical_word_coordinates == (
        one.proposal_word_coordinates + one.decision_word_coordinates
    )

    two = two_attempt_bundle["factorization_owner"].certificate
    two_parent = two_attempt_bundle["specification"]
    full = two_parent.full_logical_word_coordinates
    assert two.attempt_budget == 2
    assert two.proposal_words_per_attempt == 3
    assert two.proposal_word_count == 6
    assert two.decision_word_count == 2
    assert two.proposal_word_coordinates == (
        full[0],
        full[1],
        full[2],
        full[4],
        full[5],
        full[6],
    )
    assert two.decision_word_coordinates == (full[3], full[7])
    assert two.proposal_word_coordinates + two.decision_word_coordinates != full
    assert set(two.proposal_word_coordinates).isdisjoint(two.decision_word_coordinates)
    assert set(two.proposal_word_coordinates) | set(
        two.decision_word_coordinates
    ) == set(full)


def test_g_is_w_free_and_h_uses_exact_half_open_quota_boundaries(
    two_attempt_bundle,
    two_predecision,
):
    owner = two_attempt_bundle["factorization_owner"]
    assert two_predecision.status == "ready"
    assert len(two_predecision.rows) == owner.certificate.attempt_budget == 2
    assert two_predecision.all_attempts_scored_before_quota_stage is True
    assert two_predecision.all_ready_quotas_complete is True
    assert two_predecision.reserved_decision_words_present is False
    assert all(0 < row.acceptance_quota < (1 << 64) for row in two_predecision.rows)

    certificate = owner.certificate
    first_quota, second_quota = (row.acceptance_quota for row in two_predecision.rows)
    selected = factorization._make_applied_decision(
        certificate,
        two_predecision,
        (first_quota - 1, MAX_UINT64),
    )
    assert (
        factorization._validate_applied_record(
            selected,
            trusted_certificate=certificate,
        )
        is selected
    )
    assert selected.status == "selected"
    assert selected.selected_attempt_index == 0
    assert selected.comparison_count == 1
    assert selected.predecision_result is two_predecision

    selected_second = factorization._make_applied_decision(
        certificate,
        two_predecision,
        (first_quota, second_quota - 1),
    )
    assert (
        factorization._validate_applied_record(
            selected_second,
            trusted_certificate=certificate,
        )
        is selected_second
    )
    assert selected_second.status == "selected"
    assert selected_second.selected_attempt_index == 1
    assert selected_second.comparison_count == 2
    assert selected_second.predecision_result is two_predecision

    exhausted = factorization._make_applied_decision(
        certificate,
        two_predecision,
        (first_quota, second_quota),
    )
    assert (
        factorization._validate_applied_record(
            exhausted,
            trusted_certificate=certificate,
        )
        is exhausted
    )
    assert exhausted.status == "exhausted"
    assert exhausted.selected_attempt_index is None
    assert exhausted.comparison_count == 2
    assert exhausted.predecision_result is two_predecision
    assert selected.predecision_result_sha256 == exhausted.predecision_result_sha256
    assert selected.predecision_result_sha256 == two_predecision.result_sha256
    assert selected_second.predecision_result_sha256 == two_predecision.result_sha256


def test_ready_h_preflights_every_decision_word_before_first_comparison(
    two_attempt_bundle,
    two_predecision,
):
    owner = two_attempt_bundle["factorization_owner"]
    certificate = owner.certificate
    first_quota = two_predecision.rows[0].acceptance_quota
    assert first_quota > 0
    with pytest.raises(TypeError, match=r"decision_words\[1\]|exact integer"):
        factorization._make_applied_decision(
            certificate,
            two_predecision,
            (first_quota - 1, True),
        )
    invalid = (
        [0, 0],
        (0,),
        (0, 0, 0),
        (-1, 0),
        (MAX_UINT64 + 1, 0),
        (np.uint64(0), 0),
    )
    for words in invalid:
        with pytest.raises((TypeError, ValueError), match="tuple|length|integer|word"):
            factorization._make_applied_decision(
                certificate,
                two_predecision,
                words,
            )


def test_pure_h_passes_modeled_quota_failure_without_touching_w_but_public_h_replays(
    one_attempt_bundle,
    one_predecision,
):
    owner = one_attempt_bundle["factorization_owner"]
    certificate = owner.certificate
    failure = factorization._make_predecision_result(
        certificate,
        one_predecision.run_id,
        one_predecision.initialization_index,
        one_predecision.proposal_words,
        "quota_certification_failure",
        (),
    )
    assert failure.status == "quota_certification_failure"
    assert failure.rows == ()
    assert failure.all_ready_quotas_complete is False

    bomb = _TouchBomb()
    applied = factorization._make_applied_decision(certificate, failure, bomb)
    assert (
        factorization._validate_applied_record(
            applied,
            trusted_certificate=certificate,
        )
        is applied
    )
    assert applied.status == "quota_certification_failure"
    assert applied.decision_words is None
    assert applied.decision_words_sha256 is None
    assert applied.comparison_count == 0
    assert applied.failure_passed_through_without_decision_word_access is True
    assert bomb.calls == 0

    public_bomb = _TouchBomb()
    with pytest.raises(ValueError, match="replay|V-only"):
        owner.apply_decision_words(failure, public_bomb)
    assert public_bomb.calls == 0
    assert certificate.preparation_failure_branch_executable is False
    assert certificate.numeric_failure_probability_materialized is False

    reserved_values = {
        name: getattr(one_predecision, name)
        for name in factorization._predecision_fields()
    }
    reserved_values.update(
        status="preparation_failure",
        rows=(),
        row_sha256s=(),
        all_ready_quotas_complete=False,
        semantic_predecision_sha256=(
            factorization._semantic_predecision_sha256(
                "preparation_failure",
                (),
            )
        ),
        result_sha256="0" * 64,
    )
    reserved_values["result_sha256"] = factorization._semantic_digest(
        factorization._predecision_payload(reserved_values)
    )
    reserved = _forged(one_predecision, **reserved_values)
    with pytest.raises(ValueError, match="reserved preparation_failure"):
        factorization._validate_predecision_record(
            reserved,
            trusted_certificate=certificate,
        )


def test_word_free_row_and_semantic_projection_contain_no_w_bound_parent_data(
    two_attempt_bundle,
    two_predecision,
):
    row_fields = set(
        factorization.CounterKeyedInitialTiltRejectionPredecisionRow.__annotations__
    )
    forbidden_fragments = (
        "decision_word",
        "reserved_decision",
        "preparation_result",
        "preparation_attempt",
        "threshold_sha256",
        "checkpoint36_result",
        "checkpoint37_result",
    )
    assert not any(
        fragment in name for name in row_fields for fragment in forbidden_fragments
    )
    for row in two_predecision.rows:
        values = {name: getattr(row, name) for name in factorization._row_fields()}
        payload = factorization._row_payload(values)
        assert not any(
            fragment in name for name in payload for fragment in forbidden_fragments
        )

    owner = two_attempt_bundle["factorization_owner"]
    certificate = owner.certificate
    quotas = tuple(row.acceptance_quota for row in two_predecision.rows)
    selected = factorization._make_applied_decision(
        certificate,
        two_predecision,
        (quotas[0] - 1, MAX_UINT64),
    )
    exhausted = factorization._make_applied_decision(
        certificate,
        two_predecision,
        quotas,
    )
    for result in (selected, exhausted):
        assert (
            factorization._validate_applied_record(
                result,
                trusted_certificate=certificate,
            )
            is result
        )
    assert selected.predecision_result is two_predecision
    assert exhausted.predecision_result is two_predecision
    assert selected.predecision_result_sha256 == exhausted.predecision_result_sha256
    assert two_predecision.semantic_predecision_sha256 == (
        factorization._semantic_predecision_sha256("ready", two_predecision.rows)
    )


def test_successful_live_cp36_cp37_projection_parity_is_finite_not_universal(
    live_parity,
):
    live = live_parity["live"]
    predecision = live_parity["predecision"]
    applied = live_parity["applied"]
    witness = live_parity["witness"]
    preparation = live.preparation_result
    assert predecision.status == "ready"
    assert predecision.proposal_words == live_parity["proposal_words"]
    assert len(predecision.rows) == len(preparation.attempts) == len(live.thresholds)

    common_threshold_fields = (
        "threshold_branch",
        "decimal_precision_used",
        "ideal_probability_lower_numerator",
        "ideal_probability_lower_denominator",
        "ideal_probability_upper_numerator",
        "ideal_probability_upper_denominator",
        "ideal_probability_upper_strict",
        "acceptance_quota",
        "quota_probability_numerator",
        "quota_probability_denominator",
        "ideal_minus_quota_error_strict_upper_numerator",
        "ideal_minus_quota_error_strict_upper_denominator",
    )
    for position, (row, attempt, threshold) in enumerate(
        zip(predecision.rows, preparation.attempts, live.thresholds)
    ):
        assert row.attempt_index == attempt.attempt_index == position
        assert row.canonical_configuration_sha256 == (
            attempt.canonical_configuration_sha256
        )
        assert row.delta_numerator == attempt.q_minus_upper_bound_numerator
        assert row.delta_denominator == attempt.q_minus_upper_bound_denominator
        for name in common_threshold_fields:
            assert getattr(row, name) == getattr(threshold, name)

    assert applied.status == live.outcome
    assert applied.comparison_count == live.evaluated_attempt_count
    assert applied.selected_attempt_index == live.selected_attempt_index
    assert applied.selected_configuration_sha256 == live.selected_configuration_sha256
    assert witness.successful_projection_equal is True
    assert witness.universal_equivalence_claimed is False
    assert witness.live_failure_equivalence_claimed is False


def test_cp42_operations_do_not_invoke_cp36_through_cp40_operational_methods(
    one_attempt_bundle,
    one_predecision_evidence,
    validated_predecision_evidence,
    two_predecision_evidence,
    selected_applied_evidence,
    live_parity,
):
    owner = one_attempt_bundle["factorization_owner"]
    predecision = live_parity["predecision"]
    decision_words = live_parity["decision_words"]

    def pure_h_operations():
        applied = factorization._make_applied_decision(
            owner.certificate,
            predecision,
            decision_words,
        )
        return factorization._validate_applied_record(
            applied,
            trusted_certificate=owner.certificate,
        )

    before = _rng_snapshot()
    _, pure_h_calls = checkpoint41._profile_parent_operations(pure_h_operations)
    _assert_rng_unchanged(before)
    expected = {
        "admit": 0,
        "coordinate": 0,
        "resolve": 0,
        "decide": 0,
        "prepare": 0,
    }
    for calls in (
        one_predecision_evidence["profile_calls"],
        validated_predecision_evidence["profile_calls"],
        two_predecision_evidence["profile_calls"],
        selected_applied_evidence["profile_calls"],
        live_parity["profile_calls"],
        pure_h_calls,
    ):
        assert calls == expected


def test_all_records_and_owner_are_sealed_frozen_nonpickle_and_nonsubclass(
    one_attempt_bundle,
    one_predecision,
    selected_applied,
    live_parity,
):
    owner = one_attempt_bundle["factorization_owner"]
    records = (
        owner.certificate,
        one_predecision.rows[0],
        one_predecision,
        selected_applied,
        live_parity["witness"],
    )
    for record in records:
        field = next(iter(type(record).__annotations__))
        with pytest.raises((AttributeError, TypeError)):
            setattr(record, field, getattr(record, field))
        with pytest.raises(TypeError):
            pickle.dumps(record)
        with pytest.raises(TypeError):
            type(record)(_construction_token=object())
        with pytest.raises(TypeError):
            type("ForbiddenRecordSubclass", (type(record),), {})

    with pytest.raises(AttributeError):
        owner._certificate = owner.certificate
    with pytest.raises(AttributeError):
        del owner._certificate
    with pytest.raises(TypeError):
        pickle.dumps(owner)
    owner_type = getattr(
        factorization,
        "CounterKeyedInitialTiltRejectionPredecisionFactorizationOwner",
    )
    with pytest.raises(TypeError):
        type(
            "ForbiddenOwnerSubclass",
            (owner_type,),
            {},
        )


def test_redigested_semantic_forgery_is_rejected_at_every_record_layer(
    one_attempt_bundle,
    one_predecision,
    selected_applied,
    live_parity,
):
    owner = one_attempt_bundle["factorization_owner"]
    certificate = owner.certificate
    promoted_certificate = _redigested(
        certificate,
        factorization._certificate_fields,
        factorization._certificate_payload,
        "certificate_sha256",
        checkpoint41_factorization_assumption_discharged=True,
    )
    with pytest.raises(ValueError, match="differs|discharged"):
        factorization._validate_certificate(promoted_certificate)

    row = one_predecision.rows[0]
    forged_row = _redigested(
        row,
        factorization._row_fields,
        factorization._row_payload,
        "row_sha256",
        acceptance_quota=row.acceptance_quota - 1,
    )
    with pytest.raises(ValueError, match="acceptance_quota|row.*differs"):
        factorization._validate_row(
            forged_row,
            trusted_certificate=certificate,
        )

    forged_predecision = _redigested(
        one_predecision,
        factorization._predecision_fields,
        factorization._predecision_payload,
        "result_sha256",
        live_failure_equivalence_claimed=True,
    )
    with pytest.raises(ValueError, match="live_failure|differs"):
        owner.validate_predecision_result(forged_predecision)

    forged_applied = _redigested(
        selected_applied,
        factorization._applied_fields,
        factorization._applied_payload,
        "applied_decision_sha256",
        status="exhausted",
    )
    with pytest.raises(ValueError, match="status|selection|exhaustion"):
        owner.validate_applied_decision(forged_applied)

    witness = live_parity["witness"]
    forged_witness = _redigested(
        witness,
        factorization._witness_fields,
        factorization._witness_payload,
        "witness_sha256",
        universal_equivalence_claimed=True,
    )
    with pytest.raises(ValueError, match="universal_equivalence|differs"):
        owner.validate_successful_parity_witness(forged_witness)


def test_redigested_a2_row_reordering_is_not_a_valid_ready_predecision(
    two_attempt_bundle,
    two_predecision,
):
    rows = tuple(reversed(two_predecision.rows))
    values = {
        name: getattr(two_predecision, name)
        for name in factorization._predecision_fields()
    }
    values.update(
        rows=rows,
        row_sha256s=tuple(row.row_sha256 for row in rows),
        semantic_predecision_sha256=(
            factorization._semantic_predecision_sha256("ready", rows)
        ),
        result_sha256="0" * 64,
    )
    values["result_sha256"] = factorization._semantic_digest(
        factorization._predecision_payload(values)
    )
    forged = _forged(two_predecision, **values)
    with pytest.raises(ValueError, match="chronology"):
        two_attempt_bundle["factorization_owner"].validate_predecision_result(forged)


def test_same_digest_cross_owner_certificate_and_records_are_refused(
    one_attempt_bundle,
    one_predecision,
    selected_applied,
):
    first = one_attempt_bundle["factorization_owner"]
    second = _certify(one_attempt_bundle)
    assert second is not first
    assert second.certificate is not first.certificate
    assert second.certificate.certificate_sha256 == (
        first.certificate.certificate_sha256
    )
    assert (
        _MATCHING(
            one_attempt_bundle["source_law_owner"],
            second,
            factorization_policy=POLICY,
            factorization_role_sha256=ROLE,
        )
        is second
    )

    foreign_predecision = factorization._make_predecision_result(
        second.certificate,
        one_predecision.run_id,
        one_predecision.initialization_index,
        one_predecision.proposal_words,
        one_predecision.status,
        one_predecision.rows,
    )
    assert (
        factorization._validate_predecision_record(
            foreign_predecision,
            trusted_certificate=second.certificate,
        )
        is foreign_predecision
    )
    assert foreign_predecision.result_sha256 == one_predecision.result_sha256
    assert foreign_predecision.certificate is second.certificate
    with pytest.raises(ValueError, match="certificate identity|another"):
        first.validate_predecision_result(foreign_predecision)

    same_digest_splice = _forged(
        one_predecision,
        certificate=second.certificate,
    )
    assert same_digest_splice.result_sha256 == one_predecision.result_sha256
    with pytest.raises(ValueError, match="certificate identity|another"):
        first.validate_predecision_result(same_digest_splice)

    foreign_applied = factorization._make_applied_decision(
        second.certificate,
        foreign_predecision,
        selected_applied.decision_words,
    )
    assert (
        factorization._validate_applied_record(
            foreign_applied,
            trusted_certificate=second.certificate,
        )
        is foreign_applied
    )
    assert foreign_applied.applied_decision_sha256 == (
        selected_applied.applied_decision_sha256
    )
    with pytest.raises(ValueError, match="certificate identity|another"):
        first.validate_applied_decision(foreign_applied)


def test_forged_cached_callback_is_refused_before_hostile_execution(
    one_attempt_bundle,
    one_predecision,
):
    owner = one_attempt_bundle["factorization_owner"]
    calls = {"callback": 0}

    def forbidden(*args, **kwargs):
        del args, kwargs
        calls["callback"] += 1
        raise AssertionError("substituted callback executed")

    forged = _forge_owner(owner, _predecision_builder=forbidden)
    with pytest.raises(ValueError, match="cached callback changed"):
        forged.evaluate_predecision(
            one_predecision.run_id,
            one_predecision.initialization_index,
            one_predecision.proposal_words,
        )
    assert calls == {"callback": 0}


def test_forged_two_slot_surface_guard_is_refused_before_hostile_execution(
    one_attempt_bundle,
    one_predecision,
):
    owner = one_attempt_bundle["factorization_owner"]
    calls = {"guard": 0}

    def forbidden(*args, **kwargs):
        del args, kwargs
        calls["guard"] += 1
        raise AssertionError("forged two-slot surface guard executed")

    forged = _forge_owner(
        owner,
        _surface_guard=forbidden,
        _surface_guard_identity=forbidden,
    )
    with pytest.raises(ValueError, match="surface guard|guard identity"):
        forged.validate_predecision_result(one_predecision)
    assert calls == {"guard": 0}


def test_local_global_surface_mutation_is_refused_before_hostile_execution(
    one_attempt_bundle,
    one_predecision,
):
    owner = one_attempt_bundle["factorization_owner"]
    calls = {"surface": 0}

    def forbidden(*args, **kwargs):
        del args, kwargs
        calls["surface"] += 1
        raise AssertionError("substituted local surface executed")

    original = factorization._semantic_digest
    factorization._semantic_digest = forbidden
    try:
        with pytest.raises(ValueError, match="surface|changed"):
            owner.validate_predecision_result(one_predecision)
    finally:
        factorization._semantic_digest = original
    assert calls == {"surface": 0}


def test_dependency_global_and_class_mutation_fail_before_hostile_execution(
    one_attempt_bundle,
    one_predecision,
    live_parity,
):
    owner = one_attempt_bundle["factorization_owner"]
    calls = {"dependency": 0}

    def forbidden(*args, **kwargs):
        del args, kwargs
        calls["dependency"] += 1
        raise AssertionError("substituted dependency executed")

    original_global = factorization._decision._floor_exp_uint64_quota
    factorization._decision._floor_exp_uint64_quota = forbidden
    try:
        with pytest.raises(ValueError, match="provider surface|changed"):
            owner.validate_predecision_result(one_predecision)
    finally:
        factorization._decision._floor_exp_uint64_quota = original_global

    for name in ("_QuotaData", "_nonnegative_integer_decimal_digits"):
        original_quota_surface = getattr(factorization._decision, name)
        setattr(factorization._decision, name, forbidden)
        try:
            with pytest.raises(ValueError, match="provider surface|changed"):
                owner.validate_predecision_result(one_predecision)
        finally:
            setattr(factorization._decision, name, original_quota_surface)

    original_class = factorization._CP37_OWNER_TYPE.validate_result
    factorization._CP37_OWNER_TYPE.validate_result = forbidden
    try:
        with pytest.raises(ValueError, match="surface|changed"):
            owner.validate_successful_parity_witness(live_parity["witness"])
    finally:
        factorization._CP37_OWNER_TYPE.validate_result = original_class
    assert calls == {"dependency": 0}


def test_held_operation_detects_late_surface_guard_replacement_unexecuted(
    one_attempt_bundle,
    one_predecision,
):
    held = one_attempt_bundle["factorization_owner"].validate_predecision_result
    calls = {"guard": 0}

    def forbidden(*args, **kwargs):
        del args, kwargs
        calls["guard"] += 1
        raise AssertionError("late surface guard executed")

    original = factorization._require_surfaces
    factorization._require_surfaces = forbidden
    try:
        with pytest.raises(ValueError, match="surface guard changed|late.*surface"):
            held(one_predecision)
    finally:
        factorization._require_surfaces = original
    assert calls == {"guard": 0}


def test_policy_surface_mutation_precedes_public_input_parsing(one_attempt_bundle):
    original = factorization._POLICY
    factorization._POLICY = POLICY + "x"
    try:
        with pytest.raises(ValueError, match="surface|changed"):
            _CERTIFY(
                one_attempt_bundle["source_law_owner"],
                factorization_policy=object(),
                factorization_role_sha256=object(),
            )
    finally:
        factorization._POLICY = original


def test_injected_builtin_shadow_globals_are_refused_before_execution(
    one_attempt_bundle,
    one_predecision,
):
    owner = one_attempt_bundle["factorization_owner"]
    namespace = factorization.__dict__
    missing = object()
    calls = {
        name: 0 for name in ("globals", "any", "range", "ValueError", "list", "float")
    }

    for name in calls:

        def forbidden(*args, _name=name, **kwargs):
            del args, kwargs
            calls[_name] += 1
            raise AssertionError("injected builtin shadow executed: " + _name)

        original = namespace.get(name, missing)
        namespace[name] = forbidden
        try:
            with pytest.raises(
                ValueError,
                match="surface|namespace|shadow|unexpected|injected",
            ):
                owner.validate_predecision_result(one_predecision)
        finally:
            if original is missing:
                del namespace[name]
            else:
                namespace[name] = original
        assert calls[name] == 0

    assert calls == {
        "globals": 0,
        "any": 0,
        "range": 0,
        "ValueError": 0,
        "list": 0,
        "float": 0,
    }


def test_exposed_local_missing_sentinel_cannot_mask_globals_injection(
    one_attempt_bundle,
    one_predecision,
):
    owner = one_attempt_bundle["factorization_owner"]
    namespace = factorization.__dict__
    assert "globals" not in namespace
    namespace["globals"] = factorization._MISSING_LOCAL_GLOBAL
    try:
        with pytest.raises(
            ValueError,
            match="absent runtime global globals was injected",
        ):
            owner.validate_predecision_result(one_predecision)
    finally:
        del namespace["globals"]


def test_exposed_provider_missing_sentinel_cannot_mask_typeerror_injection(
    one_attempt_bundle,
    one_predecision,
):
    owner = one_attempt_bundle["factorization_owner"]
    namespace = factorization._decision.__dict__
    assert "TypeError" not in namespace
    namespace["TypeError"] = factorization._MISSING_PROVIDER_GLOBAL
    try:
        with pytest.raises(
            ValueError,
            match="absent provider surface TypeError was injected",
        ):
            owner.validate_predecision_result(one_predecision)
    finally:
        del namespace["TypeError"]


def test_exact_uint64_request_and_proposal_domain_is_enforced(one_attempt_bundle):
    owner = one_attempt_bundle["factorization_owner"]
    count = owner.certificate.proposal_word_count
    valid = (0,) * count
    invalid_requests = (
        (True, 0, valid),
        (0, False, valid),
        (-1, 0, valid),
        (MAX_UINT64 + 1, 0, valid),
        (0, -1, valid),
        (0, MAX_UINT64 + 1, valid),
        (0, 0, list(valid)),
        (0, 0, valid[:-1]),
        (0, 0, valid + (0,)),
        (0, 0, (True,) + valid[1:]),
        (0, 0, (-1,) + valid[1:]),
        (0, 0, (MAX_UINT64 + 1,) + valid[1:]),
        (0, 0, (np.uint64(0),) + valid[1:]),
    )
    for run_id, initialization_index, words in invalid_requests:
        with pytest.raises(
            (TypeError, ValueError),
            match="uint64|integer|word|tuple|bound",
        ):
            owner.evaluate_predecision(run_id, initialization_index, words)

    bomb = _TouchBomb()
    with pytest.raises(TypeError, match="tuple|word"):
        owner.evaluate_predecision(0, 0, bomb)
    assert bomb.calls == 0


def test_exact_integer_result_fields_reject_bool_even_when_bool_equals_integer(
    one_attempt_bundle,
    one_predecision,
    selected_applied,
):
    owner = one_attempt_bundle["factorization_owner"]
    forged_predecision = _redigested(
        one_predecision,
        factorization._predecision_fields,
        factorization._predecision_payload,
        "result_sha256",
        attempt_budget=True,
    )
    with pytest.raises(TypeError, match="attempt_budget|exact integer"):
        owner.validate_predecision_result(forged_predecision)

    forged_count = _redigested(
        selected_applied,
        factorization._applied_fields,
        factorization._applied_payload,
        "applied_decision_sha256",
        comparison_count=True,
    )
    with pytest.raises(TypeError, match="comparison_count|exact integer"):
        owner.validate_applied_decision(forged_count)

    forged_index = _redigested(
        selected_applied,
        factorization._applied_fields,
        factorization._applied_payload,
        "applied_decision_sha256",
        selected_attempt_index=False,
    )
    with pytest.raises(TypeError, match="selected_attempt_index|exact integer"):
        owner.validate_applied_decision(forged_index)


def test_configuration_event_and_coordinate_bombs_fail_exact_preflight_untouched(
    one_attempt_bundle,
    one_predecision,
):
    row = one_predecision.rows[0]

    configuration_bomb = _TouchBomb()
    with pytest.raises(TypeError, match="configuration|tuple"):
        factorization._validate_row(
            _forged(row, canonical_configuration=configuration_bomb)
        )
    assert configuration_bomb.calls == 0

    event_bomb = _TouchBomb()
    with pytest.raises(TypeError, match="event|transformed"):
        factorization._validate_row(_forged(row, canonical_configuration=(event_bomb,)))
    assert event_bomb.calls == 0

    coordinate_bomb = _TouchBomb()
    event = object.__new__(factorization._prep.TransformedEvent)
    object.__setattr__(event, "event_type", 0)
    object.__setattr__(event, "coordinates", (coordinate_bomb,))
    with pytest.raises((TypeError, ValueError), match="coordinate|binary64|finite"):
        factorization._validate_row(_forged(row, canonical_configuration=(event,)))
    assert coordinate_bomb.calls == 0

    partition_bomb = _TouchBomb()
    forged_certificate = _forged(
        one_attempt_bundle["factorization_owner"].certificate,
        proposal_word_coordinates=partition_bomb,
    )
    with pytest.raises(TypeError, match="coordinate|tuple"):
        factorization._validate_certificate(forged_certificate)
    assert partition_bomb.calls == 0


def test_nested_digest_fields_preflight_exact_text_before_hostile_comparison(
    one_attempt_bundle,
    one_predecision,
    selected_applied,
    live_parity,
):
    certificate = one_attempt_bundle["factorization_owner"].certificate

    predecision_bomb = _TouchBomb()
    for field, invalid in (
        ("proposal_words_sha256", predecision_bomb),
        ("result_sha256", True),
    ):
        with pytest.raises(TypeError, match="SHA-256|exact text"):
            factorization._validate_predecision_record(
                _forged(one_predecision, **{field: invalid}),
                trusted_certificate=certificate,
            )
    assert predecision_bomb.calls == 0

    row_digest_bomb = _TouchBomb()
    for invalid in (row_digest_bomb, True):
        digests = (invalid,) + one_predecision.row_sha256s[1:]
        with pytest.raises(TypeError, match=r"row_sha256s\[0\]|exact text"):
            factorization._validate_predecision_record(
                _forged(one_predecision, row_sha256s=digests),
                trusted_certificate=certificate,
            )
    assert row_digest_bomb.calls == 0

    applied_bomb = _TouchBomb()
    for field, invalid in (
        ("predecision_result_sha256", applied_bomb),
        ("applied_decision_sha256", True),
    ):
        with pytest.raises(TypeError, match="SHA-256|exact text"):
            factorization._validate_applied_record(
                _forged(selected_applied, **{field: invalid}),
                trusted_certificate=certificate,
            )
    assert applied_bomb.calls == 0

    witness = live_parity["witness"]
    witness_bomb = _TouchBomb()
    for field, invalid in (
        ("checkpoint37_result_sha256", witness_bomb),
        ("witness_sha256", True),
    ):
        with pytest.raises(TypeError, match="SHA-256|exact text"):
            factorization._validate_witness_record(
                _forged(witness, **{field: invalid}),
                trusted_certificate=certificate,
            )
    assert witness_bomb.calls == 0


def test_certificate_claims_keep_the_reference_evaluator_boundary(
    one_attempt_bundle,
):
    certificate = one_attempt_bundle["factorization_owner"].certificate
    for name in factorization._CERTIFICATE_POSITIVE_FLAGS:
        assert type(getattr(certificate, name)) is bool
        assert getattr(certificate, name) is True
    for name in factorization._CERTIFICATE_NEGATIVE_FLAGS:
        assert type(getattr(certificate, name)) is bool
        assert getattr(certificate, name) is False
    assert certificate.cp42_noninterference_by_input_signature_and_staging
    assert certificate.complete_quota_tuple_before_decision_stage_certified
    assert not certificate.checkpoint41_factorization_assumption_discharged
    assert not getattr(
        certificate,
        "universal_equivalence_to_live_checkpoint36_37_failure_" "semantics_certified",
    )
    assert not certificate.live_philox_source_law_certified
    assert not certificate.preparation_failure_branch_executable
    scope = certificate.certificate_scope
    for token in (
        "not-universal",
        "not-checkpoint41",
        "not-whole-record",
        "not-numeric-fibers",
        "path",
        "sampler",
        "not-portable",
        "cryptographic",
    ):
        assert token in scope, token


def test_source_ast_excludes_parent_operations_rng_and_fiber_enumeration():
    source_path = Path(factorization.__file__).resolve()
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_attributes = {
        "prepare",
        "decide",
        "resolve",
        "coordinate",
        "admit",
        "random",
        "rand",
        "randn",
        "randint",
        "choice",
        "multinomial",
    }
    forbidden_names = {
        "_CP36_PREPARE",
        "_CP37_DECIDE",
        "_CP38_RESOLVE",
        "_CP39_COORDINATE",
        "_CP40_ADMIT",
    }
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden_attributes
        if isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_names
    assert "FiniteAtomicCountingSpace" not in source
    assert "itertools.product" not in source
    assert "enumerate_fiber" not in source


def test_module_is_not_reexported_from_dependency_light_process_package():
    import heterodiff.processes as processes

    assert not hasattr(
        processes,
        "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_"
        "predecision_factorization",
    )


def test_optional_torch_boundary_is_actionable():
    project_root = Path(__file__).resolve().parents[2]
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(project_root / "src")
    module_name = (
        "heterodiff.processes.plugin_bridge_counter_keyed_initial_tilt_rejection_"
        "predecision_factorization"
    )
    script = (
        "import builtins\n"
        "original = builtins.__import__\n"
        "def blocked(name, *args, **kwargs):\n"
        "    if name == 'torch' or name.startswith('torch.'):\n"
        "        raise ModuleNotFoundError('blocked torch', name='torch')\n"
        "    return original(name, *args, **kwargs)\n"
        "builtins.__import__ = blocked\n"
        "try:\n"
        "    import " + module_name + "\n"
        "except ModuleNotFoundError as error:\n"
        "    message = str(error)\n"
        "    assert 'predecision' in message or 'factorization' in message\n"
        "    assert 'optional PyTorch' in message\n"
        "else:\n"
        "    raise AssertionError('optional import unexpectedly succeeded')\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(project_root),
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
