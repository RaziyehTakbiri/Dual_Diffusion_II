"""Independent and hostile tests for arbitrary-rational uint64 exp quotas."""

import ast
from decimal import Decimal, localcontext
from fractions import Fraction
import inspect
import pickle
import random

import pytest

from heterodiff.evaluation import exact_rational_quadratic_initial_tilt as score
from heterodiff.processes import arbitrary_rational_uint64_exp_quota as quota
from heterodiff.theory.configuration_reference import TransformedEvent


D = 1 << 64


def _fraction(certificate, prefix):
    return Fraction(
        getattr(certificate, prefix + "_numerator"),
        getattr(certificate, prefix + "_denominator"),
    )


def _independent_exact_taylor_quota(delta, maximum_degree=401):
    """Exact-rational Taylor-remainder oracle, independent of Decimal."""

    assert type(delta) is Fraction and -4 < delta < 0
    z = -delta
    partial = Fraction(1)
    term = Fraction(1)
    for degree in range(1, maximum_degree + 1):
        term *= z / degree
        partial = partial - term if degree % 2 else partial + term
        if degree % 2 and partial > 0:
            lower = partial
            upper = partial + term  # preceding even Taylor partial
            candidate = (D * lower).numerator // (D * lower).denominator
            if D * upper <= candidate + 1:
                return candidate
    raise AssertionError("independent exact Taylor oracle did not separate a cell")


@pytest.mark.parametrize(
    "delta,branch,expected",
    (
        (Fraction(0), "unity", D),
        (Fraction(-64), "below_uint64_resolution", 0),
        (Fraction(-65), "below_uint64_resolution", 0),
        (Fraction(-1, 3 * D), "below_one_uint64_cell", D - 1),
        (Fraction(-1, D), "adaptive_decimal_rational_input", D - 1),
    ),
)
def test_terminal_and_exact_boundary_branches(delta, branch, expected):
    certificate = quota.certify_arbitrary_rational_uint64_exp_quota(delta)

    assert certificate.branch == branch
    assert certificate.quota == expected
    assert certificate.decision_denominator == D
    assert certificate.unique_scaled_floor_certified is True
    assert certificate.exact_scaled_floor_under_stated_contract_certified is True
    assert (
        quota.validate_arbitrary_rational_uint64_exp_quota_certificate(certificate)
        is certificate
    )


@pytest.mark.parametrize(
    "delta", (Fraction(-1, 3), Fraction(-1, 6), Fraction(-7, 24), Fraction(-31, 24))
)
def test_nondyadic_quotas_match_independent_exact_rational_taylor(delta):
    certificate = quota.certify_arbitrary_rational_uint64_exp_quota(delta)

    assert delta.denominator & (delta.denominator - 1)
    assert certificate.branch == "adaptive_decimal_rational_input"
    assert certificate.quota == _independent_exact_taylor_quota(delta)
    assert certificate.precision in quota._precision_schedule()
    assert certificate.adaptive_rounds >= 1

    lower = _fraction(certificate, "exp_lower")
    upper = _fraction(certificate, "exp_upper")
    assert Fraction(certificate.quota, D) < upper
    assert D * lower >= certificate.quota
    assert D * upper <= certificate.quota + 1


def test_m2_exact_denominator_three_scores_are_directly_supported():
    provider = score.build_t28_m2_q_exact_score_provider()
    one = provider.evaluate(
        (TransformedEvent(1, (1.0, 1.0)),), residual_context=()
    ).exact_log_weight
    two = provider.evaluate(
        (
            TransformedEvent(1, (1.0, 1.0)),
            TransformedEvent(0, (1.0,)),
        ),
        residual_context=(),
    ).exact_log_weight

    assert one == Fraction(-7, 24)
    assert two == Fraction(-19, 24)
    for delta in (one, two):
        assert delta.denominator % 3 == 0
        certificate = quota.certify_arbitrary_rational_uint64_exp_quota(delta)
        assert certificate.quota == _independent_exact_taylor_quota(delta)
        assert certificate.decimal_correct_rounding_contract_required is True


def test_exact_input_enclosure_is_recorded_for_nonterminating_decimal():
    delta = Fraction(-7, 24)
    certificate = quota.certify_arbitrary_rational_uint64_exp_quota(delta)
    lower = _fraction(certificate, "input_lower")
    upper = _fraction(certificate, "input_upper")

    assert lower < delta < upper
    assert certificate.input_lower_strict is True
    assert certificate.input_upper_strict is True
    assert upper - lower == Fraction(1, 10**certificate.precision)
    assert certificate.exact_divmod_input_enclosure_certified is True
    assert certificate.exponential_monotonicity_transfer_certified is True
    assert certificate.adjacent_decimal_outward_padding_certified is True
    assert certificate.adaptive_nested_enclosures_certified is True


def test_terminating_decimal_has_equal_exact_input_endpoints_but_strict_exp_bounds():
    certificate = quota.certify_arbitrary_rational_uint64_exp_quota(Fraction(-1, 2))

    assert _fraction(certificate, "input_lower") == Fraction(-1, 2)
    assert _fraction(certificate, "input_upper") == Fraction(-1, 2)
    assert certificate.input_lower_strict is False
    assert certificate.input_upper_strict is False
    assert certificate.exp_lower_strict is True
    assert certificate.exp_upper_strict is True


@pytest.mark.parametrize("delta", (Fraction(0), Fraction(-64), Fraction(-1, 3 * D)))
def test_terminal_certificates_do_not_claim_unexecuted_adaptive_proofs(delta):
    certificate = quota.certify_arbitrary_rational_uint64_exp_quota(delta)

    assert certificate.terminal_rational_inequality_certified is True
    assert certificate.decimal_correct_rounding_contract_required is False
    assert certificate.exact_divmod_input_enclosure_certified is False
    assert certificate.exponential_monotonicity_transfer_certified is False
    assert certificate.adjacent_decimal_outward_padding_certified is False
    assert certificate.adaptive_nested_enclosures_certified is False


def test_adaptive_certificate_does_not_claim_terminal_proof():
    certificate = quota.certify_arbitrary_rational_uint64_exp_quota(Fraction(-1, 3))

    assert certificate.terminal_rational_inequality_certified is False
    assert certificate.decimal_correct_rounding_contract_required is True


@pytest.mark.parametrize("bad", (0, -1, 0.0, -1.0, Decimal("-1"), True, None, "-1/3"))
def test_only_exact_fraction_inputs_are_accepted(bad):
    with pytest.raises(TypeError, match="exact Fraction"):
        quota.certify_arbitrary_rational_uint64_exp_quota(bad)


def test_positive_fraction_is_rejected():
    with pytest.raises(ValueError, match="nonpositive"):
        quota.certify_arbitrary_rational_uint64_exp_quota(Fraction(1, 3))


def test_exact_integer_resource_limits_precede_terminal_shortcuts():
    over = quota.UINT64_EXP_QUOTA_MAX_INPUT_INTEGER_BITS
    with pytest.raises(quota.ArbitraryRationalUInt64ExpQuotaError, match="resource"):
        quota.certify_arbitrary_rational_uint64_exp_quota(Fraction(-1, 1 << over))
    with pytest.raises(quota.ArbitraryRationalUInt64ExpQuotaError, match="resource"):
        quota.certify_arbitrary_rational_uint64_exp_quota(Fraction(-(1 << over), 1))


def test_seeded_nondyadic_fuzz_matches_independent_high_precision_decimal_oracle():
    generator = random.Random(52_064)
    cases = []
    for _ in range(96):
        denominator = generator.randrange(3, 10_000)
        numerator = generator.randrange(1, 63 * denominator)
        delta = Fraction(-numerator, denominator)
        if delta.denominator & (delta.denominator - 1):
            cases.append(delta)
    assert len(cases) >= 70

    with localcontext() as context:
        context.prec = 500
        for delta in cases:
            expected = int(
                (Decimal(delta.numerator) / Decimal(delta.denominator)).exp()
                * Decimal(D)
            )
            certificate = quota.certify_arbitrary_rational_uint64_exp_quota(delta)
            assert certificate.quota == expected


def test_precision_ambiguity_fails_closed(monkeypatch):
    def ambiguous(delta, precision):
        del precision
        return delta, delta, Fraction(1, 4), Fraction(3, 4)

    monkeypatch.setattr(quota, "_adaptive_exp_enclosure", ambiguous)
    with pytest.raises(quota.ArbitraryRationalUInt64ExpQuotaError, match="ambiguous"):
        quota.certify_arbitrary_rational_uint64_exp_quota(Fraction(-1, 3))


def test_nonnested_adaptive_enclosures_fail_closed(monkeypatch):
    calls = []

    def nonnested(delta, precision):
        calls.append(precision)
        if len(calls) == 1:
            return delta, delta, Fraction(1, 4), Fraction(3, 4)
        return delta, delta, Fraction(1, 5), Fraction(4, 5)

    monkeypatch.setattr(quota, "_adaptive_exp_enclosure", nonnested)
    with pytest.raises(quota.ArbitraryRationalUInt64ExpQuotaError, match="not nested"):
        quota.certify_arbitrary_rational_uint64_exp_quota(Fraction(-1, 3))


def test_certificate_is_sealed_nonpickleable_and_not_publicly_constructible():
    certificate = quota.certify_arbitrary_rational_uint64_exp_quota(Fraction(-1, 3))
    with pytest.raises(TypeError, match="module-created"):
        quota.ArbitraryRationalUInt64ExpQuotaCertificate(_construction_token=None)
    with pytest.raises(TypeError, match="cannot be subclassed"):
        type("Hostile", (quota.ArbitraryRationalUInt64ExpQuotaCertificate,), {})
    with pytest.raises(TypeError, match="not pickle"):
        pickle.dumps(certificate)


@pytest.mark.parametrize(
    "field,replacement",
    (
        ("quota", 0),
        ("precision", 384),
        ("input_lower_numerator", 0),
        ("exp_upper_denominator", 1),
        ("unique_scaled_floor_certified", False),
        ("unique_scaled_floor_certified", 1),
        ("runtime_sha256", "0" * 64),
        ("certificate_sha256", "f" * 64),
    ),
)
def test_validator_recomputes_and_rejects_every_kind_of_tampering(field, replacement):
    certificate = quota.certify_arbitrary_rational_uint64_exp_quota(Fraction(-7, 24))
    object.__setattr__(certificate, field, replacement)

    with pytest.raises(
        (TypeError, ValueError, quota.ArbitraryRationalUInt64ExpQuotaError)
    ):
        quota.validate_arbitrary_rational_uint64_exp_quota_certificate(certificate)


def test_private_token_construction_still_invokes_strict_replay_validation():
    certificate = quota.certify_arbitrary_rational_uint64_exp_quota(Fraction(-1, 3))
    values = {
        name: getattr(certificate, name)
        for name in quota.ArbitraryRationalUInt64ExpQuotaCertificate.__annotations__
    }
    values["quota"] -= 1
    with pytest.raises(ValueError, match="exact replay"):
        quota.ArbitraryRationalUInt64ExpQuotaCertificate(
            _construction_token=quota._CERTIFICATE_TOKEN, **values
        )


def test_validator_preflights_hostile_large_fields_before_replay():
    makers = (
        ("exp_upper_denominator", lambda: 1 << 1_000_000),
        ("quota", lambda: 1 << 1_000_000),
        ("branch", lambda: "x" * 1_000_000),
    )
    for field, make_value in makers:
        certificate = quota.certify_arbitrary_rational_uint64_exp_quota(Fraction(-1, 3))
        object.__setattr__(certificate, field, make_value())
        with pytest.raises(
            (ValueError, quota.ArbitraryRationalUInt64ExpQuotaError),
            match="resource|range|text",
        ):
            quota.validate_arbitrary_rational_uint64_exp_quota_certificate(certificate)


def test_validator_rejects_hostile_subclass_before_field_access():
    class Hostile:
        @property
        def delta_numerator(self):
            raise AssertionError("hostile field was touched")

    with pytest.raises(TypeError, match="wrong exact quota type"):
        quota.validate_arbitrary_rational_uint64_exp_quota_certificate(Hostile())


def test_resource_preflight_categories_cover_every_certificate_field():
    text_fields = {
        "schema_version",
        "certificate_scope",
        "proof_policy",
        "proof_contract",
        "branch",
        "runtime_sha256",
        "certificate_sha256",
    }
    scalar_integer_fields = {
        "delta_numerator",
        "delta_denominator",
        "precision",
        "adaptive_rounds",
        "decision_denominator",
        "quota",
    }
    endpoint_fields = {
        prefix + suffix
        for prefix in quota._CERTIFICATE_ENDPOINT_PREFIXES
        for suffix in ("_numerator", "_denominator")
    }
    assert set(quota.ArbitraryRationalUInt64ExpQuotaCertificate.__annotations__) == (
        text_fields
        | scalar_integer_fields
        | endpoint_fields
        | set(quota._CERTIFICATE_BOOLEAN_FIELDS)
    )


def test_certificate_nonclaims_and_contract_language_are_explicit():
    certificate = quota.certify_arbitrary_rational_uint64_exp_quota(Fraction(-1, 3))

    assert certificate.decimal_implementation_formally_verified is False
    assert certificate.independent_transcendental_backend_verified is False
    assert certificate.binary_float_exp_used is False
    assert certificate.external_numeric_dependency_used is False
    assert certificate.exact_exponential_bernoulli_certified is False
    assert certificate.rejection_kernel_integrated is False
    assert certificate.runtime_portable is False
    assert certificate.cryptographic_authentication is False
    assert "under-frozen-decimal-contract" in certificate.certificate_scope
    assert "not-formal-libmpdec-verification" in certificate.certificate_scope
    assert "not-rejection-kernel-integration" in certificate.certificate_scope
    assert "conditional on the recorded trusted unchanged" in certificate.proof_contract


def test_source_has_no_external_numeric_or_cp50_dependency_and_no_binary_exp():
    source_text = inspect.getsource(quota)
    tree = ast.parse(source_text)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])

    assert not ({"numpy", "scipy", "mpmath", "torch"} & imported)
    assert (
        "plugin_bridge_counter_keyed_initial_tilt_rejection_decision" not in source_text
    )
    assert "math.exp" not in source_text
    assert "np.exp" not in source_text
    assert "float(delta" not in source_text


def test_public_surface_is_minimal_and_deterministic_replay_is_stable():
    expected = {
        "ARBITRARY_RATIONAL_UINT64_EXP_QUOTA_POLICY",
        "ARBITRARY_RATIONAL_UINT64_EXP_QUOTA_PROOF_CONTRACT",
        "ARBITRARY_RATIONAL_UINT64_EXP_QUOTA_SCHEMA_VERSION",
        "ARBITRARY_RATIONAL_UINT64_EXP_QUOTA_SCOPE",
        "ArbitraryRationalUInt64ExpQuotaCertificate",
        "ArbitraryRationalUInt64ExpQuotaError",
        "UINT64_EXP_QUOTA_DENOMINATOR",
        "UINT64_EXP_QUOTA_MAX_DECIMAL_COEFFICIENT_DIGITS",
        "UINT64_EXP_QUOTA_MAX_INPUT_INTEGER_BITS",
        "UINT64_EXP_QUOTA_MAX_PRECISION",
        "UINT64_EXP_QUOTA_PRIMARY_PRECISION",
        "UINT64_EXP_QUOTA_ZERO_CUTOFF",
        "certify_arbitrary_rational_uint64_exp_quota",
        "validate_arbitrary_rational_uint64_exp_quota_certificate",
    }
    assert set(quota.__all__) == expected

    first = quota.certify_arbitrary_rational_uint64_exp_quota(Fraction(-7, 24))
    second = quota.certify_arbitrary_rational_uint64_exp_quota(Fraction(-7, 24))
    for name in first.__annotations__:
        assert getattr(first, name) == getattr(second, name)
