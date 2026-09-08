"""Synthetic structural/reference qualification only; no study-data admission."""

from fractions import Fraction
import math
import random

import numpy as np
import pytest

from heterodiff.data.two_domain_factorized_state import (
    DyadicMass, EventEncoding, FactoredEvent, FactorizedMetadataReference,
    FactorizedStateError, PhysioStateKey, RetailStateKey, SamplingLimits,
    canonical_continued_fraction, encode_metric_event, encode_semantic_event,
    nonnegative_integer_mass, nonnegative_rational_mass, ordinal_mass,
    signed_integer_mass, utf8_string_mass,
)
from heterodiff.data.two_domain_generative_chart_proposal import (
    PhysioSemanticEvent, REPORTED_FLOAT_POLICY,
)
from heterodiff.evaluation import two_domain_count_normalized_event_cks as cks


def retail_key(**changes):
    values = dict(invoice_no="c000001", stock_code="item\x00Ω",
                  description="", quantity=-3,
                  invoice_calendar=(2010, 1, 2, 3, 4, 5, 6),
                  country=None, branch="NEGATIVE")
    values.update(changes)
    return RetailStateKey(**values)


@pytest.mark.parametrize("parameter", ["MechVent", "GCS"])
@pytest.mark.parametrize("value", [Fraction(0), Fraction(1), Fraction(3, 2),
                                   Fraction(1, 10**30), Fraction(12345, 987)])
def test_discrete_clinical_fields_are_atomic_with_no_invented_range(parameter, value):
    source = PhysioSemanticEvent(2880, parameter, value)
    encoded = encode_semantic_event(source)
    assert type(encoded) is EventEncoding
    assert encoded.event.key.dimension == 0
    assert encoded.event.key.branch == "ATOMIC"
    assert encoded.event.coordinate is None
    assert encoded.event.to_semantic_event() == source
    assert encoded.event.to_metric_event() == source.to_metric_event()
    assert encoded.exact_binary64_conversion_error == 0
    assert encoded.decoded_native_roundtrip_error == 0
    assert encoded.diagnostics()["clinical_validity_claimed"] is False


@pytest.mark.parametrize("parameter", cks.PHYSIONET_PARAMETERS)
def test_all_37_parameters_have_exact_missing_atoms(parameter):
    source = PhysioSemanticEvent(0, parameter, None)
    encoded = encode_metric_event(source.to_metric_event())
    assert encoded.event.key.branch == "MISSING"
    assert encoded.event.key.dimension == 0
    assert encoded.event.to_semantic_event() == source


@pytest.mark.parametrize("value,branch", [(Fraction(0), "ZERO"), (Fraction(1), "POSITIVE"),
                                         (Fraction(123, 8), "POSITIVE")])
def test_nonatomic_physio_chart_records_float_roundtrip_error(value, branch):
    source = PhysioSemanticEvent(1440, "HR", value)
    encoded = encode_semantic_event(source)
    assert encoded.event.key.branch == branch
    assert encoded.exact_binary64_conversion_error == 0
    assert encoded.decoded_native_roundtrip_error == encoded.event.to_semantic_event().value - value
    assert encoded.event.key.dimension == (0 if branch == "ZERO" else 1)


@pytest.mark.parametrize("value,branch", [(Fraction(-7, 8), "NEGATIVE"),
                                         (Fraction(0), "ZERO"), (Fraction(1), "POSITIVE")])
def test_retail_signed_chart_keeps_every_discrete_field_exact(value, branch):
    key = retail_key(branch=branch)
    source = key.semantic(value)
    encoded = encode_semantic_event(source)
    assert encoded.event.key == key
    decoded = encoded.event.to_semantic_event()
    assert decoded.invoice_no == "c000001"
    assert decoded.quantity == -3
    assert decoded.description == "" and decoded.country is None
    assert decoded.stock_code == "item\x00Ω"
    assert decoded.invoice_calendar == key.invoice_calendar
    assert encoded.decoded_native_roundtrip_error == decoded.unit_price - value
    assert encoded.event.to_metric_event().coordinates[1] == 1


def test_rounding_policy_is_explicit_and_never_used_for_atomic_rationals():
    source = PhysioSemanticEvent(1, "HR", Fraction(1, 3))
    with pytest.raises(FactorizedStateError, match="EXACT_BINARY64_CONVERSION_REQUIRED"):
        encode_semantic_event(source)
    encoded = encode_semantic_event(source, conversion_policy=REPORTED_FLOAT_POLICY)
    assert encoded.exact_binary64_conversion_error == Fraction.from_float(1 / 3) - Fraction(1, 3)
    assert encoded.diagnostics()["raw_decimal_or_binary64_origin_proven"] is False
    atomic = encode_semantic_event(PhysioSemanticEvent(1, "GCS", Fraction(1, 3)))
    assert atomic.event.to_semantic_event().value == Fraction(1, 3)


def test_log_exp_machine_tails_fail_without_clipping():
    key = PhysioStateKey(0, "HR", "POSITIVE")
    for coordinate in (1000.0, -1000.0):
        with pytest.raises(FactorizedStateError, match="NO_CLIPPING"):
            FactoredEvent(key, coordinate).to_metric_event()
    for value in (Fraction(10**1000), Fraction(1, 10**1000)):
        with pytest.raises(FactorizedStateError, match="OVERFLOW|UNDERFLOW"):
            encode_semantic_event(PhysioSemanticEvent(0, "HR", value),
                                  conversion_policy=REPORTED_FLOAT_POLICY)


@pytest.mark.parametrize("key", [
    lambda: PhysioStateKey(0, "MechVent", "POSITIVE"),
    lambda: PhysioStateKey(0, "GCS", "ZERO"),
    lambda: PhysioStateKey(0, "HR", "ATOMIC", Fraction(1)),
    lambda: PhysioStateKey(0, "GCS", "ATOMIC", Fraction(-1)),
    lambda: PhysioStateKey(0, "GCS", "ATOMIC", 1),
    lambda: PhysioStateKey(0, "HR", "ZERO", Fraction(0)),
    lambda: PhysioStateKey(2881, "HR", "ZERO"),
    lambda: retail_key(quantity=1.5),
    lambda: retail_key(invoice_no="C123"),
    lambda: retail_key(stock_code=""),
    lambda: retail_key(stock_code="x" * 257),
    lambda: retail_key(description="x" * 4097),
    lambda: retail_key(country="x" * 257),
    lambda: retail_key(invoice_calendar=(2011, 12, 10, 0, 0, 0, 0)),
    lambda: retail_key(invoice_calendar=[2010, 1, 1, 0, 0, 0, 0]),
    lambda: retail_key(stock_code="\ud800"),
])
def test_structurally_illegal_keys_are_not_repaired(key):
    with pytest.raises((ValueError, TypeError)):
        key()


def test_canonical_metadata_is_injective_for_optional_case_unicode_and_rationals():
    keys = [retail_key(description=None), retail_key(description=""),
            retail_key(invoice_no="C000001"), retail_key(invoice_no="000001"),
            retail_key(stock_code="é"), retail_key(stock_code="e\u0301"),
            retail_key(quantity=10**2000), retail_key(quantity=-(10**2000)),
            PhysioStateKey(0, "GCS", "ATOMIC", Fraction(1, 3)),
            PhysioStateKey(0, "GCS", "ATOMIC", Fraction(2, 3)),
            PhysioStateKey(0, "GCS", "MISSING")]
    assert len({key.canonical_bytes() for key in keys}) == len(keys)
    assert PhysioStateKey(0, "GCS", "ATOMIC", Fraction(2, 6)).canonical_bytes() == keys[-3].canonical_bytes()
    assert retail_key(quantity=10**2000).canonical_bytes() == keys[6].canonical_bytes()


def test_occurrence_sorting_preserves_duplicate_atoms_and_dimensions():
    missing = FactoredEvent(PhysioStateKey(1, "HR", "MISSING"))
    positive = FactoredEvent(PhysioStateKey(1, "HR", "POSITIVE"), 0.0)
    events = tuple(sorted((positive, missing, positive), key=lambda item: item.sort_key))
    assert len(events) == 3 and events.count(positive) == 2
    with pytest.raises(FactorizedStateError, match="ZERO_DIMENSIONAL"):
        FactoredEvent(missing.key, 0.0)
    with pytest.raises(FactorizedStateError, match="SCALAR"):
        FactoredEvent(positive.key)
    with pytest.raises(FactorizedStateError, match="SCALAR"):
        FactoredEvent(positive.key, float("nan"))


@pytest.mark.parametrize("size", [1, 2, 3, 37, 128, 1920, 2881])
def test_finite_ordinal_law_is_exact_normalized_dyadic_not_uniform(size):
    masses = [ordinal_mass(index, size).as_fraction() for index in range(size)]
    assert sum(masses) == 1
    assert all(value > 0 for value in masses)
    if size & (size - 1):
        assert max(masses) == 2 * min(masses)


def test_unbounded_integer_bit_length_law_has_declared_geometric_tail():
    for maximum_length in range(1, 9):
        bound = 2**maximum_length
        total = sum(nonnegative_integer_mass(value).as_fraction() for value in range(bound))
        assert total == 1 - Fraction(1, 2 * 4**maximum_length)
        signed_total = sum(signed_integer_mass(value).as_fraction() for value in range(-bound + 1, bound))
        assert signed_total == total
    assert signed_integer_mass(0).as_fraction() == Fraction(1, 2)
    assert signed_integer_mass(1).as_fraction() == Fraction(3, 16)
    assert signed_integer_mass(-1).as_fraction() == Fraction(3, 16)
    assert signed_integer_mass(2**10000).log() < -20000


@pytest.mark.parametrize("value,terms,mass", [
    (Fraction(0), (0,), Fraction(1, 4)),
    (Fraction(1), (1,), Fraction(3, 16)),
    (Fraction(1, 2), (0, 2), Fraction(1, 16)),
    (Fraction(1, 3), (0, 3), Fraction(3, 64)),
    (Fraction(3, 2), (1, 2), Fraction(3, 64)),
    (Fraction(2, 3), (0, 1, 2), Fraction(1, 64)),
])
def test_rational_prior_uses_unique_canonical_continued_fraction(value, terms, mass):
    assert canonical_continued_fraction(value) == terms
    assert nonnegative_rational_mass(value).as_fraction() == mass
    assert nonnegative_rational_mass(Fraction(value.numerator * 17, value.denominator * 17)).as_fraction() == mass


def test_rational_prior_gives_every_nonnegative_rational_positive_mass():
    seen = set()
    for denominator in range(1, 30):
        for numerator in range(50):
            value = Fraction(numerator, denominator)
            terms = canonical_continued_fraction(value)
            assert len(terms) == 1 or terms[-1] >= 2
            seen.add(value)
            assert nonnegative_rational_mass(value).as_fraction() > 0
    # This finite subset never renormalizes to one; all omitted rationals retain mass.
    assert sum(nonnegative_rational_mass(value).as_fraction() for value in seen) < 1


def test_utf8_one_byte_grammar_exactly_normalizes_and_preserves_empty_distinction():
    present = [chr(index) for index in range(128)]
    assert sum(utf8_string_mass(value, maximum_bytes=1, allow_empty=False).as_fraction()
               for value in present) == 1
    assert (utf8_string_mass("", maximum_bytes=1, allow_empty=True).as_fraction()
            + sum(utf8_string_mass(value, maximum_bytes=1, allow_empty=True).as_fraction()
                  for value in present)) == 1
    assert utf8_string_mass("A", maximum_bytes=4096, allow_empty=True).as_fraction() == Fraction(1, 1024)
    assert utf8_string_mass("A", maximum_bytes=4096, allow_empty=False).as_fraction() == Fraction(1, 512)


@pytest.mark.parametrize("text", ["\x00", "\x7f", "\u0080", "\u07ff", "\u0800", "\ud7ff",
                                  "\ue000", "\uffff", "\U00010000", "\U0010ffff", "é", "e\u0301"])
def test_full_valid_unicode_scalar_grammar_has_no_observed_vocabulary(text):
    assert utf8_string_mass(text, maximum_bytes=len(text.encode("utf8")), allow_empty=False).as_fraction() > 0
    key = retail_key(stock_code=text)
    mass = FactorizedMetadataReference(cks.RETAIL_DOMAIN_ID).mass(key)
    assert math.isfinite(mass.log())
    assert FactoredEvent(key, 0.0).to_metric_event().domain_id == cks.RETAIL_DOMAIN_ID


def test_large_legal_metadata_has_exact_probability_below_binary64_range_no_floor():
    key = retail_key(stock_code="x" * 256, description="Ω" * 2048,
                     country="\U0010ffff" * 64, quantity=2**10000)
    reference = FactorizedMetadataReference(cks.RETAIL_DOMAIN_ID)
    mass = reference.mass(key)
    assert reference.log_prob(key) < -10000
    assert math.exp(reference.log_prob(key)) == 0.0  # Ordinary float loses it; exact mass does not.
    assert mass.numerator > 0 and mass.denominator_exponent > 10000
    assert mass.as_fraction() > 0
    with pytest.raises(FactorizedStateError, match="RESOURCE_LIMIT"):
        mass.as_fraction(maximum_denominator_bits=128)
    assert reference.diagnostics()["joint_probability_floor"] is None


@pytest.mark.parametrize("domain", [cks.PHYSIONET_DOMAIN_ID, cks.RETAIL_DOMAIN_ID])
@pytest.mark.parametrize("kind", ["stdlib", "pcg64", "pcg64dxsm"])
def test_reference_sampling_replays_and_emits_legal_semantic_events(domain, kind):
    def seeded():
        if kind == "stdlib":
            return random.Random(98341)
        bit_generator = np.random.PCG64 if kind == "pcg64" else np.random.PCG64DXSM
        return np.random.Generator(bit_generator(98341))
    reference = FactorizedMetadataReference(domain)
    first, second = seeded(), seeded()
    events = tuple(reference.sample_event(first) for _ in range(50))
    assert events == tuple(reference.sample_event(second) for _ in range(50))
    for event in events:
        assert event.key.domain_id == domain
        assert math.isfinite(reference.log_prob(event.key))
        metric = event.to_metric_event()
        assert metric.domain_id == domain
        if not event.key.dimension:
            assert reference.event_log_density(event) == reference.log_prob(event.key)
        else:
            assert reference.event_log_density(event) == pytest.approx(
                reference.log_prob(event.key) - .5 * (math.log(2 * math.pi) + event.coordinate**2))


def test_metadata_draw_resource_refusal_is_explicit_not_a_shorter_law():
    reference = FactorizedMetadataReference(cks.PHYSIONET_DOMAIN_ID)
    with pytest.raises(FactorizedStateError, match="ENTROPY_RESOURCE_LIMIT_NO_REDRAW"):
        reference.sample_event(np.random.default_rng(9), limits=SamplingLimits(maximum_entropy_bits=1))
    with pytest.raises(FactorizedStateError, match="GENERATOR_REQUIRED"):
        reference.sample_event(np.random.Generator(np.random.MT19937(1)))
    with pytest.raises(FactorizedStateError, match="SAME_DOMAIN"):
        reference.log_prob(retail_key())


def test_exact_probability_invalid_inputs_and_scope_are_not_hidden():
    for arguments in ((0, 1), (3, 1), (1, -1), (True, 0)):
        with pytest.raises(FactorizedStateError):
            DyadicMass(*arguments)
    for value in (-1, 0.5, True):
        with pytest.raises(FactorizedStateError):
            nonnegative_integer_mass(value)
    with pytest.raises(FactorizedStateError):
        nonnegative_rational_mass(Fraction(-1))
    report = FactorizedMetadataReference(cks.PHYSIONET_DOMAIN_ID).diagnostics()
    assert report["ideal_law_full_metadata_support"] is True
    for field in ("finite_rng_exact_ideal_law_claimed", "production_adoption",
                  "clinical_validity_claimed", "configuration_count_law_selected",
                  "observation_kernel_common_support_proven", "raw_decimal_or_binary64_origin_proven"):
        assert report[field] is False


def test_density_numeric_overflow_refuses_instead_of_returning_negative_infinity():
    reference = FactorizedMetadataReference(cks.PHYSIONET_DOMAIN_ID)
    event = FactoredEvent(PhysioStateKey(0, "HR", "POSITIVE"), 1e308)
    with pytest.raises(FactorizedStateError, match="LOG_DENSITY_REPRESENTABILITY"):
        reference.event_log_density(event)
    with pytest.raises(FactorizedStateError, match="LOG_MASS_REPRESENTABILITY"):
        DyadicMass(1, 10**400).log()


@pytest.mark.parametrize("domain", [cks.PHYSIONET_DOMAIN_ID, cks.RETAIL_DOMAIN_ID])
def test_train_mixture_is_exact_normalized_and_keeps_unseen_full_support(domain):
    from heterodiff.data.two_domain_factorized_state import TrainInformedMetadataReference
    if domain == cks.PHYSIONET_DOMAIN_ID:
        a = FactoredEvent(PhysioStateKey(1, "HR", "ZERO"))
        b = FactoredEvent(PhysioStateKey(2, "GCS", "ATOMIC", Fraction(1, 3)))
        unseen = PhysioStateKey(3, "MechVent", "ATOMIC", Fraction(17, 2))
    else:
        a = FactoredEvent(retail_key(branch="ZERO"))
        b = FactoredEvent(retail_key(invoice_no="000001", branch="ZERO"))
        unseen = retail_key(invoice_no="000002", branch="ZERO")
    universal = FactorizedMetadataReference(domain)
    reference = TrainInformedMetadataReference(universal, (a, a, b), beta=Fraction(1, 5))
    qa, qb = universal.mass(a.key).as_fraction(), universal.mass(b.key).as_fraction()
    assert reference.mass(a.key).as_fraction() == Fraction(4, 5) * Fraction(2, 3) + Fraction(1, 5) * qa
    assert reference.mass(b.key).as_fraction() == Fraction(4, 5) * Fraction(1, 3) + Fraction(1, 5) * qb
    assert (reference.mass(a.key).as_fraction() + reference.mass(b.key).as_fraction()
            + Fraction(1, 5) * (1 - qa - qb)) == 1
    assert reference.mass(unseen).as_fraction() == Fraction(1, 5) * universal.mass(unseen).as_fraction() > 0
    assert reference.log_prob(unseen) == pytest.approx(math.log(0.2) + universal.log_prob(unseen))
    assert reference.mass(a.key).empirical == Fraction(2, 3)
    report = reference.diagnostics()
    assert report["train_occurrences"] == 3 and report["train_unique_keys"] == 2
    assert report["train_split_or_no_leakage_independently_verified"] is False
    assert report["heldout_unseen_key_mass_improvement_claimed"] is False
    assert report["empirical_only_support"] is False


@pytest.mark.parametrize("beta", [Fraction(0), Fraction(1), Fraction(-1), Fraction(3, 2), 0.5, True])
def test_train_mixture_rejects_beta_endpoints_and_implicit_float_parameters(beta):
    from heterodiff.data.two_domain_factorized_state import TrainInformedMetadataReference
    universal = FactorizedMetadataReference(cks.PHYSIONET_DOMAIN_ID)
    occurrence = FactoredEvent(PhysioStateKey(1, "HR", "ZERO"))
    with pytest.raises(FactorizedStateError, match="EXACT_BETA"):
        TrainInformedMetadataReference(universal, (occurrence,), beta=beta)


def test_train_mixture_requires_explicit_nonempty_same_domain_occurrence_roster():
    from heterodiff.data.two_domain_factorized_state import TrainInformedMetadataReference
    universal = FactorizedMetadataReference(cks.PHYSIONET_DOMAIN_ID)
    for roster in ((), [], (PhysioStateKey(1, "HR", "ZERO"),)):
        with pytest.raises(FactorizedStateError, match="OCCURRENCE_TUPLE"):
            TrainInformedMetadataReference(universal, roster, beta=Fraction(1, 2))
    with pytest.raises(FactorizedStateError, match="CROSS_DOMAIN"):
        TrainInformedMetadataReference(universal, (FactoredEvent(retail_key(branch="ZERO")),), beta=Fraction(1, 2))


@pytest.mark.parametrize("domain", [cks.PHYSIONET_DOMAIN_ID, cks.RETAIL_DOMAIN_ID])
def test_train_mixture_sampling_replays_and_draws_new_standard_normal_not_train_values(domain):
    from heterodiff.data.two_domain_factorized_state import TrainInformedMetadataReference
    key = (PhysioStateKey(1, "HR", "POSITIVE") if domain == cks.PHYSIONET_DOMAIN_ID
           else retail_key(branch="POSITIVE"))
    reference = TrainInformedMetadataReference(FactorizedMetadataReference(domain),
                                               (FactoredEvent(key, 1000.0),), beta=Fraction(1, 10**10))
    first, second = np.random.default_rng(7), np.random.default_rng(7)
    draws = tuple(reference.sample_event(first) for _ in range(64))
    assert draws == tuple(reference.sample_event(second) for _ in range(64))
    assert all(draw.key == key for draw in draws)
    assert len({draw.coordinate for draw in draws}) == len(draws)
    assert all(abs(draw.coordinate) < 10 for draw in draws)
    assert reference.diagnostics()["source_values_or_continuous_coordinates_fit"] is False


def test_train_mixture_non_dyadic_beta_and_occurrence_index_follow_exact_bit_intervals():
    from heterodiff.data.two_domain_factorized_state import _exact_bernoulli, _uniform_occurrence_index
    class ScriptedBits:
        def __init__(self, bits):
            self.values = iter(bits)
        def bits(self, count):
            assert count == 1
            return next(self.values)
    assert _exact_bernoulli(ScriptedBits((0, 0)), Fraction(1, 3)) is True
    assert _exact_bernoulli(ScriptedBits((1,)), Fraction(1, 3)) is False
    assert _exact_bernoulli(ScriptedBits((0, 1, 0, 0)), Fraction(1, 3)) is True
    assert _exact_bernoulli(ScriptedBits((0, 1, 1)), Fraction(1, 3)) is False
    for bits, expected in (((0, 0), 0), ((0, 1, 1), 1), ((1, 0, 0), 1), ((1, 1), 2)):
        assert _uniform_occurrence_index(ScriptedBits(bits), 3) == expected


def test_train_mixture_tiny_beta_log_prob_and_sampling_refusal_do_not_remove_branch():
    from heterodiff.data.two_domain_factorized_state import TrainInformedMetadataReference
    key = PhysioStateKey(1, "HR", "ZERO")
    unseen = PhysioStateKey(2, "HR", "ZERO")
    beta = Fraction(1, 10**1000)
    reference = TrainInformedMetadataReference(FactorizedMetadataReference(cks.PHYSIONET_DOMAIN_ID),
                                               (FactoredEvent(key),) * 3, beta=beta)
    assert float(beta) == 0.0
    assert math.isfinite(reference.log_prob(unseen)) and reference.log_prob(unseen) < -2000
    assert reference.mass(unseen).as_fraction() > 0
    assert reference.mass(key).as_fraction() < 1
    with pytest.raises(FactorizedStateError, match="MATERIALIZATION_RESOURCE_LIMIT"):
        reference.mass(unseen).as_fraction(maximum_denominator_bits=100)
    with pytest.raises(FactorizedStateError, match="ENTROPY_RESOURCE_LIMIT"):
        reference.sample_event(np.random.default_rng(9), limits=SamplingLimits(maximum_entropy_bits=1))
