"""Hostile tests for the closed generic initial-score facade."""

from fractions import Fraction
import hashlib
from pathlib import Path
import pickle
import subprocess
import sys
from types import MappingProxyType
from unittest import mock

import pytest

from heterodiff.evaluation import exact_rational_quadratic_initial_tilt as exact_source
from heterodiff.evaluation import mixed_initializer_test28_atomic_q_oracle as atomic_q
from heterodiff.processes import certified_initial_score_provider_v1 as provider_module
from heterodiff.theory.configuration_reference import (
    CappedPoissonConfigurationReference,
    TransformedEvent,
)


_M1_ADAPTER_ROLE = hashlib.sha256(b"test-score-provider-m1-adapter-v1").hexdigest()
_M2_ADAPTER_ROLE = hashlib.sha256(b"test-score-provider-m2-adapter-v1").hexdigest()
_COMPOSER_ADAPTER_ROLE = hashlib.sha256(
    b"test-score-provider-composer-adapter-v1"
).hexdigest()
_ATOMIC_Q_ADAPTER_ROLE = hashlib.sha256(
    b"test-score-provider-atomic-q-adapter-v1"
).hexdigest()


def _forge(instance, **changes):
    forged = object.__new__(type(instance))
    for name in instance.__annotations__:
        object.__setattr__(
            forged,
            name,
            changes[name] if name in changes else getattr(instance, name),
        )
    return forged


def _hostile_event(event_type, coordinates):
    event = object.__new__(TransformedEvent)
    object.__setattr__(event, "event_type", event_type)
    object.__setattr__(event, "coordinates", coordinates)
    return event


class _TouchBomb:
    def __eq__(self, other):
        del other
        raise AssertionError("hostile equality was touched")

    def __ne__(self, other):
        del other
        raise AssertionError("hostile inequality was touched")

    def __str__(self):
        raise AssertionError("hostile string conversion was touched")


@pytest.fixture(scope="module")
def m1_source():
    return exact_source.build_t28_m1_q_exact_score_provider()


@pytest.fixture(scope="module")
def m2_source():
    return exact_source.build_t28_m2_q_exact_score_provider()


@pytest.fixture(scope="module")
def m1_provider(m1_source):
    return (
        provider_module.adapt_exact_rational_quadratic_initial_tilt_score_provider_v1(
            m1_source,
            adapter_role_sha256=_M1_ADAPTER_ROLE,
        )
    )


@pytest.fixture(scope="module")
def m2_provider(m2_source):
    return (
        provider_module.adapt_exact_rational_quadratic_initial_tilt_score_provider_v1(
            m2_source,
            adapter_role_sha256=_M2_ADAPTER_ROLE,
        )
    )


@pytest.fixture(scope="module")
def atomic_q_source():
    return atomic_q.t28_a0_q_oracle_pair().score_provider


@pytest.fixture(scope="module")
def atomic_q_reference():
    return CappedPoissonConfigurationReference(
        {17: 0, 41: 0},
        {17: 0.4, 41: 0.6},
        activity=1.0,
        total_cap=2,
    )


@pytest.fixture(scope="module")
def atomic_q_provider(atomic_q_source, atomic_q_reference):
    return provider_module.adapt_atomic_q_score_table_provider_v1(
        atomic_q_source,
        reference=atomic_q_reference,
        adapter_role_sha256=_ATOMIC_Q_ADAPTER_ROLE,
    )


@pytest.fixture(scope="module")
def composer_provider():
    pytest.importorskip("torch")
    from tests.unit import (
        test_configuration_initial_tilt_composer_torch as checkpoint30,
    )

    bundle = checkpoint30._continuous_bundle()
    composer = checkpoint30._certify(bundle)
    adapted = (
        provider_module.adapt_configuration_initial_tilt_composer_score_provider_v1(
            composer,
            adapter_role_sha256=_COMPOSER_ADAPTER_ROLE,
        )
    )
    return composer, adapted


def test_module_import_is_torch_lazy():
    source_root = str(Path(__file__).resolve().parents[2] / "src")
    code = r"""
import builtins
import sys
real_import = builtins.__import__
def guarded(name, *args, **kwargs):
    if name == "torch" or name.startswith("torch."):
        raise AssertionError("torch import crossed the generic provider boundary")
    return real_import(name, *args, **kwargs)
builtins.__import__ = guarded
import heterodiff.processes.certified_initial_score_provider_v1
assert "torch" not in sys.modules
"""
    environment = {"PYTHONPATH": source_root}
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(Path(__file__).resolve().parents[2]),
        env=environment,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


def test_exact_adaptation_is_torch_lazy_and_digest_stable_across_processes():
    source_root = str(Path(__file__).resolve().parents[2] / "src")
    code = r"""
import builtins
import json
import sys
real_import = builtins.__import__
def guarded(name, *args, **kwargs):
    if name == "torch" or name.startswith("torch."):
        raise AssertionError("torch import crossed the exact-adapter boundary")
    return real_import(name, *args, **kwargs)
builtins.__import__ = guarded
from heterodiff.evaluation.exact_rational_quadratic_initial_tilt import build_t28_m1_q_exact_score_provider
from heterodiff.processes.certified_initial_score_provider_v1 import adapt_exact_rational_quadratic_initial_tilt_score_provider_v1
from heterodiff.theory.configuration_reference import TransformedEvent
source = build_t28_m1_q_exact_score_provider()
provider = adapt_exact_rational_quadratic_initial_tilt_score_provider_v1(source, adapter_role_sha256="a" * 64)
point = provider.evaluate((TransformedEvent(1, (0.5,)),), residual_context=())
assert "torch" not in sys.modules
print(json.dumps([provider.certificate.certificate_sha256, point.evaluation_sha256]))
"""
    outputs = []
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
        outputs.append(completed.stdout.strip())
    assert outputs[0] == outputs[1]


def test_atomic_q_adaptation_is_torch_lazy_and_digest_stable_across_processes():
    source_root = str(Path(__file__).resolve().parents[2] / "src")
    code = r"""
import builtins
import json
import sys
real_import = builtins.__import__
def guarded(name, *args, **kwargs):
    if name == "torch" or name.startswith("torch."):
        raise AssertionError("torch import crossed the atomic-q adapter boundary")
    return real_import(name, *args, **kwargs)
builtins.__import__ = guarded
from heterodiff.evaluation.mixed_initializer_test28_atomic_q_oracle import t28_a0_q_oracle_pair
from heterodiff.processes.certified_initial_score_provider_v1 import adapt_atomic_q_score_table_provider_v1
from heterodiff.theory.configuration_reference import CappedPoissonConfigurationReference, TransformedEvent
source = t28_a0_q_oracle_pair().score_provider
reference = CappedPoissonConfigurationReference({17: 0, 41: 0}, {17: 0.4, 41: 0.6}, activity=1.0, total_cap=2)
provider = adapt_atomic_q_score_table_provider_v1(source, reference=reference, adapter_role_sha256="b" * 64)
point = provider.evaluate((TransformedEvent(41, ()), TransformedEvent(41, ())), residual_context=())
assert "torch" not in sys.modules
print(json.dumps([provider.certificate.certificate_sha256, point.evaluation_sha256]))
"""
    outputs = []
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
        outputs.append(completed.stdout.strip())
    assert outputs[0] == outputs[1]


def test_public_owner_and_records_are_sealed(m1_provider):
    certificate = m1_provider.certificate
    evaluation = m1_provider.evaluate((), residual_context=())
    with pytest.raises(TypeError):
        provider_module.CertifiedInitialScoreProviderV1()
    with pytest.raises(TypeError):
        provider_module.ExactRationalQuadraticInitialTiltScoreAdapterV1()
    with pytest.raises(TypeError):
        provider_module.CertifiedInitialScoreProviderCertificateV1()
    with pytest.raises(TypeError):
        provider_module.CertifiedInitialScorePointEvaluationV1()
    with pytest.raises(TypeError):
        type("OwnerSubclass", (provider_module.CertifiedInitialScoreProviderV1,), {})
    with pytest.raises(TypeError):
        type(
            "AdapterSubclass",
            (provider_module.ExactRationalQuadraticInitialTiltScoreAdapterV1,),
            {},
        )
    for value in (m1_provider, m1_provider.backend_adapter, certificate, evaluation):
        with pytest.raises((TypeError, AttributeError)):
            pickle.dumps(value)
    with pytest.raises(AttributeError):
        m1_provider._certificate = certificate


def test_atomic_q_adapter_is_sealed_nonpickle_and_immutable(atomic_q_provider):
    adapter = atomic_q_provider.backend_adapter
    evaluation = atomic_q_provider.evaluate((), residual_context=())
    with pytest.raises(TypeError):
        provider_module.AtomicQScoreTableAdapterV1()
    with pytest.raises(TypeError):
        type(
            "AtomicAdapterSubclass",
            (provider_module.AtomicQScoreTableAdapterV1,),
            {},
        )
    for value in (
        adapter,
        atomic_q_provider,
        atomic_q_provider.certificate,
        evaluation,
    ):
        with pytest.raises((TypeError, AttributeError)):
            pickle.dumps(value)
    with pytest.raises(AttributeError):
        adapter._source = object()


@pytest.mark.parametrize(
    ("fixture_name", "backend_kind", "role"),
    (
        (
            "m1_provider",
            provider_module.CERTIFIED_INITIAL_SCORE_PROVIDER_V1_BACKEND_KINDS[1],
            _M1_ADAPTER_ROLE,
        ),
        (
            "m2_provider",
            provider_module.CERTIFIED_INITIAL_SCORE_PROVIDER_V1_BACKEND_KINDS[1],
            _M2_ADAPTER_ROLE,
        ),
    ),
)
def test_exact_adapter_certificate_custody_and_semantic_flags(
    request, fixture_name, backend_kind, role
):
    adapted = request.getfixturevalue(fixture_name)
    certificate = adapted.certificate
    assert certificate.schema_version == (
        provider_module.CERTIFIED_INITIAL_SCORE_PROVIDER_V1_SCHEMA_VERSION
    )
    assert certificate.backend_kind == backend_kind
    assert certificate.adapter_role_sha256 == role
    assert certificate.reference is adapted.reference
    assert certificate.source_owner is adapted.backend_adapter.source
    assert certificate.source_certificate is certificate.source_owner.certificate
    assert certificate.exact_log_weight_upper_bound == Fraction(0)
    assert certificate.exact_log_weight_lower_bound is None
    assert certificate.exact_global_upper_bound_certified is True
    assert certificate.exact_global_lower_bound_certified is False
    assert certificate.certificate_digest_directly_excludes_runtime_identity is True
    assert certificate.certificate_digest_cross_process_stable is True
    assert certificate.learned_operational_surrogate_source is False
    assert certificate.handcrafted_known_law_source is True
    assert certificate.ideal_real_extension_declared is True
    assert certificate.represented_restriction_identity_verified is True
    assert certificate.proposal_sampling_law_verified is False
    assert certificate.normalization_certified is False
    assert certificate.path_or_sampler_admitted is False
    assert certificate.formal_test_28_closed is False
    assert (
        provider_module.validate_certified_initial_score_provider_v1_certificate(
            adapted
        )
        is certificate
    )


def test_atomic_q_adapter_certificate_custody_bounds_and_nonclaims(
    atomic_q_source,
    atomic_q_provider,
    atomic_q_reference,
):
    certificate = atomic_q_provider.certificate
    adapter = atomic_q_provider.backend_adapter
    assert type(adapter) is provider_module.AtomicQScoreTableAdapterV1
    assert certificate.backend_kind == "atomic-q-score-table-v1"
    assert certificate.adapter_role_sha256 == _ATOMIC_Q_ADAPTER_ROLE
    assert certificate.source_owner is atomic_q_source
    assert certificate.source_certificate is atomic_q_source
    assert certificate.source_certificate_sha256 == atomic_q_source.record_sha256
    assert certificate.reference is atomic_q_reference
    assert certificate.reference.type_ids == (17, 41)
    assert certificate.residual_context_policy == (
        provider_module.CERTIFIED_INITIAL_SCORE_PROVIDER_V1_CONTEXT_POLICIES[1]
    )
    assert certificate.residual_context_dimension == 0
    assert certificate.fixed_residual_context == ()
    assert certificate.exact_log_weight_lower_bound == Fraction(-1)
    assert certificate.exact_log_weight_upper_bound == Fraction(1)
    assert certificate.exact_global_lower_bound_certified is True
    assert certificate.exact_global_upper_bound_certified is True
    assert certificate.certificate_digest_cross_process_stable is True
    assert certificate.learned_operational_surrogate_source is False
    assert certificate.handcrafted_known_law_source is True
    assert certificate.ideal_real_extension_declared is False
    assert certificate.represented_restriction_identity_verified is True
    assert certificate.proposal_sampling_law_verified is False
    assert certificate.analytic_pi_n_target_equality_verified is False
    assert certificate.normalization_certified is False
    assert certificate.formal_test_28_closed is False
    # These are immutable historical CP55 source-artifact flags.  Adapting the
    # table does not rewrite or reinterpret them.
    assert atomic_q_source.facade_integrated is False
    assert atomic_q_source.kernel_integrated is False
    assert adapter.parameter_key() == adapter.parameter_key()
    assert (
        provider_module.validate_certified_initial_score_provider_v1_certificate(
            atomic_q_provider
        )
        is certificate
    )


@pytest.mark.parametrize(
    ("count_vector", "expected"),
    (
        ((0, 0), Fraction(0)),
        ((0, 1), Fraction(-1, 2)),
        ((1, 0), Fraction(1, 2)),
        ((0, 2), Fraction(-1)),
        ((1, 1), Fraction(1, 2)),
        ((2, 0), Fraction(1)),
    ),
)
def test_atomic_q_count_keyed_runtime_order_projection_and_replay(
    atomic_q_provider,
    count_vector,
    expected,
):
    type_ids = atomic_q_provider.reference.type_ids
    configuration = tuple(
        TransformedEvent(type_id, ())
        for type_id, count in zip(type_ids, count_vector)
        for _ in range(count)
    )
    evaluation = atomic_q_provider.evaluate(configuration, residual_context=())
    assert evaluation.configuration == tuple(
        sorted(configuration, key=TransformedEvent.model_key)
    )
    assert evaluation.source_evaluation.count_vector == count_vector
    assert evaluation.exact_log_weight == expected
    assert evaluation.exact_log_weight_numerator == expected.numerator
    assert evaluation.exact_log_weight_denominator == expected.denominator
    assert evaluation.rounded_log_weight == float(expected)
    assert evaluation.exact_lower_bound_respected is True
    assert evaluation.exact_upper_bound_respected is True
    assert atomic_q_provider.validate_evaluation_structure(evaluation) is evaluation
    assert (
        atomic_q_provider.validate_evaluation(
            evaluation,
            configuration,
            residual_context=(),
        )
        is evaluation
    )


@pytest.mark.parametrize(
    ("configuration", "expected"),
    (
        ((), Fraction(0)),
        ((TransformedEvent(0, ()),), Fraction(0)),
        ((TransformedEvent(1, (2.0,)),), Fraction(-1)),
        ((TransformedEvent(1, (0.5,)),), Fraction(-1, 16)),
    ),
)
def test_m1_exact_score_projection_and_replay(m1_provider, configuration, expected):
    evaluation = m1_provider.evaluate(configuration, residual_context=())
    assert evaluation.configuration == m1_provider.reference.canonicalize(configuration)
    assert evaluation.exact_log_weight == expected
    assert evaluation.exact_log_weight_numerator == expected.numerator
    assert evaluation.exact_log_weight_denominator == expected.denominator
    assert evaluation.rounded_log_weight == float(expected)
    assert evaluation.source_evaluation is not None
    assert evaluation.source_evaluation_sha256 == (
        evaluation.source_evaluation.evaluation_sha256
    )
    assert evaluation.exact_upper_bound_respected is True
    assert evaluation.exact_lower_bound_respected is None
    assert evaluation.structural_validation_replayed_learned_model is False
    assert evaluation.structural_validation_replayed_rng is False
    assert m1_provider.validate_evaluation_structure(evaluation) is evaluation
    assert (
        provider_module._validate_evaluation_structure(
            evaluation, certificate=m1_provider.certificate
        )
        is evaluation
    )
    assert (
        m1_provider.validate_evaluation(evaluation, configuration, residual_context=())
        is evaluation
    )


def test_m2_nondyadic_exact_score_and_canonical_order(m2_provider):
    configuration = (
        TransformedEvent(1, (2.0, -1.0)),
        TransformedEvent(0, (0.5,)),
    )
    evaluation = m2_provider.evaluate(configuration, residual_context=())
    expected = -Fraction(1, 4) - Fraction(1, 4) * Fraction(1, 2) ** 2
    expected -= Fraction(1, 8) * 2**2
    expected -= Fraction(1, 6)
    assert evaluation.configuration == tuple(
        sorted(configuration, key=TransformedEvent.model_key)
    )
    assert evaluation.exact_log_weight == expected
    assert evaluation.exact_log_weight.denominator % 3 == 0
    assert (
        evaluation.exact_log_weight
        <= m2_provider.certificate.exact_log_weight_upper_bound
    )


def test_optional_rounded_layer_never_replaces_exact_score(m1_provider):
    huge = float.fromhex("0x1.fffffffffffffp+1023")
    evaluation = m1_provider.evaluate(
        (TransformedEvent(1, (huge,)),), residual_context=()
    )
    assert type(evaluation.exact_log_weight) is Fraction
    assert evaluation.exact_log_weight < -(10**300)
    assert evaluation.rounded_log_weight is None
    assert evaluation.source_evaluation.rounded_exact_log_weight is None
    assert evaluation.exact_upper_bound_respected is True


def test_fixed_context_and_exact_input_boundary_fail_closed(m1_provider):
    with pytest.raises((TypeError, ValueError)):
        m1_provider.evaluate((), residual_context=[])
    with pytest.raises(ValueError):
        m1_provider.evaluate((), residual_context=(0.0,))
    with pytest.raises(TypeError):
        m1_provider.evaluate([], residual_context=())
    with pytest.raises((TypeError, ValueError)):
        m1_provider.evaluate((TransformedEvent(1, (1.0,)),), residual_context=(False,))


@pytest.mark.parametrize(
    "configuration",
    (
        (_hostile_event(1, (-0.0,)),),
        (_hostile_event(1, (float("nan"),)),),
        (_hostile_event(1, (float("inf"),)),),
        (_hostile_event(1, (1,)),),
        (_hostile_event(True, (1.0,)),),
        (_hostile_event(9, (1.0,)),),
        (_hostile_event(1, ()),),
    ),
)
def test_hostile_event_internals_refused_before_source_ordering(
    m1_provider, configuration
):
    with pytest.raises((TypeError, ValueError)):
        m1_provider.evaluate(configuration, residual_context=())


def test_hostile_input_is_refused_before_exact_source_dispatch(m1_provider):
    source_type = type(m1_provider.backend_adapter.source)
    hostile = (_hostile_event(1, (-0.0,)),)
    with mock.patch.object(
        source_type,
        "evaluate",
        autospec=True,
        side_effect=AssertionError("source dispatch occurred"),
    ):
        with pytest.raises((TypeError, ValueError)):
            m1_provider.evaluate(hostile, residual_context=())


def test_matching_requires_exact_owner_and_reference_identity(m1_provider):
    assert (
        provider_module.require_matching_certified_initial_score_provider_v1(
            m1_provider, m1_provider.reference
        )
        is m1_provider
    )
    clone = CappedPoissonConfigurationReference(
        {0: 0, 1: 1}, {0: 0.4, 1: 0.6}, activity=1.0, total_cap=1
    )
    with pytest.raises(ValueError):
        provider_module.require_matching_certified_initial_score_provider_v1(
            m1_provider, clone
        )
    with pytest.raises(TypeError):
        provider_module.require_matching_certified_initial_score_provider_v1(
            object(), m1_provider.reference
        )


def test_parameter_keys_and_common_digest_helpers_are_deterministic(m1_provider):
    evaluation = m1_provider.evaluate(
        (TransformedEvent(1, (0.25,)),), residual_context=()
    )
    assert m1_provider.parameter_key() == m1_provider.parameter_key()
    assert evaluation.configuration_sha256 == provider_module._configuration_sha256(
        evaluation.configuration
    )
    assert evaluation.residual_context_sha256 == provider_module._context_sha256(())
    assert provider_module._evaluation_fields() == tuple(evaluation.__annotations__)


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("certificate_sha256", "0" * 64),
        ("backend_kind", "wrong-backend"),
        ("configuration_sha256", "0" * 64),
        ("residual_context_sha256", "0" * 64),
        ("source_evaluation_sha256", "0" * 64),
        ("exact_log_weight", Fraction(1)),
        ("exact_log_weight_numerator", 9),
        ("exact_log_weight_denominator", 9),
        ("rounded_log_weight", 0.125),
        ("exact_upper_bound_respected", False),
        ("exact_lower_bound_respected", True),
        ("structural_validation_replayed_learned_model", True),
        ("structural_validation_replayed_rng", True),
        ("evaluation_sha256", "0" * 64),
    ),
)
def test_common_point_tampering_is_refused(m1_provider, field, replacement):
    evaluation = m1_provider.evaluate(
        (TransformedEvent(1, (2.0,)),), residual_context=()
    )
    forged = _forge(evaluation, **{field: replacement})
    with pytest.raises((TypeError, ValueError)):
        m1_provider.validate_evaluation_structure(forged)


def test_hostile_evaluation_text_is_type_checked_before_comparison(m1_provider):
    evaluation = m1_provider.evaluate((), residual_context=())
    forged = _forge(evaluation, backend_kind=_TouchBomb())
    with pytest.raises(TypeError, match="exact text"):
        m1_provider.validate_evaluation_structure(forged)


def test_source_point_is_structurally_revalidated(m1_provider):
    evaluation = m1_provider.evaluate(
        (TransformedEvent(1, (2.0,)),), residual_context=()
    )
    forged_source = _forge(
        evaluation.source_evaluation,
        exact_log_weight=Fraction(-2),
    )
    forged = _forge(evaluation, source_evaluation=forged_source)
    with pytest.raises(ValueError):
        m1_provider.validate_evaluation_structure(forged)


def test_structural_validation_does_not_call_exact_source_evaluate(m1_provider):
    evaluation = m1_provider.evaluate(
        (TransformedEvent(1, (0.75,)),), residual_context=()
    )
    source_type = type(m1_provider.backend_adapter.source)
    with mock.patch.object(
        source_type,
        "evaluate",
        autospec=True,
        side_effect=AssertionError("source evaluate replayed"),
    ):
        assert m1_provider.validate_evaluation_structure(evaluation) is evaluation
        with pytest.raises(AssertionError, match="source evaluate replayed"):
            m1_provider.validate_evaluation(
                evaluation,
                evaluation.configuration,
                residual_context=(),
            )


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("backend_kind", "wrong"),
        ("adapter_role_sha256", "0" * 64),
        ("source_certificate_sha256", "0" * 64),
        ("source_parameter_sha256", "0" * 64),
        ("reference_parameter_sha256", "0" * 64),
        ("exact_log_weight_upper_bound", Fraction(1)),
        ("exact_log_weight_lower_bound", Fraction(-1)),
        ("exact_global_lower_bound_certified", True),
        ("certificate_digest_cross_process_stable", False),
        ("learned_operational_surrogate_source", True),
        ("handcrafted_known_law_source", False),
        ("ideal_real_extension_declared", False),
        ("represented_restriction_identity_verified", False),
        ("proposal_sampling_law_verified", True),
        ("formal_test_28_closed", True),
        ("certificate_sha256", "0" * 64),
    ),
)
def test_common_certificate_tampering_is_refused(m1_provider, field, replacement):
    certificate = m1_provider.certificate
    forged = _forge(certificate, **{field: replacement})
    with pytest.raises((TypeError, ValueError)):
        provider_module._validate_certificate(forged)


@pytest.mark.parametrize(
    "field",
    (
        "schema_version",
        "certificate_scope",
        "nonclaim_statement",
        "backend_kind",
        "residual_context_policy",
    ),
)
def test_hostile_certificate_text_is_type_checked_before_comparison(m1_provider, field):
    forged = _forge(m1_provider.certificate, **{field: _TouchBomb()})
    with pytest.raises(TypeError, match="exact text"):
        provider_module._validate_certificate(forged)


def test_live_adapter_and_reference_identity_sentinels_fail_closed(m1_source):
    adapted = (
        provider_module.adapt_exact_rational_quadratic_initial_tilt_score_provider_v1(
            m1_source, adapter_role_sha256="a" * 64
        )
    )
    adapter = adapted.backend_adapter
    original = adapter._source_identity
    try:
        object.__setattr__(adapter, "_source_identity", object())
        with pytest.raises(ValueError):
            adapted.revalidate_live_components()
    finally:
        object.__setattr__(adapter, "_source_identity", original)
    reference = adapted.reference
    activity = reference.activity
    try:
        object.__setattr__(reference, "activity", 2.0)
        with pytest.raises(ValueError):
            adapted.revalidate_live_components()
    finally:
        object.__setattr__(reference, "activity", activity)
    assert adapted.revalidate_live_components() is adapted.certificate


def test_digest_traversal_has_fraction_depth_node_and_text_budgets(m1_provider):
    with pytest.raises(provider_module.CertifiedInitialScoreProviderV1Error):
        provider_module._typed(
            Fraction(
                1
                << (provider_module.MAX_CERTIFIED_INITIAL_SCORE_EXACT_INTEGER_BITS + 1),
                1,
            )
        )
    nested = None
    for _ in range(provider_module.MAX_CERTIFIED_INITIAL_SCORE_DIGEST_DEPTH + 2):
        nested = (nested,)
    with pytest.raises(provider_module.CertifiedInitialScoreProviderV1Error):
        provider_module._typed(nested)
    with pytest.raises(provider_module.CertifiedInitialScoreProviderV1Error):
        provider_module._typed(
            (None,) * (provider_module.MAX_CERTIFIED_INITIAL_SCORE_DIGEST_NODES + 1)
        )
    text = "x" * provider_module.MAX_CERTIFIED_INITIAL_SCORE_DIGEST_TEXT_BYTES
    count = (
        provider_module.MAX_CERTIFIED_INITIAL_SCORE_DIGEST_TOTAL_TEXT_BYTES // len(text)
        + 1
    )
    with pytest.raises(provider_module.CertifiedInitialScoreProviderV1Error):
        provider_module._typed((text,) * count)
    with pytest.raises(provider_module.CertifiedInitialScoreProviderV1Error):
        provider_module._typed(
            "x" * (provider_module.MAX_CERTIFIED_INITIAL_SCORE_DIGEST_TEXT_BYTES + 1)
        )
    large_integer = 1 << (
        provider_module.MAX_CERTIFIED_INITIAL_SCORE_EXACT_INTEGER_BITS - 1
    )
    with pytest.raises(provider_module.CertifiedInitialScoreProviderV1Error):
        provider_module._typed((large_integer,) * 256)
    large_fraction = Fraction(large_integer, large_integer - 1)
    with pytest.raises(provider_module.CertifiedInitialScoreProviderV1Error):
        provider_module._typed((large_fraction,) * 128)
    certificate = m1_provider.certificate
    hostile_key = (
        Fraction(
            1 << (provider_module.MAX_CERTIFIED_INITIAL_SCORE_EXACT_INTEGER_BITS + 1),
            1,
        ),
    )
    forged = _forge(certificate, source_parameter_key=hostile_key)
    with pytest.raises(provider_module.CertifiedInitialScoreProviderV1Error):
        provider_module._validate_certificate(forged)


def test_reference_mapping_keys_are_type_checked_before_sorting(m1_provider):
    reference = m1_provider.reference
    original = reference.type_dimensions
    try:
        object.__setattr__(
            reference,
            "type_dimensions",
            MappingProxyType({object(): 0, 1: 1}),
        )
        with pytest.raises(TypeError):
            provider_module._validate_live_reference(reference)
    finally:
        object.__setattr__(reference, "type_dimensions", original)


@pytest.mark.parametrize(
    "reference",
    (
        CappedPoissonConfigurationReference(
            {3: 0}, {3: 1.0}, activity=1.0, total_cap=2
        ),
        CappedPoissonConfigurationReference(
            {3: 0, 7: 0, 11: 0},
            {3: 0.2, 7: 0.3, 11: 0.5},
            activity=1.0,
            total_cap=2,
        ),
        CappedPoissonConfigurationReference(
            {3: 0, 7: 1}, {3: 0.4, 7: 0.6}, activity=1.0, total_cap=2
        ),
        CappedPoissonConfigurationReference(
            {3: 0, 7: 0}, {3: 0.4, 7: 0.6}, activity=2.0, total_cap=2
        ),
        CappedPoissonConfigurationReference(
            {3: 0, 7: 0}, {3: 0.4, 7: 0.6}, activity=1.0, total_cap=1
        ),
        CappedPoissonConfigurationReference(
            {3: 0, 7: 0}, {3: 0.6, 7: 0.4}, activity=1.0, total_cap=2
        ),
    ),
)
def test_atomic_q_adapter_rejects_every_nonfixture_reference(
    atomic_q_source,
    reference,
):
    with pytest.raises(ValueError):
        provider_module.adapt_atomic_q_score_table_provider_v1(
            atomic_q_source,
            reference=reference,
            adapter_role_sha256=_ATOMIC_Q_ADAPTER_ROLE,
        )


def test_atomic_q_adapter_requires_exact_source_reference_role_and_context(
    atomic_q_source,
    atomic_q_reference,
    atomic_q_provider,
):
    with pytest.raises(TypeError):
        provider_module.adapt_atomic_q_score_table_provider_v1(
            object(),
            reference=atomic_q_reference,
            adapter_role_sha256=_ATOMIC_Q_ADAPTER_ROLE,
        )
    with pytest.raises(TypeError):
        provider_module.adapt_atomic_q_score_table_provider_v1(
            atomic_q_source,
            reference=object(),
            adapter_role_sha256=_ATOMIC_Q_ADAPTER_ROLE,
        )
    with pytest.raises(ValueError):
        provider_module.adapt_atomic_q_score_table_provider_v1(
            atomic_q_source,
            reference=atomic_q_reference,
            adapter_role_sha256="not-a-digest",
        )
    with pytest.raises(TypeError):
        atomic_q_provider.evaluate((), residual_context=[])
    with pytest.raises(ValueError):
        atomic_q_provider.evaluate((), residual_context=(0.0,))
    with pytest.raises(ValueError):
        atomic_q_provider.evaluate(
            (TransformedEvent(17, (0.0,)),),
            residual_context=(),
        )


def test_atomic_q_structural_validation_never_dispatches_and_recomputes_counts(
    atomic_q_source,
    atomic_q_provider,
):
    configuration = (TransformedEvent(17, ()), TransformedEvent(17, ()))
    evaluation = atomic_q_provider.evaluate(configuration, residual_context=())
    wrong_source_point = atomic_q_source.evaluate((0, 2))
    forged = _forge(
        evaluation,
        source_evaluation=wrong_source_point,
        source_evaluation_sha256=wrong_source_point.record_sha256,
    )
    with pytest.raises(ValueError, match="count vector differs"):
        atomic_q_provider.validate_evaluation_structure(forged)
    with mock.patch.object(
        type(atomic_q_source),
        "evaluate",
        autospec=True,
        side_effect=AssertionError("atomic-q source evaluate replayed"),
    ):
        assert atomic_q_provider.validate_evaluation_structure(evaluation) is evaluation
        with pytest.raises(AssertionError, match="source evaluate replayed"):
            atomic_q_provider.validate_evaluation(
                evaluation,
                configuration,
                residual_context=(),
            )


def test_atomic_q_full_replay_compares_fresh_point_by_value_not_identity(
    atomic_q_source,
    atomic_q_provider,
):
    configuration = (TransformedEvent(17, ()), TransformedEvent(41, ()))
    evaluation = atomic_q_provider.evaluate(configuration, residual_context=())
    original = type(atomic_q_source).evaluate
    fresh_points = []

    def fresh_dispatch(source, count_vector):
        point = original(source, count_vector)
        fresh_points.append(point)
        return point

    with mock.patch.object(
        type(atomic_q_source),
        "evaluate",
        autospec=True,
        side_effect=fresh_dispatch,
    ):
        assert (
            atomic_q_provider.validate_evaluation(
                evaluation,
                configuration,
                residual_context=(),
            )
            is evaluation
        )
    assert len(fresh_points) == 1
    assert fresh_points[0] is not evaluation.source_evaluation
    assert fresh_points[0] == evaluation.source_evaluation


def test_atomic_q_live_source_reference_and_identity_tampering_fails_closed(
    atomic_q_source,
    atomic_q_provider,
    atomic_q_reference,
):
    adapter = atomic_q_provider.backend_adapter
    source_identity = adapter._source_identity
    try:
        object.__setattr__(adapter, "_source_identity", object())
        with pytest.raises(ValueError, match="source identity"):
            atomic_q_provider.revalidate_live_components()
    finally:
        object.__setattr__(adapter, "_source_identity", source_identity)
    reference_identity = adapter._reference_identity
    try:
        object.__setattr__(adapter, "_reference_identity", object())
        with pytest.raises(ValueError, match="reference identity"):
            atomic_q_provider.revalidate_live_components()
    finally:
        object.__setattr__(adapter, "_reference_identity", reference_identity)
    source_flag = atomic_q_source.facade_integrated
    try:
        object.__setattr__(atomic_q_source, "facade_integrated", True)
        with pytest.raises(ValueError):
            atomic_q_provider.revalidate_live_components()
    finally:
        object.__setattr__(atomic_q_source, "facade_integrated", source_flag)
    activity = atomic_q_reference.activity
    try:
        object.__setattr__(atomic_q_reference, "activity", 2.0)
        with pytest.raises(ValueError, match="activity"):
            atomic_q_provider.revalidate_live_components()
    finally:
        object.__setattr__(atomic_q_reference, "activity", activity)
    assert (
        atomic_q_provider.revalidate_live_components() is atomic_q_provider.certificate
    )


def test_composer_adapter_preserves_bounded_surrogate_semantics(composer_provider):
    composer, adapted = composer_provider
    certificate = adapted.certificate
    assert certificate.backend_kind == (
        provider_module.CERTIFIED_INITIAL_SCORE_PROVIDER_V1_BACKEND_KINDS[0]
    )
    assert certificate.source_owner is composer
    assert certificate.reference is composer.reference_composer.process.reference
    assert certificate.residual_context_policy == (
        provider_module.CERTIFIED_INITIAL_SCORE_PROVIDER_V1_CONTEXT_POLICIES[0]
    )
    assert certificate.residual_context_dimension == 1
    assert certificate.fixed_residual_context is None
    assert certificate.fixed_residual_context_sha256 is None
    assert certificate.exact_log_weight_lower_bound is not None
    assert certificate.exact_log_weight_upper_bound is not None
    assert certificate.certificate_digest_directly_excludes_runtime_identity is True
    assert certificate.certificate_digest_cross_process_stable is False
    assert certificate.learned_operational_surrogate_source is True
    assert certificate.handcrafted_known_law_source is False
    assert certificate.ideal_real_extension_declared is False
    assert certificate.represented_restriction_identity_verified is False


def test_composer_adapter_exact_projection_context_and_replay(composer_provider):
    _, adapted = composer_provider
    configuration = (TransformedEvent(0, (0.25,)),)
    context = (-0.4,)
    evaluation = adapted.evaluate(configuration, residual_context=context)
    source = evaluation.source_evaluation
    expected = Fraction(
        source.exact_initial_log_factor_numerator,
        source.exact_initial_log_factor_denominator,
    )
    assert evaluation.exact_log_weight == expected
    assert evaluation.rounded_log_weight == source.initial_log_factor
    assert evaluation.exact_lower_bound_respected is True
    assert evaluation.exact_upper_bound_respected is True
    assert adapted.validate_evaluation_structure(evaluation) is evaluation
    assert (
        adapted.validate_evaluation(evaluation, configuration, residual_context=context)
        is evaluation
    )
    with pytest.raises(ValueError):
        adapted.evaluate(configuration, residual_context=())
    with pytest.raises(TypeError):
        adapted.evaluate(configuration, residual_context=(0,))


def test_composer_structural_validation_does_not_replay_forward(
    composer_provider,
):
    composer, adapted = composer_provider
    configuration = (TransformedEvent(0, (0.125,)),)
    context = (-0.4,)
    evaluation = adapted.evaluate(configuration, residual_context=context)
    with mock.patch.object(
        type(composer),
        "evaluate",
        autospec=True,
        side_effect=AssertionError("composer forward replayed"),
    ):
        assert adapted.validate_evaluation_structure(evaluation) is evaluation
        with pytest.raises(AssertionError, match="composer forward replayed"):
            adapted.validate_evaluation(
                evaluation,
                configuration,
                residual_context=context,
            )
