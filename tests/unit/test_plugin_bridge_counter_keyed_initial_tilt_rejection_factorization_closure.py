"""Hostile tests for checkpoint-43 supplied-word factorization closure."""

import ast
from contextlib import contextmanager
import dis
from fractions import Fraction
import inspect
from pathlib import Path
import pickle
import random
import sys

import numpy as np
import pytest


torch = pytest.importorskip(
    "torch", reason="factorization closure requires the PyTorch reference"
)

from heterodiff.processes import (  # noqa: E402
    plugin_bridge_counter_keyed_initial_tilt_rejection_factorization_closure as closure,
)

checkpoint42 = pytest.importorskip(  # noqa: E402
    "tests.unit.test_plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "predecision_factorization",
    reason="factorization closure requires the CP42 fixtures",
)


POLICY = getattr(
    closure,
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_"
    "FACTORIZATION_CLOSURE_POLICY",
)
ROLE = "4" * 64
MAX_UINT64 = (1 << 64) - 1
_CERTIFY = getattr(
    closure,
    "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "factorization_closure",
)
_MATCHING = getattr(
    closure,
    "require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "factorization_closure",
)
_VALIDATE_CERTIFICATE = getattr(
    closure,
    "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "factorization_closure_certificate",
)
_OWNER_TYPE = getattr(
    closure,
    "CounterKeyedInitialTiltRejectionFactorizationClosureOwner",
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


class _TouchBomb:
    def __init__(self):
        self.touched = False

    def _explode(self):
        self.touched = True
        raise AssertionError("decision words were touched")

    def __iter__(self):
        return self._explode()

    def __len__(self):
        return self._explode()

    def __getitem__(self, key):
        del key
        return self._explode()


def _with_call_fault(target_code, error, callback):
    def profiler(frame, event, arg):
        del arg
        if event == "call" and frame.f_code is target_code:
            raise error
        return profiler

    previous = sys.getprofile()
    sys.setprofile(profiler)
    try:
        return callback()
    finally:
        sys.setprofile(previous)


def _profile_combined_entrypoint(callback):
    source_law = checkpoint42.checkpoint41.source_law
    parent_codes = {
        "admit": source_law._CP40_ADMIT.__code__,
        "coordinate": source_law._CP39_COORDINATE.__code__,
        "resolve": source_law._CP38_RESOLVE.__code__,
        "decide": source_law._CP37_DECIDE.__code__,
        "prepare": source_law._CP36_PREPARE.__code__,
    }
    stage_codes = {
        _OWNER_TYPE._evaluate_operation.__code__: "g",
        _OWNER_TYPE._apply_trusted.__code__: "semantic_h",
        closure._CP42_EVALUATE.__code__: "cp42_g",
        closure._factorization._SLOT_MATERIALIZER.__code__: "transform",
        closure._factorization._TILT_EVALUATE.__code__: "score",
        closure._factorization._CP37_QUOTA.__code__: "quota",
        closure._CP42_APPLIED_BUILDER.__code__: "cp42_applied_builder",
    }
    parent_calls = {name: 0 for name in parent_codes}
    chronology = []

    def profiler(frame, event, arg):
        del arg
        if event == "call":
            for name, code in parent_codes.items():
                if frame.f_code is code:
                    parent_calls[name] += 1
        stage = stage_codes.get(frame.f_code)
        if stage is not None and event in ("call", "return"):
            chronology.append(stage + "_" + event)
        return profiler

    previous = sys.getprofile()
    sys.setprofile(profiler)
    try:
        result = callback()
    finally:
        sys.setprofile(previous)
    return result, parent_calls, tuple(chronology)


@contextmanager
def _trace_word_quota_comparisons():
    target = closure._CP42_APPLIED_BUILDER.__code__
    comparison_offsets = {
        instruction.offset
        for instruction in dis.get_instructions(target)
        if instruction.opname == "COMPARE_OP" and instruction.argrepr == "<"
    }
    assert comparison_offsets
    counter = [0]

    def local_tracer(frame, event, arg):
        del arg
        if event == "opcode" and frame.f_lasti in comparison_offsets:
            counter[0] += 1
        return local_tracer

    def global_tracer(frame, event, arg):
        del arg
        if event == "call" and frame.f_code is target:
            frame.f_trace_opcodes = True
            return local_tracer
        return None

    previous = sys.gettrace()
    sys.settrace(global_tracer)
    try:
        yield counter
    finally:
        sys.settrace(previous)


def test_wrong_cp42_return_cannot_be_silently_relabelled_f36():
    with pytest.raises(TypeError, match="wrong exact type"):
        closure._resolve_parent_evaluation(None, caught_typed_failure=False)
    with pytest.raises(TypeError, match="exact Boolean"):
        closure._resolve_parent_evaluation(
            closure._MISSING_PARENT,
            caught_typed_failure=1,
        )
    with pytest.raises(RuntimeError, match="retained"):
        closure._resolve_parent_evaluation(None, caught_typed_failure=True)
    assert (
        closure._resolve_parent_evaluation(
            closure._MISSING_PARENT,
            caught_typed_failure=True,
        )
        is None
    )


@pytest.mark.parametrize(
    "delta,quota,branch",
    (
        (Fraction(0), 1 << 64, "unity"),
        (Fraction(-64), 0, "below_uint64_resolution"),
        (Fraction(-1, 1 << 65), (1 << 64) - 1, "below_one_uint64_cell"),
        (Fraction(-1, 1 << 1_074), (1 << 64) - 1, "below_one_uint64_cell"),
    ),
)
def test_reviewed_f37_terminal_and_extreme_dyadic_boundaries(
    delta,
    quota,
    branch,
):
    result = closure._factorization._CP37_QUOTA(delta)
    assert result.quota == quota
    assert result.branch == branch


def test_reviewed_f37_strict_terminal_boundaries_enter_adaptive_side():
    denominator = 1 << 64
    below_one_boundary = closure._factorization._CP37_QUOTA(Fraction(-1, denominator))
    assert below_one_boundary.branch == "adaptive_decimal"
    assert below_one_boundary.quota == denominator - 1

    just_above_zero_cutoff = closure._factorization._CP37_QUOTA(
        Fraction(-64) + Fraction(1, 1 << 1_074)
    )
    assert just_above_zero_cutoff.branch == "adaptive_decimal"
    assert just_above_zero_cutoff.quota == 0


def test_reviewed_f37_coefficient_bound_and_invalid_routes():
    conservative_numerator_bound = (1 << 2_100) - 1
    decimal_value = closure._factorization._decision._exact_dyadic_decimal(
        Fraction(-conservative_numerator_bound, 1 << 1_074),
        name="CP43 reviewed coefficient bound",
    )
    digit_count = len(decimal_value.as_tuple().digits)
    decision_module = closure._factorization._decision
    assert digit_count <= 1_383
    assert digit_count < (
        decision_module.INITIAL_TILT_REJECTION_DECISION_MAX_DECIMAL_COEFFICIENT_DIGITS
    )
    with pytest.raises(TypeError, match="Fraction"):
        closure._factorization._CP37_QUOTA(0.0)
    with pytest.raises(
        closure._factorization._CP37_QUOTA_ERROR,
        match="dyadic",
    ):
        closure._factorization._CP37_QUOTA(Fraction(-1, 3))
    with pytest.raises(ValueError, match="nonpositive"):
        closure._factorization._CP37_QUOTA(Fraction(1, 2))


@pytest.fixture(scope="module")
def one_attempt_bundle():
    return checkpoint42.one_attempt_bundle.__wrapped__()


@pytest.fixture(scope="module")
def owner(one_attempt_bundle):
    before = _rng_snapshot()
    result = _CERTIFY(
        one_attempt_bundle["factorization_owner"],
        closure_policy=POLICY,
        closure_role_sha256=ROLE,
    )
    _assert_rng_unchanged(before)
    return result


@pytest.fixture(scope="module")
def two_attempt_owner(one_attempt_bundle):
    parent = checkpoint42.two_attempt_bundle.__wrapped__(one_attempt_bundle)
    return _CERTIFY(
        parent["factorization_owner"],
        closure_policy=POLICY,
        closure_role_sha256="5" * 64,
    )


@pytest.fixture(scope="module")
def two_predecision(two_attempt_owner):
    return two_attempt_owner.evaluate_predecision(
        43_007,
        7,
        (0,) * two_attempt_owner.certificate.proposal_word_count,
    )


@pytest.fixture(scope="module")
def live_checkpoint37(one_attempt_bundle):
    return checkpoint42.live_checkpoint37.__wrapped__(one_attempt_bundle)


@pytest.fixture(scope="module")
def one_pass_evidence(owner, live_checkpoint37):
    live = live_checkpoint37["live"]
    before = _rng_snapshot()
    result, calls, chronology = _profile_combined_entrypoint(
        lambda: owner.evaluate_and_apply(
            live.run_id,
            live.initialization_index,
            live_checkpoint37["proposal_words"],
            live_checkpoint37["decision_words"],
        )
    )
    _assert_rng_unchanged(before)
    return {"result": result, "calls": calls, "chronology": chronology}


@pytest.fixture(scope="module")
def one_pass(one_pass_evidence):
    return one_pass_evidence["result"]


@pytest.fixture(scope="module")
def full_outcome_witness(owner, one_pass, live_checkpoint37):
    before = _rng_snapshot()
    witness = owner.witness_successful_full_outcome_parity(
        one_pass,
        live_checkpoint37["live"],
    )
    assert owner.validate_successful_full_outcome_parity_witness(witness) is witness
    _assert_rng_unchanged(before)
    return witness


def test_public_api_signatures_and_factorization_boundary(owner):
    expected = {
        "CounterKeyedInitialTiltRejectionFactorizationClosureCertificate",
        "CounterKeyedInitialTiltRejectionFactorizationClosurePredecision",
        "CounterKeyedInitialTiltRejectionFactorizationClosureAppliedDecision",
        "CounterKeyedInitialTiltRejectionFullOutcomeParityWitness",
        "CounterKeyedInitialTiltRejectionFactorizationClosureOwner",
        "PluginBridgeCounterKeyedInitialTiltRejectionFactorizationClosureError",
        "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_"
        "factorization_closure",
        "require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_"
        "factorization_closure",
        "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_"
        "factorization_closure_certificate",
    }
    assert expected <= set(closure.__all__)
    assert len(closure.__all__) == len(set(closure.__all__))
    g = inspect.signature(owner.evaluate_predecision)
    h = inspect.signature(owner.apply_decision_words)
    combined = inspect.signature(owner.evaluate_and_apply)
    assert tuple(g.parameters) == (
        "run_id",
        "initialization_index",
        "proposal_words",
    )
    assert tuple(h.parameters) == ("predecision_result", "decision_words")
    assert tuple(combined.parameters) == (
        "run_id",
        "initialization_index",
        "proposal_words",
        "decision_words",
    )
    assert "decision" not in tuple(g.parameters)


def test_certificate_binds_cp42_and_records_exact_claim_boundary(
    one_attempt_bundle,
    owner,
):
    certificate = owner.certificate
    parent = one_attempt_bundle["factorization_owner"].certificate
    assert certificate.checkpoint42_certificate is parent
    assert certificate.checkpoint42_certificate_sha256 == parent.certificate_sha256
    assert certificate.factorization_hypothesis_sha256 == (
        parent.factorization_hypothesis_sha256
    )
    assert certificate.proposal_coordinate_sha256 == (parent.proposal_coordinate_sha256)
    assert certificate.decision_coordinate_sha256 == (parent.decision_coordinate_sha256)
    positive = closure._CERTIFICATE_POSITIVE_FLAGS
    negative = closure._CERTIFICATE_NEGATIVE_FLAGS
    assert all(getattr(certificate, name) is True for name in positive)
    assert all(getattr(certificate, name) is False for name in negative)
    assert (
        certificate.cp43_defined_reference_factorization_discharged_by_construction
        is True
    )
    assert (
        certificate.abstract_product_uniform_corollary_recorded_under_explicit_premises
        is True
    )
    assert certificate.construction_contract_enforced is True
    assert certificate.complete_g_before_semantic_h_certified is True
    assert certificate.semantic_h43_failure_passthrough_without_w_access_certified
    assert certificate.semantic_h43_full_w_preflight_before_comparison_certified
    assert not hasattr(certificate, "complete_g_before_h_certified")
    assert certificate.combined_entrypoint_single_g_evaluation_certified is True
    assert certificate.public_h_replays_g_for_custody_disclosed is True
    assert certificate.separately_invoked_public_h_replay_free is False
    assert certificate.transient_failure_public_h_passthrough_certified is False
    assert certificate.checkpoint41_live_parent_factorization_discharged is False
    assert certificate.natural_f37_reachability_resolved is False
    assert certificate.generic_exception_totalization_certified is False
    assert certificate.f37_arithmetic_argument_sha256 == (
        closure._f37_arithmetic_argument_sha256()
    )
    assert certificate.claim_evidence_ledger_sha256 == (
        closure._evidence_ledger_sha256()
    )
    assert "not-self-attested" in certificate.claim_evidence_ledger
    assert "not-machine-proof" in certificate.f37_arithmetic_argument
    assert "deterministic-replay-stable-total-G" in (
        certificate.product_uniform_corollary
    )
    assert "3072-digit" in certificate.f37_reachability_conclusion
    assert (
        _MATCHING(
            one_attempt_bundle["factorization_owner"],
            owner,
            closure_policy=POLICY,
            closure_role_sha256=ROLE,
        )
        is owner
    )
    assert (
        _VALIDATE_CERTIFICATE(
            one_attempt_bundle["factorization_owner"],
            owner,
            closure_policy=POLICY,
            closure_role_sha256=ROLE,
        )
        is certificate
    )


@pytest.mark.parametrize("owner_name", ("owner", "two_attempt_owner"))
def test_full_word_partition_round_trips_exact_cp41_interleaving(
    request,
    owner_name,
):
    current = request.getfixturevalue(owner_name)
    certificate = current.certificate
    full = tuple(
        range(certificate.proposal_word_count + certificate.decision_word_count)
    )
    proposal, decision = current.split_full_words(full)
    assert len(proposal) == certificate.proposal_word_count
    assert len(decision) == certificate.decision_word_count
    assert set(proposal).isdisjoint(decision)
    assert set(proposal) | set(decision) == set(full)
    parent = certificate.checkpoint42_certificate
    full_coordinates = parent.checkpoint36_certificate.logical_word_coordinates
    coordinate_words = dict(zip(full_coordinates, full))
    expected_proposal = tuple(
        coordinate_words[coordinate] for coordinate in parent.proposal_word_coordinates
    )
    expected_decision = tuple(
        coordinate_words[coordinate] for coordinate in parent.decision_word_coordinates
    )
    assert (proposal, decision) == (expected_proposal, expected_decision)
    assert current.join_full_words(proposal, decision) == full
    if certificate.attempt_budget == 2:
        assert proposal + decision != full


def test_combined_entrypoint_single_g_matches_live_successful_projection(
    one_pass,
    one_pass_evidence,
    live_checkpoint37,
):
    live = live_checkpoint37["live"]
    predecision = one_pass.predecision_result
    cp42 = one_pass.checkpoint42_applied_decision
    assert predecision.status == "ready"
    assert predecision.checkpoint42_result.status == "ready"
    assert one_pass.status == live.outcome
    assert one_pass.comparison_count == live.evaluated_attempt_count
    assert one_pass.selected_attempt_index == live.selected_attempt_index
    assert one_pass.selected_configuration_sha256 == live.selected_configuration_sha256
    assert one_pass.decision_words_validated_before_first_comparison is True
    assert cp42.predecision_result is predecision.checkpoint42_result
    assert one_pass_evidence["calls"] == {
        "admit": 0,
        "coordinate": 0,
        "resolve": 0,
        "decide": 0,
        "prepare": 0,
    }
    chronology = one_pass_evidence["chronology"]
    assert chronology.count("g_call") == 1
    assert chronology.count("g_return") == 1
    assert chronology.count("semantic_h_call") == 1
    assert chronology.count("semantic_h_return") == 1
    assert chronology.count("cp42_g_call") == 1
    assert chronology.count("cp42_g_return") == 1
    assert chronology.count("cp42_applied_builder_call") == 1
    assert chronology.count("cp42_applied_builder_return") == 1
    assert chronology.index("g_return") < chronology.index("semantic_h_call")
    g_prefix = chronology[: chronology.index("g_return")]
    assert "cp42_g_call" in g_prefix
    assert "cp42_g_return" in g_prefix
    assert "transform_call" in g_prefix
    assert "score_call" in g_prefix
    assert "quota_call" in g_prefix
    assert "semantic_h_call" not in g_prefix
    assert "cp42_applied_builder_call" not in g_prefix


def test_full_outcome_witness_binds_words_thresholds_and_outcome(
    full_outcome_witness,
    one_pass,
    live_checkpoint37,
):
    witness = full_outcome_witness
    assert witness.applied_decision is one_pass
    assert witness.checkpoint37_result is live_checkpoint37["live"]
    assert witness.threshold_projection_equal is True
    assert witness.decision_word_tuple_equal is True
    assert witness.outcome_equal is True
    assert witness.comparison_count_equal is True
    assert witness.selected_attempt_index_equal is True
    assert witness.selected_configuration_equal is True
    assert witness.successful_full_outcome_projection_equal is True
    assert witness.universal_equivalence_claimed is False
    assert witness.live_failure_equivalence_claimed is False


@pytest.mark.parametrize(
    "delta,expected_quota,expected_status",
    (
        (Fraction(-64), 0, "exhausted"),
        (Fraction(0), 1 << 64, "selected"),
    ),
)
def test_semantic_h_covers_both_synthetic_quota_endpoints(
    owner,
    delta,
    expected_quota,
    expected_status,
):
    parent_certificate = owner.certificate.checkpoint42_certificate
    quota = closure._factorization._CP37_QUOTA(delta)
    assert quota.quota == expected_quota
    row = closure._factorization._make_row(
        0,
        (),
        delta,
        quota,
        trusted_certificate=parent_certificate,
    )
    cp42_predecision = closure._factorization._make_predecision_result(
        parent_certificate,
        43_006,
        6,
        (0,) * parent_certificate.proposal_word_count,
        "ready",
        (row,),
    )
    predecision = closure._make_predecision(
        owner.certificate,
        43_006,
        6,
        cp42_predecision.proposal_words,
        cp42_predecision,
    )
    for word in (0, MAX_UINT64):
        applied = owner._apply_trusted(
            predecision,
            (word,),
            owner._owner_snapshot(),
        )
        assert applied.status == expected_status
        assert applied.comparison_count == 1
        assert applied.selected_attempt_index == (
            0 if expected_status == "selected" else None
        )


def test_semantic_h_preflights_late_malformed_w_before_any_comparison(
    two_attempt_owner,
    two_predecision,
):
    first_quota = two_predecision.checkpoint42_result.rows[0].acceptance_quota
    assert first_quota > 0
    bomb = checkpoint42._TouchBomb()
    with _trace_word_quota_comparisons() as comparison_counter:
        with pytest.raises(TypeError, match=r"decision_words\[1\]|exact integer"):
            two_attempt_owner._apply_trusted(
                two_predecision,
                (first_quota - 1, bomb),
                two_attempt_owner._owner_snapshot(),
            )
    assert comparison_counter == [0]
    assert bomb.calls == 0


def test_semantic_h_realizes_first_second_and_exhausted_branches(
    two_attempt_owner,
    two_predecision,
):
    quotas = tuple(
        row.acceptance_quota for row in two_predecision.checkpoint42_result.rows
    )
    assert len(quotas) == 2
    assert all(0 < quota < (1 << 64) for quota in quotas)
    cases = (
        ((quotas[0] - 1, MAX_UINT64), "selected", 0, 1),
        ((quotas[0], quotas[1] - 1), "selected", 1, 2),
        ((quotas[0], quotas[1]), "exhausted", None, 2),
    )
    for words, status, index, comparisons in cases:
        applied = two_attempt_owner._apply_trusted(
            two_predecision,
            words,
            two_attempt_owner._owner_snapshot(),
        )
        assert applied.status == status
        assert applied.selected_attempt_index == index
        assert applied.comparison_count == comparisons


@pytest.mark.parametrize(
    "target_code,error",
    (
        (
            closure._factorization._prep._CP28_MATERIALIZE_SLOT_FIELDS.__code__,
            closure._REFERENCE_ERROR("test-only typed CP28 failure"),
        ),
        (
            closure._factorization._TILT_EVALUATE.__code__,
            closure._TILT_ERROR("test-only typed CP30 failure"),
        ),
    ),
    ids=("cp28", "cp30"),
)
def test_declared_typed_preparation_failures_become_f36_without_w_access(
    owner,
    target_code,
    error,
):
    bomb = _TouchBomb()
    words = (0,) * owner.certificate.proposal_word_count
    before = _rng_snapshot()
    result = _with_call_fault(
        target_code,
        error,
        lambda: owner.evaluate_and_apply(43_001, 1, words, bomb),
    )
    _assert_rng_unchanged(before)
    assert result.status == "preparation_failure"
    assert result.predecision_result.typed_preparation_failure_totalized is True
    assert result.predecision_result.checkpoint42_result is None
    assert result.decision_words is None
    assert result.comparison_count == 0
    assert result.failure_passed_through_without_decision_word_access is True
    assert bomb.touched is False


def test_exact_quota_failure_becomes_f37_and_h_never_touches_w(owner):
    bomb = _TouchBomb()
    words = (0,) * owner.certificate.proposal_word_count
    error = closure._factorization._CP37_QUOTA_ERROR("test-only exact quota failure")
    before = _rng_snapshot()
    result = _with_call_fault(
        closure._factorization._CP37_QUOTA.__code__,
        error,
        lambda: owner.evaluate_and_apply(43_002, 2, words, bomb),
    )
    _assert_rng_unchanged(before)
    assert result.status == "quota_certification_failure"
    assert result.predecision_result.checkpoint42_result.status == (
        "quota_certification_failure"
    )
    assert result.decision_words is None
    assert result.comparison_count == 0
    assert result.failure_passed_through_without_decision_word_access is True
    assert bomb.touched is False


@pytest.mark.parametrize(
    "target_code,error,expected_status",
    (
        (
            closure._factorization._TILT_EVALUATE.__code__,
            closure._TILT_ERROR("transient CP30 failure"),
            "preparation_failure",
        ),
        (
            closure._factorization._CP37_QUOTA.__code__,
            closure._factorization._CP37_QUOTA_ERROR("transient CP37 failure"),
            "quota_certification_failure",
        ),
    ),
    ids=("f36", "f37"),
)
def test_separate_public_h_requires_replay_stable_failure_and_never_touches_w(
    owner,
    target_code,
    error,
    expected_status,
):
    words = (0,) * owner.certificate.proposal_word_count
    predecision = _with_call_fault(
        target_code,
        error,
        lambda: owner.evaluate_predecision(43_005, 5, words),
    )
    assert predecision.status == expected_status
    bomb = _TouchBomb()
    with pytest.raises(ValueError, match="replay"):
        owner.apply_decision_words(predecision, bomb)
    assert bomb.touched is False


@pytest.mark.parametrize(
    "target_code,error_type,expected_status",
    (
        (
            closure._factorization._TILT_EVALUATE.__code__,
            closure._TILT_ERROR,
            "preparation_failure",
        ),
        (
            closure._factorization._CP37_QUOTA.__code__,
            closure._factorization._CP37_QUOTA_ERROR,
            "quota_certification_failure",
        ),
    ),
    ids=("f36", "f37"),
)
def test_separate_public_h_passes_through_replay_stable_failures_without_w(
    owner,
    target_code,
    error_type,
    expected_status,
):
    words = (0,) * owner.certificate.proposal_word_count
    predecision = _with_call_fault(
        target_code,
        error_type("replay-stable failure during public G"),
        lambda: owner.evaluate_predecision(43_008, 8, words),
    )
    bomb = _TouchBomb()
    applied = _with_call_fault(
        target_code,
        error_type("replay-stable failure during public-H custody replay"),
        lambda: owner.apply_decision_words(predecision, bomb),
    )
    assert predecision.status == expected_status
    assert applied.status == expected_status
    assert applied.predecision_result is predecision
    assert applied.decision_words is None
    assert applied.comparison_count == 0
    assert applied.failure_passed_through_without_decision_word_access is True
    assert bomb.touched is False


@pytest.mark.parametrize(
    "target_code,error",
    (
        (
            closure._factorization._TILT_EVALUATE.__code__,
            ValueError("unexpected internal failure"),
        ),
        (
            closure._factorization._TILT_EVALUATE.__code__,
            ArithmeticError("generic arithmetic refusal"),
        ),
        (
            closure._factorization._TILT_EVALUATE.__code__,
            closure._factorization._prep.PluginBridgeCounterKeyedInitialTiltRejectionPreparationError(
                "CP36 refusal"
            ),
        ),
        (
            closure._factorization._TILT_EVALUATE.__code__,
            type("TiltSubclass", (closure._TILT_ERROR,), {})("CP30 subclass"),
        ),
        (
            closure._factorization._prep._CP28_MATERIALIZE_SLOT_FIELDS.__code__,
            type("ReferenceSubclass", (closure._REFERENCE_ERROR,), {})("CP28 subclass"),
        ),
        (
            closure._factorization._CP37_QUOTA.__code__,
            type(
                "QuotaSubclass",
                (closure._factorization._CP37_QUOTA_ERROR,),
                {},
            )("CP37 subclass"),
        ),
    ),
    ids=(
        "value",
        "arithmetic",
        "cp36",
        "cp30-subclass",
        "cp28-subclass",
        "f37-subclass",
    ),
)
def test_unexpected_and_subclass_errors_remain_exact_refusals(
    owner,
    target_code,
    error,
):
    words = (0,) * owner.certificate.proposal_word_count
    with pytest.raises(type(error)) as caught:
        _with_call_fault(
            target_code,
            error,
            lambda: owner.evaluate_predecision(43_003, 3, words),
        )
    assert caught.value is error


@pytest.mark.parametrize(
    "field,value,error_type",
    (
        ("run_id", True, TypeError),
        ("run_id", -1, ValueError),
        ("run_id", 1 << 64, ValueError),
        ("initialization_index", np.int64(0), TypeError),
        ("initialization_index", -1, ValueError),
        ("initialization_index", 1 << 64, ValueError),
        ("proposal_words", [], TypeError),
        ("proposal_words", (), ValueError),
    ),
)
def test_invalid_public_g_domains_refuse_before_totalization(
    owner,
    field,
    value,
    error_type,
):
    arguments = {
        "run_id": 43_004,
        "initialization_index": 4,
        "proposal_words": (0,) * owner.certificate.proposal_word_count,
    }
    arguments[field] = value
    with pytest.raises(error_type):
        owner.evaluate_predecision(**arguments)


@pytest.mark.parametrize(
    "bad_word,error_type",
    (
        (True, TypeError),
        (np.int64(0), TypeError),
        (-1, ValueError),
        (1 << 64, ValueError),
    ),
)
def test_invalid_public_g_proposal_entries_refuse(owner, bad_word, error_type):
    words = [0] * owner.certificate.proposal_word_count
    words[-1] = bad_word
    with pytest.raises(error_type):
        owner.evaluate_predecision(43_009, 9, tuple(words))


@pytest.mark.parametrize(
    "bad_words,error_type",
    (
        ([], TypeError),
        ((), ValueError),
        ((True, 0), TypeError),
        ((np.int64(0), 0), TypeError),
        ((-1, 0), ValueError),
        ((1 << 64, 0), ValueError),
    ),
)
def test_invalid_semantic_h_decision_domains_refuse_before_comparison(
    two_attempt_owner,
    two_predecision,
    bad_words,
    error_type,
):
    with _trace_word_quota_comparisons() as comparison_counter:
        with pytest.raises(error_type):
            two_attempt_owner._apply_trusted(
                two_predecision,
                bad_words,
                two_attempt_owner._owner_snapshot(),
            )
    assert comparison_counter == [0]


def test_split_join_invalid_domains_and_cross_owner_predecision_refuse(
    owner,
    two_attempt_owner,
    one_pass,
):
    certificate = owner.certificate
    full_length = certificate.proposal_word_count + certificate.decision_word_count
    with pytest.raises(TypeError):
        owner.split_full_words([0] * full_length)
    with pytest.raises(ValueError):
        owner.split_full_words((0,) * (full_length - 1))
    malformed_full = [0] * full_length
    malformed_full[-1] = True
    with pytest.raises(TypeError):
        owner.split_full_words(tuple(malformed_full))
    with pytest.raises(TypeError):
        owner.join_full_words(
            [0] * certificate.proposal_word_count,
            (0,) * certificate.decision_word_count,
        )
    with pytest.raises(TypeError):
        owner.join_full_words(
            (0,) * certificate.proposal_word_count,
            (True,) * certificate.decision_word_count,
        )
    bomb = _TouchBomb()
    with pytest.raises(ValueError, match="certificate"):
        two_attempt_owner.apply_decision_words(one_pass.predecision_result, bomb)
    assert bomb.touched is False


def test_records_owners_and_public_constructors_are_sealed(owner, one_pass):
    with pytest.raises(AttributeError):
        owner._certificate = owner.certificate
    with pytest.raises(AttributeError):
        del owner._certificate
    for value in (
        owner,
        owner.certificate,
        one_pass.predecision_result,
        one_pass,
    ):
        with pytest.raises(TypeError):
            pickle.dumps(value)
    with pytest.raises(TypeError):
        closure.CounterKeyedInitialTiltRejectionFactorizationClosureCertificate(
            _construction_token=object()
        )


def test_live_certificate_revalidation_rejects_object_level_mutation(owner):
    certificate = owner.certificate
    field = "cp43_defined_reference_factorization_discharged_by_construction"
    original = getattr(certificate, field)
    object.__setattr__(certificate, field, False)
    try:
        with pytest.raises(ValueError):
            _VALIDATE_CERTIFICATE(
                owner.factorization_owner,
                owner,
                closure_policy=POLICY,
                closure_role_sha256=ROLE,
            )
        full_words = (0,) * (
            certificate.proposal_word_count + certificate.decision_word_count
        )
        with pytest.raises(ValueError):
            owner.split_full_words(full_words)
        with pytest.raises(ValueError):
            owner.join_full_words(
                (0,) * certificate.proposal_word_count,
                (0,) * certificate.decision_word_count,
            )
    finally:
        object.__setattr__(certificate, field, original)
    assert (
        _VALIDATE_CERTIFICATE(
            owner.factorization_owner,
            owner,
            closure_policy=POLICY,
            closure_role_sha256=ROLE,
        )
        is certificate
    )


@pytest.mark.parametrize(
    "method_name",
    (
        "validate_predecision_result",
        "apply_decision_words",
        "_require_owner_snapshot",
    ),
)
def test_runtime_fingerprint_rejects_bound_cp43_method_drift(
    owner,
    monkeypatch,
    method_name,
):
    def altered_method(self, *args, **kwargs):
        del self, args, kwargs
        raise AssertionError("altered CP43 method executed")

    monkeypatch.setattr(_OWNER_TYPE, method_name, altered_method)
    with pytest.raises(ValueError, match="runtime digest"):
        closure._validate_certificate(owner.certificate)


def test_semantic_h_refuses_foreign_stage_snapshot_before_w_access(
    owner,
    two_attempt_owner,
    one_pass,
):
    bomb = _TouchBomb()
    foreign_snapshot = two_attempt_owner._owner_snapshot()
    with pytest.raises(
        closure.PluginBridgeCounterKeyedInitialTiltRejectionFactorizationClosureError,
        match="owner changed during operation",
    ):
        owner._apply_trusted(one_pass.predecision_result, bomb, foreign_snapshot)
    assert bomb.touched is False


@pytest.mark.parametrize(
    "field,replacement,error_match",
    (
        ("closure_role_sha256", "6" * 64, "role"),
        ("checkpoint42_owner_runtime_identity", 1, "owner identity"),
    ),
)
def test_redigested_dynamic_certificate_binding_mutations_refuse(
    owner,
    field,
    replacement,
    error_match,
):
    certificate = owner.certificate
    original_value = getattr(certificate, field)
    if field == "checkpoint42_owner_runtime_identity" and replacement == original_value:
        replacement += 1
    original_digest = certificate.certificate_sha256
    object.__setattr__(certificate, field, replacement)
    values = {
        name: getattr(certificate, name) for name in closure._certificate_fields()
    }
    values["certificate_sha256"] = closure._SEMANTIC_DIGEST(
        closure._certificate_payload(values)
    )
    object.__setattr__(
        certificate,
        "certificate_sha256",
        values["certificate_sha256"],
    )
    try:
        with pytest.raises(ValueError, match=error_match):
            _VALIDATE_CERTIFICATE(
                owner.factorization_owner,
                owner,
                closure_policy=POLICY,
                closure_role_sha256=ROLE,
            )
    finally:
        object.__setattr__(certificate, field, original_value)
        object.__setattr__(certificate, "certificate_sha256", original_digest)


def test_plain_and_redigested_tampering_refuses(owner, one_pass, full_outcome_witness):
    plain = _forged(one_pass, status="exhausted")
    with pytest.raises(ValueError):
        owner.validate_applied_decision(plain)
    forged = _forged(full_outcome_witness, universal_equivalence_claimed=True)
    values = {name: getattr(forged, name) for name in closure._witness_fields()}
    values["witness_sha256"] = closure._SEMANTIC_DIGEST(
        closure._witness_payload(values)
    )
    redigested = _forged(forged, witness_sha256=values["witness_sha256"])
    with pytest.raises(ValueError, match="universal"):
        owner.validate_successful_full_outcome_parity_witness(redigested)


def test_cross_owner_applied_and_witness_records_refuse(
    two_attempt_owner,
    one_pass,
    full_outcome_witness,
):
    with pytest.raises(ValueError, match="certificate"):
        two_attempt_owner.validate_applied_decision(one_pass)
    with pytest.raises(ValueError, match="certificate"):
        two_attempt_owner.validate_successful_full_outcome_parity_witness(
            full_outcome_witness
        )


def test_redigested_predecision_applied_and_f37_argument_tampering_refuses(
    owner,
    one_pass,
):
    predecision = one_pass.predecision_result
    predecision_values = {
        name: getattr(predecision, name) for name in closure._predecision_fields()
    }
    predecision_values["run_id"] += 1
    predecision_values["result_sha256"] = closure._SEMANTIC_DIGEST(
        closure._predecision_payload(predecision_values)
    )
    forged_predecision = _forged(predecision, **predecision_values)
    with pytest.raises(ValueError):
        owner.validate_predecision_result(forged_predecision)

    applied_values = {
        name: getattr(one_pass, name) for name in closure._applied_fields()
    }
    applied_values["comparison_count"] += 1
    applied_values["applied_decision_sha256"] = closure._SEMANTIC_DIGEST(
        closure._applied_payload(applied_values)
    )
    forged_applied = _forged(one_pass, **applied_values)
    with pytest.raises(ValueError):
        owner.validate_applied_decision(forged_applied)

    certificate = owner.certificate
    certificate_values = {
        name: getattr(certificate, name) for name in closure._certificate_fields()
    }
    forged_argument = certificate.f37_arithmetic_argument + ";forged"
    certificate_values["f37_arithmetic_argument"] = forged_argument
    certificate_values["f37_arithmetic_argument_sha256"] = closure._SEMANTIC_DIGEST(
        {
            "domain": "cp43-f37-arithmetic-argument-v1",
            "argument": forged_argument,
        }
    )
    certificate_values["certificate_sha256"] = closure._SEMANTIC_DIGEST(
        closure._certificate_payload(certificate_values)
    )
    forged_certificate = _forged(certificate, **certificate_values)
    with pytest.raises(ValueError):
        closure._validate_certificate(forged_certificate)

    for text_field in ("claim_evidence_ledger", "product_uniform_corollary"):
        text_values = {
            name: getattr(certificate, name) for name in closure._certificate_fields()
        }
        forged_text = text_values[text_field] + ";forged"
        text_values[text_field] = forged_text
        if text_field == "claim_evidence_ledger":
            text_values["claim_evidence_ledger_sha256"] = closure._SEMANTIC_DIGEST(
                {
                    "domain": "cp43-claim-evidence-ledger-v1",
                    "ledger": forged_text,
                }
            )
        text_values["certificate_sha256"] = closure._SEMANTIC_DIGEST(
            closure._certificate_payload(text_values)
        )
        forged_text_certificate = _forged(certificate, **text_values)
        with pytest.raises(ValueError):
            closure._validate_certificate(forged_text_certificate)


def test_source_has_no_rng_calls_or_parent_operational_calls():
    source_path = Path(closure.__file__)
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_imports = {"random", "numpy.random", "torch.random", "secrets"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(alias.name not in forbidden_imports for alias in node.names)
        if isinstance(node, ast.ImportFrom):
            assert node.module not in forbidden_imports
    assert ".prepare(" not in source
    assert ".decide(" not in source
    assert ".resolve(" not in source
    assert ".coordinate(" not in source
    assert ".admit(" not in source


def test_current_live_witness_uses_an_interior_adaptive_quota(one_pass):
    rows = one_pass.predecision_result.checkpoint42_result.rows
    assert rows
    assert all(0 < row.acceptance_quota < (1 << 64) for row in rows)
    assert all(row.threshold_branch == "adaptive_decimal" for row in rows)
    assert one_pass.certificate.natural_f37_reachability_resolved is False
    assert one_pass.certificate.whole_record_equivalence_certified is False
