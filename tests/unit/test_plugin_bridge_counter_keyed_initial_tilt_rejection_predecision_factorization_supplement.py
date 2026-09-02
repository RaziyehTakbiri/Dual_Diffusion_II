"""Focused supplemental coverage for checkpoint-42 staged factorization."""

from fractions import Fraction
import sys

import pytest


checkpoint42 = pytest.importorskip(
    "tests.unit.test_plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "predecision_factorization",
    reason="staged predecision factorization requires PyTorch",
)
factorization = checkpoint42.factorization


MAX_UINT64 = (1 << 64) - 1


@pytest.fixture(scope="module")
def one_attempt_bundle():
    return checkpoint42.one_attempt_bundle.__wrapped__()


@pytest.fixture(scope="module")
def two_attempt_bundle(one_attempt_bundle):
    return checkpoint42.two_attempt_bundle.__wrapped__(one_attempt_bundle)


@pytest.fixture(scope="module")
def two_predecision_evidence(two_attempt_bundle):
    owner = two_attempt_bundle["factorization_owner"]
    words = (0,) * owner.certificate.proposal_word_count
    before = checkpoint42._rng_snapshot()
    result, chronology = _profile_g_stage_order(
        lambda: owner.evaluate_predecision(42_001, 8, words)
    )
    checkpoint42._assert_rng_unchanged(before)
    return {"result": result, "stage_chronology": chronology}


@pytest.fixture(scope="module")
def two_predecision(two_predecision_evidence):
    return two_predecision_evidence["result"]


def _profile_g_stage_order(callback):
    """Observe callback completion order without replacing a callback."""

    watched = {
        factorization._SLOT_MATERIALIZER.__code__: "transform",
        factorization._TILT_EVALUATE.__code__: "score",
        factorization._TILT_VALIDATE.__code__: "score_validation",
        factorization._CP37_QUOTA.__code__: "quota",
    }
    chronology = []

    def profiler(frame, event, arg):
        del arg
        stage = watched.get(frame.f_code)
        if stage is not None and event in ("call", "return"):
            chronology.append(stage + "_" + event)

    previous = sys.getprofile()
    sys.setprofile(profiler)
    try:
        result = callback()
    finally:
        sys.setprofile(previous)
    return result, tuple(chronology)


def _with_first_quota_call_fault(callback):
    """Inject the exact modeled quota exception without replacing custody state."""

    calls = 0
    target = factorization._CP37_QUOTA.__code__

    def profiler(frame, event, arg):
        del arg
        nonlocal calls
        if event == "call" and frame.f_code is target:
            calls += 1
            raise factorization._CP37_QUOTA_ERROR("test-only first-quota-call fault")

    previous = sys.getprofile()
    sys.setprofile(profiler)
    try:
        result = callback()
    finally:
        sys.setprofile(previous)
    assert calls == 1
    return result


@pytest.mark.parametrize(
    "delta, expected_quota, expected_status",
    (
        (Fraction(-64), 0, "exhausted"),
        (Fraction(0), 1 << 64, "selected"),
    ),
)
def test_validated_pure_h_covers_both_quota_endpoints(
    one_attempt_bundle,
    delta,
    expected_quota,
    expected_status,
):
    certificate = one_attempt_bundle["factorization_owner"].certificate
    data = factorization._CP37_QUOTA(delta)
    assert data.quota == expected_quota
    row = factorization._make_row(
        0,
        (),
        delta,
        data,
        trusted_certificate=certificate,
    )
    endpoint_parent = factorization._make_predecision_result(
        certificate,
        0,
        0,
        (0,) * certificate.proposal_word_count,
        "ready",
        (row,),
    )
    assert (
        factorization._validate_predecision_record(
            endpoint_parent,
            trusted_certificate=certificate,
        )
        is endpoint_parent
    )

    for word in (0, MAX_UINT64):
        applied = factorization._make_applied_decision(
            certificate,
            endpoint_parent,
            (word,),
        )
        assert (
            factorization._validate_applied_record(
                applied,
                trusted_certificate=certificate,
            )
            is applied
        )
        assert applied.status == expected_status
        assert applied.comparison_count == 1
        assert applied.selected_attempt_index == (
            0 if expected_status == "selected" else None
        )


def test_public_h_preflights_late_malformed_w_before_first_comparison(
    two_attempt_bundle,
    two_predecision,
):
    owner = two_attempt_bundle["factorization_owner"]
    first_quota = two_predecision.rows[0].acceptance_quota
    assert first_quota > 0
    bomb = checkpoint42._TouchBomb()

    with pytest.raises(TypeError, match=r"decision_words\[1\]|exact integer"):
        owner.apply_decision_words(
            two_predecision,
            (first_quota - 1, bomb),
        )
    assert bomb.calls == 0


def test_fault_injected_g_failure_replays_through_public_h_without_touching_w(
    one_attempt_bundle,
):
    """Exercise the modeled path; this is not natural-failure reachability."""

    owner = one_attempt_bundle["factorization_owner"]
    words = (0,) * owner.certificate.proposal_word_count
    before = checkpoint42._rng_snapshot()
    failure = _with_first_quota_call_fault(
        lambda: owner.evaluate_predecision(42_004, 11, words)
    )
    assert failure.status == "quota_certification_failure"
    assert failure.rows == ()

    bomb = checkpoint42._TouchBomb()
    applied = _with_first_quota_call_fault(
        lambda: owner.apply_decision_words(failure, bomb)
    )
    assert applied.status == "quota_certification_failure"
    assert applied.predecision_result is failure
    assert applied.decision_words is None
    assert applied.decision_words_sha256 is None
    assert applied.comparison_count == 0
    assert applied.failure_passed_through_without_decision_word_access is True
    assert bomb.calls == 0
    checkpoint42._assert_rng_unchanged(before)


def test_dynamic_g_order_completes_all_transforms_and_scores_before_first_quota(
    two_attempt_bundle,
    two_predecision_evidence,
):
    owner = two_attempt_bundle["factorization_owner"]
    certificate = owner.certificate
    result = two_predecision_evidence["result"]
    chronology = two_predecision_evidence["stage_chronology"]
    assert result.status == "ready"

    first_quota = chronology.index("quota_call")
    prefix = chronology[:first_quota]
    suffix = chronology[first_quota:]
    transform_count = (
        certificate.attempt_budget
        * certificate.checkpoint36_certificate.manifest.total_cap
    )
    score_count = 2 * certificate.attempt_budget
    expected = {
        "transform_call": transform_count,
        "transform_return": transform_count,
        # Each direct score is replayed once by the exact CP30 validator.
        "score_call": score_count,
        "score_return": score_count,
        "score_validation_call": certificate.attempt_budget,
        "score_validation_return": certificate.attempt_budget,
    }
    for event, count in expected.items():
        assert prefix.count(event) == count
        assert event not in suffix
