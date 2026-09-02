"""Hostile tests for checkpoint-46 explicit source-model contracts."""

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
    "torch", reason="explicit source-model certification requires PyTorch"
)

from heterodiff.processes import (  # noqa: E402
    plugin_bridge_counter_keyed_initial_tilt_rejection_explicit_source_model_contract as contract,
)

checkpoint45 = pytest.importorskip(  # noqa: E402
    "tests.unit.test_plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "fixed_address_source_support_obstruction",
    reason="explicit source-model certification requires the CP45 fixture",
)


ROLE = "9" * 64
POLICY = getattr(
    contract,
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_EXPLICIT_SOURCE_MODEL_"
    "CONTRACT_POLICY",
)
DECLARE = getattr(
    contract,
    "declare_plugin_bridge_counter_keyed_initial_tilt_rejection_external_"
    "finite_request_law",
)
VALIDATE_DECLARATION = getattr(
    contract,
    "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_external_"
    "finite_request_law_declaration",
)
CERTIFY = getattr(
    contract,
    "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_explicit_"
    "source_model_contract",
)
MATCHING = getattr(
    contract,
    "require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "explicit_source_model_contract",
)
VALIDATE_CERTIFICATE = getattr(
    contract,
    "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_explicit_"
    "source_model_contract_certificate",
)
CAPSULE_EVENT = contract.INITIAL_TILT_REJECTION_COMPLETE_CAPSULE_CONDITIONING
RETURN_EVENT = contract.INITIAL_TILT_REJECTION_RETURNED_RESULT_CONDITIONING


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


@contextmanager
def _trace_cp46_boundaries():
    codes = checkpoint45._operation_codes()
    codes[
        "cp44_execute"
    ] = (
        checkpoint45.checkpoint44.adapter.CounterKeyedInitialTiltRejectionFactorizedExecutionAdapterOwner.execute.__code__
    )
    codes["cp45_live_binding"] = contract._CP45_OWNER_LIVE_BINDING.__code__
    codes[
        "cp45_structural_certificate_validation"
    ] = contract._CP45_VALIDATE_CERTIFICATE.__code__
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

    def __bool__(self):
        return self._touched("truth conversion")

    def __eq__(self, other):
        del other
        return self._touched("equality")

    def __ne__(self, other):
        del other
        return self._touched("inequality")

    def __lt__(self, other):
        del other
        return self._touched("ordering")

    def __hash__(self):
        return self._touched("hashing")

    def __int__(self):
        return self._touched("integer conversion")

    def __index__(self):
        return self._touched("index conversion")

    def __iter__(self):
        return self._touched("iteration")

    def __len__(self):
        return self._touched("length")


def _conditional_pushforward(request_law, mapping):
    mass = sum(
        (
            probability
            for request, probability in request_law.items()
            if mapping[request] is not None
        ),
        Fraction(0),
    )
    if mass == 0:
        return None
    pushed = {}
    for request, probability in request_law.items():
        image = mapping[request]
        if image is not None:
            pushed[image] = pushed.get(image, Fraction(0)) + probability / mass
    return pushed


def _total_variation(left, right, domain):
    domain = tuple(domain)
    assert sum(left.values()) == 1
    assert sum(right.values()) == 1
    return Fraction(1, 2) * sum(
        abs(left.get(value, Fraction(0)) - right.get(value, Fraction(0)))
        for value in domain
    )


@pytest.fixture(scope="module")
def source_support_owner():
    bundle = checkpoint45.one_attempt_bundle.__wrapped__()
    closure_owner = checkpoint45.factorization_closure_owner.__wrapped__(bundle)
    execution_owner = checkpoint45.factorized_execution_owner.__wrapped__(closure_owner)
    evidence = checkpoint45.certification_evidence.__wrapped__(execution_owner)
    return evidence["owner"]


@pytest.fixture(scope="module")
def owner_bound_evidence(source_support_owner):
    before = _rng_snapshot()
    with _trace_cp46_boundaries() as calls:
        declaration = DECLARE(((0, 0, 1), (0, 1, 2), (3, 4, 3)), mass_denominator=6)
        owner = CERTIFY(
            source_support_owner,
            source_model_policy=POLICY,
            source_model_role_sha256=ROLE,
        )
        fixed = owner.fixed_request_model(7, 11, conditioning_event=CAPSULE_EVENT)
        external = owner.external_request_law_model(
            declaration, conditioning_event=RETURN_EVENT
        )
        fixed_return = owner.fixed_request_model(
            13, 17, conditioning_event=RETURN_EVENT
        )
        external_capsule = owner.external_request_law_model(
            declaration, conditioning_event=CAPSULE_EVENT
        )
        assert owner.validate_source_model(fixed) is fixed
        assert owner.validate_source_model(external) is external
        validated = VALIDATE_CERTIFICATE(
            source_support_owner,
            owner,
            source_model_policy=POLICY,
            source_model_role_sha256=ROLE,
        )
    _assert_rng_unchanged(before)
    return {
        "source_support_owner": source_support_owner,
        "owner": owner,
        "declaration": declaration,
        "fixed": fixed,
        "external": external,
        "fixed_return": fixed_return,
        "external_capsule": external_capsule,
        "validated": validated,
        "calls": calls,
    }


def test_public_export_surface_signatures_and_scope_constants_are_exact():
    expected = {
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_EXPLICIT_SOURCE_"
        "MODEL_CONTRACT_SCHEMA_VERSION",
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_EXPLICIT_SOURCE_"
        "MODEL_CONTRACT_POLICY",
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_EXPLICIT_SOURCE_"
        "MODEL_CONTRACT_SCOPE",
        "INITIAL_TILT_REJECTION_FIXED_REQUEST_SOURCE_MODEL_THEOREM",
        "INITIAL_TILT_REJECTION_EXTERNAL_FINITE_REQUEST_LAW_SUPPORT_THEOREM",
        "INITIAL_TILT_REJECTION_CURRENT_REQUEST_SURFACE_CAPACITY_THEOREM",
        "INITIAL_TILT_REJECTION_FULL_PRODUCT_UNIFORM_SOURCE_SUPPORT_AND_FIBER_"
        "CRITERION",
        "INITIAL_TILT_REJECTION_EXTERNAL_SOURCE_TO_OUTPUT_TV_NONCONVERSE",
        "INITIAL_TILT_REJECTION_EXPLICIT_SOURCE_MODEL_RAW_WORD_DOMAIN_SIZE",
        "INITIAL_TILT_REJECTION_EXPLICIT_SOURCE_MODEL_REQUEST_COORDINATES",
        "INITIAL_TILT_REJECTION_EXTERNAL_FINITE_REQUEST_LAW_MAX_SUPPORT",
        "INITIAL_TILT_REJECTION_EXTERNAL_FINITE_REQUEST_LAW_MAX_INTEGER_BITS",
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_EXTERNAL_FINITE_"
        "REQUEST_LAW_DECLARATION_SCOPE",
        "INITIAL_TILT_REJECTION_FIXED_REQUEST_MODE",
        "INITIAL_TILT_REJECTION_EXTERNAL_FINITE_REQUEST_LAW_MODE",
        "INITIAL_TILT_REJECTION_COMPLETE_CAPSULE_CONDITIONING",
        "INITIAL_TILT_REJECTION_RETURNED_RESULT_CONDITIONING",
        "CounterKeyedInitialTiltRejectionExternalFiniteRequestLawDeclaration",
        "CounterKeyedInitialTiltRejectionExplicitSourceModelContractCertificate",
        "CounterKeyedInitialTiltRejectionFixedRequestReplaySourceModel",
        "CounterKeyedInitialTiltRejectionExternalFiniteRequestLawSourceModel",
        "CounterKeyedInitialTiltRejectionExplicitSourceModelContractOwner",
        "PluginBridgeCounterKeyedInitialTiltRejectionExplicitSourceModelContractError",
        "declare_plugin_bridge_counter_keyed_initial_tilt_rejection_external_"
        "finite_request_law",
        "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_external_"
        "finite_request_law_declaration",
        "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_explicit_"
        "source_model_contract",
        "require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_"
        "explicit_source_model_contract",
        "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_explicit_"
        "source_model_contract_certificate",
    }
    assert set(contract.__all__) == expected
    assert len(contract.__all__) == len(set(contract.__all__)) == 28
    assert (
        contract.INITIAL_TILT_REJECTION_EXPLICIT_SOURCE_MODEL_REQUEST_COORDINATES == 2
    )
    assert (
        contract.INITIAL_TILT_REJECTION_EXPLICIT_SOURCE_MODEL_RAW_WORD_DOMAIN_SIZE
        == (1 << 64)
    )
    assert CAPSULE_EVENT == "complete-validated-capsule-event"
    assert RETURN_EVENT == "checkpoint44-returned-result-event"
    assert "at-most-4096-atoms" in (
        contract.PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_EXTERNAL_FINITE_REQUEST_LAW_DECLARATION_SCOPE
    )
    assert "iff-every-output-fiber" in (
        contract.INITIAL_TILT_REJECTION_FULL_PRODUCT_UNIFORM_SOURCE_SUPPORT_AND_FIBER_CRITERION
    )
    assert "neither-external-law-realization" in (
        contract.INITIAL_TILT_REJECTION_FULL_PRODUCT_UNIFORM_SOURCE_SUPPORT_AND_FIBER_CRITERION
    )

    assert tuple(inspect.signature(DECLARE).parameters) == (
        "request_mass_rows",
        "mass_denominator",
    )
    declare_parameters = inspect.signature(DECLARE).parameters
    assert (
        declare_parameters["request_mass_rows"].kind
        is inspect.Parameter.POSITIONAL_OR_KEYWORD
    )
    assert declare_parameters["mass_denominator"].kind is inspect.Parameter.KEYWORD_ONLY
    assert declare_parameters["mass_denominator"].default is inspect.Parameter.empty
    assert tuple(inspect.signature(VALIDATE_DECLARATION).parameters) == ("declaration",)
    assert tuple(inspect.signature(CERTIFY).parameters) == (
        "source_support_owner",
        "source_model_policy",
        "source_model_role_sha256",
    )
    certify_parameters = inspect.signature(CERTIFY).parameters
    assert (
        certify_parameters["source_support_owner"].kind
        is inspect.Parameter.POSITIONAL_OR_KEYWORD
    )
    for name in ("source_model_policy", "source_model_role_sha256"):
        assert certify_parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
        assert certify_parameters[name].default is inspect.Parameter.empty
    assert tuple(inspect.signature(MATCHING).parameters) == (
        "source_support_owner",
        "owner",
        "source_model_policy",
        "source_model_role_sha256",
    )
    assert tuple(inspect.signature(VALIDATE_CERTIFICATE).parameters) == tuple(
        inspect.signature(MATCHING).parameters
    )
    for operation in (MATCHING, VALIDATE_CERTIFICATE):
        parameters = inspect.signature(operation).parameters
        assert parameters["source_support_owner"].kind is (
            inspect.Parameter.POSITIONAL_OR_KEYWORD
        )
        assert parameters["owner"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
        for name in ("source_model_policy", "source_model_role_sha256"):
            assert parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
            assert parameters[name].default is inspect.Parameter.empty


def test_exact_finite_request_law_declarations_are_canonical_and_validated():
    declaration = DECLARE(((0, 0, 1), (0, 1, 2), (3, 4, 3)), mass_denominator=6)
    assert VALIDATE_DECLARATION(declaration) is declaration
    assert declaration.request_mass_rows == ((0, 0, 1), (0, 1, 2), (3, 4, 3))
    assert declaration.mass_denominator == 6
    assert declaration.support_size == 3
    assert declaration.request_surface_support_log2 == 128
    assert declaration.canonical_sorted_unique_positive_rows is True
    assert declaration.exact_rational_normalization_certified is True
    assert declaration.reduced_common_denominator_certified is True
    assert declaration.declarative_only is True
    assert declaration.external_realization_certified is False
    assert declaration.sampling_defined is False
    assert declaration.physical_randomness_certified is False

    point = DECLARE(((5, 7, 1),), mass_denominator=1)
    assert point.point_mass_request_law is True
    large = (1 << 16_000) + 1
    large_declaration = DECLARE(((0, 0, large), (0, 1, 1)), mass_denominator=large + 1)
    assert large_declaration.mass_denominator.bit_length() == 16_001
    assert large_declaration.support_size == 2


def test_declaration_preflight_rejects_malformed_and_noncanonical_inputs():
    too_many = tuple((index, 0, 1) for index in range(4097))
    cases = (
        ([], 1, TypeError),
        ((), 1, ValueError),
        (((0, 0),), 1, ValueError),
        (([0, 0, 1],), 1, TypeError),
        (((True, 0, 1),), 1, TypeError),
        (((0, False, 1),), 1, TypeError),
        (((0, 0, True),), 1, TypeError),
        (((0, 0, 0),), 1, ValueError),
        (((1 << 64, 0, 1),), 1, ValueError),
        (((0, 0, 1),), True, TypeError),
        (((0, 0, 1), (0, 0, 1)), 2, ValueError),
        (((0, 1, 1), (0, 0, 1)), 2, ValueError),
        (((0, 0, 1), (0, 1, 1)), 3, ValueError),
        (((0, 0, 2), (0, 1, 2)), 4, ValueError),
        (((0, 0, 1 << 16_384),), 1 << 16_384, ValueError),
        (too_many, 4097, ValueError),
    )
    for rows, denominator, exception_type in cases:
        with pytest.raises(exception_type):
            DECLARE(rows, mass_denominator=denominator)


def test_declaration_hostile_values_refuse_without_touching_them():
    outer = _TouchBomb()
    with pytest.raises(TypeError):
        DECLARE(outer, mass_denominator=1)
    assert outer.calls == 0

    for position in range(3):
        bomb = _TouchBomb()
        row = [0, 0, 1]
        row[position] = bomb
        with pytest.raises(TypeError):
            DECLARE((tuple(row),), mass_denominator=1)
        assert bomb.calls == 0

    denominator = _TouchBomb()
    with pytest.raises(TypeError):
        DECLARE(((0, 0, 1),), mass_denominator=denominator)
    assert denominator.calls == 0


def test_declaration_is_sealed_nonsubclassable_nonpickleable_and_digest_bound():
    declaration = DECLARE(((0, 0, 1), (0, 1, 2), (3, 4, 3)), mass_denominator=6)
    with pytest.raises((AttributeError, TypeError)):
        declaration.support_size = 4
    with pytest.raises(TypeError):
        pickle.dumps(declaration)
    with pytest.raises(TypeError):

        class _DeclarationSubclass(type(declaration)):
            pass

    with pytest.raises(TypeError):
        type(declaration)(
            _construction_token=object(),
            **{
                name: getattr(declaration, name)
                for name in type(declaration).__annotations__
            },
        )

    promoted = _forged(declaration, external_realization_certified=True)
    with pytest.raises(ValueError):
        VALIDATE_DECLARATION(promoted)
    values = {name: getattr(promoted, name) for name in type(promoted).__annotations__}
    values["declaration_sha256"] = contract._semantic_digest(
        contract._declaration_payload(values)
    )
    redigested = _forged(promoted, declaration_sha256=values["declaration_sha256"])
    with pytest.raises(ValueError):
        VALIDATE_DECLARATION(redigested)


def test_declaration_digest_alone_rejects_an_otherwise_valid_law_change():
    declaration = DECLARE(((0, 0, 1), (0, 1, 2), (3, 4, 3)), mass_denominator=6)
    alternative = contract._declaration_summary(((0, 0, 2), (0, 1, 1), (3, 4, 3)), 6)
    stale_digest = _forged(declaration, **alternative)
    with pytest.raises(ValueError, match="digest differs"):
        VALIDATE_DECLARATION(stale_digest)
    values = {
        name: getattr(stale_digest, name) for name in type(stale_digest).__annotations__
    }
    redigested = _forged(
        stale_digest,
        declaration_sha256=contract._semantic_digest(
            contract._declaration_payload(values)
        ),
    )
    assert VALIDATE_DECLARATION(redigested) is redigested


def test_exact_partial_pushforwards_obey_support_and_tv_bounds():
    requests = tuple(range(4))
    outputs = tuple(range(4))
    uniform_output = {output: Fraction(1, 4) for output in outputs}
    laws = (
        {request: Fraction(1, 4) for request in requests},
        {
            0: Fraction(1, 10),
            1: Fraction(2, 10),
            2: Fraction(3, 10),
            3: Fraction(4, 10),
        },
        {0: Fraction(1, 2), 3: Fraction(1, 2)},
    )
    checked = 0
    for law in laws:
        support = len(law)
        for images in product((None, *outputs), repeat=len(requests)):
            mapping = dict(zip(requests, images))
            pushed = _conditional_pushforward(law, mapping)
            if pushed is None:
                continue
            assert sum(pushed.values()) == 1
            assert len(pushed) <= support
            assert _total_variation(pushed, uniform_output, outputs) >= (
                1 - Fraction(min(support, len(outputs)), len(outputs))
            )
            checked += 1
    assert checked == 1848


def test_uniform_input_pushforward_is_uniform_exactly_for_bijections():
    domain = tuple(range(4))
    law = {value: Fraction(1, 4) for value in domain}
    uniform = law.copy()
    for images in product(domain, repeat=4):
        pushed = _conditional_pushforward(law, dict(zip(domain, images)))
        assert (pushed == uniform) is (len(set(images)) == 4)


def test_nonuniform_law_with_balanced_conditional_fibers_pushes_to_uniform():
    request_law = {
        0: Fraction(4, 30),
        1: Fraction(8, 30),
        2: Fraction(3, 30),
        3: Fraction(9, 30),
        4: Fraction(6, 30),
    }
    partial_map = {0: "a", 1: "a", 2: "b", 3: "b", 4: None}
    assert len(set(request_law.values())) > 1
    assert sum(
        probability
        for request, probability in request_law.items()
        if partial_map[request] is not None
    ) == Fraction(4, 5)
    assert _conditional_pushforward(request_law, partial_map) == {
        "a": Fraction(1, 2),
        "b": Fraction(1, 2),
    }


def test_fixed_point_tv_is_exact_and_reused_external_request_can_break_iid():
    base = 3
    length = 3
    domain = tuple(product(range(base), repeat=length))
    point = domain[5]
    point_mass = {point: Fraction(1)}
    uniform = {value: Fraction(1, len(domain)) for value in domain}
    assert _total_variation(point_mass, uniform, domain) == (
        1 - Fraction(1, base**length)
    )
    reused_external_joint = {(0, 0): Fraction(1, 2), (1, 1): Fraction(1, 2)}
    iid_product_joint = {
        (left, right): Fraction(1, 4) for left in (0, 1) for right in (0, 1)
    }
    assert reused_external_joint != iid_product_joint
    assert (
        sum(
            probability
            for (left, _), probability in reused_external_joint.items()
            if left == 0
        )
        == sum(
            probability
            for (_, right), probability in reused_external_joint.items()
            if right == 0
        )
        == Fraction(1, 2)
    )
    assert len(point_mass) == 1


def test_uniform_marginals_do_not_imply_joint_product_uniformity():
    joint = {(0, 0): Fraction(1, 2), (1, 1): Fraction(1, 2)}
    left = {
        value: sum(
            probability for (first, _), probability in joint.items() if first == value
        )
        for value in (0, 1)
    }
    right = {
        value: sum(
            probability for (_, second), probability in joint.items() if second == value
        )
        for value in (0, 1)
    }
    product_joint = {
        (first, second): left[first] * right[second]
        for first in (0, 1)
        for second in (0, 1)
    }
    assert left == right == {0: Fraction(1, 2), 1: Fraction(1, 2)}
    assert joint != product_joint


def test_conditioning_can_induce_dependence_and_zero_mass_is_undefined():
    requests = tuple(product((0, 1), repeat=2))
    uniform = {request: Fraction(1, 4) for request in requests}
    diagonal_mapping = {
        request: request if request[0] == request[1] else None for request in requests
    }
    conditioned = _conditional_pushforward(uniform, diagonal_mapping)
    assert conditioned == {(0, 0): Fraction(1, 2), (1, 1): Fraction(1, 2)}
    total_refusal = {request: None for request in requests}
    assert _conditional_pushforward(uniform, total_refusal) is None


def test_derived_coordinates_never_increase_primitive_support_capacity():
    seeds = (0, 1)
    seed_law = {seed: Fraction(1, 2) for seed in seeds}
    requests = tuple(product((0, 1), repeat=2))
    outputs = tuple(range(4))
    checked = 0
    for derived_requests in product(requests, repeat=2):
        request_law = {}
        for seed, probability in seed_law.items():
            request = derived_requests[seed]
            request_law[request] = request_law.get(request, Fraction(0)) + probability
        assert len(request_law) <= 2
        for images in product((None, *outputs), repeat=4):
            request_to_output = dict(zip(requests, images))
            pushed = _conditional_pushforward(request_law, request_to_output)
            if pushed is not None:
                assert len(pushed) <= 2
            checked += 1
    assert checked == 10_000


def test_nonuniform_injection_stays_nonuniform_and_constant_output_erases_tv():
    law = {0: Fraction(1, 4), 1: Fraction(3, 4)}
    injection = {0: "a", 1: "b"}
    pushed = _conditional_pushforward(law, injection)
    assert pushed == {"a": Fraction(1, 4), "b": Fraction(3, 4)}
    assert pushed != {"a": Fraction(1, 2), "b": Fraction(1, 2)}

    reference = {0: Fraction(1, 2), 1: Fraction(1, 2)}
    assert _total_variation(law, reference, (0, 1)) == Fraction(1, 4)
    constant = {0: "same", 1: "same"}
    assert _conditional_pushforward(law, constant) == {"same": Fraction(1)}
    assert _conditional_pushforward(reference, constant) == {"same": Fraction(1)}


def test_source_ast_has_no_direct_sampling_allocation_semantic_or_power_surface():
    source_path = Path(contract.__file__)
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_imports = {"random", "secrets", "numpy", "torch"}
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not (imported & forbidden_imports)
    assert not any(
        isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow)
        for node in ast.walk(tree)
    )
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "pow"
        for node in ast.walk(tree)
    )
    left_shifts = (
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.LShift)
    )
    left_shifts = tuple(left_shifts)
    assert len(left_shifts) == 1
    assert isinstance(left_shifts[0].left, ast.Constant)
    assert left_shifts[0].left.value == 1
    assert isinstance(left_shifts[0].right, ast.Constant)
    assert left_shifts[0].right.value == 64
    forbidden_call_fragments = (
        "random_raw",
        "allocate_initial_tilt_rejection_protocol",
        "evaluate_and_apply",
        "execute",
    )
    call_text = tuple(
        ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)
    )
    assert all(
        fragment not in call
        for call in call_text
        for fragment in forbidden_call_fragments
    )
    live_binding_callers = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if any(
                isinstance(child, ast.Call)
                and ast.unparse(child.func) == "_CP45_OWNER_LIVE_BINDING"
                for child in ast.walk(node)
            ):
                live_binding_callers.add(node.name)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == "revalidate_live_ancestry"
        ):
            if any(
                isinstance(child, ast.Call)
                and ast.unparse(child.func) == "_CP45_OWNER_LIVE_BINDING"
                for child in ast.walk(node)
            ):
                live_binding_callers.add(node.name)
    assert live_binding_callers == {"_make_certificate", "revalidate_live_ancestry"}
    owner_class = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name
        == "CounterKeyedInitialTiltRejectionExplicitSourceModelContractOwner"
    )
    cached_methods = {
        node.name: node
        for node in owner_class.body
        if isinstance(node, ast.FunctionDef)
        and node.name
        in (
            "fixed_request_model",
            "external_request_law_model",
            "validate_source_model",
        )
    }
    assert set(cached_methods) == {
        "fixed_request_model",
        "external_request_law_model",
        "validate_source_model",
    }
    for method in cached_methods.values():
        method_calls = {
            ast.unparse(node.func)
            for node in ast.walk(method)
            if isinstance(node, ast.Call)
        }
        assert "self.revalidate_live_ancestry" not in method_calls
        assert "_CP45_OWNER_LIVE_BINDING" not in method_calls


def test_owner_bound_certificate_ancestry_truth_table_and_nonclaims(
    owner_bound_evidence,
):
    evidence = owner_bound_evidence
    owner = evidence["owner"]
    certificate = owner.certificate
    parent = evidence["source_support_owner"].certificate
    cp44 = parent.checkpoint44_certificate
    assert evidence["validated"] is certificate
    assert certificate.checkpoint45_certificate is parent
    assert certificate.checkpoint45_certificate_sha256 == parent.certificate_sha256
    assert certificate.checkpoint45_owner_runtime_identity == id(
        evidence["source_support_owner"]
    )
    assert certificate.checkpoint44_certificate_sha256 == cp44.certificate_sha256
    assert certificate.process_parameter_sha256 == cp44.process_parameter_sha256
    assert certificate.full_word_count == cp44.full_word_count
    assert certificate.full_word_count > certificate.request_coordinate_count == 2
    assert certificate.proposal_word_count + certificate.decision_word_count == (
        certificate.full_word_count
    )
    assert certificate.product_uniform_capsule_support_log2 == (
        64 * certificate.full_word_count
    )
    expected_positive = {
        "exact_checkpoint45_owner_binding_certified",
        "exact_transitive_checkpoint44_36_27_26_binding_inherited",
        "exact_checkpoint44_capsule_partition_inherited",
        "fixed_and_external_models_type_separated",
        "fixed_request_point_mass_theorem_inherited",
        "external_finite_request_support_theorem_certified",
        "conditioning_cannot_enlarge_support_certified",
        "success_value_independence_not_required_certified",
        "current_two_coordinate_request_capacity_obstruction_certified",
        "source_to_output_tv_nonconverse_recorded",
        "declaration_and_model_construction_source_allocation_and_semantic_"
        "operation_free_certified",
        "model_construction_parent_owner_live_binding_free_certified",
        "no_caller_global_rng_state_mutation_certified",
        "cached_model_descriptor_boundary_recorded",
        "explicit_live_ancestry_revalidation_available",
        "declaration_support_cap_separate_from_analytic_surface_capacity_recorded",
        "support_capacity_necessary_not_sufficient_and_fiber_balance_criterion_"
        "recorded",
    }
    expected_negative = {
        "external_request_law_realization_certified",
        "external_request_sampling_certified",
        "live_request_uniformity_certified",
        "live_request_coordinate_independence_certified",
        "full_capsule_product_uniformity_certified",
        "nondegenerate_v_w_independence_certified",
        "numeric_capsule_acquisition_probability_certified",
        "numeric_return_probability_certified",
        "numeric_refusal_probability_certified",
        "unconditional_capsule_law_certified",
        "unconditional_output_law_certified",
        "semantic_output_tv_lower_bound_certified",
        "transitive_rng_call_absence_certified",
        "hidden_entropy_or_environment_accounted",
        "physical_randomness_certified",
        "cross_call_freshness_certified",
        "per_model_live_checkpoint45_ancestry_revalidation_certified",
        "conditioning_event_positive_mass_certified",
        "current_request_surface_sufficient_for_product_uniform_capsule",
        "source_support_sufficiency_for_product_uniformity_certified",
        "weighted_fiber_balance_certified",
        "external_full_entropy_source_interface_implemented",
        "loaded_code_integrity_certified",
        "runtime_portable",
        "cryptographic_authentication",
        "initializer_admissible",
        "path_admissible",
        "sampler_admissible",
        "scientific_claim_promoted",
        "model_quality_claim_promoted",
        "generality_claim_promoted",
    }
    assert set(contract._CERTIFICATE_POSITIVE_FLAGS) == expected_positive
    assert set(contract._CERTIFICATE_NEGATIVE_FLAGS) == expected_negative
    assert not (expected_positive & expected_negative)
    for name in expected_positive:
        assert getattr(certificate, name) is True
    for name in expected_negative:
        assert getattr(certificate, name) is False
    assert certificate.passed is True


def test_owner_bound_fixed_and_external_models_are_conditional_cached_descriptors(
    owner_bound_evidence,
):
    evidence = owner_bound_evidence
    fixed = evidence["fixed"]
    external = evidence["external"]
    fixed_return = evidence["fixed_return"]
    external_capsule = evidence["external_capsule"]
    assert (
        type(fixed)
        is contract.CounterKeyedInitialTiltRejectionFixedRequestReplaySourceModel
    )
    assert type(external) is (
        contract.CounterKeyedInitialTiltRejectionExternalFiniteRequestLawSourceModel
    )
    assert fixed.model_mode == contract.INITIAL_TILT_REJECTION_FIXED_REQUEST_MODE
    assert fixed.conditioning_event == CAPSULE_EVENT
    assert (fixed.run_id, fixed.initialization_index) == (7, 11)
    assert fixed.request_support_size == fixed.capsule_support_size_upper_bound == 1
    assert fixed.conditional_source_law_formula == (
        "if-P(%s)>0-then-nu_%s=Dirac-at-symbolic-capsule-for-request-(7,11)"
        % (CAPSULE_EVENT, CAPSULE_EVENT)
    )
    assert fixed.conditional_exact_source_tv_formula == (
        "if-P(%s)>0-then-TV(nu_%s,U_L)=1-2^(-64*%d)"
        % (CAPSULE_EVENT, CAPSULE_EVENT, fixed.full_word_count)
    )
    assert fixed.fixed_request_point_mass_under_positive_event_derived is True
    assert fixed.fixed_request_exact_tv_under_positive_event_derived is True
    assert (
        fixed.degenerate_constant_v_w_factorization_under_positive_event_recorded
        is True
    )
    assert fixed.capsule_value_materialized is False
    assert fixed.request_executed is False

    assert external.model_mode == (
        contract.INITIAL_TILT_REJECTION_EXTERNAL_FINITE_REQUEST_LAW_MODE
    )
    assert external.conditioning_event == RETURN_EVENT
    assert external.declaration is evidence["declaration"]
    assert external.declared_request_support_size == 3
    assert external.declared_mass_denominator == 6
    assert external.capsule_support_size_upper_bound == 3
    assert external.uniform_support_mass_upper_bound_numerator == 3
    assert external.uniform_support_mass_upper_bound_denominator_log2 == (
        64 * external.full_word_count
    )
    assert external.conditional_source_tv_lower_bound_formula == (
        "if-P(%s)>0-then-TV(nu_%s,U_L)>=1-3/2^(%d)"
        % (RETURN_EVENT, RETURN_EVENT, 64 * external.full_word_count)
    )
    assert external.conditional_support_bound_under_positive_event_derived is True
    assert external.success_value_independence_required is False
    assert external.external_request_law_realization_certified is False
    assert external.request_sampling_defined is False
    assert fixed_return.conditioning_event == RETURN_EVENT
    assert (fixed_return.run_id, fixed_return.initialization_index) == (13, 17)
    assert external_capsule.conditioning_event == CAPSULE_EVENT
    assert external_capsule.declaration is evidence["declaration"]

    for model in (fixed, external, fixed_return, external_capsule):
        assert model.cached_descriptor_only is True
        assert model.live_checkpoint45_ancestry_revalidated_for_this_model is False
        assert model.conditional_event_positive_mass_required is True
        assert model.conditional_event_positive_mass_certified is False
        assert model.conditional_capsule_law_instantiated is False
        assert model.nondegenerate_v_w_independence_certified is False
        assert model.physical_randomness_certified is False
        assert model.cross_call_freshness_certified is False
        assert model.semantic_output_tv_lower_bound_certified is False


def test_owner_bound_certification_models_validation_are_rng_and_operation_safe(
    owner_bound_evidence,
):
    calls = owner_bound_evidence["calls"]
    for name in ("cp27_allocate", "cp43_combined", "cp43_g", "cp43_h", "cp44_execute"):
        assert calls[name] == 0
    assert calls["cp45_live_binding"] == 3
    assert calls["cp45_structural_certificate_validation"] == 26


def test_owner_bound_records_and_owner_are_sealed_and_nonpickleable(
    owner_bound_evidence,
):
    evidence = owner_bound_evidence
    records = (
        evidence["declaration"],
        evidence["owner"].certificate,
        evidence["fixed"],
        evidence["external"],
    )
    for record in records:
        with pytest.raises((AttributeError, TypeError)):
            object_name = next(iter(type(record).__annotations__))
            setattr(record, object_name, getattr(record, object_name))
        with pytest.raises(TypeError):
            pickle.dumps(record)
        with pytest.raises(TypeError):
            type(record)(
                _construction_token=object(),
                **{
                    name: getattr(record, name) for name in type(record).__annotations__
                },
            )

    classes = tuple(type(record) for record in records) + (type(evidence["owner"]),)
    for record_type in classes:
        with pytest.raises(TypeError):
            type("ForbiddenSubclass", (record_type,), {})
    with pytest.raises(AttributeError):
        evidence["owner"]._certificate = evidence["owner"].certificate
    with pytest.raises(TypeError):
        pickle.dumps(evidence["owner"])


def test_owner_bound_plain_redigested_and_hostile_tampering_refuses(
    owner_bound_evidence, monkeypatch
):
    owner = owner_bound_evidence["owner"]
    fixed = owner_bound_evidence["fixed"]
    external = owner_bound_evidence["external"]
    certificate = owner.certificate

    promoted_fixed = _forged(fixed, physical_randomness_certified=True)
    fixed_values = {
        name: getattr(promoted_fixed, name)
        for name in type(promoted_fixed).__annotations__
    }
    fixed_digest = contract._semantic_digest(
        contract._fixed_model_payload(fixed_values)
    )
    promoted_fixed = _forged(promoted_fixed, source_model_sha256=fixed_digest)
    with pytest.raises(ValueError):
        owner.validate_source_model(promoted_fixed)

    promoted_external = _forged(
        external, external_request_law_realization_certified=True
    )
    external_values = {
        name: getattr(promoted_external, name)
        for name in type(promoted_external).__annotations__
    }
    external_digest = contract._semantic_digest(
        contract._external_model_payload(external_values)
    )
    promoted_external = _forged(promoted_external, source_model_sha256=external_digest)
    with pytest.raises(ValueError):
        owner.validate_source_model(promoted_external)

    promoted_certificate = _forged(certificate, scientific_claim_promoted=True)
    certificate_values = {
        name: getattr(promoted_certificate, name)
        for name in type(promoted_certificate).__annotations__
    }
    certificate_digest = contract._semantic_digest(
        contract._certificate_payload(certificate_values)
    )
    promoted_certificate = _forged(
        promoted_certificate, certificate_sha256=certificate_digest
    )
    with pytest.raises(ValueError):
        contract._validate_certificate(promoted_certificate)

    hostile = _TouchBomb()
    hostile_certificate = _forged(certificate, scientific_claim_promoted=hostile)
    hostile_fixed = _forged(fixed, physical_randomness_certified=hostile)
    hostile_external = _forged(
        external, external_request_law_realization_certified=hostile
    )
    parent_calls = []

    def parent_replacement(*args, **kwargs):
        parent_calls.append((args, kwargs))
        raise AssertionError("parent validation ran before hostile preflight")

    with monkeypatch.context() as patcher:
        patcher.setattr(contract, "_CP45_VALIDATE_CERTIFICATE", parent_replacement)
        with pytest.raises(TypeError):
            contract._validate_certificate(hostile_certificate)
        with pytest.raises(TypeError):
            contract._validate_fixed_model(hostile_fixed)
        with pytest.raises(TypeError):
            contract._validate_external_model(hostile_external)
    assert hostile.calls == 0
    assert parent_calls == []


def test_owner_bound_digest_only_certificate_and_model_changes_refuse(
    owner_bound_evidence,
):
    evidence = owner_bound_evidence
    owner = evidence["owner"]
    certificate = owner.certificate
    fixed = evidence["fixed"]
    external = evidence["external"]

    other_role = _forged(certificate, source_model_role_sha256="a" * 64)
    with pytest.raises(ValueError, match="digest differs"):
        contract._validate_certificate(other_role)

    alternate_summary = contract._fixed_model_summary(
        certificate,
        id(owner),
        fixed.conditioning_event,
        fixed.run_id + 1,
        fixed.initialization_index,
    )
    other_valid_request = _forged(fixed, **alternate_summary)
    with pytest.raises(ValueError, match="digest differs"):
        contract._validate_fixed_model(other_valid_request)

    alternate_declaration = DECLARE(
        ((0, 0, 2), (0, 1, 1), (3, 4, 3)), mass_denominator=6
    )
    alternate_external_summary = contract._external_model_summary(
        certificate,
        id(owner),
        alternate_declaration,
        external.conditioning_event,
    )
    other_valid_law = _forged(external, **alternate_external_summary)
    with pytest.raises(ValueError, match="digest differs"):
        contract._validate_external_model(other_valid_law)


def test_owner_bound_cross_owner_and_owner_identity_splicing_refuse(
    owner_bound_evidence,
):
    evidence = owner_bound_evidence
    owner = evidence["owner"]
    other = contract.CounterKeyedInitialTiltRejectionExplicitSourceModelContractOwner(
        evidence["source_support_owner"],
        owner.certificate,
        _construction_token=contract._OWNER_TOKEN,
    )
    assert other is not owner
    with pytest.raises(ValueError):
        other.validate_source_model(evidence["fixed"])

    forged_identity = _forged(
        evidence["fixed"], source_model_owner_runtime_identity=id(other)
    )
    values = {
        name: getattr(forged_identity, name)
        for name in type(forged_identity).__annotations__
    }
    forged_identity = _forged(
        forged_identity,
        source_model_sha256=contract._semantic_digest(
            contract._fixed_model_payload(values)
        ),
    )
    with pytest.raises(ValueError):
        owner.validate_source_model(forged_identity)


def test_owner_bound_hostile_inputs_refuse_without_touch_or_live_operation(
    owner_bound_evidence,
):
    owner = owner_bound_evidence["owner"]
    for arguments in (
        (_TouchBomb(), 0, CAPSULE_EVENT),
        (0, _TouchBomb(), CAPSULE_EVENT),
        (0, 0, _TouchBomb()),
    ):
        run_id, initialization_index, event = arguments
        bombs = tuple(value for value in arguments if isinstance(value, _TouchBomb))
        with _trace_cp46_boundaries() as calls:
            with pytest.raises(TypeError):
                owner.fixed_request_model(
                    run_id, initialization_index, conditioning_event=event
                )
        assert all(bomb.calls == 0 for bomb in bombs)
        assert all(count == 0 for count in calls.values())

    declaration_bomb = _TouchBomb()
    with _trace_cp46_boundaries() as external_calls:
        with pytest.raises(TypeError):
            owner.external_request_law_model(
                declaration_bomb, conditioning_event=RETURN_EVENT
            )
    assert declaration_bomb.calls == 0
    assert all(count == 0 for count in external_calls.values())
    with _trace_cp46_boundaries() as invalid_event_calls:
        with pytest.raises(ValueError):
            owner.fixed_request_model(
                0, 0, conditioning_event="not-a-cp46-conditioning-event"
            )
    assert all(count == 0 for count in invalid_event_calls.values())
    with pytest.raises(TypeError):
        owner.fixed_request_model(True, 0, conditioning_event=CAPSULE_EVENT)
    with pytest.raises(TypeError):
        owner.fixed_request_model(np.int64(0), 0, conditioning_event=CAPSULE_EVENT)


def test_owner_bound_local_parent_and_public_helper_drift_refuse_before_execution(
    owner_bound_evidence, monkeypatch
):
    evidence = owner_bound_evidence
    owner = evidence["owner"]

    replacements = (
        (contract, "_GCD", lambda: DECLARE(((0, 0, 1),), mass_denominator=1)),
        (
            contract,
            "_JSON_DUMPS",
            lambda: DECLARE(((0, 0, 1),), mass_denominator=1),
        ),
        (
            contract._obstruction,
            "_validate_certificate_values",
            lambda: DECLARE(((0, 0, 1),), mass_denominator=1),
        ),
        (
            contract,
            "_require_sha256",
            lambda: CERTIFY(
                evidence["source_support_owner"],
                source_model_policy=POLICY,
                source_model_role_sha256=ROLE,
            ),
        ),
        (
            contract,
            "_require_sha256",
            lambda: MATCHING(
                evidence["source_support_owner"],
                owner,
                source_model_policy=POLICY,
                source_model_role_sha256=ROLE,
            ),
        ),
    )
    for namespace, name, action in replacements:
        calls = []

        def replacement(*args, **kwargs):
            calls.append((args, kwargs))
            raise AssertionError("replacement executed")

        with monkeypatch.context() as patcher:
            patcher.setattr(namespace, name, replacement)
            with pytest.raises(ValueError):
                action()
        assert calls == []

    guard_calls = []

    def guard_replacement(*args, **kwargs):
        guard_calls.append((args, kwargs))
        raise AssertionError("replacement guard executed")

    with monkeypatch.context() as patcher:
        patcher.setattr(contract, "_LOCAL_SURFACE_GUARD", guard_replacement)
        with pytest.raises(ValueError):
            owner.fixed_request_model(0, 0, conditioning_event=CAPSULE_EVENT)
    assert guard_calls == []

    with monkeypatch.context() as patcher:
        patcher.setattr(
            contract,
            "CounterKeyedInitialTiltRejectionExplicitSourceModelContractOwner",
            object,
        )
        with pytest.raises(ValueError):
            owner.fixed_request_model(0, 0, conditioning_event=CAPSULE_EVENT)
