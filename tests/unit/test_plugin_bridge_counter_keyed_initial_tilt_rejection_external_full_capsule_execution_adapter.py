"""Hostile tests for checkpoint-47 external full-capsule execution."""

import ast
from contextlib import contextmanager
from fractions import Fraction
import inspect
from itertools import product
from pathlib import Path
import pickle
import random
import sys
import threading
import types

import numpy as np
import pytest


torch = pytest.importorskip(
    "torch", reason="external full-capsule certification requires PyTorch"
)

from heterodiff.processes import (  # noqa: E402
    plugin_bridge_counter_keyed_initial_tilt_rejection_external_full_capsule_execution_adapter as adapter,
)

checkpoint46 = pytest.importorskip(  # noqa: E402
    "tests.unit.test_plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "explicit_source_model_contract",
    reason="external full-capsule certification requires the CP46 fixture",
)


POLICY = getattr(
    adapter,
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_"
    "EXECUTION_ADAPTER_POLICY",
)
CERTIFY = getattr(
    adapter,
    "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_external_full_"
    "capsule_execution_adapter",
)
MATCHING = getattr(
    adapter,
    "require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_"
    "external_full_capsule_execution_adapter",
)
VALIDATE_CERTIFICATE = getattr(
    adapter,
    "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_external_"
    "full_capsule_execution_adapter_certificate",
)

CERTIFICATE_TYPE = getattr(
    adapter,
    "CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterCertificate",
)
RECEIPT_TYPE = getattr(
    adapter,
    "CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterProviderReceipt",
)
RESULT_TYPE = getattr(
    adapter,
    "CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionResult",
)
SNAPSHOT_TYPE = getattr(
    adapter,
    "CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterLedgerSnapshot",
)
OWNER_TYPE = getattr(
    adapter,
    "CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterOwner",
)
ERROR_TYPE = getattr(
    adapter,
    "PluginBridgeCounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterError",
)

SOURCE_INSTANCE_SHA256 = "a" * 64
PROVIDER_ROLE_SHA256 = "b" * 64
EXECUTION_ROLE_SHA256 = "c" * 64
MAX_RETIRED_DRAWS = 32
VALID_DRAW_INDEX = 10
SAME_VALUE_DRAW_INDEX = 11
EXCEPTION_DRAW_INDEX = 12
MALFORMED_OUTER_DRAW_INDEX = 13
MALFORMED_ELEMENT_DRAW_INDEX = 14
ATOMIC_DRAW_INDEX = 15


class _ProviderFailure(RuntimeError):
    pass


def _operation_codes():
    calls = checkpoint46.checkpoint45.checkpoint44._call_codes()
    calls["cp44_execute"] = adapter._CP44_OWNER_TYPE.execute.__code__
    calls["cp46_live_revalidation"] = adapter._CP46_LIVE_REVALIDATE.__code__
    calls["cp46_cached_binding"] = adapter._CP46_CACHED_BINDING.__code__
    return calls


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


def _uniform(domain):
    domain = tuple(domain)
    return {value: Fraction(1, len(domain)) for value in domain}


def _total_variation(left, right, domain):
    domain = tuple(domain)
    assert sum(left.values()) == 1
    assert sum(right.values()) == 1
    return Fraction(1, 2) * sum(
        abs(left.get(value, Fraction(0)) - right.get(value, Fraction(0)))
        for value in domain
    )


def _conditional_law(base_law, success_weights):
    success_mass = sum(
        probability * success_weights[value] for value, probability in base_law.items()
    )
    if success_mass == 0:
        return None
    return {
        value: probability * success_weights[value] / success_mass
        for value, probability in base_law.items()
        if success_weights[value] != 0
    }


def _pushforward(law, mapping):
    pushed = {}
    for value, probability in law.items():
        image = mapping[value]
        pushed[image] = pushed.get(image, Fraction(0)) + probability
    return pushed


def test_required_public_surface_and_owner_method_signatures_are_exact():
    expected = {
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_EXTERNAL_FULL_"
        "CAPSULE_EXECUTION_ADAPTER_SCHEMA_VERSION",
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_EXTERNAL_FULL_"
        "CAPSULE_EXECUTION_ADAPTER_POLICY",
        "PLUGIN_BRIDGE_COUNTER_KEYED_INITIAL_TILT_REJECTION_EXTERNAL_FULL_"
        "CAPSULE_EXECUTION_ADAPTER_SCOPE",
        "INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_INTERFACE_CAPACITY_THEOREM",
        "INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_PRODUCT_LAW_THEOREM",
        "INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_SUCCESS_CONDITIONING_CAVEAT",
        "INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_RAW_WORD_DOMAIN_SIZE",
        "INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_MIN_RETIRED_DRAWS",
        "INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_MAX_RETIRED_DRAWS",
        "INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_PROVIDER_MODE",
        "CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterCertificate",
        "CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterProviderReceipt",
        "CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterResult",
        "CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterLedgerSnapshot",
        "CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterRetiredDrawLedgerSnapshot",
        "CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterOwner",
        "PluginBridgeCounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterError",
        "certify_plugin_bridge_counter_keyed_initial_tilt_rejection_external_full_capsule_execution_adapter",
        "require_matching_plugin_bridge_counter_keyed_initial_tilt_rejection_external_full_capsule_execution_adapter",
        "validate_plugin_bridge_counter_keyed_initial_tilt_rejection_external_full_capsule_execution_adapter_certificate",
    }
    assert set(adapter.__all__) == expected
    assert len(adapter.__all__) == len(set(adapter.__all__)) == 20
    assert CERTIFICATE_TYPE.__name__ in expected
    assert RECEIPT_TYPE.__name__ in expected
    assert RESULT_TYPE.__name__ in expected
    assert SNAPSHOT_TYPE.__name__ in expected
    assert OWNER_TYPE.__name__ in expected
    assert issubclass(ERROR_TYPE, Exception)
    assert (
        adapter.CounterKeyedInitialTiltRejectionExternalFullCapsuleExecutionAdapterRetiredDrawLedgerSnapshot
        is SNAPSHOT_TYPE
    )
    assert (
        adapter.INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_RAW_WORD_DOMAIN_SIZE
        == (1 << 64)
    )
    assert adapter.INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_PROVIDER_MODE == (
        "direct-exact-tuple-of-L-uint64-words"
    )

    assert tuple(inspect.signature(CERTIFY).parameters) == (
        "source_model_owner",
        "full_capsule_provider",
        "source_instance_sha256",
        "provider_role_sha256",
        "execution_policy",
        "execution_role_sha256",
        "max_retired_draws",
    )
    assert tuple(inspect.signature(MATCHING).parameters) == (
        "source_model_owner",
        "full_capsule_provider",
        "owner",
        "source_instance_sha256",
        "provider_role_sha256",
        "execution_policy",
        "execution_role_sha256",
        "max_retired_draws",
    )
    assert tuple(inspect.signature(VALIDATE_CERTIFICATE).parameters) == tuple(
        inspect.signature(MATCHING).parameters
    )
    for operation in (CERTIFY, MATCHING, VALIDATE_CERTIFICATE):
        parameters = inspect.signature(operation).parameters
        positional = ("source_model_owner", "full_capsule_provider")
        if operation is not CERTIFY:
            positional += ("owner",)
        for name in positional:
            assert parameters[name].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
        for name in (
            "source_instance_sha256",
            "provider_role_sha256",
            "execution_policy",
            "execution_role_sha256",
            "max_retired_draws",
        ):
            assert parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
            assert parameters[name].default is inspect.Parameter.empty

    assert tuple(inspect.signature(OWNER_TYPE.execute).parameters) == (
        "self",
        "run_id",
        "initialization_index",
        "draw_index",
    )
    assert tuple(inspect.signature(OWNER_TYPE.validate_result).parameters) == (
        "self",
        "result",
    )
    assert tuple(inspect.signature(OWNER_TYPE.ledger_snapshot).parameters) == ("self",)
    assert tuple(inspect.signature(OWNER_TYPE.validate_ledger_snapshot).parameters) == (
        "self",
        "snapshot",
    )
    assert tuple(inspect.signature(OWNER_TYPE.revalidate_live_ancestry).parameters) == (
        "self",
    )
    assert isinstance(OWNER_TYPE.certificate, property)
    assert isinstance(OWNER_TYPE.source_model_owner, property)


def test_toy_full_capsule_uniform_law_is_exact():
    domain = tuple(product(range(4), repeat=2))
    law = _uniform(domain)
    assert len(domain) == len(law) == 16
    assert sum(law.values()) == 1
    assert set(law.values()) == {Fraction(1, 16)}
    assert _total_variation(law, _uniform(domain), domain) == 0


def test_uniform_marginals_do_not_imply_product_uniformity():
    values = tuple(range(4))
    domain = tuple(product(values, repeat=2))
    diagonal = {(value, value): Fraction(1, 4) for value in values}
    first = {
        value: sum(
            probability for pair, probability in diagonal.items() if pair[0] == value
        )
        for value in values
    }
    second = {
        value: sum(
            probability for pair, probability in diagonal.items() if pair[1] == value
        )
        for value in values
    }
    assert first == second == _uniform(values)
    assert _total_variation(diagonal, _uniform(domain), domain) == Fraction(3, 4)


def test_reusing_one_capsule_breaks_cross_call_iid():
    capsules = tuple(product(range(2), repeat=2))
    joint_domain = tuple(product(capsules, repeat=2))
    reused = {(capsule, capsule): Fraction(1, 4) for capsule in capsules}
    product_uniform = _uniform(joint_domain)
    assert _total_variation(reused, product_uniform, joint_domain) == Fraction(3, 4)
    for position in (0, 1):
        marginal = {
            capsule: sum(
                probability
                for pair, probability in reused.items()
                if pair[position] == capsule
            )
            for capsule in capsules
        }
        assert marginal == _uniform(capsules)


def test_value_dependent_success_biases_but_independent_success_does_not():
    domain = tuple(range(4))
    uniform = _uniform(domain)
    value_dependent = _conditional_law(
        uniform,
        {value: Fraction(int(value < 2)) for value in domain},
    )
    independent = _conditional_law(
        uniform,
        {value: Fraction(1, 2) for value in domain},
    )
    assert value_dependent == {0: Fraction(1, 2), 1: Fraction(1, 2)}
    assert _total_variation(value_dependent, uniform, domain) == Fraction(1, 2)
    assert independent == uniform


def test_identity_ingestion_is_exact_and_balanced_fibers_are_necessary_and_sufficient():
    domain = tuple(product(range(4), repeat=2))
    law = _uniform(domain)
    identity = {capsule: capsule for capsule in domain}
    assert _pushforward(law, identity) == law

    outputs = (0, 1, 2, 3)
    for images in product(outputs, repeat=len(outputs)):
        mapping = dict(zip(outputs, images))
        pushed = _pushforward(_uniform(outputs), mapping)
        fiber_sizes = tuple(images.count(output) for output in outputs)
        assert (pushed == _uniform(outputs)) is (fiber_sizes == (1, 1, 1, 1))


def test_success_conditioning_is_uniform_exactly_for_balanced_positive_weights():
    domain = tuple(range(4))
    law = _uniform(domain)
    checked = 0
    for raw_weights in product(range(3), repeat=len(domain)):
        weights = {
            value: Fraction(weight, 2) for value, weight in zip(domain, raw_weights)
        }
        conditional = _conditional_law(law, weights)
        if conditional is None:
            continue
        positive_weights = tuple(weight for weight in weights.values() if weight > 0)
        is_full_uniform = conditional == law
        assert is_full_uniform is (
            len(positive_weights) == len(domain) and len(set(positive_weights)) == 1
        )
        checked += 1
    assert checked == (3**4 - 1)


def test_lossy_ingestion_cannot_preserve_full_capsule_uniformity():
    domain = tuple(product(range(4), repeat=2))
    uniform = _uniform(domain)
    lossy = {capsule: capsule[0] for capsule in domain}
    pushed = _pushforward(uniform, lossy)
    assert pushed == _uniform(range(4))
    lifted = {(value, 0): probability for value, probability in pushed.items()}
    assert len(lifted) == 4 < len(domain)
    assert _total_variation(lifted, uniform, domain) == Fraction(3, 4)


def test_constant_semantic_map_erases_source_tv_and_blocks_a_tv_nonconverse():
    source_domain = tuple(range(4))
    uniform = _uniform(source_domain)
    point = {0: Fraction(1)}
    assert _total_variation(point, uniform, source_domain) == Fraction(3, 4)
    constant = {value: "same-output" for value in source_domain}
    assert _pushforward(point, constant) == _pushforward(uniform, constant)


def test_full_capsule_support_and_point_mass_tv_are_exact():
    for base in (2, 3, 4):
        for length in (1, 2, 3):
            domain = tuple(product(range(base), repeat=length))
            uniform = _uniform(domain)
            point = {domain[-1]: Fraction(1)}
            assert len(domain) == base**length
            assert _total_variation(point, uniform, domain) == (
                1 - Fraction(1, base**length)
            )


def test_support_size_tv_lower_bound_is_tight_for_uniform_subsets():
    domain = tuple(range(8))
    uniform = _uniform(domain)
    for support_size in range(1, len(domain) + 1):
        subset = domain[:support_size]
        supported = _uniform(subset)
        assert _total_variation(supported, uniform, domain) == (
            1 - Fraction(support_size, len(domain))
        )


def test_every_toy_codec_permutation_preserves_uniformity_bijectively():
    domain = tuple(range(4))
    law = _uniform(domain)
    checked = 0
    for encoded in product(domain, repeat=len(domain)):
        if len(set(encoded)) != len(domain):
            continue
        encode = dict(zip(domain, encoded))
        decode = {value: key for key, value in encode.items()}
        assert _pushforward(law, encode) == law
        assert all(decode[encode[value]] == value for value in domain)
        checked += 1
    assert checked == 24


def test_whole_capsule_product_uniformity_has_exact_uniform_coordinates():
    capsules = tuple(product(range(4), repeat=2))
    law = _uniform(capsules)
    for coordinate in (0, 1):
        marginal = {
            value: sum(
                probability
                for capsule, probability in law.items()
                if capsule[coordinate] == value
            )
            for value in range(4)
        }
        assert marginal == _uniform(range(4))
    for left, right in product(range(4), repeat=2):
        assert law[(left, right)] == Fraction(1, 4) * Fraction(1, 4)


def test_zero_success_mass_has_no_conditional_capsule_law():
    domain = tuple(range(4))
    assert (
        _conditional_law(_uniform(domain), {value: Fraction(0) for value in domain})
        is None
    )


def test_deterministic_ingestion_never_enlarges_finite_source_support():
    requests = tuple(range(4))
    request_laws = (
        _uniform(requests),
        {0: Fraction(1, 2), 3: Fraction(1, 2)},
        {2: Fraction(1)},
    )
    for law in request_laws:
        for images in product(range(4), repeat=len(requests)):
            mapping = dict(zip(requests, images))
            pushed = _pushforward(law, mapping)
            assert len(pushed) <= len(law)


def test_direct_word_identity_preserves_uint64_boundaries_and_order():
    words = (
        0,
        1,
        255,
        256,
        1 << 63,
        (1 << 64) - 1,
        0xAAAAAAAAAAAAAAAA,
        0x5555555555555555,
    )
    ingested = adapter._exact_words(
        words,
        name="provider_full_words",
        length=len(words),
    )
    assert ingested is words
    assert ingested == words
    assert ingested[::-1] != words


def test_direct_word_preflight_rejects_malformed_outer_shape_and_elements():
    valid = (0, 1, (1 << 64) - 1)
    cases = (
        (list(valid), TypeError),
        (iter(valid), TypeError),
        (valid[:-1], ValueError),
        (valid + (0,), ValueError),
        ((False, 1, 2), TypeError),
        ((np.int64(0), 1, 2), TypeError),
        ((0.0, 1, 2), TypeError),
        ((-1, 1, 2), ValueError),
        (((1 << 64), 1, 2), ValueError),
        (((1 << 256), 1, 2), ValueError),
    )
    for value, error_type in cases:
        with pytest.raises(error_type):
            adapter._exact_words(value, name="provider_full_words", length=3)


def test_direct_word_and_scalar_preflight_do_not_coerce_hostile_values():
    word = _TouchBomb()
    with pytest.raises(TypeError):
        adapter._exact_words(
            (word,),
            name="provider_full_words",
            length=1,
        )
    assert word.calls == 0

    scalar = _TouchBomb()
    with pytest.raises(TypeError):
        adapter._exact_uint64(scalar, name="draw_index")
    assert scalar.calls == 0


def test_retired_draw_bound_and_claim_polarities_are_exact():
    minimum = adapter.INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_MIN_RETIRED_DRAWS
    maximum = adapter.INITIAL_TILT_REJECTION_EXTERNAL_FULL_CAPSULE_MAX_RETIRED_DRAWS
    assert adapter._bounded_retired_draws(minimum) == minimum == 1
    assert adapter._bounded_retired_draws(maximum) == maximum == 65536
    for value, error_type in (
        (True, TypeError),
        (np.int64(1), TypeError),
        (minimum - 1, ValueError),
        (maximum + 1, ValueError),
    ):
        with pytest.raises(error_type):
            adapter._bounded_retired_draws(value)
    assert set(adapter._CERTIFICATE_POSITIVE_FLAGS).isdisjoint(
        adapter._CERTIFICATE_NEGATIVE_FLAGS
    )
    assert "provider_product_uniform_law_certified" in (
        adapter._CERTIFICATE_NEGATIVE_FLAGS
    )
    assert "provider_iid_across_calls_certified" in (
        adapter._CERTIFICATE_NEGATIVE_FLAGS
    )
    assert "scientific_claim_promoted" in adapter._CERTIFICATE_NEGATIVE_FLAGS
    assert (
        "hostile_same_process_private_state_tamper_resilience_certified"
        in adapter._CERTIFICATE_NEGATIVE_FLAGS
    )


def test_transitive_local_surfaces_and_constant_only_code_changes_are_detected():
    frozen = dict(adapter._FROZEN_LOCAL_SURFACES)
    for name in (
        "_LOCK_FACTORY",
        "_SHA256",
        "_MARSHAL_DUMPS",
        "_CODE_FINGERPRINT_FORMAT",
        "_PYTHON_VERSION",
        "_PYTHON_IMPLEMENTATION",
        "_CERTIFICATE_TOKEN",
        "_validate_certificate_values",
        "_validate_receipt_values",
        "_validate_result_values",
        "_validate_ledger_snapshot_values",
        "_validate_ledger_rows",
        "_retirement_chain_sha256s",
    ):
        assert frozen[name] is getattr(adapter, name)

    def returns_one():
        return 1

    constants = tuple(
        2 if value == 1 else value for value in returns_one.__code__.co_consts
    )
    changed = types.FunctionType(
        returns_one.__code__.replace(co_consts=constants),
        returns_one.__globals__,
    )
    assert returns_one() == 1
    assert changed() == 2
    assert adapter._code_sha256(returns_one) != adapter._code_sha256(changed)

    def returns_none():
        return None

    late_interned_text = "".join(
        ("cp47 late ", "interning regression ", "payload 20491237")
    )
    late_interned_code = returns_none.__code__.replace(
        co_consts=(None, late_interned_text)
    )
    late_interned_function = types.FunctionType(
        late_interned_code,
        returns_none.__globals__,
    )
    digest_before_interning = adapter._code_sha256(late_interned_function)
    assert sys.intern(late_interned_text) is late_interned_text
    assert adapter._code_sha256(late_interned_function) == digest_before_interning
    assert adapter._CODE_FINGERPRINT_FORMAT == (
        "python-marshal-v2-no-reference-table-exact-constant-domain-"
        "process-identity-default-fingerprint-v1"
    )

    original_code = adapter._exact_uint64.__code__
    original_runtime_sha256 = adapter._runtime_sha256()
    runtime_text = "".join(
        ("cp47 runtime late ", "interning regression ", "payload 91822351")
    )
    adapter._exact_uint64.__code__ = original_code.replace(
        co_consts=original_code.co_consts + (runtime_text,)
    )
    try:
        augmented_runtime_sha256 = adapter._runtime_sha256()
        assert augmented_runtime_sha256 != original_runtime_sha256
        assert sys.intern(runtime_text) is runtime_text
        assert adapter._runtime_sha256() == augmented_runtime_sha256
    finally:
        adapter._exact_uint64.__code__ = original_code
    assert adapter._runtime_sha256() == original_runtime_sha256

    def returns_float():
        return 1.5

    with pytest.raises(TypeError):
        adapter._code_sha256(returns_float)

    class FakeCodeCarrier:
        __code__ = 1
        __defaults__ = None
        __kwdefaults__ = None

    with pytest.raises(TypeError):
        adapter._code_sha256(FakeCodeCarrier())

    def contains_nested_float_code():
        def returns_nested_float():
            return 1.5

        return returns_nested_float

    with pytest.raises(TypeError):
        adapter._code_sha256(contains_nested_float_code)

    class BadDefaultsCarrier:
        __code__ = returns_none.__code__
        __defaults__ = []
        __kwdefaults__ = None

    with pytest.raises(TypeError):
        adapter._code_sha256(BadDefaultsCarrier())

    class BadKeywordDefaultsCarrier:
        __code__ = returns_none.__code__
        __defaults__ = None
        __kwdefaults__ = ()

    with pytest.raises(TypeError):
        adapter._code_sha256(BadKeywordDefaultsCarrier())

    first_default_identity = object()
    second_default_identity = object()

    def first_default(value=first_default_identity):
        return value

    def second_default(value=second_default_identity):
        return value

    second_default.__code__ = first_default.__code__
    assert adapter._code_sha256(first_default) != adapter._code_sha256(second_default)


def test_internal_bounded_ledger_rows_are_canonical_and_hostile_safe():
    rows = ((0, 1, 2, 10), (1, 3, 4, 11))
    assert adapter._validate_ledger_rows(rows, max_retired_draws=2) is rows
    cases = (
        (list(rows), TypeError),
        (((0, 1, 2),), TypeError),
        (((1, 1, 2, 10),), ValueError),
        (((0, 1, 2, 10), (1, 3, 4, 10)), ValueError),
        (((0, True, 2, 10),), TypeError),
        (((0, 1 << 64, 2, 10),), ValueError),
        (rows, ValueError),
    )
    for value, error_type in cases:
        capacity = 1 if value is rows else 2
        with pytest.raises(error_type):
            adapter._validate_ledger_rows(value, max_retired_draws=capacity)

    bomb = _TouchBomb()
    with pytest.raises(TypeError):
        adapter._validate_ledger_rows(
            ((0, 1, 2, bomb),),
            max_retired_draws=1,
        )
    assert bomb.calls == 0


def test_source_ast_excludes_entropy_legacy_execution_and_unscoped_cp43_calls():
    source_path = Path(adapter.__file__)
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".")[0])
    assert imported_roots.isdisjoint({"random", "secrets", "numpy", "torch"})

    call_text = tuple(
        ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)
    )
    forbidden = (
        "os.urandom",
        "os.getrandom",
        "os.getentropy",
        "secrets.",
        "numpy.random",
        "np.random",
        "torch.random",
        "_CP27_ALLOCATE",
        "_CP44_EXECUTE",
        "_CP36_PREPARE",
        "_CP37_DECIDE",
    )
    assert all(fragment not in call for call in call_text for fragment in forbidden)

    marshal_calls = tuple(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and ast.unparse(node.func) == "_MARSHAL_DUMPS"
    )
    assert len(marshal_calls) == 1
    assert len(marshal_calls[0].args) == 2
    assert isinstance(marshal_calls[0].args[1], ast.Constant)
    assert marshal_calls[0].args[1].value == 2
    assert marshal_calls[0].keywords == []

    owner_class = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == OWNER_TYPE.__name__
    )
    scoped_calls = {
        "self._split_full_words",
        "self._join_full_words",
        "self._evaluate_and_apply",
    }
    callers = {}
    for node in owner_class.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        calls = {
            ast.unparse(child.func)
            for child in ast.walk(node)
            if isinstance(child, ast.Call)
        }
        used = calls & scoped_calls
        if used:
            callers[node.name] = used
    assert callers == {"execute": scoped_calls}


@pytest.fixture(scope="module")
def owner_evidence():
    source_support_owner = checkpoint46.source_support_owner.__wrapped__()
    source_model_owner = checkpoint46.CERTIFY(
        source_support_owner,
        source_model_policy=checkpoint46.POLICY,
        source_model_role_sha256=checkpoint46.ROLE,
    )

    provider_calls = []
    provider_failure = _ProviderFailure("provider refused this retired draw")
    provider_bomb = _TouchBomb()

    def full_words(count):
        boundary_words = (
            0,
            1,
            255,
            256,
            1 << 63,
            (1 << 64) - 1,
            0xAAAAAAAAAAAAAAAA,
            0x5555555555555555,
        )
        return tuple(
            boundary_words[index % len(boundary_words)] for index in range(count)
        )

    def provider(source_instance_sha256, draw_index, full_word_count):
        provider_calls.append((source_instance_sha256, draw_index, full_word_count))
        words = full_words(full_word_count)
        if draw_index == EXCEPTION_DRAW_INDEX:
            raise provider_failure
        if draw_index == MALFORMED_OUTER_DRAW_INDEX:
            return list(words)
        if draw_index == MALFORMED_ELEMENT_DRAW_INDEX:
            malformed = list(words)
            malformed[-1] = provider_bomb
            return tuple(malformed)
        return words

    before = _rng_snapshot()
    with _trace_operations() as certification_calls:
        owner = CERTIFY(
            source_model_owner,
            provider,
            source_instance_sha256=SOURCE_INSTANCE_SHA256,
            provider_role_sha256=PROVIDER_ROLE_SHA256,
            execution_policy=POLICY,
            execution_role_sha256=EXECUTION_ROLE_SHA256,
            max_retired_draws=MAX_RETIRED_DRAWS,
        )

    with _trace_operations() as valid_calls:
        first_result = owner.execute(101, 201, VALID_DRAW_INDEX)
    first_snapshot = owner.ledger_snapshot()

    with _trace_operations() as same_value_calls:
        same_value_result = owner.execute(102, 202, SAME_VALUE_DRAW_INDEX)

    before_duplicate_provider_calls = len(provider_calls)
    with _trace_operations() as duplicate_calls:
        with pytest.raises(ERROR_TYPE) as duplicate_info:
            owner.execute(999, 998, VALID_DRAW_INDEX)
    assert len(provider_calls) == before_duplicate_provider_calls

    with _trace_operations() as exception_calls:
        with pytest.raises(_ProviderFailure) as provider_info:
            owner.execute(103, 203, EXCEPTION_DRAW_INDEX)

    with _trace_operations() as malformed_outer_calls:
        with pytest.raises(TypeError) as malformed_outer_info:
            owner.execute(104, 204, MALFORMED_OUTER_DRAW_INDEX)

    with _trace_operations() as malformed_element_calls:
        with pytest.raises(TypeError) as malformed_element_info:
            owner.execute(105, 205, MALFORMED_ELEMENT_DRAW_INDEX)

    barrier = threading.Barrier(3)
    atomic_outcomes = []

    def reserve_same_draw():
        barrier.wait()
        try:
            ordinal = owner._reserve_draw(106, 206, ATOMIC_DRAW_INDEX)
        except Exception as error:  # exact type is asserted below
            atomic_outcomes.append(("error", error))
        else:
            atomic_outcomes.append(("reserved", ordinal))

    threads = tuple(threading.Thread(target=reserve_same_draw) for _ in range(2))
    for thread in threads:
        thread.start()
    barrier.wait()
    for thread in threads:
        thread.join(timeout=30)
        assert not thread.is_alive()

    with _trace_operations() as result_validation_calls:
        assert owner.validate_result(first_result) is first_result
        assert owner.validate_result(same_value_result) is same_value_result

    final_snapshot = owner.ledger_snapshot()
    with _trace_operations() as snapshot_validation_calls:
        assert owner.validate_ledger_snapshot(final_snapshot) is final_snapshot
    with pytest.raises(ValueError) as stale_snapshot_info:
        owner.validate_ledger_snapshot(first_snapshot)
    _assert_rng_unchanged(before)

    return {
        "source_support_owner": source_support_owner,
        "source_model_owner": source_model_owner,
        "owner": owner,
        "provider": provider,
        "provider_calls": provider_calls,
        "provider_failure": provider_failure,
        "provider_bomb": provider_bomb,
        "first_result": first_result,
        "same_value_result": same_value_result,
        "first_snapshot": first_snapshot,
        "final_snapshot": final_snapshot,
        "duplicate_error": duplicate_info.value,
        "provider_error": provider_info.value,
        "malformed_outer_error": malformed_outer_info.value,
        "malformed_element_error": malformed_element_info.value,
        "stale_snapshot_error": stale_snapshot_info.value,
        "atomic_outcomes": tuple(atomic_outcomes),
        "certification_calls": certification_calls,
        "valid_calls": valid_calls,
        "same_value_calls": same_value_calls,
        "duplicate_calls": duplicate_calls,
        "exception_calls": exception_calls,
        "malformed_outer_calls": malformed_outer_calls,
        "malformed_element_calls": malformed_element_calls,
        "result_validation_calls": result_validation_calls,
        "snapshot_validation_calls": snapshot_validation_calls,
    }


def test_owner_bound_certificate_ancestry_capacity_and_nonclaims(owner_evidence):
    evidence = owner_evidence
    owner = evidence["owner"]
    certificate = owner.certificate
    cp46 = evidence["source_model_owner"].certificate
    cp45 = evidence["source_support_owner"].certificate
    cp44 = cp45.checkpoint44_certificate
    cp43 = cp44.checkpoint43_certificate

    assert owner.source_model_owner is evidence["source_model_owner"]
    assert certificate.checkpoint46_certificate is cp46
    assert certificate.checkpoint46_certificate_sha256 == cp46.certificate_sha256
    assert certificate.checkpoint45_certificate_sha256 == cp45.certificate_sha256
    assert certificate.checkpoint44_certificate_sha256 == cp44.certificate_sha256
    assert certificate.checkpoint43_certificate_sha256 == cp43.certificate_sha256
    assert certificate.checkpoint46_owner_runtime_identity == id(
        evidence["source_model_owner"]
    )
    assert certificate.checkpoint45_owner_runtime_identity == id(
        evidence["source_support_owner"]
    )
    assert certificate.provider_callback_runtime_identity == id(evidence["provider"])
    assert certificate.source_instance_sha256 == SOURCE_INSTANCE_SHA256
    assert certificate.provider_role_sha256 == PROVIDER_ROLE_SHA256
    assert certificate.execution_role_sha256 == EXECUTION_ROLE_SHA256
    assert certificate.max_retired_draws == MAX_RETIRED_DRAWS
    assert certificate.raw_word_domain_size == (1 << 64)
    assert certificate.full_word_count == (
        certificate.proposal_word_count + certificate.decision_word_count
    )
    assert certificate.provider_return_interface_support_log2 == (
        64 * certificate.full_word_count
    )
    assert certificate.passed is True
    for name in adapter._CERTIFICATE_POSITIVE_FLAGS:
        assert getattr(certificate, name) is True
    for name in adapter._CERTIFICATE_NEGATIVE_FLAGS:
        assert getattr(certificate, name) is False


def test_certification_execution_and_validation_operation_counts_are_exact(
    owner_evidence,
):
    forbidden = (
        "cp27_allocate",
        "cp27_public_validate",
        "cp27_structural_validate",
        "cp36_preflight",
        "cp36_prepare",
        "cp37_decide",
        "cp44_execute",
    )
    certification = owner_evidence["certification_calls"]
    assert certification["cp46_live_revalidation"] == 1
    assert certification["cp46_cached_binding"] == 3
    for name in forbidden + (
        "cp43_split",
        "cp43_join",
        "cp43_combined",
        "cp43_g",
        "cp43_semantic_h",
        "cp43_structural_validate",
    ):
        assert certification[name] == 0

    for key in ("valid_calls", "same_value_calls"):
        calls = owner_evidence[key]
        for name in forbidden:
            assert calls[name] == 0
        assert calls["cp46_live_revalidation"] == 0
        assert calls["cp46_cached_binding"] == 6
        assert calls["cp43_split"] == 2
        assert calls["cp43_join"] == 1
        assert calls["cp43_combined"] == 1
        assert calls["cp43_g"] == 1
        assert calls["cp43_semantic_h"] == 1
        assert calls["cp43_structural_validate"] == 2

    for key in (
        "duplicate_calls",
        "exception_calls",
        "malformed_outer_calls",
        "malformed_element_calls",
    ):
        calls = owner_evidence[key]
        for name in forbidden + (
            "cp43_split",
            "cp43_join",
            "cp43_combined",
            "cp43_g",
            "cp43_semantic_h",
            "cp43_structural_validate",
            "cp46_live_revalidation",
        ):
            assert calls[name] == 0
        assert calls["cp46_cached_binding"] == 1

    validation = owner_evidence["result_validation_calls"]
    for name in forbidden + (
        "cp43_split",
        "cp43_join",
        "cp43_combined",
        "cp43_g",
        "cp43_semantic_h",
        "cp46_live_revalidation",
    ):
        assert validation[name] == 0
    assert validation["cp43_structural_validate"] == 2
    assert validation["cp46_cached_binding"] == 4
    assert owner_evidence["snapshot_validation_calls"]["cp46_cached_binding"] == 2
    assert all(
        count == 0
        for name, count in owner_evidence["snapshot_validation_calls"].items()
        if name != "cp46_cached_binding"
    )


def test_provider_receipts_retain_exact_words_and_equal_values_under_distinct_ids(
    owner_evidence,
):
    first = owner_evidence["first_result"]
    second = owner_evidence["same_value_result"]
    certificate = owner_evidence["owner"].certificate
    assert type(first) is type(second) is RESULT_TYPE
    assert type(first.provider_receipt) is RECEIPT_TYPE
    assert first.source_full_words is first.provider_receipt.returned_full_words
    assert second.source_full_words is second.provider_receipt.returned_full_words
    assert first.source_full_words == second.source_full_words
    assert first.draw_index == VALID_DRAW_INDEX
    assert second.draw_index == SAME_VALUE_DRAW_INDEX
    assert first.provider_receipt.receipt_sha256 != (
        second.provider_receipt.receipt_sha256
    )
    for result in (first, second):
        receipt = result.provider_receipt
        assert receipt.certificate is certificate
        assert receipt.owner_runtime_identity == id(owner_evidence["owner"])
        assert result.owner_runtime_identity == id(owner_evidence["owner"])
        assert result.retirement_chain_sha256 == receipt.retirement_chain_sha256
        assert receipt.requested_full_word_count == certificate.full_word_count
        assert receipt.provider_invocation_count == 1
        assert receipt.draw_retired_before_provider_invocation is True
        assert receipt.provider_return_type_exact_tuple is True
        assert receipt.provider_return_words_exact_uint64 is True
        assert receipt.direct_identity_ingestion is True
        assert receipt.provider_law_or_totality_certified is False
        assert receipt.cryptographic_attestation is False
        assert result.semantic_status in (
            "selected",
            "exhausted",
            "preparation_failure",
            "factorization_failure",
        )
        assert result.checkpoint43_combined_evaluated_once is True
        assert result.structural_validation_is_nonreplaying is True
        assert result.provider_law_or_iid_certified is False
        assert result.unconditional_returned_result_law_certified is False


def test_provider_failures_burn_draws_without_retry_and_ledger_is_atomic(
    owner_evidence,
):
    evidence = owner_evidence
    owner = evidence["owner"]
    full_word_count = owner.certificate.full_word_count
    expected_draws = (
        VALID_DRAW_INDEX,
        SAME_VALUE_DRAW_INDEX,
        EXCEPTION_DRAW_INDEX,
        MALFORMED_OUTER_DRAW_INDEX,
        MALFORMED_ELEMENT_DRAW_INDEX,
    )
    assert tuple(call[1] for call in evidence["provider_calls"]) == expected_draws
    assert all(
        call == (SOURCE_INSTANCE_SHA256, draw, full_word_count)
        for call, draw in zip(evidence["provider_calls"], expected_draws)
    )
    assert evidence["provider_error"] is evidence["provider_failure"]
    assert type(evidence["malformed_outer_error"]) is TypeError
    assert type(evidence["malformed_element_error"]) is TypeError
    assert type(evidence["duplicate_error"]) is ERROR_TYPE
    assert evidence["provider_bomb"].calls == 0

    outcomes = evidence["atomic_outcomes"]
    assert len(outcomes) == 2
    reserved = tuple(value for status, value in outcomes if status == "reserved")
    refused = tuple(value for status, value in outcomes if status == "error")
    assert reserved == (5,)
    assert len(refused) == 1 and type(refused[0]) is ERROR_TYPE

    first = evidence["first_snapshot"]
    final = evidence["final_snapshot"]
    assert type(first) is type(final) is SNAPSHOT_TYPE
    assert first.retired_draw_rows == ((0, 101, 201, VALID_DRAW_INDEX),)
    assert final.retired_draw_count == 6
    assert final.retired_draw_rows == (
        (0, 101, 201, VALID_DRAW_INDEX),
        (1, 102, 202, SAME_VALUE_DRAW_INDEX),
        (2, 103, 203, EXCEPTION_DRAW_INDEX),
        (3, 104, 204, MALFORMED_OUTER_DRAW_INDEX),
        (4, 105, 205, MALFORMED_ELEMENT_DRAW_INDEX),
        (5, 106, 206, ATOMIC_DRAW_INDEX),
    )
    assert final.owner_runtime_identity == id(owner)
    assert type(owner._retired_draw_state) is tuple
    assert all(type(part) is tuple for part in owner._retired_draw_state)
    assert len(final.retirement_chain_sha256s) == final.retired_draw_count
    assert final.retirement_chain_head_sha256 == final.retirement_chain_sha256s[-1]
    assert first.retirement_chain_sha256s == (
        owner_evidence["first_result"].retirement_chain_sha256,
    )
    assert final.current_owner_comparison_required is True
    assert type(evidence["stale_snapshot_error"]) is ValueError


def test_records_owner_and_constructors_are_sealed_nonpickleable(owner_evidence):
    evidence = owner_evidence
    owner = evidence["owner"]
    records = (
        owner.certificate,
        evidence["first_result"].provider_receipt,
        evidence["first_result"],
        evidence["final_snapshot"],
    )
    for record in records:
        field = next(iter(type(record).__annotations__))
        with pytest.raises((AttributeError, TypeError)):
            setattr(record, field, getattr(record, field))
        with pytest.raises(TypeError):
            pickle.dumps(record)
        with pytest.raises(TypeError):
            type(record)(
                _construction_token=object(),
                **{
                    name: getattr(record, name) for name in type(record).__annotations__
                },
            )
        with pytest.raises(TypeError):
            type("ForbiddenSubclass", (type(record),), {})

    with pytest.raises(AttributeError):
        owner._certificate = owner.certificate
    with pytest.raises(TypeError):
        pickle.dumps(owner)
    with pytest.raises(TypeError):
        type("ForbiddenOwnerSubclass", (type(owner),), {})
    with pytest.raises(TypeError):
        OWNER_TYPE(None, None, None, None, _construction_token=object())


def test_hostile_scalar_inputs_refuse_before_provider_parent_or_ledger(
    owner_evidence,
):
    owner = owner_evidence["owner"]
    provider_count = len(owner_evidence["provider_calls"])
    ledger_rows = owner_evidence["final_snapshot"].retired_draw_rows
    cases = (
        ((_TouchBomb(), 0, 20), TypeError),
        ((0, _TouchBomb(), 21), TypeError),
        ((0, 0, _TouchBomb()), TypeError),
        ((True, 0, 22), TypeError),
        ((np.int64(0), 0, 23), TypeError),
        ((-1, 0, 24), ValueError),
        (((1 << 64), 0, 25), ValueError),
    )
    for arguments, error_type in cases:
        bombs = tuple(value for value in arguments if isinstance(value, _TouchBomb))
        with _trace_operations() as calls:
            with pytest.raises(error_type):
                owner.execute(*arguments)
        assert all(bomb.calls == 0 for bomb in bombs)
        assert all(count == 0 for count in calls.values())
    assert len(owner_evidence["provider_calls"]) == provider_count
    assert owner.ledger_snapshot().retired_draw_rows == ledger_rows


def test_plain_redigested_digest_only_and_hostile_tampering_refuses(
    owner_evidence,
):
    owner = owner_evidence["owner"]
    result = owner_evidence["first_result"]
    receipt = result.provider_receipt
    snapshot = owner_evidence["final_snapshot"]
    certificate = owner.certificate

    promoted_result = _forged(result, provider_law_or_iid_certified=True)
    with pytest.raises(ValueError):
        owner.validate_result(promoted_result)
    promoted_values = {
        name: getattr(promoted_result, name)
        for name in type(promoted_result).__annotations__
    }
    redigested_result = _forged(
        promoted_result,
        result_sha256=adapter._semantic_digest(
            adapter._result_payload(promoted_values)
        ),
    )
    with pytest.raises(ValueError):
        owner.validate_result(redigested_result)
    with pytest.raises(ValueError):
        owner.validate_result(_forged(result, result_sha256="f" * 64))

    bool_ordinal_result = _forged(result, retirement_ordinal=False)
    bool_result_values = {
        name: getattr(bool_ordinal_result, name)
        for name in type(bool_ordinal_result).__annotations__
    }
    bool_ordinal_result = _forged(
        bool_ordinal_result,
        result_sha256=adapter._semantic_digest(
            adapter._result_payload(bool_result_values)
        ),
    )
    with pytest.raises((TypeError, ValueError)):
        owner.validate_result(bool_ordinal_result)

    promoted_receipt = _forged(receipt, direct_identity_ingestion=False)
    receipt_values = {
        name: getattr(promoted_receipt, name)
        for name in type(promoted_receipt).__annotations__
    }
    redigested_receipt = _forged(
        promoted_receipt,
        receipt_sha256=adapter._semantic_digest(
            adapter._receipt_payload(receipt_values)
        ),
    )
    with pytest.raises(ValueError):
        adapter._validate_receipt_record(
            redigested_receipt,
            trusted_certificate=certificate,
        )

    bool_ordinal_receipt = _forged(receipt, retirement_ordinal=False)
    bool_receipt_values = {
        name: getattr(bool_ordinal_receipt, name)
        for name in type(bool_ordinal_receipt).__annotations__
    }
    bool_ordinal_receipt = _forged(
        bool_ordinal_receipt,
        receipt_sha256=adapter._semantic_digest(
            adapter._receipt_payload(bool_receipt_values)
        ),
    )
    with pytest.raises((TypeError, ValueError)):
        adapter._validate_receipt_record(
            bool_ordinal_receipt,
            trusted_certificate=certificate,
        )

    promoted_snapshot = _forged(
        snapshot,
        current_owner_comparison_required=False,
    )
    snapshot_values = {
        name: getattr(promoted_snapshot, name)
        for name in type(promoted_snapshot).__annotations__
    }
    redigested_snapshot = _forged(
        promoted_snapshot,
        snapshot_sha256=adapter._semantic_digest(
            adapter._ledger_snapshot_payload(snapshot_values)
        ),
    )
    with pytest.raises(ValueError):
        owner.validate_ledger_snapshot(redigested_snapshot)
    with pytest.raises(ValueError):
        owner.validate_ledger_snapshot(_forged(snapshot, snapshot_sha256="e" * 64))

    promoted_certificate = _forged(certificate, scientific_claim_promoted=True)
    certificate_values = {
        name: getattr(promoted_certificate, name)
        for name in type(promoted_certificate).__annotations__
    }
    redigested_certificate = _forged(
        promoted_certificate,
        certificate_sha256=adapter._semantic_digest(
            adapter._certificate_payload(certificate_values)
        ),
    )
    with pytest.raises(ValueError):
        adapter._validate_certificate(redigested_certificate)
    with pytest.raises(ValueError):
        adapter._validate_certificate(_forged(certificate, certificate_sha256="d" * 64))

    bomb = _TouchBomb()
    hostile = _forged(result, provider_law_or_iid_certified=bomb)
    with pytest.raises(TypeError):
        adapter._validate_result_record(
            hostile,
            trusted_certificate=certificate,
        )
    assert bomb.calls == 0


def test_cross_owner_result_and_ledger_splicing_refuses_without_replay(
    owner_evidence,
):
    evidence = owner_evidence
    owner = evidence["owner"]
    ancestry = adapter._bound_cached_ancestry(evidence["source_model_owner"])
    other = OWNER_TYPE(
        evidence["source_model_owner"],
        evidence["provider"],
        owner.certificate,
        ancestry,
        _construction_token=adapter._OWNER_TOKEN,
    )
    assert other is not owner
    assert other._reserve_draw(101, 201, VALID_DRAW_INDEX) == 0
    other_snapshot = other.ledger_snapshot()
    assert other_snapshot.retired_draw_rows == ((0, 101, 201, VALID_DRAW_INDEX),)
    assert other_snapshot.retirement_chain_sha256s != (
        evidence["first_snapshot"].retirement_chain_sha256s
    )
    provider_count = len(evidence["provider_calls"])
    with _trace_operations() as result_calls:
        with pytest.raises(ValueError):
            other.validate_result(evidence["first_result"])
    with _trace_operations() as snapshot_calls:
        with pytest.raises(ValueError):
            other.validate_ledger_snapshot(evidence["final_snapshot"])
    with pytest.raises(ValueError):
        owner.validate_ledger_snapshot(other_snapshot)
    assert len(evidence["provider_calls"]) == provider_count
    for calls in (result_calls, snapshot_calls):
        assert calls["cp27_allocate"] == 0
        assert calls["cp44_execute"] == 0
        assert calls["cp43_combined"] == 0
        assert calls["cp43_g"] == 0
        assert calls["cp43_semantic_h"] == 0
        assert calls["cp46_live_revalidation"] == 0


def test_provider_local_cp46_and_cp43_drift_refuse_before_provider(
    owner_evidence,
    monkeypatch,
):
    evidence = owner_evidence
    owner = evidence["owner"]
    provider_count = len(evidence["provider_calls"])
    ledger_rows = owner.ledger_snapshot().retired_draw_rows
    replacement_calls = []

    def replacement(*args, **kwargs):
        replacement_calls.append((args, kwargs))
        raise AssertionError("drift replacement executed")

    drift_cases = (
        (adapter, "_semantic_digest"),
        (adapter, "_validate_result_values"),
        (adapter, "_LOCK_FACTORY"),
        (adapter._contract, "_validate_certificate"),
        (adapter._CP43_OWNER_TYPE, "split_full_words"),
    )
    for offset, (namespace, name) in enumerate(drift_cases):
        with monkeypatch.context() as patcher:
            patcher.setattr(namespace, name, replacement)
            with _trace_operations() as calls:
                with pytest.raises(ValueError):
                    owner.execute(301, 401, 50 + offset)
        assert calls["cp27_allocate"] == 0
        assert calls["cp44_execute"] == 0
        assert calls["cp43_combined"] == 0
        assert calls["cp43_g"] == 0
        assert calls["cp43_semantic_h"] == 0

    original_provider = owner._full_capsule_provider
    object.__setattr__(owner, "_full_capsule_provider", replacement)
    try:
        with _trace_operations() as provider_drift_calls:
            with pytest.raises(ValueError):
                owner.execute(304, 404, 53)
    finally:
        object.__setattr__(owner, "_full_capsule_provider", original_provider)
    assert provider_drift_calls["cp43_combined"] == 0
    assert provider_drift_calls["cp43_g"] == 0
    assert provider_drift_calls["cp43_semantic_h"] == 0
    assert replacement_calls == []
    assert len(evidence["provider_calls"]) == provider_count
    assert owner.ledger_snapshot().retired_draw_rows == ledger_rows
