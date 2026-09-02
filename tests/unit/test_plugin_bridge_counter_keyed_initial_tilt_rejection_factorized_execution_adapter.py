"""Hostile tests for checkpoint-44 factorized execution adapter."""

import ast
from contextlib import contextmanager
import inspect
from pathlib import Path
import pickle
import random
import sys

import numpy as np
import pytest


torch = pytest.importorskip(
    "torch", reason="factorized execution requires the PyTorch reference"
)

from heterodiff.processes import (  # noqa: E402
    plugin_bridge_counter_keyed_initial_tilt_rejection_factorized_execution_adapter as adapter,
)

checkpoint43 = pytest.importorskip(  # noqa: E402
    "tests.unit.test_plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "factorization_closure",
    reason="factorized execution requires the CP43 fixtures",
)


POLICY = getattr(
    adapter,
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_"
    "ADAPTER_POLICY",
)
ROLE = "6" * 64
MAX_UINT64 = (1 << 64) - 1
_CERTIFY = getattr(
    adapter,
    "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "factorized_execution_adapter",
)
_MATCHING = getattr(
    adapter,
    "require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "factorized_execution_adapter",
)
_VALIDATE_CERTIFICATE = getattr(
    adapter,
    "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "factorized_execution_adapter_certificate",
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


def _call_codes():
    closure_owner = adapter._CP43_OWNER_TYPE
    return {
        "cp27_allocate": adapter._CP27_ALLOCATE.__code__,
        "cp27_public_validate": adapter._CP27_OWNER_TYPE.validate_result.__code__,
        "cp27_structural_validate": adapter._CP27_VALIDATE_RESULT_RECORD.__code__,
        "cp36_preflight": adapter._CP36_PREFLIGHT_PROTOCOL_TREE.__code__,
        "cp36_prepare": adapter._CP36_OWNER_TYPE.prepare.__code__,
        "cp37_decide": adapter._CP37_OWNER_TYPE.decide.__code__,
        "cp43_split": adapter._CP43_SPLIT_FULL_WORDS.__code__,
        "cp43_join": adapter._CP43_JOIN_FULL_WORDS.__code__,
        "cp43_combined": adapter._CP43_EVALUATE_AND_APPLY.__code__,
        "cp43_g": closure_owner._evaluate_operation.__code__,
        "cp43_semantic_h": closure_owner._apply_trusted.__code__,
        "cp43_structural_validate": adapter._CP43_VALIDATE_APPLIED_RECORD.__code__,
    }


@contextmanager
def _trace_calls(*, fault_code=None, fault=None, on_call=None):
    codes = _call_codes()
    calls = {name: 0 for name in codes}

    def profiler(frame, event, arg):
        del arg
        if event != "call":
            return profiler
        for name, code in codes.items():
            if frame.f_code is code:
                calls[name] += 1
        if fault_code is not None and frame.f_code is fault_code:
            if on_call is not None:
                on_call(frame)
            if fault is not None:
                raise fault
        return profiler

    previous = sys.getprofile()
    sys.setprofile(profiler)
    try:
        yield calls
    finally:
        sys.setprofile(previous)


def test_runtime_code_fingerprint_is_refcount_stable_and_code_sensitive():
    runtime_before = adapter._runtime_sha256()
    code_type = type(adapter._runtime_sha256.__code__)
    nested = next(
        value
        for value in adapter.CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterOwner.execute.__code__.co_consts
        if type(value) is code_type and value.co_name == "require_source_custody"
    )
    assert adapter._runtime_sha256() == runtime_before
    with _trace_calls():
        assert adapter._runtime_sha256() == runtime_before
    del nested
    assert adapter._runtime_sha256() == runtime_before

    original_code = adapter._full_words_sha256.__code__

    def altered_full_words_sha256(words):
        del words
        return "0" * 64

    try:
        adapter._full_words_sha256.__code__ = altered_full_words_sha256.__code__
        assert adapter._runtime_sha256() != runtime_before
    finally:
        adapter._full_words_sha256.__code__ = original_code
    assert adapter._runtime_sha256() == runtime_before


@pytest.fixture(scope="module")
def one_attempt_bundle():
    return checkpoint43.one_attempt_bundle.__wrapped__()


@pytest.fixture(scope="module")
def factorization_closure_owner(one_attempt_bundle):
    return checkpoint43.owner.__wrapped__(one_attempt_bundle)


@pytest.fixture(scope="module")
def owner(factorization_closure_owner):
    before = _rng_snapshot()
    result = _CERTIFY(
        factorization_closure_owner,
        execution_policy=POLICY,
        execution_role_sha256=ROLE,
    )
    _assert_rng_unchanged(before)
    return result


@pytest.fixture(scope="module")
def execution_evidence(owner):
    before = _rng_snapshot()
    with _trace_calls() as calls:
        result = owner.execute(44_001, 1)
    _assert_rng_unchanged(before)
    return {"result": result, "calls": calls}


@pytest.fixture(scope="module")
def execution_result(execution_evidence):
    return execution_evidence["result"]


def test_public_api_signatures_and_exact_export_surface(
    factorization_closure_owner,
    owner,
):
    expected = {
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FACTORIZED_"
        "EXECUTION_ADAPTER_SCHEMA_VERSION",
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FACTORIZED_"
        "EXECUTION_ADAPTER_POLICY",
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FACTORIZED_"
        "EXECUTION_ADAPTER_SCOPE",
        "INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_ADAPTER_SOURCE_STATUSES",
        "INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_ADAPTER_SEMANTIC_STATUSES",
        "INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_ADAPTER_THEOREM",
        "INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_ADAPTER_"
        "SOURCE_FAILURE_SEMANTICS",
        "INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_ADAPTER_"
        "PRODUCT_UNIFORM_COROLLARY",
        "INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_ADAPTER_" "CP41_SYMBOLIC_MIXTURE",
        "CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterCertificate",
        "CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterResult",
        "CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterOwner",
        "PluginBridgeCounterKeyedInitialTiltRejectionFactorizedExecutionAdapterError",
        "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_"
        "factorized_execution_adapter",
        "require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_"
        "factorized_execution_adapter",
        "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_"
        "factorized_execution_adapter_certificate",
    }
    assert set(adapter.__all__) == expected
    assert len(adapter.__all__) == len(set(adapter.__all__))
    assert tuple(inspect.signature(owner.execute).parameters) == (
        "run_id",
        "initialization_index",
    )
    assert tuple(inspect.signature(owner.validate_result).parameters) == ("result",)
    assert owner.factorization_closure_owner is factorization_closure_owner
    assert (
        adapter.INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_ADAPTER_SOURCE_STATUSES
        == ("acquired",)
    )
    assert (
        adapter.INITIAL_TILT_REJECTION_FACTORIZED_EXECUTION_ADAPTER_SEMANTIC_STATUSES
        == (
            "preparation_failure",
            "quota_certification_failure",
            "selected",
            "exhausted",
        )
    )


def test_certificate_exact_ancestry_truth_table_and_claim_boundary(
    factorization_closure_owner,
    owner,
):
    certificate = owner.certificate
    cp43 = factorization_closure_owner.certificate
    cp42 = cp43.checkpoint42_certificate
    assert certificate.checkpoint43_certificate is cp43
    assert certificate.checkpoint37_certificate is owner._decision_owner.certificate
    assert certificate.checkpoint36_certificate is owner._preparation_owner.certificate
    assert certificate.checkpoint27_certificate is owner._protocol_owner.certificate
    assert certificate.checkpoint42_certificate_sha256 == cp42.certificate_sha256
    assert certificate.checkpoint41_certificate_sha256 == (
        cp42.checkpoint41_certificate_sha256
    )
    assert certificate.factorization_hypothesis_sha256 == (
        cp42.factorization_hypothesis_sha256
    )
    assert certificate.checkpoint43_owner_runtime_identity == id(
        factorization_closure_owner
    )
    assert certificate.checkpoint37_owner_runtime_identity == id(owner._decision_owner)
    assert certificate.checkpoint36_owner_runtime_identity == id(
        owner._preparation_owner
    )
    assert certificate.checkpoint27_owner_runtime_identity == id(owner._protocol_owner)
    assert all(
        getattr(certificate, name) is True
        for name in adapter._CERTIFICATE_POSITIVE_FLAGS
    )
    assert all(
        getattr(certificate, name) is False
        for name in adapter._CERTIFICATE_NEGATIVE_FLAGS
    )
    assert certificate.pointwise_returned_result_relation_certified
    assert certificate.canonical_semantic_projection_equality_certified
    assert certificate.source_acquisition_checks_precede_semantic_execution_certified
    assert certificate.post_combined_custody_checks_certified
    assert (
        certificate.abstract_product_uniform_corollary_recorded_under_explicit_premises
    )
    assert certificate.cp41_symbolic_mixture_recorded_under_explicit_premises
    assert not certificate.checkpoint41_original_live_parent_factorization_discharged
    assert not certificate.live_philox_source_law_certified
    assert not certificate.live_v_w_independence_certified
    assert not certificate.natural_f37_failure_exhibited
    assert not certificate.natural_f37_unreachability_proved
    assert not certificate.adaptive_floor_separation_proved
    assert not certificate.successful_source_allocation_implies_return_certified
    assert not certificate.unconditional_adapter_pushforward_certified
    assert not certificate.precombined_source_refusal_totalized
    assert not certificate.postcombined_refusal_totalized
    assert (
        not certificate.concurrent_or_aba_external_record_mutation_resilience_certified
    )
    assert not certificate.inherited_cp27_internal_validation_replay_free
    assert (
        "abstract-supplied-full-word-capsule"
        in certificate.abstract_product_uniform_corollary
    )
    assert (
        "deterministic-replay-stable-total-G43"
        in certificate.abstract_product_uniform_corollary
    )
    assert "S44_rj(Z)=T43_rj(split43(Z))" in (
        certificate.abstract_product_uniform_corollary
    )
    assert "sum_B(lambda_B*e_B)" in certificate.abstract_product_uniform_corollary
    assert "sum_B(lambda_B*m_B(x))" in (certificate.abstract_product_uniform_corollary)
    assert (
        "no-live-Philox-source-or-unconditional-adapter-law-follows"
        in certificate.abstract_product_uniform_corollary
    )
    assert "symbolic-only" in certificate.cp41_symbolic_mixture
    assert "on-every-call-that-returns-a-CP44-result" in (
        certificate.factorized_execution_theorem
    )
    assert "pi(T44_rj(Z))=pi(T43_rj(V,W))" in (certificate.factorized_execution_theorem)
    assert "post-combined-exception-or-custody-refusal" in (
        certificate.factorized_execution_theorem
    )
    assert (
        "trusted-runtime-procedural-not-portable-or-cryptographic-custody"
        in certificate.certificate_scope
    )
    assert (
        _MATCHING(
            factorization_closure_owner,
            owner,
            execution_policy=POLICY,
            execution_role_sha256=ROLE,
        )
        is owner
    )
    assert (
        _VALIDATE_CERTIFICATE(
            factorization_closure_owner,
            owner,
            execution_policy=POLICY,
            execution_role_sha256=ROLE,
        )
        is certificate
    )


def test_one_live_allocation_calls_cp43_once_and_bypasses_legacy_route(
    execution_evidence,
):
    result = execution_evidence["result"]
    calls = execution_evidence["calls"]
    assert calls["cp27_allocate"] == 1
    assert calls["cp27_public_validate"] == 1
    assert calls["cp27_structural_validate"] == 3
    assert calls["cp36_prepare"] == 0
    assert calls["cp37_decide"] == 0
    assert calls["cp43_combined"] == 1
    assert calls["cp43_g"] == 1
    assert calls["cp43_semantic_h"] == 1
    assert calls["cp43_join"] == 1
    # CP43.join_full_words invokes its own inverse split check.
    assert calls["cp43_split"] == 2
    assert result.source_status == "acquired"
    assert result.semantic_status in ("selected", "exhausted")
    assert result.checkpoint43_combined_evaluated_once is True
    assert result.source_failure_totalized_as_f36_or_f37 is False
    assert result.legacy_checkpoint36_or_checkpoint37_result_claimed is False


def test_full_capsule_flatten_split_join_order_and_semantic_projection(
    factorization_closure_owner,
    owner,
    execution_result,
):
    result = execution_result
    certificate = owner.certificate
    source = result.source_protocol_result
    flat = tuple(word for entry in source.entries for word in entry.raw64_words)
    assert flat == result.source_full_words
    assert len(flat) == certificate.full_word_count
    assert source.entry_sha256s is result.source_entry_sha256s
    proposal, decision = factorization_closure_owner.split_full_words(flat)
    assert proposal == result.source_proposal_words
    assert decision == result.source_decision_words
    assert factorization_closure_owner.join_full_words(proposal, decision) == flat
    assert adapter._partition_full_words(flat, certificate) == (proposal, decision)
    assert result.source_full_words_sha256 == adapter._full_words_sha256(flat)
    assert result.source_proposal_words_sha256 == adapter._proposal_words_sha256(
        proposal
    )
    assert result.source_decision_words_sha256 == adapter._decision_words_sha256(
        decision
    )
    applied = result.checkpoint43_applied_decision
    projection = (
        applied.status,
        applied.comparison_count,
        applied.selected_attempt_index,
        applied.selected_configuration_sha256,
    )
    assert result.canonical_semantic_projection == projection
    assert result.canonical_semantic_projection_sha256 == (
        adapter._semantic_projection_sha256(projection)
    )
    assert result.semantic_status == applied.status
    assert result.comparison_count == applied.comparison_count
    assert result.selected_attempt_index == applied.selected_attempt_index
    assert result.selected_configuration_sha256 == applied.selected_configuration_sha256
    assert applied.predecision_result.proposal_words == proposal
    assert applied.decision_words == decision


def test_public_validation_is_structural_and_replays_no_source_g_or_h(
    owner,
    execution_result,
):
    before = _rng_snapshot()
    with _trace_calls() as calls:
        checked = owner.validate_result(execution_result)
    _assert_rng_unchanged(before)
    assert checked is execution_result
    assert calls["cp27_allocate"] == 0
    assert calls["cp27_public_validate"] == 0
    assert calls["cp27_structural_validate"] == 1
    assert calls["cp36_prepare"] == 0
    assert calls["cp37_decide"] == 0
    assert calls["cp43_split"] == 0
    assert calls["cp43_join"] == 0
    assert calls["cp43_combined"] == 0
    assert calls["cp43_g"] == 0
    assert calls["cp43_semantic_h"] == 0
    assert calls["cp43_structural_validate"] == 1


def test_source_boundary_exception_propagates_exactly_without_semantic_result(owner):
    error = adapter._protocol.PluginBridgeCounterKeyedInitializerProtocolError(
        "test-only source allocation refusal"
    )
    before = _rng_snapshot()
    with _trace_calls(fault_code=adapter._CP27_ALLOCATE.__code__, fault=error) as calls:
        with pytest.raises(type(error)) as caught:
            owner.execute(44_101, 2)
    _assert_rng_unchanged(before)
    assert caught.value is error
    assert calls["cp27_allocate"] == 1
    assert calls["cp43_combined"] == 0
    assert calls["cp43_g"] == 0
    assert calls["cp36_prepare"] == 0
    assert calls["cp37_decide"] == 0


@pytest.mark.parametrize(
    "target_code,error,expected_status",
    (
        (
            adapter._factorization._TILT_EVALUATE.__code__,
            adapter._closure._TILT_ERROR("test-only exact synthetic F36"),
            "preparation_failure",
        ),
        (
            adapter._factorization._CP37_QUOTA.__code__,
            adapter._factorization._CP37_QUOTA_ERROR("test-only exact synthetic F37"),
            "quota_certification_failure",
        ),
    ),
    ids=("fault-injected-f36", "fault-injected-f37"),
)
def test_exact_post_source_f36_f37_keep_capsule_as_boundary_evidence(
    owner,
    target_code,
    error,
    expected_status,
):
    run_id = 44_102 if expected_status == "preparation_failure" else 44_103
    before = _rng_snapshot()
    with _trace_calls(fault_code=target_code, fault=error) as calls:
        result = owner.execute(run_id, 3)
    _assert_rng_unchanged(before)
    assert calls["cp27_allocate"] == 1
    assert calls["cp43_combined"] == 1
    assert calls["cp36_prepare"] == 0
    assert calls["cp37_decide"] == 0
    assert result.source_status == "acquired"
    assert result.semantic_status == expected_status
    assert result.comparison_count == 0
    assert result.selected_attempt_index is None
    assert result.selected_configuration_sha256 is None
    assert result.checkpoint43_applied_decision.decision_words is None
    assert len(result.source_decision_words) == owner.certificate.decision_word_count
    assert result.source_decision_words_are_boundary_evidence is True
    assert result.complete_source_capsule_retained is True
    assert result.source_failure_totalized_as_f36_or_f37 is False
    assert owner.validate_result(result) is result
    assert owner.certificate.natural_f37_failure_exhibited is False
    assert owner.certificate.natural_f37_unreachability_proved is False


class _TiltErrorSubclass(adapter._closure._TILT_ERROR):
    pass


@pytest.mark.parametrize(
    "error",
    (
        ValueError("test-only generic post-source refusal"),
        _TiltErrorSubclass("test-only exact-error subclass refusal"),
    ),
    ids=("generic", "typed-subclass"),
)
def test_generic_and_typed_subclass_post_source_errors_propagate_exactly(
    owner,
    error,
):
    before = _rng_snapshot()
    with _trace_calls(
        fault_code=adapter._factorization._TILT_EVALUATE.__code__,
        fault=error,
    ) as calls:
        with pytest.raises(type(error)) as caught:
            owner.execute(44_104, 4)
    _assert_rng_unchanged(before)
    assert caught.value is error
    assert calls["cp27_allocate"] == 1
    assert calls["cp43_combined"] == 1
    assert calls["cp36_prepare"] == 0
    assert calls["cp37_decide"] == 0


def test_records_owner_and_public_constructors_are_sealed_nonpickle_objects(
    owner,
    execution_result,
):
    for value in (owner, owner.certificate, execution_result):
        with pytest.raises(AttributeError):
            value.new_field = 1

    for value in (
        owner,
        owner.certificate,
        execution_result,
        execution_result.source_protocol_result,
        execution_result.checkpoint43_applied_decision,
    ):
        with pytest.raises(TypeError):
            pickle.dumps(value)
    with pytest.raises(TypeError):
        adapter.CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterCertificate(
            _construction_token=object()
        )
    with pytest.raises(TypeError):
        adapter.CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterResult(
            _construction_token=object(),
            _trusted_source_token=object(),
        )
    with pytest.raises(TypeError):

        class BadResult(
            adapter.CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterResult
        ):
            pass


def test_plain_and_redigested_result_and_certificate_claim_tampering_refuses(
    owner,
    execution_result,
):
    alternate = (
        "exhausted" if execution_result.semantic_status != "exhausted" else "selected"
    )
    plain = _forged(execution_result, semantic_status=alternate)
    with pytest.raises(ValueError):
        owner.validate_result(plain)

    result_values = {
        name: getattr(execution_result, name) for name in adapter._result_fields()
    }
    result_values["source_failure_totalized_as_f36_or_f37"] = True
    result_values["result_sha256"] = adapter._SEMANTIC_DIGEST(
        adapter._result_payload(result_values)
    )
    redigested_result = _forged(execution_result, **result_values)
    with pytest.raises(ValueError):
        owner.validate_result(redigested_result)

    certificate = owner.certificate
    certificate_values = {
        name: getattr(certificate, name) for name in adapter._certificate_fields()
    }
    certificate_values[
        "checkpoint41_original_live_parent_factorization_discharged"
    ] = True
    certificate_values["certificate_sha256"] = adapter._SEMANTIC_DIGEST(
        adapter._certificate_payload(certificate_values)
    )
    redigested_certificate = _forged(certificate, **certificate_values)
    with pytest.raises(ValueError):
        adapter._validate_certificate(redigested_certificate)


def test_cross_owner_result_refuses(factorization_closure_owner, execution_result):
    foreign = _CERTIFY(
        factorization_closure_owner,
        execution_policy=POLICY,
        execution_role_sha256="7" * 64,
    )
    assert foreign.certificate is not execution_result.certificate
    with pytest.raises(ValueError, match="certificate"):
        foreign.validate_result(execution_result)


def test_nested_source_and_semantic_record_mutation_refuses_and_restores(
    owner,
    execution_result,
):
    before = _rng_snapshot()
    source_entry = execution_result.source_protocol_result.entries[0]
    original_words = source_entry.raw64_words
    changed_words = ((original_words[0] + 1) & MAX_UINT64,) + original_words[1:]
    object.__setattr__(source_entry, "raw64_words", changed_words)
    try:
        with pytest.raises(
            ValueError,
            match=r"^initializer protocol raw-word identity differs$",
        ):
            owner.validate_result(execution_result)
    finally:
        object.__setattr__(source_entry, "raw64_words", original_words)

    applied = execution_result.checkpoint43_applied_decision
    original_status = applied.status
    changed_status = "exhausted" if original_status != "exhausted" else "selected"
    object.__setattr__(applied, "status", changed_status)
    try:
        with pytest.raises(
            ValueError,
            match=r"^CP43 and CP42 applied statuses differ$",
        ):
            owner.validate_result(execution_result)
    finally:
        object.__setattr__(applied, "status", original_status)
    assert owner.validate_result(execution_result) is execution_result
    _assert_rng_unchanged(before)


def test_persistent_midoperation_source_mutation_is_caught_at_custody_boundary(owner):
    before = _rng_snapshot()
    mutation = {}

    def mutate_source(frame):
        source = frame.f_back.f_locals["source"]
        entry = source.entries[0]
        original = entry.raw64_words
        changed = ((original[0] + 1) & MAX_UINT64,) + original[1:]
        mutation.update(entry=entry, original=original)
        object.__setattr__(entry, "raw64_words", changed)

    try:
        with _trace_calls(
            fault_code=adapter._CP43_EVALUATE_AND_APPLY.__code__,
            on_call=mutate_source,
        ) as calls:
            with pytest.raises(
                ValueError,
                match=(
                    r"^attempt parent entry 0 entry field raw64_words "
                    r"changed identity$"
                ),
            ):
                owner.execute(44_105, 5)
    finally:
        if mutation:
            object.__setattr__(mutation["entry"], "raw64_words", mutation["original"])
    _assert_rng_unchanged(before)
    assert calls["cp27_allocate"] == 1
    assert calls["cp43_combined"] == 1
    assert calls["cp43_g"] == 1
    assert calls["cp43_semantic_h"] == 1
    assert mutation


def test_owner_rebinding_and_dependency_surface_drift_refuse_before_allocation(
    owner,
    monkeypatch,
):
    original = owner._protocol_allocate
    touched = []

    def forbidden(*args, **kwargs):
        del args, kwargs
        touched.append("allocate")
        raise AssertionError("changed callback must not execute")

    object.__setattr__(owner, "_protocol_allocate", forbidden)
    try:
        with _trace_calls() as calls:
            with pytest.raises(ValueError, match="cached callback"):
                owner.execute(44_106, 6)
    finally:
        object.__setattr__(owner, "_protocol_allocate", original)
    assert touched == []
    assert calls["cp27_allocate"] == 0

    def altered_combined(self, *args, **kwargs):
        del self, args, kwargs
        raise AssertionError("altered CP43 method must not execute")

    with monkeypatch.context() as patch:
        patch.setattr(
            adapter._CP43_OWNER_TYPE,
            "evaluate_and_apply",
            altered_combined,
        )
        with pytest.raises(ValueError):
            adapter._validate_certificate(owner.certificate)
    assert adapter._validate_certificate(owner.certificate) is owner.certificate


def test_source_has_no_legacy_route_or_caller_global_rng_surface(owner):
    source = Path(adapter.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    direct_imports = {
        (alias.name, alias.asname)
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert direct_imports == {
        ("hashlib", None),
        ("marshal", None),
        ("platform", None),
        ("sys", None),
    }
    from_imports = {
        (node.module, node.level, alias.name, alias.asname)
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    assert from_imports == {
        ("__future__", 0, "annotations", None),
        ("dataclasses", 0, "dataclass", None),
        ("typing", 0, "Dict", None),
        ("typing", 0, "Mapping", None),
        ("typing", 0, "Optional", None),
        ("typing", 0, "Tuple", None),
        (
            "heterodiff.processes",
            0,
            "plugin_bridge_counter_keyed_initial_tilt_rejection_"
            "factorization_closure",
            None,
        ),
    }
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        assert not (isinstance(node.func, ast.Name) and node.func.id == "__import__")
        assert not (
            isinstance(node.func, ast.Attribute) and node.func.attr == "import_module"
        )
    marshal_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "marshal"
        and node.func.attr == "dumps"
    ]
    assert len(marshal_calls) == 1
    assert len(marshal_calls[0].args) == 2
    assert isinstance(marshal_calls[0].args[1], ast.Constant)
    assert marshal_calls[0].args[1].value == 2
    assert not marshal_calls[0].keywords
    assert "python-marshal-v2-no-reference-table-exact-constant-domain-v1" in source
    assert ".prepare(" not in source
    assert ".decide(" not in source
    assert "rng" not in inspect.signature(owner.execute).parameters
    assert "retry" not in inspect.signature(owner.execute).parameters
    assert (
        owner.certificate.no_adapter_added_source_word_or_caller_global_rng_call_certified
    )
    assert owner.certificate.no_checkpoint36_prepare_or_checkpoint37_decide_certified


def test_execute_adds_no_second_cp27_structural_validation_after_allocate():
    owner_type = adapter.CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterOwner
    assert (
        "_validate_protocol_result_record" not in owner_type.execute.__code__.co_names
    )
    assert (
        "_CP27_VALIDATE_RESULT_RECORD"
        not in adapter._validate_result_values.__code__.co_names
    )
    assert (
        "_validate_protocol_result_record"
        in owner_type.validate_result.__code__.co_names
    )


@pytest.mark.parametrize(
    "run_id,initialization_index,error_type",
    (
        (True, 0, TypeError),
        (-1, 0, ValueError),
        (1 << 64, 0, ValueError),
        (0, np.int64(0), TypeError),
        (0, -1, ValueError),
        (0, 1 << 64, ValueError),
    ),
)
def test_invalid_execution_domains_refuse_before_source_allocation(
    owner,
    run_id,
    initialization_index,
    error_type,
):
    with _trace_calls() as calls:
        with pytest.raises(error_type):
            owner.execute(run_id, initialization_index)
    assert calls["cp27_allocate"] == 0
    assert calls["cp43_combined"] == 0


def test_invalid_result_domain_refuses_without_operational_replay(owner):
    with _trace_calls() as calls:
        with pytest.raises(TypeError, match="wrong exact CP44 type"):
            owner.validate_result(object())
    assert all(count == 0 for count in calls.values())
