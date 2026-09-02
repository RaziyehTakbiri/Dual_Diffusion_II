"""Hostile tests for checkpoint-45 fixed-address source support obstruction."""

import ast
from contextlib import contextmanager
from fractions import Fraction
import inspect
from itertools import product
from pathlib import Path
import pickle
import random
import sys

import numpy as np
import pytest


torch = pytest.importorskip(
    "torch", reason="source-support certification requires the PyTorch reference"
)

from heterodiff.processes import (  # noqa: E402
    plugin_bridge_counter_keyed_initial_tilt_rejection_fixed_address_source_support_obstruction as obstruction,
)

checkpoint44 = pytest.importorskip(  # noqa: E402
    "tests.unit.test_plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "factorized_execution_adapter",
    reason="source-support certification requires the CP44 fixture",
)


ROLE = "8" * 64
ARBITRARY_LARGE_K = (1 << 16_384) + 123
POLICY = getattr(
    obstruction,
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FIXED_ADDRESS_SOURCE_"
    "SUPPORT_OBSTRUCTION_POLICY",
)
_CERTIFY = getattr(
    obstruction,
    "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_fixed_address_"
    "source_support_obstruction",
)
_MATCHING = getattr(
    obstruction,
    "require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_fixed_"
    "address_source_support_obstruction",
)
_VALIDATE_CERTIFICATE = getattr(
    obstruction,
    "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_fixed_address_"
    "source_support_obstruction_certificate",
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


def _operation_codes():
    adapter = checkpoint44.adapter
    closure_owner = adapter._CP43_OWNER_TYPE
    return {
        "cp27_allocate": adapter._CP27_ALLOCATE.__code__,
        "cp43_combined": adapter._CP43_EVALUATE_AND_APPLY.__code__,
        "cp43_g": closure_owner._evaluate_operation.__code__,
        "cp43_h": closure_owner._apply_trusted.__code__,
    }


@contextmanager
def _trace_operations():
    codes = _operation_codes()
    calls = {name: 0 for name in codes}

    def profiler(frame, event, arg):
        del arg
        if event == "call":
            for name, code in codes.items():
                if frame.f_code is code:
                    calls[name] += 1
        return profiler

    previous = sys.getprofile()
    sys.setprofile(profiler)
    try:
        yield calls
    finally:
        sys.setprofile(previous)


class _TouchBomb:
    def __init__(self):
        self.calls = 0

    def _touched(self, operation):
        self.calls += 1
        raise AssertionError("hostile object was touched by " + operation)

    def __eq__(self, other):
        del other
        return self._touched("equality")

    def __ne__(self, other):
        del other
        return self._touched("inequality")

    def __lt__(self, other):
        del other
        return self._touched("ordering")

    def __int__(self):
        return self._touched("integer conversion")

    def __index__(self):
        return self._touched("index conversion")

    def __iter__(self):
        return self._touched("iteration")


def _uniform(domain):
    domain = tuple(domain)
    return {value: Fraction(1, len(domain)) for value in domain}


def _total_variation(left, right, domain):
    domain = tuple(domain)
    domain_set = set(domain)
    assert set(left) <= domain_set
    assert set(right) <= domain_set
    assert all(probability >= 0 for probability in left.values())
    assert all(probability >= 0 for probability in right.values())
    assert sum(left.values()) == 1
    assert sum(right.values()) == 1
    return Fraction(1, 2) * sum(
        abs(left.get(value, Fraction(0)) - right.get(value, Fraction(0)))
        for value in domain
    )


def _conditional_pushforward(request_law, mapping):
    success_mass = sum(
        probability
        for request, probability in request_law.items()
        if mapping[request] is not None
    )
    if success_mass == 0:
        return None
    pushed = {}
    for request, probability in request_law.items():
        image = mapping[request]
        if image is not None:
            pushed[image] = pushed.get(image, Fraction(0)) + (
                probability / success_mass
            )
    return pushed


def _coordinate_support_lower_bound(base, free_coordinates, output_coordinates):
    if free_coordinates >= output_coordinates:
        return Fraction(0)
    return Fraction(
        base**output_coordinates - base**free_coordinates,
        base**output_coordinates,
    )


def _point_mass_tv_from_uniform(base, output_coordinates):
    if output_coordinates == 0:
        return Fraction(0)
    return Fraction(base**output_coordinates - 1, base**output_coordinates)


@pytest.fixture(scope="module")
def one_attempt_bundle():
    return checkpoint44.one_attempt_bundle.__wrapped__()


@pytest.fixture(scope="module")
def factorization_closure_owner(one_attempt_bundle):
    return checkpoint44.factorization_closure_owner.__wrapped__(one_attempt_bundle)


@pytest.fixture(scope="module")
def factorized_execution_owner(factorization_closure_owner):
    return checkpoint44.owner.__wrapped__(factorization_closure_owner)


@pytest.fixture(scope="module")
def certification_evidence(factorized_execution_owner):
    before = _rng_snapshot()
    with _trace_operations() as calls:
        result = _CERTIFY(
            factorized_execution_owner,
            obstruction_policy=POLICY,
            obstruction_role_sha256=ROLE,
        )
    _assert_rng_unchanged(before)
    return {"owner": result, "calls": calls}


@pytest.fixture(scope="module")
def owner(certification_evidence):
    return certification_evidence["owner"]


@pytest.fixture(scope="module")
def bound_evidence(owner):
    before = _rng_snapshot()
    with _trace_operations() as calls:
        bounds = tuple(owner.source_support_bound(free) for free in (0, 1, 2))
        large_bound = owner.source_support_bound(ARBITRARY_LARGE_K)
        for bound in bounds:
            assert owner.validate_bound(bound) is bound
        assert owner.validate_bound(large_bound) is large_bound
    _assert_rng_unchanged(before)
    return {"bounds": bounds, "large_bound": large_bound, "calls": calls}


def test_public_api_signatures_and_exact_export_surface(
    factorized_execution_owner,
    owner,
):
    expected = {
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FIXED_ADDRESS_"
        "SOURCE_SUPPORT_OBSTRUCTION_SCHEMA_VERSION",
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FIXED_ADDRESS_"
        "SOURCE_SUPPORT_OBSTRUCTION_POLICY",
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_FIXED_ADDRESS_"
        "SOURCE_SUPPORT_OBSTRUCTION_SCOPE",
        "INITIAL_TILT_REJECTION_FIXED_ADDRESS_SOURCE_TV_THEOREM",
        "INITIAL_TILT_REJECTION_FREE_REQUEST_SOURCE_SUPPORT_TV_THEOREM",
        "INITIAL_TILT_REJECTION_SOURCE_TO_OUTPUT_TV_NONCONVERSE",
        "INITIAL_TILT_REJECTION_FIXED_ADDRESS_RAW_WORD_DOMAIN_SIZE",
        "INITIAL_TILT_REJECTION_FIXED_ADDRESS_CURRENT_REQUEST_COORDINATES",
        "CounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionCertificate",
        "CounterKeyedInitialTiltRejectionFixedAddressSourceSupportBound",
        "CounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionOwner",
        "PluginBridgeCounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionError",
        "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_fixed_address_"
        "source_support_obstruction",
        "require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_"
        "fixed_address_source_support_obstruction",
        "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_fixed_"
        "address_source_support_obstruction_certificate",
    }
    assert set(obstruction.__all__) == expected
    assert len(obstruction.__all__) == len(set(obstruction.__all__))
    assert owner.factorized_execution_owner is factorized_execution_owner
    error_type = getattr(
        obstruction,
        "PluginBridgeCounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionError",
    )
    assert issubclass(error_type, ArithmeticError)

    certify_parameters = inspect.signature(_CERTIFY).parameters
    assert tuple(certify_parameters) == (
        "factorized_execution_owner",
        "obstruction_policy",
        "obstruction_role_sha256",
    )
    assert (
        certify_parameters["obstruction_policy"].kind is inspect.Parameter.KEYWORD_ONLY
    )
    assert (
        certify_parameters["obstruction_role_sha256"].kind
        is inspect.Parameter.KEYWORD_ONLY
    )
    assert tuple(inspect.signature(_MATCHING).parameters) == (
        "factorized_execution_owner",
        "owner",
        "obstruction_policy",
        "obstruction_role_sha256",
    )
    assert tuple(inspect.signature(_VALIDATE_CERTIFICATE).parameters) == (
        "factorized_execution_owner",
        "owner",
        "obstruction_policy",
        "obstruction_role_sha256",
    )
    assert tuple(inspect.signature(owner.source_support_bound).parameters) == (
        "free_uint64_request_coordinates",
    )
    assert tuple(inspect.signature(owner.validate_bound).parameters) == ("bound",)

    expected_bound_fields = (
        "certificate",
        "certificate_sha256",
        "full_word_count",
        "free_uint64_request_coordinates",
        "source_support_log2_upper_bound",
        "product_uniform_support_log2",
        "support_exponent_gap",
        "tv_lower_bound_formula",
        "strict_product_uniform_obstruction",
        "fixed_returned_request_exact_tv_certified",
        "fixed_returned_request_exact_tv_formula",
        "conditional_on_success_only",
        "success_value_independence_required",
        "output_tv_lower_bound_certified",
        "within_current_cp44_request_surface",
        "bound_sha256",
    )
    assert (
        tuple(
            obstruction.CounterKeyedInitialTiltRejectionFixedAddressSourceSupportBound.__annotations__
        )
        == expected_bound_fields
    )


def test_certificate_exact_ancestry_truth_table_and_claim_boundary(
    factorized_execution_owner,
    owner,
):
    certificate = owner.certificate
    cp44 = factorized_execution_owner.certificate
    cp36 = cp44.checkpoint36_certificate
    cp27 = cp44.checkpoint27_certificate
    cp26 = cp27.checkpoint26_certificate

    assert certificate.checkpoint44_certificate is cp44
    assert certificate.checkpoint44_certificate_sha256 == cp44.certificate_sha256
    assert certificate.checkpoint44_owner_runtime_identity == id(
        factorized_execution_owner
    )
    assert certificate.checkpoint36_certificate_sha256 == cp36.certificate_sha256
    assert certificate.checkpoint36_word_family_hypothesis_sha256 == (
        cp36.word_family_hypothesis.hypothesis_sha256
    )
    assert certificate.checkpoint27_certificate_sha256 == cp27.certificate_sha256
    assert certificate.checkpoint26_certificate_sha256 == cp26.certificate_sha256
    assert certificate.process_parameter_sha256 == cp44.process_parameter_sha256
    assert certificate.raw_word_domain_size == 1 << 64
    assert certificate.full_word_count == cp44.full_word_count
    assert certificate.current_request_coordinate_count == 2
    assert certificate.product_uniform_support_log2 == 64 * cp44.full_word_count
    assert certificate.fixed_request_tv_exponent_gap == cp44.full_word_count
    assert certificate.one_free_request_tv_exponent_gap == cp44.full_word_count - 1
    assert certificate.two_free_request_tv_exponent_gap == cp44.full_word_count - 2
    expected_positive_flags = {
        "exact_checkpoint44_owner_binding_certified",
        "exact_transitive_checkpoint36_27_26_binding_certified",
        "same_runtime_fixed_address_replay_inherited",
        "within_capsule_logical_coordinate_distinctness_inherited",
        "cp43_split_join_coordinate_permutation_inherited",
        "fixed_returned_request_point_mass_theorem_certified",
        "conditional_success_support_theorem_certified",
        "conditioning_cannot_enlarge_support_certified",
        "support_exponents_stored_without_huge_denominators",
        "source_to_output_tv_nonconverse_recorded",
        "source_and_semantic_operation_free_certification_and_bound_description_certified",
        "no_caller_global_rng_state_mutation_certified",
    }
    expected_negative_flags = {
        "live_product_uniform_source_certified",
        "nondegenerate_live_v_w_independence_certified",
        "allocation_success_value_independence_certified",
        "allocation_or_refusal_probability_certified",
        "unconditional_adapter_law_certified",
        "semantic_output_tv_lower_bound_certified",
        "transitive_rng_call_absence_certified",
        "hidden_entropy_or_random_runtime_accounted",
        "physical_randomness_certified",
        "cross_call_freshness_certified",
        "runtime_portable",
        "cryptographic_authentication",
        "initializer_admissible",
        "path_admissible",
        "sampler_admissible",
        "scientific_claim_promoted",
        "model_quality_claim_promoted",
        "generality_claim_promoted",
        "loaded_code_integrity_certified",
    }
    assert set(obstruction._CERTIFICATE_POSITIVE_FLAGS) == expected_positive_flags
    assert set(obstruction._CERTIFICATE_NEGATIVE_FLAGS) == expected_negative_flags
    assert expected_positive_flags.isdisjoint(expected_negative_flags)
    assert all(getattr(certificate, name) is True for name in expected_positive_flags)
    assert all(getattr(certificate, name) is False for name in expected_negative_flags)
    assert certificate.passed is True
    assert "TV(delta_z,U_L)=1-D^(-L)" in certificate.fixed_request_tv_theorem
    assert "conditional-success-source-support-is-at-most-D^k" in (
        certificate.free_request_support_tv_theorem
    )
    assert "no-output-TV-lower-bound-follows" in (
        certificate.source_to_output_tv_nonconverse
    )
    assert certificate.live_product_uniform_source_certified is False
    assert certificate.nondegenerate_live_v_w_independence_certified is False
    assert certificate.semantic_output_tv_lower_bound_certified is False
    assert certificate.allocation_or_refusal_probability_certified is False
    assert certificate.no_caller_global_rng_state_mutation_certified is True
    assert certificate.transitive_rng_call_absence_certified is False
    assert certificate.loaded_code_integrity_certified is False
    assert "deterministic-local-Philox-runtime-probe" in certificate.obstruction_policy
    assert "without-caller-global-rng-state-mutation" in certificate.certificate_scope

    assert (
        _MATCHING(
            factorized_execution_owner,
            owner,
            obstruction_policy=POLICY,
            obstruction_role_sha256=ROLE,
        )
        is owner
    )
    assert (
        _VALIDATE_CERTIFICATE(
            factorized_execution_owner,
            owner,
            obstruction_policy=POLICY,
            obstruction_role_sha256=ROLE,
        )
        is certificate
    )


def test_actual_cp44_zero_one_two_coordinate_bounds_are_exact(bound_evidence):
    bounds = bound_evidence["bounds"]
    length = bounds[0].certificate.full_word_count
    assert length > 2
    assert tuple(bound.free_uint64_request_coordinates for bound in bounds) == (0, 1, 2)
    assert len({bound.bound_sha256 for bound in bounds}) == 3

    for free, bound in enumerate(bounds):
        assert bound.certificate is bounds[0].certificate
        assert bound.certificate_sha256 == bound.certificate.certificate_sha256
        assert bound.full_word_count == length
        assert bound.source_support_log2_upper_bound == 64 * free
        assert bound.product_uniform_support_log2 == 64 * length
        assert bound.support_exponent_gap == length - free
        assert bound.tv_lower_bound_formula == "1-2^(-64*%d)" % (length - free)
        assert bound.strict_product_uniform_obstruction is True
        assert bound.fixed_returned_request_exact_tv_certified is (free == 0)
        assert bound.fixed_returned_request_exact_tv_formula == (
            "1-2^(-64*%d)" % length if free == 0 else "0"
        )
        assert bound.conditional_on_success_only is True
        assert bound.success_value_independence_required is False
        assert bound.output_tv_lower_bound_certified is False
        assert bound.within_current_cp44_request_surface is True

    large = bound_evidence["large_bound"]
    assert large.free_uint64_request_coordinates == ARBITRARY_LARGE_K
    assert large.source_support_log2_upper_bound == 64 * ARBITRARY_LARGE_K
    assert large.product_uniform_support_log2 == 64 * length
    assert large.support_exponent_gap == 0
    assert large.tv_lower_bound_formula == "0"
    assert large.strict_product_uniform_obstruction is False
    assert large.fixed_returned_request_exact_tv_certified is False
    assert large.within_current_cp44_request_surface is False


def test_private_general_support_helper_edges_and_clamp_are_exact():
    zero = obstruction._support_bound_values(0, 0)
    assert zero == {
        "full_word_count": 0,
        "free_uint64_request_coordinates": 0,
        "source_support_log2_upper_bound": 0,
        "product_uniform_support_log2": 0,
        "support_exponent_gap": 0,
        "tv_lower_bound_formula": "0",
        "strict_product_uniform_obstruction": False,
        "fixed_returned_request_exact_tv_certified": True,
        "fixed_returned_request_exact_tv_formula": "0",
        "within_current_cp44_request_surface": True,
    }
    equal = obstruction._support_bound_values(3, 3)
    assert equal["support_exponent_gap"] == 0
    assert equal["tv_lower_bound_formula"] == "0"
    assert equal["strict_product_uniform_obstruction"] is False
    assert equal["source_support_log2_upper_bound"] == 192
    assert equal["product_uniform_support_log2"] == 192
    assert equal["within_current_cp44_request_surface"] is False

    wider = obstruction._support_bound_values(3, 4)
    assert wider["support_exponent_gap"] == 0
    assert wider["tv_lower_bound_formula"] == "0"
    assert wider["strict_product_uniform_obstruction"] is False
    assert wider["source_support_log2_upper_bound"] == 256
    assert wider["product_uniform_support_log2"] == 192
    assert wider["within_current_cp44_request_surface"] is False

    one_gap = obstruction._support_bound_values(3, 2)
    assert one_gap["support_exponent_gap"] == 1
    assert one_gap["tv_lower_bound_formula"] == "1-2^(-64*1)"
    assert one_gap["strict_product_uniform_obstruction"] is True
    assert one_gap["within_current_cp44_request_surface"] is True

    arbitrary_large = obstruction._support_bound_values(3, ARBITRARY_LARGE_K)
    assert arbitrary_large["free_uint64_request_coordinates"] == ARBITRARY_LARGE_K
    assert arbitrary_large["source_support_log2_upper_bound"] == (
        64 * ARBITRARY_LARGE_K
    )
    assert arbitrary_large["support_exponent_gap"] == 0
    assert arbitrary_large["tv_lower_bound_formula"] == "0"
    assert arbitrary_large["strict_product_uniform_obstruction"] is False


def test_independent_exact_enumeration_covers_injective_and_colliding_maps():
    base = 2
    requests = tuple(product(range(base), repeat=1))
    outputs = tuple(product(range(base), repeat=2))
    request_law = _uniform(requests)
    uniform_output = _uniform(outputs)
    universal_bound = _coordinate_support_lower_bound(base, 1, 2)
    saw_injective = False
    saw_collision = False

    for images in product(outputs, repeat=len(requests)):
        mapping = dict(zip(requests, images))
        pushed = _conditional_pushforward(request_law, mapping)
        distance = _total_variation(pushed, uniform_output, outputs)
        assert distance >= universal_bound
        if len(set(images)) == len(images):
            saw_injective = True
            assert distance == universal_bound
        else:
            saw_collision = True
            assert distance == _point_mass_tv_from_uniform(base, 2)

    assert saw_injective is True
    assert saw_collision is True


def test_independent_exact_enumeration_covers_nonuniform_request_laws():
    base = 2
    requests = tuple(product(range(base), repeat=1))
    outputs = tuple(product(range(base), repeat=2))
    uniform_output = _uniform(outputs)
    universal_bound = _coordinate_support_lower_bound(base, 1, 2)
    cases = (
        (
            {requests[0]: Fraction(3, 8), requests[1]: Fraction(5, 8)},
            universal_bound,
        ),
        (
            {requests[0]: Fraction(1, 8), requests[1]: Fraction(7, 8)},
            Fraction(5, 8),
        ),
    )

    for request_law, expected_minimum in cases:
        distances = set()
        for images in product(outputs, repeat=len(requests)):
            mapping = dict(zip(requests, images))
            pushed = _conditional_pushforward(request_law, mapping)
            distance = _total_variation(pushed, uniform_output, outputs)
            assert distance >= universal_bound
            distances.add(distance)
        assert min(distances) == expected_minimum


def test_independent_exact_enumeration_covers_conditioned_partial_success():
    base = 2
    requests = tuple(product(range(base), repeat=1))
    outputs = tuple(product(range(base), repeat=2))
    request_law = _uniform(requests)
    uniform_output = _uniform(outputs)
    universal_bound = _coordinate_support_lower_bound(base, 1, 2)
    saw_total_refusal = False
    success_counts = {1: 0, 2: 0}
    distance_counts = {Fraction(1, 2): 0, Fraction(3, 4): 0}

    for images in product(outputs + (None,), repeat=len(requests)):
        mapping = dict(zip(requests, images))
        pushed = _conditional_pushforward(request_law, mapping)
        if pushed is None:
            saw_total_refusal = True
            continue
        distance = _total_variation(pushed, uniform_output, outputs)
        assert distance >= universal_bound
        success_count = sum(image is not None for image in images)
        success_counts[success_count] += 1
        distance_counts[distance] += 1

    assert saw_total_refusal is True
    assert success_counts == {1: 8, 2: 16}
    assert distance_counts == {Fraction(1, 2): 12, Fraction(3, 4): 12}


def test_nonuniform_partial_success_needs_no_success_value_independence():
    base = 3
    requests = tuple(product(range(base), repeat=1))
    outputs = tuple(product(range(base), repeat=2))
    request_law = {
        requests[0]: Fraction(1, 6),
        requests[1]: Fraction(1, 3),
        requests[2]: Fraction(1, 2),
    }
    uniform_output = _uniform(outputs)
    universal_bound = _coordinate_support_lower_bound(base, 1, 2)
    successful_maps = 0

    for images in product(outputs + (None,), repeat=len(requests)):
        mapping = dict(zip(requests, images))
        pushed = _conditional_pushforward(request_law, mapping)
        if pushed is None:
            continue
        successful_maps += 1
        assert _total_variation(pushed, uniform_output, outputs) >= universal_bound

    assert successful_maps == 999


def test_independent_k_zero_is_exact_point_mass_obstruction():
    base = 3
    output_coordinates = 2
    outputs = tuple(product(range(base), repeat=output_coordinates))
    point_mass = {outputs[0]: Fraction(1)}
    distance = _total_variation(point_mass, _uniform(outputs), outputs)
    assert distance == Fraction(8, 9)
    assert distance == _point_mass_tv_from_uniform(base, output_coordinates)
    assert distance == _coordinate_support_lower_bound(base, 0, output_coordinates)


def test_independent_general_edges_have_no_false_positive_lower_bound():
    base = 2
    assert _coordinate_support_lower_bound(base, 0, 0) == 0
    assert _coordinate_support_lower_bound(base, 2, 2) == 0
    assert _coordinate_support_lower_bound(base, 3, 2) == 0

    empty_domain = ((),)
    assert (
        _total_variation(_uniform(empty_domain), _uniform(empty_domain), empty_domain)
        == 0
    )

    square_requests = tuple(product(range(base), repeat=2))
    square_outputs = tuple(product(range(base), repeat=2))
    identity_pushforward = _conditional_pushforward(
        _uniform(square_requests),
        dict(zip(square_requests, square_outputs)),
    )
    assert (
        _total_variation(
            identity_pushforward,
            _uniform(square_outputs),
            square_outputs,
        )
        == 0
    )

    wide_requests = tuple(product(range(base), repeat=3))
    short_outputs = tuple(product(range(base), repeat=2))
    projection = {request: request[:2] for request in wide_requests}
    projected = _conditional_pushforward(_uniform(wide_requests), projection)
    assert _total_variation(projected, _uniform(short_outputs), short_outputs) == 0


def test_constant_semantic_map_destroys_every_source_tv_lower_bound():
    base = 2
    output_coordinates = 2
    source_domain = tuple(product(range(base), repeat=output_coordinates))
    source_uniform = _uniform(source_domain)
    source_point_mass = {source_domain[0]: Fraction(1)}
    source_tv = _total_variation(source_point_mass, source_uniform, source_domain)
    assert source_tv == _point_mass_tv_from_uniform(base, output_coordinates)
    assert source_tv > 0

    semantic_domain = ("constant", "unused")
    uniform_pushforward = {semantic_domain[0]: sum(source_uniform.values())}
    point_pushforward = {semantic_domain[0]: sum(source_point_mass.values())}
    output_tv = _total_variation(
        point_pushforward,
        uniform_pushforward,
        semantic_domain,
    )
    assert output_tv == 0
    assert output_tv <= source_tv


def test_certification_bound_description_and_validation_are_operation_free(
    certification_evidence,
    bound_evidence,
    factorized_execution_owner,
    owner,
):
    assert all(count == 0 for count in certification_evidence["calls"].values())
    assert all(count == 0 for count in bound_evidence["calls"].values())

    before = _rng_snapshot()
    with _trace_operations() as calls:
        assert (
            _MATCHING(
                factorized_execution_owner,
                owner,
                obstruction_policy=POLICY,
                obstruction_role_sha256=ROLE,
            )
            is owner
        )
        assert (
            _VALIDATE_CERTIFICATE(
                factorized_execution_owner,
                owner,
                obstruction_policy=POLICY,
                obstruction_role_sha256=ROLE,
            )
            is owner.certificate
        )
        assert owner.validate_bound(bound_evidence["bounds"][0]) is (
            bound_evidence["bounds"][0]
        )
    _assert_rng_unchanged(before)
    assert all(count == 0 for count in calls.values())


def test_records_and_owner_are_sealed_nonsubclassable_and_nonpickle(
    factorized_execution_owner,
    owner,
    bound_evidence,
):
    certificate_type = getattr(
        obstruction,
        "CounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionCertificate",
    )
    bound_type = (
        obstruction.CounterKeyedInitialTiltRejectionFixedAddressSourceSupportBound
    )
    owner_type = getattr(
        obstruction,
        "CounterKeyedInitialTiltRejectionFixedAddressSourceSupportObstructionOwner",
    )
    certificate = owner.certificate
    bound = bound_evidence["bounds"][0]
    for value in (owner, certificate, bound):
        with pytest.raises(AttributeError):
            value.new_field = 1
        with pytest.raises(TypeError):
            pickle.dumps(value)
    with pytest.raises(AttributeError):
        del owner._certificate

    with pytest.raises(TypeError):
        certificate_type(_construction_token=object())
    with pytest.raises(TypeError):
        bound_type(_construction_token=object())
    with pytest.raises(TypeError):
        owner_type(
            factorized_execution_owner,
            certificate,
            _construction_token=object(),
        )

    with pytest.raises(TypeError):

        class BadCertificate(certificate_type):
            pass

    with pytest.raises(TypeError):

        class BadBound(bound_type):
            pass

    with pytest.raises(TypeError):

        class BadOwner(owner_type):
            pass


def test_plain_and_redigested_certificate_and_bound_tampering_refuse(
    owner,
    bound_evidence,
):
    certificate = owner.certificate
    bound = bound_evidence["bounds"][0]

    plain_bound = _forged(bound, tv_lower_bound_formula="0")
    with pytest.raises(ValueError):
        owner.validate_bound(plain_bound)

    bound_values = {name: getattr(bound, name) for name in obstruction._bound_fields()}
    bound_values["output_tv_lower_bound_certified"] = True
    bound_values["bound_sha256"] = obstruction._semantic_digest(
        obstruction._bound_payload(bound_values)
    )
    redigested_bound = _forged(bound, **bound_values)
    with pytest.raises(ValueError):
        owner.validate_bound(redigested_bound)

    certificate_values = {
        name: getattr(certificate, name) for name in obstruction._certificate_fields()
    }
    certificate_values["live_product_uniform_source_certified"] = True
    certificate_values["certificate_sha256"] = obstruction._semantic_digest(
        obstruction._certificate_payload(certificate_values)
    )
    redigested_certificate = _forged(certificate, **certificate_values)
    with pytest.raises(ValueError):
        obstruction._validate_certificate(redigested_certificate)


def test_redigested_parent_runtime_identity_tamper_refuses_in_owner_context(owner):
    certificate = owner.certificate
    values = {
        name: getattr(certificate, name) for name in obstruction._certificate_fields()
    }
    values["checkpoint44_owner_runtime_identity"] += 1
    values["certificate_sha256"] = obstruction._semantic_digest(
        obstruction._certificate_payload(values)
    )
    forged_certificate = _forged(certificate, **values)

    forged_owner = object.__new__(type(owner))
    for name in type(owner).__slots__:
        value = getattr(owner, name)
        if name in ("_certificate", "_certificate_identity"):
            value = forged_certificate
        object.__setattr__(forged_owner, name, value)
    with pytest.raises(ValueError, match="runtime identity"):
        forged_owner.source_support_bound(0)


def test_cross_owner_bound_refuses_even_when_semantic_digests_match(
    factorized_execution_owner,
    bound_evidence,
):
    before = _rng_snapshot()
    with _trace_operations() as calls:
        foreign = _CERTIFY(
            factorized_execution_owner,
            obstruction_policy=POLICY,
            obstruction_role_sha256=ROLE,
        )
        bound = bound_evidence["bounds"][0]
        assert foreign.certificate is not bound.certificate
        assert foreign.certificate.certificate_sha256 == bound.certificate_sha256
        with pytest.raises(ValueError, match="another owner"):
            foreign.validate_bound(bound)
    _assert_rng_unchanged(before)
    assert all(count == 0 for count in calls.values())


def test_hostile_and_invalid_domains_refuse_without_touch_or_operation(owner):
    bomb = _TouchBomb()
    cases = (
        (True, TypeError),
        (np.int64(0), TypeError),
        (-1, ValueError),
        (bomb, TypeError),
    )
    before = _rng_snapshot()
    with _trace_operations() as calls:
        for value, error_type in cases:
            with pytest.raises(error_type):
                owner.source_support_bound(value)
        with pytest.raises(TypeError, match="wrong exact CP45 type"):
            owner.validate_bound(bomb)
    _assert_rng_unchanged(before)
    assert bomb.calls == 0
    assert all(count == 0 for count in calls.values())

    with pytest.raises(TypeError):
        obstruction._support_bound_values(True, 0)
    with pytest.raises(TypeError):
        obstruction._support_bound_values(0, np.int64(0))
    with pytest.raises(ValueError):
        obstruction._support_bound_values(-1, 0)


def test_hostile_forged_record_fields_are_preflighted_before_equality(
    owner,
    bound_evidence,
):
    certificate_bomb = _TouchBomb()
    hostile_certificate = _forged(
        owner.certificate,
        schema_version=certificate_bomb,
    )
    with pytest.raises(TypeError):
        obstruction._validate_certificate(hostile_certificate)
    assert certificate_bomb.calls == 0

    bound_bomb = _TouchBomb()
    hostile_bound = _forged(
        bound_evidence["bounds"][0],
        certificate_sha256=bound_bomb,
    )
    with pytest.raises(TypeError):
        owner.validate_bound(hostile_bound)
    assert bound_bomb.calls == 0


def test_parent_and_local_dependency_drift_refuse_before_hostile_callback(
    owner,
    bound_evidence,
    monkeypatch,
):
    touched = []

    def forbidden(*args, **kwargs):
        del args, kwargs
        touched.append("dependency")
        raise AssertionError("altered dependency must not execute")

    before = _rng_snapshot()
    with monkeypatch.context() as patch:
        patch.setattr(obstruction._adapter, "_validate_certificate", forbidden)
        with _trace_operations() as calls:
            with pytest.raises(ValueError):
                owner.source_support_bound(0)
    _assert_rng_unchanged(before)
    assert touched == []
    assert all(count == 0 for count in calls.values())

    local_cases = (
        ("_make_bound", lambda: owner.source_support_bound(0)),
        ("_support_bound_values", lambda: owner.source_support_bound(0)),
        (
            "_validate_bound",
            lambda: owner.validate_bound(bound_evidence["bounds"][0]),
        ),
        ("_LOCAL_SURFACE_GUARD", lambda: owner.source_support_bound(0)),
        ("_require_local_surfaces", lambda: owner.source_support_bound(0)),
    )
    for name, operation in local_cases:
        with monkeypatch.context() as patch:
            patch.setattr(obstruction, name, forbidden)
            with _trace_operations() as calls:
                with pytest.raises(ValueError):
                    operation()
        assert touched == []
        assert all(count == 0 for count in calls.values())

    replacement_owner_token = object()
    with monkeypatch.context() as patch:
        patch.setattr(obstruction, "_OWNER_TOKEN", replacement_owner_token)
        with pytest.raises(ValueError, match="local surface changed"):
            type(owner)(
                owner.factorized_execution_owner,
                owner.certificate,
                _construction_token=replacement_owner_token,
            )

    with monkeypatch.context() as patch:
        patch.setattr(
            obstruction._CP44_OWNER_TYPE,
            "_require_owner_snapshot",
            forbidden,
        )
        with _trace_operations() as calls:
            with pytest.raises(ValueError):
                owner.validate_bound(owner.source_support_bound(0))
    assert touched == []
    assert all(count == 0 for count in calls.values())


def test_source_has_no_allocation_semantic_or_direct_rng_import_surface():
    source = Path(obstruction.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    direct_import_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    from_import_roots = {
        (node.module or "").split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert not ({"random", "numpy", "torch"} & direct_import_roots)
    assert not ({"random", "numpy", "torch"} & from_import_roots)

    called_attributes = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert not (
        {
            "allocate",
            "execute",
            "evaluate_and_apply",
            "_evaluate_operation",
            "_apply_trusted",
        }
        & called_attributes
    )
    support_tree = ast.parse(inspect.getsource(obstruction._support_bound_values))
    assert not any(
        isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow)
        for node in ast.walk(support_tree)
    )
