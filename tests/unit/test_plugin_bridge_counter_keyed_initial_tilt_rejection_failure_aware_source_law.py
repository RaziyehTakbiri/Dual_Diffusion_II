"""Hostile tests for checkpoint-41 failure-aware abstract source laws."""

import ast
from fractions import Fraction
import importlib
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
    "torch", reason="failure-aware rejection source laws require PyTorch"
)

source_law = importlib.import_module(  # noqa: E402
    "heterodiff.processes.plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "failure_aware_source_law"
)
checkpoint40 = importlib.import_module(  # noqa: E402
    "tests.unit.test_plugin_bridge_counter_keyed_initial_tilt_rejection_admission"
)


SOURCE_POLICY = getattr(
    source_law,
    "PLUGIN_BRIDGE_INITIAL_TILT_REJECTION_FAILURE_AWARE_SOURCE_LAW_POLICY",
)
SOURCE_ROLE = "a" * 64
ADMISSION_ROLE = "9" * 64
DYADIC_DENOMINATOR = 1 << 64
_DECLARE = getattr(
    source_law,
    "declare_initial_tilt_rejection_predecision_factorization_hypothesis",
)
_VALIDATE_HYPOTHESIS = getattr(
    source_law,
    "validate_initial_tilt_rejection_predecision_factorization_hypothesis",
)
_CERTIFY = getattr(
    source_law,
    "certify_initial_tilt_rejection_failure_aware_source_law",
)
_MATCHING = getattr(
    source_law,
    "require_matching_initial_tilt_rejection_failure_aware_source_law",
)
_VALIDATE_CERTIFICATE = getattr(
    source_law,
    "validate_initial_tilt_rejection_failure_aware_source_law_certificate",
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


def _redigested(record, fields, payload, digest_name, **updates):
    values = {name: updates.get(name, getattr(record, name)) for name in fields()}
    values[digest_name] = "0" * 64
    values[digest_name] = source_law._semantic_digest(payload(values))
    return _forged(record, **values)


class _EqualityBomb:
    def __init__(self):
        self.calls = 0

    def __eq__(self, other):
        del other
        self.calls += 1
        raise AssertionError("hostile equality must not execute")

    def __ne__(self, other):
        del other
        self.calls += 1
        raise AssertionError("hostile inequality must not execute")


def _profile_parent_operations(callback):
    watched = {
        "admit": source_law._CP40_ADMIT.__code__,
        "coordinate": source_law._CP39_COORDINATE.__code__,
        "resolve": source_law._CP38_RESOLVE.__code__,
        "decide": source_law._CP37_DECIDE.__code__,
        "prepare": source_law._CP36_PREPARE.__code__,
    }
    calls = {name: 0 for name in watched}

    def profiler(frame, event, arg):
        del arg
        if event == "call":
            for name, code in watched.items():
                if frame.f_code is code:
                    calls[name] += 1
        return profiler

    previous = sys.getprofile()
    sys.setprofile(profiler)
    try:
        result = callback()
    finally:
        sys.setprofile(previous)
    return result, calls


def _certification_only_lineage():
    checkpoint39 = checkpoint40.checkpoint39
    checkpoint38 = checkpoint39.checkpoint38
    checkpoint37 = checkpoint38.checkpoint37
    checkpoint36 = checkpoint38.checkpoint36
    checkpoint28 = checkpoint36.checkpoint28
    checkpoint30 = checkpoint36.checkpoint30

    bundle = checkpoint28.atomic_bundle.__wrapped__()
    potential = bundle["potential_composer"]
    bundle["totalized_guide"] = potential.totalized_guide
    bundle["totalized_residual"] = potential.totalized_residual
    bundle["initial_tilt"] = checkpoint30._certify(bundle)
    _, preparation_owner = checkpoint36._certify(
        bundle,
        attempt_budget=1,
        role="2" * 64,
    )
    decision_owner = checkpoint37._CERTIFY(
        preparation_owner,
        decision_policy=checkpoint37.DECISION_POLICY,
        decision_role_sha256="3" * 64,
    )
    word_hypothesis = checkpoint38._DECLARE(
        hypothesis_scope=(
            checkpoint38.law.FIXED_BATCH_IID_UINT64_DECISION_WORD_HYPOTHESIS_SCOPE
        ),
        word_source_premise=(
            checkpoint38.law.FIXED_BATCH_IID_UINT64_DECISION_WORD_PREMISE
        ),
    )
    finite_batch_owner = checkpoint38._CERTIFY(
        decision_owner,
        word_hypothesis,
        law_policy=checkpoint38.LAW_POLICY,
        law_role_sha256="4" * 64,
    )
    coordination_owner = checkpoint39._CERTIFY(
        finite_batch_owner,
        coordination_policy=checkpoint39.COORDINATION_POLICY,
        coordination_role_sha256="5" * 64,
    )
    admission_owner = checkpoint40._CERTIFY(
        coordination_owner,
        admission_policy=checkpoint40.ADMISSION_POLICY,
        admission_role_sha256=ADMISSION_ROLE,
    )
    return {
        **bundle,
        "preparation_owner": preparation_owner,
        "decision_owner": decision_owner,
        "finite_batch_owner": finite_batch_owner,
        "coordination_owner": coordination_owner,
        "admission_owner": admission_owner,
    }


@pytest.fixture(scope="module")
def certified_bundle():
    """Build CP41 without invoking any CP36--CP40 operational method."""

    before = _rng_snapshot()

    def construct():
        bundle = _certification_only_lineage()
        admission_owner = bundle["admission_owner"]
        hypothesis = _DECLARE(
            admission_owner,
            hypothesis_scope=getattr(
                source_law,
                "INITIAL_TILT_REJECTION_PREDECISION_FACTORIZATION_" "HYPOTHESIS_SCOPE",
            ),
            factorization_premise=(
                source_law.INITIAL_TILT_REJECTION_FAILURE_AWARE_FACTORIZATION_PREMISE
            ),
        )
        owner = _CERTIFY(
            admission_owner,
            hypothesis,
            source_law_policy=SOURCE_POLICY,
            source_law_role_sha256=SOURCE_ROLE,
        )
        specification = owner.describe()
        return {
            **bundle,
            "factorization_hypothesis": hypothesis,
            "source_law_owner": owner,
            "specification": specification,
        }

    bundle, calls = _profile_parent_operations(construct)
    _assert_rng_unchanged(before)
    assert calls == {
        "admit": 0,
        "coordinate": 0,
        "resolve": 0,
        "decide": 0,
        "prepare": 0,
    }
    bundle["construction_calls"] = calls
    return bundle


@pytest.fixture(scope="module")
def two_attempt_bundle(certified_bundle):
    """Reuse the atomic base to certify an operation-free two-attempt law."""

    checkpoint39 = checkpoint40.checkpoint39
    checkpoint38 = checkpoint39.checkpoint38
    checkpoint37 = checkpoint38.checkpoint37
    checkpoint36 = checkpoint38.checkpoint36
    before = _rng_snapshot()

    def construct():
        _, preparation_owner = checkpoint36._certify(
            certified_bundle,
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
        factorization_hypothesis = _DECLARE(
            admission_owner,
            hypothesis_scope=getattr(
                source_law,
                "INITIAL_TILT_REJECTION_PREDECISION_FACTORIZATION_" "HYPOTHESIS_SCOPE",
            ),
            factorization_premise=(
                source_law.INITIAL_TILT_REJECTION_FAILURE_AWARE_FACTORIZATION_PREMISE
            ),
        )
        owner = _CERTIFY(
            admission_owner,
            factorization_hypothesis,
            source_law_policy=SOURCE_POLICY,
            source_law_role_sha256="1" * 64,
        )
        return {
            "preparation_owner": preparation_owner,
            "decision_owner": decision_owner,
            "finite_batch_owner": finite_batch_owner,
            "coordination_owner": coordination_owner,
            "admission_owner": admission_owner,
            "factorization_hypothesis": factorization_hypothesis,
            "source_law_owner": owner,
            "specification": owner.describe(),
        }

    bundle, calls = _profile_parent_operations(construct)
    _assert_rng_unchanged(before)
    assert calls == {
        "admit": 0,
        "coordinate": 0,
        "resolve": 0,
        "decide": 0,
        "prepare": 0,
    }
    bundle["construction_calls"] = calls
    return bundle


def test_public_api_constants_signatures_and_exports_are_exact(certified_bundle):
    owner = certified_bundle["source_law_owner"]
    expected_exports = (
        "PLUGIN_BRIDGE_INITIAL_TILT_REJECTION_FAILURE_AWARE_SOURCE_LAW_"
        "SCHEMA_VERSION",
        "PLUGIN_BRIDGE_INITIAL_TILT_REJECTION_FAILURE_AWARE_SOURCE_LAW_POLICY",
        "PLUGIN_BRIDGE_INITIAL_TILT_REJECTION_FAILURE_AWARE_SOURCE_LAW_SCOPE",
        "INITIAL_TILT_REJECTION_FAILURE_AWARE_SOURCE_ATOMS",
        "INITIAL_TILT_REJECTION_FAILURE_AWARE_SOURCE_PREMISE",
        "INITIAL_TILT_REJECTION_FAILURE_AWARE_FACTORIZATION_PREMISE",
        "INITIAL_TILT_REJECTION_PREDECISION_FACTORIZATION_HYPOTHESIS_" "SCHEMA_VERSION",
        "INITIAL_TILT_REJECTION_PREDECISION_FACTORIZATION_HYPOTHESIS_SCOPE",
        "INITIAL_TILT_REJECTION_FAILURE_AWARE_FIBER_DEFINITION",
        "INITIAL_TILT_REJECTION_FAILURE_AWARE_AUGMENTED_LAW",
        "INITIAL_TILT_REJECTION_FAILURE_AWARE_NORMALIZATION_THEOREM",
        "INITIAL_TILT_REJECTION_FAILURE_AWARE_AUGMENTED_TV_THEOREM",
        "INITIAL_TILT_REJECTION_FAILURE_AWARE_SELECTED_TV_THEOREM",
        "INITIAL_TILT_REJECTION_FAILURE_AWARE_SELECTED_TV_PROOF",
        "INITIAL_TILT_REJECTION_FAILURE_AWARE_DATA_PROCESSING_THEOREM",
        "INITIAL_TILT_REJECTION_FAILURE_AWARE_SOURCE_DYADIC_DENOMINATOR",
        "INITIAL_TILT_REJECTION_FAILURE_AWARE_SOURCE_MAX_COORDINATES",
        "InitialTiltRejectionPredecisionFactorizationHypothesis",
        "CounterKeyedInitialTiltRejectionFailureAwareSourceLawCertificate",
        "CounterKeyedInitialTiltRejectionFailureAwareSourceLawSymbolicSpecification",
        "CounterKeyedInitialTiltRejectionFailureAwareSourceLawOwner",
        "PluginBridgeCounterKeyedInitialTiltRejectionFailureAwareSourceLawError",
        "declare_initial_tilt_rejection_predecision_factorization_hypothesis",
        "validate_initial_tilt_rejection_predecision_factorization_hypothesis",
        "certify_initial_tilt_rejection_failure_aware_source_law",
        "require_matching_initial_tilt_rejection_failure_aware_source_law",
        "validate_initial_tilt_rejection_failure_aware_source_law_certificate",
    )
    assert tuple(source_law.__all__) == expected_exports
    assert len(source_law.__all__) == len(set(source_law.__all__))
    assert all(hasattr(source_law, name) for name in source_law.__all__)
    assert source_law.INITIAL_TILT_REJECTION_FAILURE_AWARE_SOURCE_ATOMS == (
        "preparation_failure",
        "quota_certification_failure",
        "exhaustion",
        "configuration",
    )
    assert (
        source_law.INITIAL_TILT_REJECTION_FAILURE_AWARE_SOURCE_DYADIC_DENOMINATOR
        == DYADIC_DENOMINATOR
    )
    assert source_law.INITIAL_TILT_REJECTION_FAILURE_AWARE_SOURCE_MAX_COORDINATES == (
        65_536
    )
    assert tuple(inspect.signature(owner.describe).parameters) == ()
    assert tuple(inspect.signature(owner.validate_specification).parameters) == (
        "specification",
    )
    for function in (_CERTIFY, _MATCHING, _VALIDATE_CERTIFICATE):
        parameters = inspect.signature(function).parameters
        assert parameters["source_law_policy"].kind is inspect.Parameter.KEYWORD_ONLY
        assert (
            parameters["source_law_role_sha256"].kind is inspect.Parameter.KEYWORD_ONLY
        )
    declare_parameters = inspect.signature(_DECLARE).parameters
    assert declare_parameters["hypothesis_scope"].kind is (
        inspect.Parameter.KEYWORD_ONLY
    )
    assert declare_parameters["factorization_premise"].kind is (
        inspect.Parameter.KEYWORD_ONLY
    )


def test_explicit_factorization_hypothesis_is_bound_and_not_executable_proof(
    certified_bundle,
):
    hypothesis = certified_bundle["factorization_hypothesis"]
    preparation = certified_bundle["preparation_owner"].certificate
    finite = certified_bundle["finite_batch_owner"].certificate
    assert _VALIDATE_HYPOTHESIS(hypothesis) is hypothesis
    assert hypothesis.checkpoint36_word_family_hypothesis is (
        preparation.word_family_hypothesis
    )
    assert hypothesis.checkpoint38_word_law_hypothesis is finite.word_law_hypothesis
    assert hypothesis.attempt_budget == 1
    assert hypothesis.proposal_word_count == 3
    assert hypothesis.decision_word_count == 1
    assert hypothesis.abstract_functional_noninterference_assumed is True
    assert hypothesis.existing_artifacts_motivate_but_do_not_prove_factorization
    assert hypothesis.executable_arbitrary_word_evaluator_equivalence_proved is False
    assert hypothesis.live_preparation_failure_independence_certified is False
    assert hypothesis.live_philox_statement is False


def test_certificate_binds_exact_transitive_ancestry_and_conservative_claims(
    certified_bundle,
):
    owner = certified_bundle["source_law_owner"]
    certificate = owner.certificate
    assert owner.admission_owner is certified_bundle["admission_owner"]
    assert (
        owner.factorization_hypothesis is certified_bundle["factorization_hypothesis"]
    )
    assert certificate.checkpoint40_certificate is (
        certified_bundle["admission_owner"].certificate
    )
    assert certificate.checkpoint39_certificate is (
        certified_bundle["coordination_owner"].certificate
    )
    assert certificate.checkpoint38_certificate is (
        certified_bundle["finite_batch_owner"].certificate
    )
    assert certificate.checkpoint37_certificate is (
        certified_bundle["decision_owner"].certificate
    )
    assert certificate.checkpoint36_certificate is (
        certified_bundle["preparation_owner"].certificate
    )
    assert certificate.checkpoint40_owner_runtime_identity == id(
        certified_bundle["admission_owner"]
    )
    for name in source_law._CERTIFICATE_POSITIVE_FLAGS:
        assert getattr(certificate, name) is True
    for name in source_law._CERTIFICATE_NEGATIVE_FLAGS:
        assert getattr(certificate, name) is False
    assert certificate.reserved_decision_coordinate_partition_certified is True
    assert certificate.functional_noninterference_proved_by_executable_evaluator is (
        False
    )
    assert not hasattr(
        certificate,
        "reserved_decision_coordinate_factorization_certified",
    )
    assert (
        _VALIDATE_CERTIFICATE(
            owner.admission_owner,
            owner.factorization_hypothesis,
            owner,
            source_law_policy=SOURCE_POLICY,
            source_law_role_sha256=SOURCE_ROLE,
        )
        is certificate
    )


def test_coordinate_partition_uses_final_block_as_decision_oracle(certified_bundle):
    certificate = certified_bundle["source_law_owner"].certificate
    specification = certified_bundle["specification"]
    preparation = certified_bundle["preparation_owner"].certificate
    assert preparation.block_raw64_word_counts == (3, 1)
    assert preparation.blocks_per_attempt == 2
    assert preparation.reference_words_per_attempt == 3
    assert certificate.proposal_words_per_attempt == 3
    assert certificate.proposal_word_count == 3
    assert certificate.decision_word_count == 1
    assert certificate.total_word_count == 4
    assert specification.full_logical_word_coordinates == (
        specification.proposal_word_coordinates
        + specification.decision_word_coordinates
    )
    assert specification.full_logical_word_coordinates == (
        (
            (0, source_law._prep.INITIAL_TILT_REJECTION_DOMAIN_TAG),
            (0, 0, source_law._prep.INITIAL_TILT_REJECTION_STAGE_INDEX, 0),
            0,
        ),
        (
            (0, source_law._prep.INITIAL_TILT_REJECTION_DOMAIN_TAG),
            (0, 0, source_law._prep.INITIAL_TILT_REJECTION_STAGE_INDEX, 0),
            1,
        ),
        (
            (0, source_law._prep.INITIAL_TILT_REJECTION_DOMAIN_TAG),
            (0, 0, source_law._prep.INITIAL_TILT_REJECTION_STAGE_INDEX, 0),
            2,
        ),
        (
            (0, source_law._prep.INITIAL_TILT_REJECTION_DOMAIN_TAG),
            (0, 0, source_law._prep.INITIAL_TILT_REJECTION_STAGE_INDEX, 1),
            0,
        ),
    )
    assert set(specification.proposal_word_coordinates).isdisjoint(
        specification.decision_word_coordinates
    )
    assert specification.full_coordinate_sha256 == certificate.full_coordinate_sha256
    assert specification.proposal_coordinate_sha256 == (
        certificate.proposal_coordinate_sha256
    )
    assert specification.decision_coordinate_sha256 == (
        certificate.decision_coordinate_sha256
    )


def test_two_attempt_coordinate_partition_is_disjoint_complete_and_bound(
    two_attempt_bundle,
):
    owner = two_attempt_bundle["source_law_owner"]
    hypothesis = two_attempt_bundle["factorization_hypothesis"]
    certificate = owner.certificate
    specification = two_attempt_bundle["specification"]
    preparation = two_attempt_bundle["preparation_owner"].certificate
    domain_tag = source_law._prep.INITIAL_TILT_REJECTION_DOMAIN_TAG
    stage = source_law._prep.INITIAL_TILT_REJECTION_STAGE_INDEX

    def coordinate(block, offset):
        return ((0, domain_tag), (0, 0, stage, block), offset)

    expected_full = (
        coordinate(0, 0),
        coordinate(0, 1),
        coordinate(0, 2),
        coordinate(1, 0),
        coordinate(2, 0),
        coordinate(2, 1),
        coordinate(2, 2),
        coordinate(3, 0),
    )
    expected_proposal = (
        coordinate(0, 0),
        coordinate(0, 1),
        coordinate(0, 2),
        coordinate(2, 0),
        coordinate(2, 1),
        coordinate(2, 2),
    )
    expected_decision = (coordinate(1, 0), coordinate(3, 0))
    assert preparation.attempt_budget == 2
    assert preparation.block_raw64_word_counts == (3, 1)
    assert preparation.blocks_per_attempt == 2
    assert hypothesis.attempt_budget == certificate.attempt_budget == 2
    assert hypothesis.proposal_word_count == certificate.proposal_word_count == 6
    assert hypothesis.decision_word_count == certificate.decision_word_count == 2
    assert certificate.proposal_words_per_attempt == 3
    assert certificate.total_word_count == 8
    assert certificate.common_dyadic_denominator_exponent == 8
    assert specification.full_logical_word_coordinates == expected_full
    assert specification.proposal_word_coordinates == expected_proposal
    assert specification.decision_word_coordinates == expected_decision
    assert specification.proposal_word_count == 6
    assert specification.decision_word_count == 2
    assert specification.total_word_count == 8
    assert specification.common_dyadic_denominator_exponent == 8
    assert set(expected_proposal).isdisjoint(expected_decision)
    assert set(expected_proposal) | set(expected_decision) == set(expected_full)
    assert len(set(expected_full)) == len(expected_full) == 8
    assert expected_proposal + expected_decision != expected_full
    for name in (
        "full_coordinate_sha256",
        "proposal_coordinate_sha256",
        "decision_coordinate_sha256",
    ):
        assert getattr(hypothesis, name) == getattr(certificate, name)
        assert getattr(certificate, name) == getattr(specification, name)
    assert owner.admission_owner is two_attempt_bundle["admission_owner"]
    assert owner.factorization_hypothesis is hypothesis
    assert owner.describe() is specification
    assert two_attempt_bundle["construction_calls"] == {
        "admit": 0,
        "coordinate": 0,
        "resolve": 0,
        "decide": 0,
        "prepare": 0,
    }


def test_symbolic_specification_has_exact_atoms_counts_and_absent_masses(
    certified_bundle,
):
    specification = certified_bundle["specification"]
    certificate = certified_bundle["source_law_owner"].certificate
    assert specification.certificate is certificate
    assert specification.source_atoms == (
        "preparation_failure",
        "quota_certification_failure",
        "exhaustion",
        "configuration",
    )
    assert specification.attempt_budget == 1
    assert specification.raw_word_domain_size == DYADIC_DENOMINATOR
    assert specification.proposal_word_count == 3
    assert specification.decision_word_count == 1
    assert specification.total_word_count == 4
    assert specification.common_dyadic_denominator_base == DYADIC_DENOMINATOR
    assert specification.common_dyadic_denominator_exponent == 4
    assert certificate.common_dyadic_denominator_exponent == 4
    for name in source_law._SPECIFICATION_ABSENT_FIELDS:
        assert getattr(specification, name) is None
    for name in source_law._SPECIFICATION_POSITIVE_FLAGS:
        assert getattr(specification, name) is True
    for name in source_law._SPECIFICATION_NEGATIVE_FLAGS:
        assert getattr(specification, name) is False
    assert specification.universal_augmented_tv_strict_upper_numerator == 1
    assert (
        specification.universal_augmented_tv_strict_upper_denominator
        == DYADIC_DENOMINATOR
    )
    assert owner_describe_and_validate(certified_bundle) is specification


def owner_describe_and_validate(certified_bundle):
    owner = certified_bundle["source_law_owner"]
    described = owner.describe()
    assert owner.validate_specification(described) is described
    return described


def test_construction_description_and_validation_make_zero_parent_operational_calls(
    certified_bundle,
):
    owner = certified_bundle["source_law_owner"]
    before = _rng_snapshot()
    result, calls = _profile_parent_operations(
        lambda: (owner.describe(), owner.validate_specification(owner.describe()))
    )
    _assert_rng_unchanged(before)
    assert result == (
        certified_bundle["specification"],
        certified_bundle["specification"],
    )
    assert (
        certified_bundle["construction_calls"]
        == calls
        == {
            "admit": 0,
            "coordinate": 0,
            "resolve": 0,
            "decide": 0,
            "prepare": 0,
        }
    )


def test_symbolic_formulas_name_rho_zero_factor_one_and_positive_selection_gate(
    certified_bundle,
):
    specification = certified_bundle["specification"]
    assert specification.source_premise == (
        source_law.INITIAL_TILT_REJECTION_FAILURE_AWARE_SOURCE_PREMISE
    )
    assert specification.factorization_premise == (
        source_law.INITIAL_TILT_REJECTION_FAILURE_AWARE_FACTORIZATION_PREMISE
    )
    assert specification.fiber_definition == (
        source_law.INITIAL_TILT_REJECTION_FAILURE_AWARE_FIBER_DEFINITION
    )
    assert specification.augmented_law_definition == (
        source_law.INITIAL_TILT_REJECTION_FAILURE_AWARE_AUGMENTED_LAW
    )
    assert specification.normalization_theorem == (
        source_law.INITIAL_TILT_REJECTION_FAILURE_AWARE_NORMALIZATION_THEOREM
    )
    assert specification.augmented_tv_theorem == (
        source_law.INITIAL_TILT_REJECTION_FAILURE_AWARE_AUGMENTED_TV_THEOREM
    )
    assert specification.selected_tv_theorem == (
        source_law.INITIAL_TILT_REJECTION_FAILURE_AWARE_SELECTED_TV_THEOREM
    )
    assert specification.selected_tv_proof == (
        source_law.INITIAL_TILT_REJECTION_FAILURE_AWARE_SELECTED_TV_PROOF
    )
    assert specification.data_processing_theorem == (
        source_law.INITIAL_TILT_REJECTION_FAILURE_AWARE_DATA_PROCESSING_THEOREM
    )
    assert "if-rho=0-then-TV(P_aug,Q_aug)=0" in specification.augmented_tv_theorem
    assert "if-S_Q=0-dyadic-selected-law-and-bound-undefined" in (
        specification.selected_tv_theorem
    )
    assert "Delta=TV(P_aug,Q_aug)" in specification.selected_tv_theorem
    assert "TV(P,Q)/max(a,b)" in specification.selected_tv_proof
    assert "Delta/S_P" in specification.selected_tv_theorem
    assert "rho*A/(D*S_Q)" in specification.selected_tv_theorem
    assert "no-product-mixture-formula-is-claimed" in (
        specification.data_processing_theorem
    )


def _tiny_failure_aware_mixture(predecisions, kernels):
    """Independently aggregate an equally weighted finite source."""

    source_weight = Fraction(1, len(predecisions))
    masses = {}
    for outcome in predecisions:
        if outcome in ("F36", "F37"):
            atom = ("failure", outcome)
            masses[atom] = masses.get(atom, Fraction(0)) + source_weight
            continue
        kernel = kernels[outcome]
        for atom, probability in kernel:
            masses[atom] = masses.get(atom, Fraction(0)) + (source_weight * probability)
    return masses


def _total_variation(left, right):
    atoms = set(left) | set(right)
    numerator = sum(
        (abs(left.get(atom, 0) - right.get(atom, 0)) for atom in atoms),
        Fraction(0),
    )
    return numerator / 2


def test_independent_tiny_mixture_normalizes_and_aggregates_duplicate_states():
    empty = ("configuration", ())
    state = ("configuration", ("x",))
    exhaustion = ("exhaustion", None)
    kernels = {
        "B0": (
            (exhaustion, Fraction(1, 4)),
            (empty, Fraction(1, 4)),
            (empty, Fraction(1, 4)),
            (state, Fraction(1, 4)),
        ),
        "B1": (
            (exhaustion, Fraction(1, 2)),
            (empty, Fraction(1, 4)),
            (state, Fraction(1, 4)),
        ),
    }
    mixture = _tiny_failure_aware_mixture(("F36", "F37", "B0", "B1"), kernels)
    assert mixture == {
        ("failure", "F36"): Fraction(1, 4),
        ("failure", "F37"): Fraction(1, 4),
        exhaustion: Fraction(3, 16),
        empty: Fraction(3, 16),
        state: Fraction(1, 8),
    }
    assert sum(mixture.values(), Fraction(0)) == 1
    assert empty != exhaustion
    assert mixture[empty] == Fraction(3, 16)


def test_independent_all_failure_branch_has_rho_zero_identity_and_no_selection():
    predecisions = ("F36", "F37", "F36", "F37")
    dyadic = _tiny_failure_aware_mixture(predecisions, {})
    ideal = _tiny_failure_aware_mixture(predecisions, {})
    assert (
        dyadic
        == ideal
        == {
            ("failure", "F36"): Fraction(1, 2),
            ("failure", "F37"): Fraction(1, 2),
        }
    )
    assert _total_variation(ideal, dyadic) == 0
    selection_mass = sum(
        (mass for atom, mass in dyadic.items() if atom[0] == "configuration"),
        Fraction(0),
    )
    assert selection_mass == 0


def test_independent_positive_rho_can_have_ideal_but_no_dyadic_selected_law():
    configuration = ("configuration", ("x",))
    exhaustion = ("exhaustion", None)
    predecisions = ("F36", "B")
    dyadic = _tiny_failure_aware_mixture(
        predecisions,
        {"B": ((exhaustion, Fraction(1)),)},
    )
    ideal = _tiny_failure_aware_mixture(
        predecisions,
        {
            "B": (
                (exhaustion, Fraction(3, 4)),
                (configuration, Fraction(1, 4)),
            )
        },
    )

    def selected_law(law):
        selected = {
            atom: mass for atom, mass in law.items() if atom[0] == "configuration"
        }
        selection_mass = sum(selected.values(), Fraction(0))
        if selection_mass == 0:
            return selection_mass, None
        return selection_mass, {
            atom: mass / selection_mass for atom, mass in selected.items()
        }

    rho = Fraction(1, 2)
    ideal_selection_mass, ideal_selected = selected_law(ideal)
    dyadic_selection_mass, dyadic_selected = selected_law(dyadic)
    comparison = (
        None
        if ideal_selected is None or dyadic_selected is None
        else _total_variation(ideal_selected, dyadic_selected)
    )
    assert rho > 0
    assert ideal_selection_mass == Fraction(1, 8)
    assert dyadic_selection_mass == 0 < ideal_selection_mass
    assert ideal_selected == {configuration: Fraction(1)}
    assert dyadic_selected is None
    assert comparison is None
    assert _total_variation(ideal, dyadic) == Fraction(1, 8)
    assert "Delta=TV(P_aug,Q_aug)" in (
        source_law.INITIAL_TILT_REJECTION_FAILURE_AWARE_SELECTED_TV_THEOREM
    )


def test_independent_conditioning_uses_the_factor_one_maximum_mass_bound():
    selected = {"x", "y"}
    ideal = {
        "x": Fraction(3, 10),
        "y": Fraction(1, 5),
        "exhaustion": Fraction(1, 10),
        "failure": Fraction(2, 5),
    }
    dyadic = {
        "x": Fraction(1, 4),
        "y": Fraction(3, 20),
        "exhaustion": Fraction(1, 5),
        "failure": Fraction(2, 5),
    }
    ideal_mass = sum((ideal[atom] for atom in selected), Fraction(0))
    dyadic_mass = sum((dyadic[atom] for atom in selected), Fraction(0))
    ideal_selected = {atom: ideal[atom] / ideal_mass for atom in selected}
    dyadic_selected = {atom: dyadic[atom] / dyadic_mass for atom in selected}
    augmented_tv = _total_variation(ideal, dyadic)
    selected_tv = _total_variation(ideal_selected, dyadic_selected)
    assert ideal_mass == Fraction(1, 2) >= dyadic_mass == Fraction(2, 5)
    assert augmented_tv == Fraction(1, 10)
    assert selected_tv == Fraction(1, 40)
    assert selected_tv <= augmented_tv / max(ideal_mass, dyadic_mass)


def test_matching_requires_exact_parent_hypothesis_policy_role_and_owner(
    certified_bundle,
):
    owner = certified_bundle["source_law_owner"]
    parent = certified_bundle["admission_owner"]
    hypothesis = certified_bundle["factorization_hypothesis"]
    assert (
        _MATCHING(
            parent,
            hypothesis,
            owner,
            source_law_policy=SOURCE_POLICY,
            source_law_role_sha256=SOURCE_ROLE,
        )
        is owner
    )
    alien_parent = checkpoint40._CERTIFY(
        certified_bundle["coordination_owner"],
        admission_policy=checkpoint40.ADMISSION_POLICY,
        admission_role_sha256="b" * 64,
    )
    with pytest.raises(ValueError, match="another CP40 parent"):
        _MATCHING(
            alien_parent,
            hypothesis,
            owner,
            source_law_policy=SOURCE_POLICY,
            source_law_role_sha256=SOURCE_ROLE,
        )
    alien_hypothesis = _DECLARE(
        parent,
        hypothesis_scope=getattr(
            source_law,
            "INITIAL_TILT_REJECTION_PREDECISION_FACTORIZATION_" "HYPOTHESIS_SCOPE",
        ),
        factorization_premise=(
            source_law.INITIAL_TILT_REJECTION_FAILURE_AWARE_FACTORIZATION_PREMISE
        ),
    )
    assert alien_hypothesis is not hypothesis
    assert alien_hypothesis.hypothesis_sha256 == hypothesis.hypothesis_sha256
    with pytest.raises(ValueError, match="another factorization premise"):
        _MATCHING(
            parent,
            alien_hypothesis,
            owner,
            source_law_policy=SOURCE_POLICY,
            source_law_role_sha256=SOURCE_ROLE,
        )
    with pytest.raises(ValueError, match="source_law_policy"):
        _MATCHING(
            parent,
            hypothesis,
            owner,
            source_law_policy=SOURCE_POLICY + "x",
            source_law_role_sha256=SOURCE_ROLE,
        )
    with pytest.raises(ValueError, match="role"):
        _MATCHING(
            parent,
            hypothesis,
            owner,
            source_law_policy=SOURCE_POLICY,
            source_law_role_sha256="c" * 64,
        )
    with pytest.raises(TypeError, match="wrong exact CP41 type"):
        _MATCHING(
            parent,
            hypothesis,
            object(),
            source_law_policy=SOURCE_POLICY,
            source_law_role_sha256=SOURCE_ROLE,
        )


def test_hypothesis_forgery_and_redigested_semantic_changes_fail_closed(
    certified_bundle,
):
    hypothesis = certified_bundle["factorization_hypothesis"]
    forged = _forged(
        hypothesis,
        abstract_functional_noninterference_assumed=False,
    )
    with pytest.raises(
        ValueError,
        match="abstract_functional_noninterference_assumed differs",
    ):
        _VALIDATE_HYPOTHESIS(forged)
    redigested = _redigested(
        hypothesis,
        source_law._factorization_hypothesis_fields,
        source_law._hypothesis_payload,
        "hypothesis_sha256",
        abstract_functional_noninterference_assumed=False,
    )
    with pytest.raises(ValueError, match="differs"):
        _VALIDATE_HYPOTHESIS(redigested)
    bad_parent_digest = _redigested(
        hypothesis,
        source_law._factorization_hypothesis_fields,
        source_law._hypothesis_payload,
        "hypothesis_sha256",
        checkpoint36_word_family_hypothesis_sha256="d" * 64,
    )
    with pytest.raises(ValueError, match="parent digest differs"):
        _VALIDATE_HYPOTHESIS(bad_parent_digest)


def test_redigested_factorization_word_counts_must_match_the_coordinate_split(
    certified_bundle,
):
    hypothesis = certified_bundle["factorization_hypothesis"]
    redigested = _redigested(
        hypothesis,
        source_law._factorization_hypothesis_fields,
        source_law._hypothesis_payload,
        "hypothesis_sha256",
        proposal_word_count=hypothesis.proposal_word_count + 1,
    )
    with pytest.raises(
        ValueError,
        match="factorization hypothesis proposal count differs from CP36",
    ):
        _CERTIFY(
            certified_bundle["admission_owner"],
            redigested,
            source_law_policy=SOURCE_POLICY,
            source_law_role_sha256=SOURCE_ROLE,
        )


def test_redigested_certificate_and_specification_forgery_fail_closed(
    certified_bundle,
):
    owner = certified_bundle["source_law_owner"]
    certificate = owner.certificate
    specification = certified_bundle["specification"]
    certificate_forgery = _redigested(
        certificate,
        source_law._certificate_fields,
        source_law._certificate_payload,
        "certificate_sha256",
        formal_test28_closed=True,
    )
    with pytest.raises(ValueError, match="differs"):
        source_law._validate_certificate(certificate_forgery)
    parent_splice = _redigested(
        certificate,
        source_law._certificate_fields,
        source_law._certificate_payload,
        "certificate_sha256",
        checkpoint39_certificate=_forged(certificate.checkpoint39_certificate),
    )
    with pytest.raises(ValueError, match="CP40-to-CP39 identity differs"):
        source_law._validate_certificate(parent_splice)
    numeric_forgery = _redigested(
        specification,
        source_law._specification_fields,
        source_law._specification_payload,
        "specification_sha256",
        successful_source_mass_rho=1,
    )
    with pytest.raises(ValueError, match="must be absent"):
        source_law._validate_specification(numeric_forgery)
    coordinate_forgery = _redigested(
        specification,
        source_law._specification_fields,
        source_law._specification_payload,
        "specification_sha256",
        proposal_word_coordinates=tuple(
            reversed(specification.proposal_word_coordinates)
        ),
    )
    with pytest.raises(ValueError, match="coordinate partition differs"):
        source_law._validate_specification(coordinate_forgery)
    alien_certificate = _forged(certificate)
    specification_splice = _forged(
        specification,
        certificate=alien_certificate,
    )
    with pytest.raises(ValueError, match="certificate identity differs"):
        owner.validate_specification(specification_splice)


def test_forged_owner_identity_and_callback_changes_fail_before_description(
    certified_bundle,
):
    owner = certified_bundle["source_law_owner"]
    forged_identity = _forge_owner(
        owner,
        _certificate_identity=_forged(owner.certificate),
    )
    with pytest.raises(ValueError, match="owner identity changed"):
        forged_identity.describe()

    calls = {"builder": 0}

    def forbidden(*args, **kwargs):
        del args, kwargs
        calls["builder"] += 1
        raise AssertionError("substituted builder must not execute")

    forged_callback = _forge_owner(owner, _specification_builder=forbidden)
    with pytest.raises(ValueError, match="cached callback changed"):
        forged_callback.describe()
    assert calls == {"builder": 0}


def test_declaration_preflights_parent_scope_and_premise(certified_bundle):
    parent = certified_bundle["admission_owner"]
    scope = getattr(
        source_law,
        "INITIAL_TILT_REJECTION_PREDECISION_FACTORIZATION_HYPOTHESIS_SCOPE",
    )
    premise = source_law.INITIAL_TILT_REJECTION_FAILURE_AWARE_FACTORIZATION_PREMISE
    with pytest.raises(TypeError, match="wrong exact CP40 type"):
        _DECLARE(
            certified_bundle["coordination_owner"],
            hypothesis_scope=scope,
            factorization_premise=premise,
        )
    with pytest.raises(ValueError, match="hypothesis_scope differs"):
        _DECLARE(
            parent,
            hypothesis_scope=scope + "x",
            factorization_premise=premise,
        )
    with pytest.raises(ValueError, match="factorization_premise differs"):
        _DECLARE(
            parent,
            hypothesis_scope=scope,
            factorization_premise=premise + "x",
        )
    with pytest.raises(TypeError, match="exact text"):
        _DECLARE(
            parent,
            hypothesis_scope=True,
            factorization_premise=premise,
        )


def test_records_and_owner_are_immutable_sealed_nonpickle_and_nonsubclass(
    certified_bundle,
):
    owner = certified_bundle["source_law_owner"]
    records = (
        certified_bundle["factorization_hypothesis"],
        owner.certificate,
        certified_bundle["specification"],
    )
    for record in records:
        with pytest.raises((AttributeError, TypeError)):
            setattr(record, "schema_version", "forged")
        with pytest.raises(TypeError):
            pickle.dumps(record)
    with pytest.raises(AttributeError):
        owner._certificate = owner.certificate
    with pytest.raises(AttributeError):
        del owner._certificate
    with pytest.raises(TypeError):
        pickle.dumps(owner)
    specification_type = getattr(
        source_law,
        "CounterKeyedInitialTiltRejectionFailureAwareSourceLawSymbolicSpecification",
    )
    classes = (
        source_law.InitialTiltRejectionPredecisionFactorizationHypothesis,
        source_law.CounterKeyedInitialTiltRejectionFailureAwareSourceLawCertificate,
        specification_type,
    )
    for cls in classes:
        with pytest.raises(TypeError):
            cls(_construction_token=object())
        with pytest.raises(TypeError):

            class ForbiddenRecordSubclass(cls):
                pass

    with pytest.raises(TypeError):

        class ForbiddenOwnerSubclass(
            source_law.CounterKeyedInitialTiltRejectionFailureAwareSourceLawOwner
        ):
            pass


def test_local_surface_substitution_fails_before_hostile_wrapper_executes(
    certified_bundle,
):
    owner = certified_bundle["source_law_owner"]
    original = source_law._semantic_digest
    calls = {"wrapper": 0}

    def forbidden(*args, **kwargs):
        del args, kwargs
        calls["wrapper"] += 1
        raise AssertionError("substituted local surface must not execute")

    source_law._semantic_digest = forbidden
    try:
        with pytest.raises(
            ValueError,
            match="operation surface _semantic_digest changed",
        ):
            owner.describe()
    finally:
        source_law._semantic_digest = original
    assert calls == {"wrapper": 0}


def test_dependency_global_and_class_surface_substitution_fail_closed(
    certified_bundle,
):
    owner = certified_bundle["source_law_owner"]
    calls = {"operation": 0}

    def forbidden(*args, **kwargs):
        del args, kwargs
        calls["operation"] += 1
        raise AssertionError("substituted parent operation must not execute")

    original_global = source_law._CP40_ADMIT
    source_law._CP40_ADMIT = forbidden
    try:
        with pytest.raises(ValueError, match="operation surface _CP40_ADMIT changed"):
            owner.describe()
    finally:
        source_law._CP40_ADMIT = original_global
    original_class = source_law._CP40_OWNER_TYPE.admit
    source_law._CP40_OWNER_TYPE.admit = forbidden
    try:
        with pytest.raises(ValueError, match="dependency class surface changed"):
            owner.describe()
    finally:
        source_law._CP40_OWNER_TYPE.admit = original_class
    assert calls == {"operation": 0}


def test_held_hypothesis_validator_detects_private_text_guard_substitution(
    certified_bundle,
):
    hypothesis = certified_bundle["factorization_hypothesis"]
    original = source_law._require_text
    calls = {"guard": 0}

    def forbidden(*args, **kwargs):
        del args, kwargs
        calls["guard"] += 1
        raise AssertionError("substituted text guard must not execute")

    source_law._require_text = forbidden
    try:
        with pytest.raises(
            ValueError,
            match="operation surface _require_text changed",
        ):
            _VALIDATE_HYPOTHESIS(hypothesis)
    finally:
        source_law._require_text = original
    assert calls == {"guard": 0}


def test_held_public_api_detects_late_surface_replacement_without_executing_it(
    certified_bundle,
):
    hypothesis = certified_bundle["factorization_hypothesis"]
    original = source_law._require_surfaces
    calls = {"surface": 0}

    def forbidden(*args, **kwargs):
        del args, kwargs
        calls["surface"] += 1
        raise AssertionError("substituted surface guard must not execute")

    source_law._require_surfaces = forbidden
    try:
        with pytest.raises(
            ValueError,
            match="late operation surface _require_surfaces changed",
        ):
            _VALIDATE_HYPOTHESIS(hypothesis)
    finally:
        source_law._require_surfaces = original
    assert calls == {"surface": 0}


def test_policy_substitution_is_caught_before_public_input_parsing(certified_bundle):
    original = source_law._POLICY
    source_law._POLICY = SOURCE_POLICY + "x"
    try:
        with pytest.raises(ValueError, match="operation surface _POLICY changed"):
            _CERTIFY(
                object(),
                object(),
                source_law_policy=object(),
                source_law_role_sha256=object(),
            )
    finally:
        source_law._POLICY = original


def test_hostile_source_atom_is_rejected_before_equality(certified_bundle):
    specification = certified_bundle["specification"]
    bomb = _EqualityBomb()
    forged = _forged(
        specification,
        source_atoms=(
            "preparation_failure",
            "quota_certification_failure",
            "exhaustion",
            bomb,
        ),
    )
    with pytest.raises(TypeError, match=r"source_atoms\[3\].*exact text"):
        source_law._validate_specification(forged)
    assert bomb.calls == 0


def test_source_ast_bans_rng_fiber_enumeration_and_parent_operation_calls():
    source_path = Path(source_law.__file__)
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
    top_levels = {name.split(".")[0] for name in imported_modules}
    assert top_levels.isdisjoint({"random", "numpy", "itertools"})
    forbidden_calls = {
        "_CP40_ADMIT",
        "_CP39_COORDINATE",
        "_CP38_RESOLVE",
        "_CP37_DECIDE",
        "_CP36_PREPARE",
    }
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert called_names.isdisjoint(forbidden_calls)
    called_attributes = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert called_attributes.isdisjoint(
        {"admit", "coordinate", "resolve", "decide", "prepare"}
    )
    assert "itertools.product" not in source
    assert "cartesian_prod" not in source
    assert "range(_D)" not in source
    owner_class = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "CounterKeyedInitialTiltRejectionFailureAwareSourceLawOwner"
    )
    describe = next(
        node
        for node in owner_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "describe"
    )
    assert not any(
        isinstance(
            node,
            (
                ast.For,
                ast.While,
                ast.ListComp,
                ast.SetComp,
                ast.DictComp,
                ast.GeneratorExp,
            ),
        )
        for node in ast.walk(describe)
    )


def test_module_is_not_reexported_from_dependency_light_process_package():
    import heterodiff.processes as processes

    assert not hasattr(
        processes,
        "certify_initial_tilt_rejection_failure_aware_source_law",
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
                "rejection_failure_aware_source_law"
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
