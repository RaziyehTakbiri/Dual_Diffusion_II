"""Independent hostile tests for the CP61 whole-seed MC design precursor."""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, make_dataclass
from fractions import Fraction
import hashlib
import inspect
import json
from math import comb
from pathlib import Path
import pickle
import subprocess
import sys

import pytest

from heterodiff.evaluation import (
    mixed_initializer_test28_bounded_sir_diagnostics as diagnostics,
)
from heterodiff.evaluation import (
    mixed_initializer_test28_uniform_seed_pushforward as pushforward,
)
from heterodiff.evaluation import (
    mixed_initializer_test28_whole_seed_mc_design as design,
)


_ZERO_SHA256 = "0" * 64
_N = 2_048
_K_MIN = 1_040
_TAIL = Fraction(1, 110_800)
_FAMILY_ALPHA = Fraction(1, 100)
_FIXTURES = ("T28-M1-Q", "T28-M2-Q")
_REJECTION_BUDGETS = (1, 4, 16, 64)
_SIR_BUDGETS = (8, 32, 128, 512)
_REJECTION_CELLS = (
    "returned-rejection-selected-before-deadline",
    "returned-rejection-exhausted-before-deadline",
    "preexecution-refusal-before-deadline",
    "execution-failure-before-deadline",
    "timeout-censored-at-deadline",
)
_SIR_CELLS = (
    "returned-sir-selected-before-deadline",
    "preexecution-refusal-before-deadline",
    "execution-failure-before-deadline",
    "timeout-censored-at-deadline",
)
_COMPACT_ESTIMAND_SEMANTICS = (
    "fixture-id-strategy-budget-row-key",
    "deadline-scoped-observable-cell-tag-with-timeout-at-deadline",
    "optional-one-based-rejection-first-attempt",
    "optional-cp58-feature-id-bounds-and-exact-selected-feature-value",
)
_INCLUDED_STABLE_TRACE_SEMANTICS = (
    "stable-request-digest-and-fixture-strategy-budget-plan-seed",
    "stable-local-source-and-facade-provider-certificate-digests",
    "reference-and-source-parameter-digests",
    "role-context-and-stable-runtime-record",
    "derived-role-seeds-and-rng-state-hashes",
    "canonical-configuration-values-with-binary64-bytes",
    "independently-recomputed-provider-and-configuration-digests",
    "exact-q-delta-quota-certificate-decision-word-and-acceptance-records",
    (
        "every-rejection-attempt-slot-or-complete-sir-cloud-score-weight-bytes-"
        "ess-and-resampling-record"
    ),
    "closed-outcome-status-and-failure-code",
)
_EXCLUDED_VOLATILE_TRACE_CUSTODY = (
    "raw-runtime-identity-and-object-identity-fields",
    "address-bearing-representations-and-unbounded-exception-text",
    "plan-sha256",
    "kernel-owner-and-execution-certificate-sha256",
    (
        "nested-scored-attempt-particle-and-result-hashes-that-inherit-runtime-"
        "identity"
    ),
)

# These predecessor identities and this order are hard-coded evidence, not
# reconstructed by calling CP60's private row builder.
_ROWS = (
    (
        "T28-M1-Q",
        "bounded-rejection",
        1,
        "d76e7f25460b8a38d00f32542422d864fcef9c7740b9af6d4c7d62b9fdfcee7a",
        "d4d930b46ab39a0f8a0f9cb2e65a896d3361876969fb783456ceee6e2f4d9160",
    ),
    (
        "T28-M1-Q",
        "bounded-rejection",
        4,
        "00659ec7b82ffee45bd0d0acf68c60329f427a2ec2e7904694d5ef5a5e386080",
        "8366db2154dd8e56577653a8c7bf27067bd190bd76d205daab422c55396bb6f8",
    ),
    (
        "T28-M1-Q",
        "bounded-rejection",
        16,
        "3b511499c530c8f2b9cee6886a28fb9f4db3d40d43d348b7c12c9a002a713fae",
        "deff18f198aacc3e70711d6b0f747be62686f181030b47e87beec301554ff782",
    ),
    (
        "T28-M1-Q",
        "bounded-rejection",
        64,
        "03bd3438cb844ae19416431f39a6ed61b3cfd22c2593dee80acdaf42f55cac21",
        "ce302962eda91df8d8af1b775de48b8fc83ed06b390fd4061e23e309fa553f38",
    ),
    (
        "T28-M1-Q",
        "fixed-budget-sir",
        8,
        "221d4dd57aba464cce571de0005794094105bc928742745f25fc8371a9bbfeaa",
        "dfbc72991541d23f3cdeeecb3ddba460c839967676ffdc1d3cc92e3a8a57ebc5",
    ),
    (
        "T28-M1-Q",
        "fixed-budget-sir",
        32,
        "43a4ab7b219a2e1f313e7c8d04133fbace6ca9e7b85298d94dc9d2a725114276",
        "7fd96a443a40de0631f785a7b0d2c00611fbe5359185f81164af8e0530b758a3",
    ),
    (
        "T28-M1-Q",
        "fixed-budget-sir",
        128,
        "2880c960e3cb04378b0e841011e642772c11770fd20e9f59adadd3e69fc04545",
        "164690f7b8693f50892be435fd2b7e8c28ba8927209da5c39429469f2e9261f0",
    ),
    (
        "T28-M1-Q",
        "fixed-budget-sir",
        512,
        "2471f1816d0f976cdc1d267d58794a07dd6279192fa911e4d2ad265b9b2a4abf",
        "b840599e28a1cb4a3197e503e4fe694860eb783ee66a6440d81fa6a1571c6c8b",
    ),
    (
        "T28-M2-Q",
        "bounded-rejection",
        1,
        "4b4f42597f351c3e1f90ee9c333a84d3c1a489e9b3d478223cec50a43e9cb947",
        "2ed1233312fde9a35d4dfa88e8bcd7ba654fec4a06e78b7e7222312a372a8a79",
    ),
    (
        "T28-M2-Q",
        "bounded-rejection",
        4,
        "399f23bb850b1b450780b74a1101713fab31d3d8add9476b473f8c201da110e3",
        "fbc8ec85b991e495e8666c3d0a54a60e33195493d7b2365be3f58c627239f775",
    ),
    (
        "T28-M2-Q",
        "bounded-rejection",
        16,
        "0dfff79a87e0f5598f3cadc434df5cad08c8cc05272b9704daae53ea2d614b06",
        "8696cfe0a24c82af274f98adc3a6fe8ca270123f7f50f0d9595beea1cf3e0cc4",
    ),
    (
        "T28-M2-Q",
        "bounded-rejection",
        64,
        "108d3e94ae4007708687b810a2719b52f64d0048ba95c3448d64a89132d6ace8",
        "6cacbb2fddcc91ddd24a0a3eac3e5a1173fabc017e1d100babe82bf6a0efa14d",
    ),
    (
        "T28-M2-Q",
        "fixed-budget-sir",
        8,
        "2bace4f2262efd5f1e93d974fc0d1f884d9f62a4ac4343ce98f4c9ece15028e7",
        "1eb5454bbcfde0274deec91030e22ddecb4ab7eeda164a10eac4547a8259a407",
    ),
    (
        "T28-M2-Q",
        "fixed-budget-sir",
        32,
        "52fc434f07d1b3e1547d4564522328bfa414b23bb2ce34723c6174d6eca458ba",
        "4e1e978e901ef11d644c70a337990f556d0bc7f1251a8ddd27d0069438ff1dc5",
    ),
    (
        "T28-M2-Q",
        "fixed-budget-sir",
        128,
        "68b96d706e0f6cfa54358481a8633fa60910eee3d74b4327def13a5bddd1ab8c",
        "0d699f76655f5558788872324adff18ca347a7392428f7a342396176c16ceec2",
    ),
    (
        "T28-M2-Q",
        "fixed-budget-sir",
        512,
        "366a20c37e4ed8394eaa5699d2942168a7ff2f01d385933d50785fbf33e76960",
        "22027ae08c0a673cba4866656d868102eafc6b336d57225028dfe96bf65fa71b",
    ),
)

_REGISTRY_SHA256S = {
    "T28-M1-Q": "314a54638d17f8dcb4b4313a92594306643254ab4a958aeb9d81efd5786a0406",
    "T28-M2-Q": "e740e5927d2242aa0d945f4a252a638cae6aa4757f31ed24094c188b715929e8",
}

_M1_FEATURES = (
    (
        "count/eq/0",
        0,
        1,
        "d8cf3abf8acca4e87a529d00a7e7f0206a886997e83747f050eff27895f477ee",
    ),
    (
        "count/eq/1",
        0,
        1,
        "e0e0c87cb30db0f7771729f898cc5228f74e509e62c2c7b7131aaf973ec08cd1",
    ),
    (
        "type/0/occupancy",
        0,
        1,
        "172ac2a5e625b63a27ced9520b4f874debba34884efd08d62056f1de1fa0a278",
    ),
    (
        "type/1/occupancy",
        0,
        1,
        "aa8e57660f7f6cc844b1262da44662af31fd4c575eb931dcda429c095af8ebfa",
    ),
    (
        "coordinate/1/axis0/odd",
        -1,
        1,
        "af78aeefacaeb384bfae608451801508b501519ee582212003a080dba67e2a97",
    ),
    (
        "coordinate/1/axis0/even",
        0,
        1,
        "fbb627761ad4e54089e9524df715e8f83b369b17584f62d63e5004c71309512b",
    ),
)

_M2_FEATURES = (
    (
        "count/eq/0",
        0,
        1,
        "d8cf3abf8acca4e87a529d00a7e7f0206a886997e83747f050eff27895f477ee",
    ),
    (
        "count/eq/1",
        0,
        1,
        "e0e0c87cb30db0f7771729f898cc5228f74e509e62c2c7b7131aaf973ec08cd1",
    ),
    (
        "count/eq/2",
        0,
        1,
        "b046d5d71e9030561355e018c27ebef1edcb3690c58ac4fbdfc9f4361bcde6db",
    ),
    (
        "type/0/occupancy",
        0,
        1,
        "db712cf53aaa76e27207b7afcfc9d3c9585d101df47d2bb6b6a08318fc66cad4",
    ),
    (
        "type/1/occupancy",
        0,
        1,
        "2fa01655462716d00b426334c8008a1673569d7b1d39838b69e3f468d9c472be",
    ),
    (
        "coordinate/0/axis0/odd",
        -1,
        1,
        "58e97de0d09a09d30226fc357b8360acdca0b8e45fd509b9df026648cf802dff",
    ),
    (
        "coordinate/0/axis0/even",
        0,
        1,
        "d83044e7f204fd1d49b9136200e959620ff28fb817608d79d1414d9cd9a1a804",
    ),
    (
        "coordinate/1/axis0/odd",
        -1,
        1,
        "a256acde4b5c41c7fed3db1180334208d75445c0fad119fa0698095940d77dfc",
    ),
    (
        "coordinate/1/axis0/even",
        0,
        1,
        "769607220a694e2c64bdc2df72ca44cc92eb7d291c71aee98149cb68679c39d8",
    ),
    (
        "coordinate/1/axis1/odd",
        -1,
        1,
        "05b702adf96247be101d1a94b6a63ce2c996e070bf1b63ddeb9991251f3f88e6",
    ),
    (
        "coordinate/1/axis1/even",
        0,
        1,
        "22c2b2232df21c580d15c085257bbf62693f449841c6ae359a8d6649d5ac2650",
    ),
    (
        "coordinate/1/diag-plus-3-4/odd",
        -1,
        1,
        "106f66b3bfe087dc187b7802b6a149e337cc3bc092a132389b22cb7e8239f76b",
    ),
    (
        "coordinate/1/diag-plus-3-4/even",
        0,
        1,
        "864d0faf9cec2e271a88bba8a476a722ef588082f6040830c040445afb71ee70",
    ),
    (
        "coordinate/1/diag-minus-3-4/odd",
        -1,
        1,
        "c3247f44fbfdbc2fc393d5836dc6dd5b6b6bc548c4f547f4122c1077bb5dfb47",
    ),
    (
        "coordinate/1/diag-minus-3-4/even",
        0,
        1,
        "c863829293cadabbf587ba4b34b630577d87017cb6372514cc61c694ea08f919",
    ),
    (
        "pair-type/0/0",
        0,
        1,
        "56b3362c2089a99d614cb479156f02e981fab3430d4eca47ac4f75a01d5983c4",
    ),
    (
        "pair-type/0/1",
        0,
        1,
        "44db786ec46e260b5e55a96f6fa0f01bbe5e9b59a731dd1a30a282c76e2203ce",
    ),
    (
        "pair-type/1/1",
        0,
        1,
        "e01a3e398714b6f372fabc9ea4faf24e09310799bc2c93b33f80cf31664d9627",
    ),
    (
        "pair-projection/0/axis0/0/axis0",
        -1,
        1,
        "269c4b95ae31a0ad72fbcf800817b0b6955c70a07f03951219bc600e621fd4f3",
    ),
    (
        "pair-projection/0/axis0/1/axis0",
        -1,
        1,
        "f08256103f5b6a6b80dbb9fa1630feca319c9f71b53379164d77eee18195a95c",
    ),
    (
        "pair-projection/0/axis0/1/axis1",
        -1,
        1,
        "7b2a560e03401377795c6f6ccd2410807f4fa0e3db7f1ce2c701f429892e931e",
    ),
    (
        "pair-projection/0/axis0/1/diag-plus-3-4",
        -1,
        1,
        "f17da42bb42b577b42c6de7766997ea9c39d95abfffc1ae3a0b1f3b01b6598a6",
    ),
    (
        "pair-projection/0/axis0/1/diag-minus-3-4",
        -1,
        1,
        "7c668ef4cd806de6b05cc8435b89a181499f8d8f44a4100798bccb01e1e47e10",
    ),
    (
        "pair-projection/1/axis0/1/axis0",
        -1,
        1,
        "f2e1968a50c59acac378885c6a9c4a631def23b6bf63d4ad74cb763e87d5a768",
    ),
    (
        "pair-projection/1/axis0/1/axis1",
        -1,
        1,
        "cad9200a6a7cfbca3a79167800baf4b8889be18345944916397477df34540968",
    ),
    (
        "pair-projection/1/axis0/1/diag-plus-3-4",
        -1,
        1,
        "7cd22043bab94a2950c12b229a72eae6037795779dde3cce293359a8d29c0b37",
    ),
    (
        "pair-projection/1/axis0/1/diag-minus-3-4",
        -1,
        1,
        "dae15c9acf9fe1ac5cbaff0d18f1655c915d226b590f01930fcca4edbd7ceb9c",
    ),
    (
        "pair-projection/1/axis1/1/axis1",
        -1,
        1,
        "5d3169678ee34228d3a126e8e55b3f6399fb99ebb45395e0663d218a95b0fd1d",
    ),
    (
        "pair-projection/1/axis1/1/diag-plus-3-4",
        -1,
        1,
        "9ecb7afe46ce2aad182ea4b9f05497796f5775f6507996505c449b70ec817cae",
    ),
    (
        "pair-projection/1/axis1/1/diag-minus-3-4",
        -1,
        1,
        "e15ed152b3890021c8815a1f34e68f0e7a949b75a1386d6b4b9382308974118c",
    ),
    (
        "pair-projection/1/diag-plus-3-4/1/diag-plus-3-4",
        -1,
        1,
        "1b506871d99566c407e0d458a6fe49562b3279a85e10d4f94a325b0b80d2d110",
    ),
    (
        "pair-projection/1/diag-plus-3-4/1/diag-minus-3-4",
        -1,
        1,
        "1bdb07bf4f34c90d966ef99ca0936e49e3c072e6e86bbcf200800223bb8cb765",
    ),
    (
        "pair-projection/1/diag-minus-3-4/1/diag-minus-3-4",
        -1,
        1,
        "61a7a2ea814b8a9c7539f153bed878f78d22846f81a25ce7df3776c7c455464e",
    ),
)


class _IntSubclass(int):
    pass


class _StrSubclass(str):
    pass


class _TupleSubclass(tuple):
    pass


class _ProtocolBomb:
    def __len__(self):
        raise AssertionError("hostile __len__ was invoked")

    def __iter__(self):
        raise AssertionError("hostile __iter__ was invoked")

    def __eq__(self, other):
        del other
        raise AssertionError("hostile __eq__ was invoked")


def _forge(instance, **changes):
    names = {item.name for item in fields(type(instance))}
    assert set(changes) <= names
    forged = object.__new__(type(instance))
    for item in fields(type(instance)):
        object.__setattr__(
            forged, item.name, changes.get(item.name, getattr(instance, item.name))
        )
    return forged


def _all_estimands(bundle) -> tuple:
    return (
        bundle.observable_estimands
        + bundle.rejection_first_attempt_estimands
        + bundle.selected_conditional_feature_estimands
    )


def _independent_canonical(value):
    record_tags = {
        design.CP61StableTraceProjectionContractV1: (
            "stable-trace-projection-contract-v1"
        ),
        design.CP61MCRowDesignV1: "mc-row-design-v1",
        design.CP61EstimandV1: "estimand-v1",
        design.CP61MultiplicityAndPrecisionV1: "multiplicity-and-precision-v1",
        design.CP61ResourceBudgetV1: "resource-budget-v1",
        design.CP61WholeSeedMCDesignBundleV1: "whole-seed-mc-design-bundle-v1",
    }
    if value is None or type(value) is bool or type(value) is str:
        return value
    if type(value) is int:
        return {
            "cp61_exact_integer_hex": ("-" if value < 0 else "+")
            + format(abs(value), "x")
        }
    if type(value) is Fraction:
        return {
            "cp61_exact_fraction_v1": {
                "numerator": _independent_canonical(value.numerator),
                "denominator": _independent_canonical(value.denominator),
            }
        }
    if type(value) is tuple:
        return [_independent_canonical(item) for item in value]
    if type(value) is dict:
        assert all(type(key) is str for key in value)
        return {key: _independent_canonical(value[key]) for key in sorted(value)}
    if type(value) in record_tags:
        return {
            "cp61_record_type": record_tags[type(value)],
            "fields": {
                item.name: _independent_canonical(getattr(value, item.name))
                for item in fields(type(value))
            },
        }
    raise TypeError("unsupported independent CP61 canonical value")


def _independent_canonical_bytes(value) -> bytes:
    return json.dumps(
        _independent_canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")


def _independent_digest(kind: str, payload: dict) -> str:
    payload = dict(payload)
    if "record_sha256" in payload:
        payload["record_sha256"] = _ZERO_SHA256
    return hashlib.sha256(
        b"cp61-test28-whole-seed-mc-design-v1\x00"
        + kind.encode("ascii")
        + b"\x00"
        + _independent_canonical_bytes(payload)
    ).hexdigest()


def _independent_record_digest(value, kind: str) -> str:
    return _independent_digest(
        kind,
        {item.name: getattr(value, item.name) for item in fields(type(value))},
    )


def _redigest(value, kind: str):
    return _forge(value, record_sha256=_independent_record_digest(value, kind))


def _binomial_cdf(n: int, x: int, p: Fraction) -> Fraction:
    """Independent exact binomial lower tail for small hostile calibrations."""

    assert 0 <= x <= n and 0 <= p <= 1
    return sum(
        (Fraction(comb(n, k)) * p**k * (1 - p) ** (n - k) for k in range(x + 1)),
        Fraction(0),
    )


def _feature_triples(registry):
    return tuple(
        (
            feature.feature_id,
            int(feature.lower_bound),
            int(feature.upper_bound),
            feature.record_sha256,
        )
        for feature in registry.features
    )


def _row_key(row_ordinal: int, row: tuple) -> str:
    fixture_id, strategy, budget = row[:3]
    return "row-%02d/%s/%s/budget-%d" % (
        row_ordinal,
        fixture_id,
        strategy,
        budget,
    )


def _expected_estimand_ids() -> tuple:
    observable = []
    first = []
    selected_features = []
    for row_ordinal, row in enumerate(_ROWS, 1):
        fixture_id, strategy, budget = row[:3]
        row_key = _row_key(row_ordinal, row)
        cells = _REJECTION_CELLS if strategy == "bounded-rejection" else _SIR_CELLS
        observable.extend("cp61/observable/%s/%s" % (row_key, cell) for cell in cells)
        if strategy == "bounded-rejection":
            first.extend(
                "cp61/rejection-first-attempt/%s/attempt-%d" % (row_key, attempt)
                for attempt in range(1, budget + 1)
            )
        features = _M1_FEATURES if fixture_id == "T28-M1-Q" else _M2_FEATURES
        selected_features.extend(
            "cp61/selected-feature/%s/%s" % (row_key, feature[0])
            for feature in features
        )
    return tuple(observable), tuple(first), tuple(selected_features)


def test_independent_row_order_and_cp60_predecessor_hashes_are_exact() -> None:
    bundle = pushforward.cp60_whole_seed_pushforward_bundle()
    observed = tuple(
        (
            row.fixture_id,
            row.strategy,
            row.budget,
            row.request_template_sha256,
            row.record_sha256,
        )
        for row in bundle.ordered_definitions
    )
    assert observed == _ROWS
    assert len(observed) == len(set(item[:3] for item in observed)) == 16


def test_independent_cp58_feature_registry_ids_ranges_and_digests() -> None:
    expected = {"T28-M1-Q": _M1_FEATURES, "T28-M2-Q": _M2_FEATURES}
    for fixture_id in _FIXTURES:
        registry = diagnostics.cp58_feature_registry(fixture_id)
        assert registry.record_sha256 == _REGISTRY_SHA256S[fixture_id]
        assert _feature_triples(registry) == expected[fixture_id]
        assert len(registry.features) == (6 if fixture_id == "T28-M1-Q" else 33)
        assert all(
            feature.upper_bound - feature.lower_bound in (1, 2)
            for feature in registry.features
        )


def test_independent_554_object_family_rederivation() -> None:
    rejection_rows = len(_FIXTURES) * len(_REJECTION_BUDGETS)
    sir_rows = len(_FIXTURES) * len(_SIR_BUDGETS)
    observable_cells = rejection_rows * 5 + sir_rows * 4
    first_index_cells = len(_FIXTURES) * sum(_REJECTION_BUDGETS)
    selected_features = 8 * len(_M1_FEATURES) + 8 * len(_M2_FEATURES)
    assert (observable_cells, first_index_cells, selected_features) == (72, 170, 312)
    assert observable_cells + first_index_cells + selected_features == 554


def test_bundle_rows_and_all_row_link_ordinal_slices_are_exact() -> None:
    bundle = design.cp61_whole_seed_mc_design_bundle()
    assert type(bundle.ordered_rows) is tuple
    assert len(bundle.ordered_rows) == 16

    observable_cursor = 1
    first_attempt_cursor = 73
    feature_cursor = 243
    projection_sha256 = bundle.stable_trace_projection_contract.record_sha256
    for row_ordinal, (row, expected) in enumerate(zip(bundle.ordered_rows, _ROWS), 1):
        fixture_id, strategy, budget, request_sha256, definition_sha256 = expected
        cells = (
            design.CP61_TEST28_REJECTION_OBSERVABLE_CELLS
            if strategy == "bounded-rejection"
            else design.CP61_TEST28_SIR_OBSERVABLE_CELLS
        )
        features = _M1_FEATURES if fixture_id == "T28-M1-Q" else _M2_FEATURES
        observable_ordinals = tuple(
            range(observable_cursor, observable_cursor + len(cells))
        )
        first_attempt_count = budget if strategy == "bounded-rejection" else 0
        first_attempt_ordinals = tuple(
            range(first_attempt_cursor, first_attempt_cursor + first_attempt_count)
        )
        feature_ordinals = tuple(range(feature_cursor, feature_cursor + len(features)))

        assert type(row) is design.CP61MCRowDesignV1
        assert (
            row.row_ordinal,
            row.fixture_id,
            row.strategy,
            row.budget,
            row.cp60_request_template_sha256,
            row.cp60_definition_record_sha256,
        ) == (
            row_ordinal,
            fixture_id,
            strategy,
            budget,
            request_sha256,
            definition_sha256,
        )
        assert row.cp60_bundle_sha256 == design.CP61_TEST28_CP60_BUNDLE_SHA256
        assert row.cp58_feature_registry_sha256 == _REGISTRY_SHA256S[fixture_id]
        assert row.stable_trace_projection_contract_sha256 == projection_sha256
        assert row.observable_cell_labels == cells
        assert row.observable_estimand_ordinals == observable_ordinals
        assert row.first_attempt_estimand_ordinals == first_attempt_ordinals
        assert row.selected_feature_estimand_ordinals == feature_ordinals
        assert row.selected_feature_ids == tuple(item[0] for item in features)
        assert row.selected_feature_lower_bounds == tuple(
            Fraction(item[1]) for item in features
        )
        assert row.selected_feature_upper_bounds == tuple(
            Fraction(item[2]) for item in features
        )
        assert row.external_seed_count == _N
        assert row.deadline_seconds == 300
        assert row.same_seed_ordinal_reuse_across_rows_required is True
        assert row.cross_row_pairing_required_without_independence is True
        assert row.volatile_runtime_or_result_hashes_semantically_authoritative is False

        observable_cursor += len(cells)
        first_attempt_cursor += first_attempt_count
        feature_cursor += len(features)

    assert (observable_cursor, first_attempt_cursor, feature_cursor) == (
        73,
        243,
        555,
    )


def test_all_554_estimand_ids_ordinals_and_family_fields_are_exact() -> None:
    bundle = design.cp61_whole_seed_mc_design_bundle()
    expected_id_groups = _expected_estimand_ids()
    actual_groups = (
        bundle.observable_estimands,
        bundle.rejection_first_attempt_estimands,
        bundle.selected_conditional_feature_estimands,
    )
    assert tuple(len(group) for group in actual_groups) == (72, 170, 312)
    assert tuple(
        tuple(item.estimand_id for item in group) for group in actual_groups
    ) == (expected_id_groups)
    all_estimands = _all_estimands(bundle)
    assert tuple(item.estimand_ordinal for item in all_estimands) == tuple(
        range(1, 555)
    )
    assert len({item.estimand_id for item in all_estimands}) == 554
    assert len({item.record_sha256 for item in all_estimands}) == 554

    projection_sha256 = bundle.stable_trace_projection_contract.record_sha256
    observable_index = first_index = feature_index = 0
    for row_ordinal, row_data in enumerate(_ROWS, 1):
        fixture_id, strategy, budget, _, definition_sha256 = row_data
        cells = _REJECTION_CELLS if strategy == "bounded-rejection" else _SIR_CELLS
        for cell in cells:
            estimand = bundle.observable_estimands[observable_index]
            assert type(estimand) is design.CP61EstimandV1
            assert (
                estimand.estimand_family,
                estimand.row_ordinal,
                estimand.fixture_id,
                estimand.strategy,
                estimand.budget,
                estimand.observable_cell_label,
            ) == (
                "observable-cell",
                row_ordinal,
                fixture_id,
                strategy,
                budget,
                cell,
            )
            assert estimand.first_attempt_one_based is None
            assert estimand.feature_id is None
            assert estimand.feature_lower_bound is None
            assert estimand.feature_upper_bound is None
            assert estimand.feature_range is None
            assert estimand.target_feature_halfwidth is None
            assert estimand.cp60_definition_record_sha256 == definition_sha256
            assert estimand.cp58_feature_registry_sha256 is None
            assert estimand.cp58_feature_definition_sha256 is None
            assert estimand.denominator_mode == "all-2048-external-seed-ordinals"
            assert estimand.minimum_denominator_count == _N
            assert estimand.uncertainty_method == (
                "clopper-pearson-exact-rational-outward-bisection"
            )
            assert estimand.deadline_scoped_observation is True
            assert estimand.observed_before_deadline_only is (
                cell != "timeout-censored-at-deadline"
            )
            assert estimand.timeout_censored_at_deadline is (
                cell == "timeout-censored-at-deadline"
            )
            assert estimand.validated_return_before_deadline_required is (
                cell
                in (
                    "returned-rejection-selected-before-deadline",
                    "returned-rejection-exhausted-before-deadline",
                    "returned-sir-selected-before-deadline",
                )
            )
            assert estimand.returned_before_deadline_only is (
                estimand.validated_return_before_deadline_required
            )
            assert estimand.timeout_censored_is_semantic_nonreturn is False
            assert estimand.conditional_on_selected is False
            observable_index += 1

        if strategy == "bounded-rejection":
            for attempt in range(1, budget + 1):
                estimand = bundle.rejection_first_attempt_estimands[first_index]
                assert type(estimand) is design.CP61EstimandV1
                assert (
                    estimand.estimand_family,
                    estimand.row_ordinal,
                    estimand.fixture_id,
                    estimand.strategy,
                    estimand.budget,
                    estimand.observable_cell_label,
                    estimand.first_attempt_one_based,
                ) == (
                    "rejection-first-attempt",
                    row_ordinal,
                    fixture_id,
                    strategy,
                    budget,
                    None,
                    attempt,
                )
                assert estimand.feature_id is None
                assert estimand.feature_lower_bound is None
                assert estimand.feature_upper_bound is None
                assert estimand.feature_range is None
                assert estimand.target_feature_halfwidth is None
                assert estimand.cp60_definition_record_sha256 == definition_sha256
                assert estimand.cp58_feature_registry_sha256 is None
                assert estimand.cp58_feature_definition_sha256 is None
                assert estimand.denominator_mode == ("all-2048-external-seed-ordinals")
                assert estimand.minimum_denominator_count == _N
                assert estimand.uncertainty_method == (
                    "clopper-pearson-exact-rational-outward-bisection"
                )
                assert estimand.deadline_scoped_observation is True
                assert estimand.observed_before_deadline_only is True
                assert estimand.returned_before_deadline_only is True
                assert estimand.timeout_censored_at_deadline is False
                assert estimand.validated_return_before_deadline_required is True
                assert estimand.timeout_censored_is_semantic_nonreturn is False
                assert estimand.conditional_on_selected is False
                first_index += 1

        features = _M1_FEATURES if fixture_id == "T28-M1-Q" else _M2_FEATURES
        for feature_id, lower, upper, feature_sha256 in features:
            estimand = bundle.selected_conditional_feature_estimands[feature_index]
            width = Fraction(upper - lower)
            assert type(estimand) is design.CP61EstimandV1
            assert (
                estimand.estimand_family,
                estimand.row_ordinal,
                estimand.fixture_id,
                estimand.strategy,
                estimand.budget,
                estimand.observable_cell_label,
                estimand.first_attempt_one_based,
                estimand.feature_id,
            ) == (
                "selected-conditional-feature",
                row_ordinal,
                fixture_id,
                strategy,
                budget,
                None,
                None,
                feature_id,
            )
            assert estimand.feature_lower_bound == Fraction(lower)
            assert estimand.feature_upper_bound == Fraction(upper)
            assert estimand.feature_range == width
            assert estimand.target_feature_halfwidth == width * Fraction(3, 40)
            assert estimand.cp60_definition_record_sha256 == definition_sha256
            assert (
                estimand.cp58_feature_registry_sha256 == _REGISTRY_SHA256S[fixture_id]
            )
            assert estimand.cp58_feature_definition_sha256 == feature_sha256
            assert estimand.denominator_mode == (
                "predeadline-selected-count-in-this-row"
            )
            assert estimand.minimum_denominator_count == _K_MIN
            assert estimand.uncertainty_method == (
                "bounded-feature-hoeffding-fixed-range-halfwidth"
            )
            assert estimand.deadline_scoped_observation is True
            assert estimand.observed_before_deadline_only is True
            assert estimand.returned_before_deadline_only is True
            assert estimand.timeout_censored_at_deadline is False
            assert estimand.validated_return_before_deadline_required is True
            assert estimand.timeout_censored_is_semantic_nonreturn is False
            assert estimand.conditional_on_selected is True
            feature_index += 1

    assert (observable_index, first_index, feature_index) == (72, 170, 312)
    for estimand in all_estimands:
        assert estimand.familywise_error_budget == _FAMILY_ALPHA
        assert estimand.per_estimator_error_budget == Fraction(1, 55_400)
        assert estimand.per_tail_error_budget == _TAIL
        assert estimand.stable_trace_projection_contract_sha256 == projection_sha256
        assert estimand.estimate_observed is False
        assert estimand.interval_computed is False


def test_independent_request_and_work_totals_are_exact() -> None:
    requests = len(_ROWS) * _N
    rejection_slots = len(_FIXTURES) * _N * sum(_REJECTION_BUDGETS)
    sir_slots = len(_FIXTURES) * _N * sum(_SIR_BUDGETS)
    proposal_slots = rejection_slots + sir_slots
    # M1 has cap/dimension (1, 1); M2 has cap/dimension (2, 2).
    worst_occurrences = _N * (1 + 2) * (sum(_REJECTION_BUDGETS) + sum(_SIR_BUDGETS))
    worst_coordinates = _N * (1 + 4) * (sum(_REJECTION_BUDGETS) + sum(_SIR_BUDGETS))
    assert requests == 32_768
    assert rejection_slots == 348_160
    assert sir_slots == 2_785_280
    assert proposal_slots == 3_133_440
    assert worst_occurrences == 4_700_160
    assert worst_coordinates == 7_833_600


def test_public_scalar_design_constants_match_independent_arithmetic() -> None:
    assert design.CP61_TEST28_FIXTURE_IDS == _FIXTURES
    assert design.CP61_TEST28_STRATEGIES == (
        "bounded-rejection",
        "fixed-budget-sir",
    )
    assert design.CP61_TEST28_REJECTION_BUDGET_GRID == _REJECTION_BUDGETS
    assert design.CP61_TEST28_SIR_BUDGET_GRID == _SIR_BUDGETS
    assert design.CP61_TEST28_ROW_COUNT == len(_ROWS) == 16
    assert design.CP61_TEST28_EXTERNAL_SEED_COUNT == _N
    assert design.CP61_TEST28_PLAN_SEED_BITS == 64
    assert design.CP61_TEST28_DEADLINE_SECONDS == 300
    assert design.CP61_TEST28_OBSERVABLE_ESTIMAND_COUNT == 72
    assert design.CP61_TEST28_REJECTION_FIRST_ATTEMPT_ESTIMAND_COUNT == 170
    assert design.CP61_TEST28_SELECTED_FEATURE_ESTIMAND_COUNT == 312
    assert design.CP61_TEST28_BINOMIAL_ESTIMAND_COUNT == 242
    assert design.CP61_TEST28_ESTIMAND_COUNT == 554
    assert design.CP61_TEST28_M1_FEATURE_COUNT == len(_M1_FEATURES) == 6
    assert design.CP61_TEST28_M2_FEATURE_COUNT == len(_M2_FEATURES) == 33
    assert design.CP61_TEST28_FAMILYWISE_ERROR_BUDGET == _FAMILY_ALPHA
    assert design.CP61_TEST28_PER_ESTIMATOR_ERROR_BUDGET == Fraction(1, 55_400)
    assert design.CP61_TEST28_PER_TAIL_ERROR_BUDGET == _TAIL
    assert design.CP61_TEST28_CP_BISECTION_STEPS == 256
    assert design.CP61_TEST28_MINIMUM_SELECTED_COUNT == _K_MIN
    assert design.CP61_TEST28_FEATURE_HALFWIDTH_RANGE_MULTIPLIER == Fraction(3, 40)
    assert design.CP61_TEST28_HOEFFDING_EXPONENT == Fraction(117, 10)
    assert design.CP61_TEST28_TAYLOR_MAXIMUM_DEGREE == 17
    assert design.CP61_TEST28_TAYLOR_LOWER_BOUND > 110_800
    assert design.CP61_TEST28_TOTAL_REQUEST_COUNT == 32_768
    assert design.CP61_TEST28_REJECTION_PROPOSAL_SLOT_COUNT == 348_160
    assert design.CP61_TEST28_SIR_PROPOSAL_SLOT_COUNT == 2_785_280
    assert design.CP61_TEST28_TOTAL_PROPOSAL_SLOT_COUNT == 3_133_440
    assert design.CP61_TEST28_SIR_RESAMPLING_DRAW_COUNT == 16_384
    assert design.CP61_TEST28_MAX_EVENT_OCCURRENCE_COUNT == 4_700_160
    assert design.CP61_TEST28_MAX_COORDINATE_COUNT == 7_833_600


def test_source_and_predecessor_custody_constants_match_live_bytes() -> None:
    assert (
        hashlib.sha256(Path(diagnostics.__file__).read_bytes()).hexdigest()
        == design.CP61_TEST28_CP58_SOURCE_SHA256
    )
    assert (
        hashlib.sha256(Path(pushforward.__file__).read_bytes()).hexdigest()
        == design.CP61_TEST28_CP60_SOURCE_SHA256
    )
    cp60_bundle = pushforward.cp60_whole_seed_pushforward_bundle()
    assert cp60_bundle.record_sha256 == design.CP61_TEST28_CP60_BUNDLE_SHA256
    assert (
        design.CP61_TEST28_M1_FEATURE_REGISTRY_SHA256 == _REGISTRY_SHA256S["T28-M1-Q"]
    )
    assert (
        design.CP61_TEST28_M2_FEATURE_REGISTRY_SHA256 == _REGISTRY_SHA256S["T28-M2-Q"]
    )


def test_stable_projection_contract_includes_semantics_and_excludes_identity() -> None:
    bundle = design.cp61_whole_seed_mc_design_bundle()
    projection = bundle.stable_trace_projection_contract
    expected_formula = (
        "project each future retained raw trace to every stable request, source, "
        "facade-provider, runtime, RNG-state, configuration-value, exact-score, "
        "quota/word/acceptance and complete strategy-trace semantic field plus the "
        "closed status/failure code; exclude only raw runtime/object identities,"
        " address-bearing repr, plan and owner/execution-certificate hashes, and "
        "nested/result hashes inheriting those identities; never discard raw trace"
    )
    assert type(projection) is design.CP61StableTraceProjectionContractV1
    assert design.CP61_TEST28_STABLE_TRACE_PROJECTION_FORMULA == expected_formula
    assert projection.projection_formula == expected_formula
    assert projection.included_semantics == _INCLUDED_STABLE_TRACE_SEMANTICS
    assert projection.excluded_volatile_custody == _EXCLUDED_VOLATILE_TRACE_CUSTODY
    assert (
        design.CP61_TEST28_STABLE_TRACE_PROJECTION_INCLUDED_SEMANTICS
        == _INCLUDED_STABLE_TRACE_SEMANTICS
    )
    assert (
        design.CP61_TEST28_STABLE_TRACE_PROJECTION_EXCLUDED_CUSTODY
        == _EXCLUDED_VOLATILE_TRACE_CUSTODY
    )
    assert "  " not in projection.projection_formula
    assert projection.projection_formula == projection.projection_formula.strip()
    assert projection.future_raw_trace_retention_required is True
    assert projection.raw_trace_digest_only_permitted is False
    assert projection.stable_projection_replaces_raw_trace is False
    assert projection.full_stable_trace_projection_required is True
    assert projection.stable_request_digest_retention_required is True
    assert (
        projection.stable_facade_provider_certificate_digest_retention_required is True
    )
    assert projection.stable_runtime_record_retention_required is True
    assert projection.plan_seed_and_derived_rng_state_retention_required is True
    assert projection.runtime_identifiers_in_semantic_projection is False
    assert (
        projection.volatile_plan_certificate_nested_result_hashes_in_semantic_projection
        is False
    )
    assert projection.compact_estimand_projection_is_full_stable_trace is False
    assert projection.full_trace_law_estimated is False
    assert projection.total_variation_estimated is False
    assert projection.projection_instantiated_on_observed_traces is False
    assert projection.cross_process_projection_parity_verified is False
    included_text = ";".join(projection.included_semantics)
    excluded_text = ";".join(projection.excluded_volatile_custody)
    for stable_term in (
        "stable-request",
        "source",
        "provider-certificate",
        "rng-state",
        "binary64",
        "configuration-digests",
        "quota-certificate",
        "rejection-attempt-slot",
        "sir-cloud",
        "failure-code",
    ):
        assert stable_term in included_text
    for volatile_term in (
        "runtime-identity",
        "object-identity",
        "address-bearing",
        "plan-sha256",
        "owner-and-execution-certificate",
        "nested-scored-attempt-particle-and-result-hashes",
    ):
        assert volatile_term in excluded_text


def test_seed_sampling_no_retry_infrastructure_and_nonclaim_flags_are_exact() -> None:
    bundle = design.cp61_whole_seed_mc_design_bundle()
    assert bundle.fixture_ids == _FIXTURES
    assert bundle.rejection_budget_grid == _REJECTION_BUDGETS
    assert bundle.sir_budget_grid == _SIR_BUDGETS
    assert bundle.seed_ordinals == tuple(range(1, _N + 1))
    assert bundle.external_seed_count == _N
    assert bundle.external_seed_bits == 64
    assert bundle.external_seed_sampling_mode == (
        "future-external-iid-uniform-uint64-with-replacement"
    )
    for field_name in (
        "same_seed_ordinal_reuse_across_all_rows_required",
        "external_seed_draws_iid_uniform_uint64_with_replacement_required",
        "duplicate_seed_value_retention_required",
        "timeout_censoring_retention_required",
        "predeclared_design_only",
        "predecessor_inventories_hardcoded",
        "predecessor_source_and_record_hashes_are_frozen_custody_bindings",
        "infrastructure_failure_invalidates_entire_mc_attempt",
        "observable_cell_partition_requires_infrastructure_fidelity",
        "stable_design_semantic_digest_binds_predecessor_sources_and_registries",
        "stable_design_semantic_digest_excludes_volatile_identity_hashes",
    ):
        assert getattr(bundle, field_name) is True, field_name
    for field_name in (
        "duplicate_seed_value_retry_permitted",
        "outcome_dropping_permitted",
        "sample_topup_permitted",
        "cross_row_outcomes_assumed_independent",
        "timeout_censored_identified_with_semantic_nonreturn",
        "cp58_or_cp60_imported_or_loaded_by_builder",
        "live_predecessor_parity_verified_by_builder",
        "infrastructure_failure_is_estimand_cell",
        "infrastructure_failure_folded_into_execution_failure",
        "infrastructure_failure_folded_into_timeout_censoring",
        "infrastructure_failure_draw_retried_replaced_or_topped_up",
        "infrastructure_fidelity_verified",
        "requests_fully_bound",
        "runtime_fully_bound",
        "source_capsule_fully_bound",
        "external_supervisor_fully_bound",
        "external_seed_source_verified",
        "cross_ordinal_iid_uniformity_verified",
        "current_fixed_hash_seed_plan_is_external_iid_seed_sample",
        "seed_sample_recorded",
        "raw_trace_sample_recorded",
        "requests_executed",
        "intervals_computed",
        "operational_predictions_derived",
        "full_trace_law_estimated",
        "total_variation_estimated",
        "power_guarantee_claimed",
        "confirmatory_evidence",
        "manuscript_claim_promoted",
        "formal_test_28_closed",
        "stable_design_semantic_digest_is_full_trace_law_digest",
    ):
        assert getattr(bundle, field_name) is False, field_name
    assert bundle.deadline_seconds == 300
    assert bundle.formal_test_28_status == "OPEN"
    assert bundle.infrastructure_failure_policy == (
        design.CP61_TEST28_INFRASTRUCTURE_FAILURE_POLICY
    )
    for forbidden_fold in (
        "estimand cell",
        "execution failure",
        "timeout",
        "retry",
        "replacement",
        "top-up",
    ):
        assert forbidden_fold in bundle.infrastructure_failure_policy


def test_multiplicity_precision_and_resource_records_are_exact() -> None:
    bundle = design.cp61_whole_seed_mc_design_bundle()
    precision = bundle.multiplicity_and_precision
    assert type(precision) is design.CP61MultiplicityAndPrecisionV1
    assert (
        precision.estimand_count,
        precision.binomial_estimand_count,
        precision.selected_feature_estimand_count,
    ) == (554, 242, 312)
    assert precision.familywise_error_budget == _FAMILY_ALPHA
    assert precision.per_estimator_error_budget == Fraction(1, 55_400)
    assert precision.per_tail_error_budget == _TAIL
    assert precision.bonferroni_estimator_sum == _FAMILY_ALPHA
    assert precision.bonferroni_tail_sum == _FAMILY_ALPHA
    assert precision.clopper_pearson_bisection_steps == 256
    assert precision.public_cp_calibration_max_trial_count == 128
    assert precision.clopper_pearson_exact_rational_tail_evaluation is True
    assert precision.clopper_pearson_outward_rounding is True
    assert precision.zero_success_upper_endpoint_strictly_positive is True
    assert precision.all_success_lower_endpoint_strictly_less_than_one is True
    assert precision.minimum_selected_count == _K_MIN
    assert precision.feature_halfwidth_range_multiplier == Fraction(3, 40)
    assert precision.hoeffding_exponent_at_minimum_count == Fraction(117, 10)
    assert precision.taylor_maximum_degree == 17
    assert precision.exp_exponent_taylor_lower_bound > 110_800
    assert precision.reciprocal_per_tail_error_budget == 110_800
    assert precision.taylor_lower_bound_exceeds_reciprocal_tail_budget is True
    assert (
        precision.bounded_feature_one_sided_tail_bound_strictly_below_per_tail_budget
        is True
    )
    assert (
        precision.bounded_feature_two_sided_failure_strictly_below_per_estimator_budget
        is True
    )
    assert precision.below_minimum_selected_count_produces_no_interval is True
    assert precision.future_interval_algorithm_predeclared is True
    assert precision.future_n2048_intervals_computed is False
    assert precision.intervals_computed is False
    assert precision.simultaneous_coverage_realized is False
    assert precision.power_guarantee_claimed is False

    resources = bundle.resource_budget
    assert type(resources) is design.CP61ResourceBudgetV1
    assert (
        resources.external_seed_count,
        resources.row_count,
        resources.total_request_count,
        resources.rejection_proposal_slot_count,
        resources.sir_proposal_slot_count,
        resources.total_proposal_slot_count,
        resources.sir_resampling_draw_count,
        resources.maximum_event_occurrence_count,
        resources.maximum_coordinate_count,
    ) == (
        _N,
        16,
        32_768,
        348_160,
        2_785_280,
        3_133_440,
        16_384,
        4_700_160,
        7_833_600,
    )
    assert resources.resource_caps_predeclared is True
    assert resources.total_request_count_is_scheduled is True
    assert resources.proposal_slot_counts_are_planned_maxima_not_observed is True
    assert resources.event_and_coordinate_counts_are_planned_maxima_not_observed is True
    assert resources.resources_allocated is False
    assert resources.execution_performed is False


def test_observable_cells_are_deadline_scoped_and_exclude_nonreturn() -> None:
    assert design.CP61_TEST28_REJECTION_OBSERVABLE_CELLS == _REJECTION_CELLS
    assert design.CP61_TEST28_SIR_OBSERVABLE_CELLS == _SIR_CELLS
    assert "deadline" in design.CP61_TEST28_WHOLE_SEED_MC_SCOPE
    assert "semantic-nonreturn" in design.CP61_TEST28_WHOLE_SEED_MC_SCOPE
    assert all(
        "nonreturn" not in cell
        for cell in (
            design.CP61_TEST28_REJECTION_OBSERVABLE_CELLS
            + design.CP61_TEST28_SIR_OBSERVABLE_CELLS
        )
    )


def test_exact_taylor_hoeffding_and_familywise_certificate() -> None:
    # For epsilon=(range)*3/40 and K=1040, range cancels exactly.
    exponent = 2 * _K_MIN * Fraction(3, 40) ** 2
    assert exponent == Fraction(117, 10)

    term = partial_16 = partial_17 = Fraction(1)
    for order in range(1, 18):
        term *= exponent / order
        partial_17 += term
        if order == 16:
            partial_16 = partial_17
    assert partial_16 < 110_800 < partial_17
    # Positive Taylor terms prove exp(117/10)>110800 without evaluating exp.
    assert partial_17 == Fraction(
        428_914_006_377_131_589_846_189_933_005_011,
        3_753_164_800_000_000_000_000_000_000,
    )
    assert 554 * 2 * _TAIL == _FAMILY_ALPHA
    assert design.CP61_TEST28_HOEFFDING_EXPONENT_FORMULA == (
        "2*Kmin*(3/40)^2=2*1040*9/1600=117/10"
    )
    assert design.CP61_TEST28_TAYLOR_LOWER_BOUND_FORMULA == (
        "sum_{j=0}^{17}(117/10)^j/j!="
        "428914006377131589846189933005011/"
        "3753164800000000000000000000>110800"
    )
    precision = design.cp61_whole_seed_mc_design_bundle().multiplicity_and_precision
    assert precision.hoeffding_exponent_formula == (
        design.CP61_TEST28_HOEFFDING_EXPONENT_FORMULA
    )
    assert precision.taylor_lower_bound_formula == (
        design.CP61_TEST28_TAYLOR_LOWER_BOUND_FORMULA
    )


def test_hoeffding_range_scaling_and_k_threshold_are_not_off_by_one() -> None:
    for width, epsilon in ((1, Fraction(3, 40)), (2, Fraction(3, 20))):
        at_threshold = 2 * _K_MIN * epsilon**2 / width**2
        below_threshold = 2 * (_K_MIN - 1) * epsilon**2 / width**2
        assert at_threshold == Fraction(117, 10)
        assert below_threshold < Fraction(117, 10)
    assert Fraction(_K_MIN, _N) == Fraction(65, 128)


def test_selected_feature_rule_is_a_conditional_mean_with_no_topup_or_ratio() -> None:
    bundle = design.cp61_whole_seed_mc_design_bundle()
    precision = bundle.multiplicity_and_precision
    formula = precision.feature_halfwidth_formula
    assert "sample-feature-mean" in formula
    assert "K>=1040" in formula
    assert "otherwise publish no feature interval" in formula
    assert "numerator" not in formula
    assert "ratio" not in formula
    assert bundle.sample_topup_permitted is False
    assert precision.below_minimum_selected_count_produces_no_interval is True
    assert all(
        estimand.denominator_mode == "predeadline-selected-count-in-this-row"
        and estimand.minimum_denominator_count == _K_MIN
        and estimand.conditional_on_selected is True
        for estimand in bundle.selected_conditional_feature_estimands
    )

    def planned_interval(mean, lower, upper, selected_count):
        if selected_count < _K_MIN:
            return None
        halfwidth = (upper - lower) * Fraction(3, 40)
        return max(lower, mean - halfwidth), min(upper, mean + halfwidth)

    assert planned_interval(Fraction(1, 2), Fraction(0), Fraction(1), 1_039) is None
    assert planned_interval(Fraction(1, 2), Fraction(0), Fraction(1), 1_040) == (
        Fraction(17, 40),
        Fraction(23, 40),
    )
    assert planned_interval(Fraction(-1), Fraction(-1), Fraction(1), 1_040) == (
        Fraction(-1),
        Fraction(-17, 20),
    )


def test_exact_cp_tail_orientation_on_toy_calibrations() -> None:
    # For x=0, the upper endpoint solves (1-u)^n=tail.  These small exact
    # examples catch reversed tails without relying on a beta-quantile API.
    assert _binomial_cdf(3, 0, Fraction(1, 2)) == Fraction(1, 8)
    assert _binomial_cdf(3, 1, Fraction(1, 2)) == Fraction(1, 2)
    p = Fraction(1, 4)
    assert _binomial_cdf(4, 0, p) == Fraction(81, 256)
    assert 1 - _binomial_cdf(4, 0, p) == Fraction(175, 256)
    assert _binomial_cdf(4, 4, p) == 1


@pytest.mark.parametrize(("successes", "trials"), ((0, 1), (1, 1), (3, 8)))
def test_cp61_exact_cp_bisection_has_unique_outward_orientation(
    successes, trials
) -> None:
    lower, upper = design.cp61_exact_clopper_pearson_outward_calibration_interval(
        successes, trials
    )
    step = Fraction(1, 1 << 256)
    assert 0 <= lower <= upper <= 1
    if successes == 0:
        assert lower == 0
    else:
        tail_at_lower = 1 - _binomial_cdf(trials, successes - 1, lower)
        tail_after_lower = 1 - _binomial_cdf(trials, successes - 1, lower + step)
        assert tail_at_lower < _TAIL <= tail_after_lower
    if successes == trials:
        assert upper == 1
    else:
        tail_at_upper = _binomial_cdf(trials, successes, upper)
        tail_before_upper = _binomial_cdf(trials, successes, upper - step)
        assert tail_at_upper <= _TAIL < tail_before_upper


def test_cp61_cp_bisection_rejects_hostile_counts_and_integer_subclasses() -> None:
    for successes, trials in (
        (True, 8),
        (_IntSubclass(1), 8),
        (1, _IntSubclass(8)),
        (-1, 8),
        (9, 8),
        (0, 0),
        (0, 129),
        (0, 2_048),
    ):
        with pytest.raises((TypeError, ValueError)):
            design.cp61_exact_clopper_pearson_outward_calibration_interval(
                successes, trials
            )


def test_cp61_bisection_pins_initial_brackets_step_count_and_equality_rule(
    monkeypatch,
) -> None:
    seen = []

    def equal_to_delta(probability, trial_count, start, stop):
        seen.append((probability, trial_count, start, stop))
        return 0

    monkeypatch.setattr(design, "_tail_compare_delta", equal_to_delta)
    lower, upper = design.cp61_exact_clopper_pearson_outward_calibration_interval(1, 2)
    step = Fraction(1, 1 << 256)
    assert (lower, upper) == (Fraction(0), step)
    assert len(seen) == 512
    expected_midpoints = tuple(Fraction(1, 1 << power) for power in range(1, 257))
    assert tuple(item[0] for item in seen[:256]) == expected_midpoints
    assert tuple(item[0] for item in seen[256:]) == expected_midpoints
    assert all(item[1:] == (2, 1, 2) for item in seen[:256])
    assert all(item[1:] == (2, 0, 1) for item in seen[256:])

    # Boundary handling is endpoint-wise: only the boundary endpoint is
    # fixed; the other endpoint still performs all 256 equality-directed
    # bisections and is published outward.
    seen.clear()
    assert design.cp61_exact_clopper_pearson_outward_calibration_interval(0, 2) == (
        Fraction(0),
        step,
    )
    assert len(seen) == 256
    assert all(item[1:] == (2, 0, 0) for item in seen)
    seen.clear()
    assert design.cp61_exact_clopper_pearson_outward_calibration_interval(2, 2) == (
        Fraction(0),
        Fraction(1),
    )
    assert len(seen) == 256
    assert all(item[1:] == (2, 2, 2) for item in seen)


def test_future_cp_interval_formula_uniquely_predeclares_every_update() -> None:
    expected = (
        "for X~Binomial(n,p), lower=0 when k=0;otherwise initialize lo=0,hi=1 "
        "and perform exactly 256 updates with mid=(lo+hi)/2 and exact-rational "
        "T=P_mid(X>=k):if T<delta set lo=mid,else including equality set hi=mid;"
        "publish lower=lo;upper=1 when k=n;otherwise initialize lo=0,hi=1 and "
        "perform exactly 256 updates with mid=(lo+hi)/2 and exact-rational "
        "C=P_mid(X<=k):if C>delta set lo=mid,else including equality set hi=mid;"
        "publish upper=hi"
    )
    bundle = design.cp61_whole_seed_mc_design_bundle()
    assert design.CP61_TEST28_CP_INTERVAL_FORMULA == expected
    assert bundle.multiplicity_and_precision.clopper_pearson_interval_formula == (
        expected
    )


def test_central_n128_calibration_completes_bounded_and_has_exact_brackets() -> None:
    source_root = str(Path(__file__).resolve().parents[2] / "src")
    code = r"""
from heterodiff.evaluation import mixed_initializer_test28_whole_seed_mc_design as d
lower, upper = d.cp61_exact_clopper_pearson_outward_calibration_interval(64, 128)
print(lower.numerator)
print(lower.denominator)
print(upper.numerator)
print(upper.denominator)
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(Path(__file__).resolve().parents[2]),
        env={"PYTHONPATH": source_root},
        text=True,
        capture_output=True,
        timeout=15,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    numbers = tuple(int(item) for item in completed.stdout.splitlines())
    assert len(numbers) == 4
    lower = Fraction(numbers[0], numbers[1])
    upper = Fraction(numbers[2], numbers[3])
    step = Fraction(1, 1 << 256)
    assert 0 < lower < Fraction(1, 2) < upper < 1
    assert upper == 1 - lower
    assert lower.denominator == upper.denominator == 1 << 256
    assert 1 - _binomial_cdf(128, 63, lower) < _TAIL
    assert 1 - _binomial_cdf(128, 63, lower + step) >= _TAIL
    assert _binomial_cdf(128, 64, upper) <= _TAIL
    assert _binomial_cdf(128, 64, upper - step) > _TAIL


def test_future_n2048_zero_count_cp_upper_bound_is_positive_but_uncomputed() -> None:
    # u=1-tail^(1/n).  Exact dyadic brackets are checked by raising their
    # complements to n; this avoids treating a rounded display as authority.
    lower = Fraction(5_655_568_811_460, 10**15)
    upper = Fraction(5_655_568_811_461, 10**15)
    assert (1 - lower) ** _N > _TAIL
    assert (1 - upper) ** _N < _TAIL
    assert 0 < lower < upper < Fraction(6, 1_000)

    bundle = design.cp61_whole_seed_mc_design_bundle()
    precision = bundle.multiplicity_and_precision
    assert precision.zero_success_upper_endpoint_strictly_positive is True
    assert precision.future_interval_algorithm_predeclared is True
    assert precision.public_cp_calibration_max_trial_count == 128
    assert precision.future_n2048_intervals_computed is False
    assert precision.intervals_computed is False
    assert bundle.intervals_computed is False
    with pytest.raises(ValueError):
        design.cp61_exact_clopper_pearson_outward_calibration_interval(0, _N)

    cp_lower, cp_upper = design.cp61_exact_clopper_pearson_outward_calibration_interval(
        0, 128
    )
    step = Fraction(1, 1 << 256)
    assert cp_lower == 0
    assert 0 < cp_upper < Fraction(1, 10)
    assert (1 - cp_upper) ** 128 <= _TAIL
    assert (1 - (cp_upper - step)) ** 128 > _TAIL


def test_timeout_censor_cannot_identify_semantic_nonreturn_or_full_selected_law() -> None:
    observed = (
        "returned-selected-before-deadline",
        "timeout-censored-at-deadline",
    )
    finite_slow_completion = {
        observed[0]: ("selected", "a"),
        observed[1]: ("selected", "b"),
    }
    semantic_nonreturn = {
        observed[0]: ("selected", "a"),
        observed[1]: ("nonreturn", None),
    }
    assert tuple(finite_slow_completion) == tuple(semantic_nonreturn) == observed
    assert finite_slow_completion != semantic_nonreturn
    assert "nonreturn" not in _REJECTION_CELLS
    assert "nonreturn" not in _SIR_CELLS


def test_shared_seed_blocks_do_not_imply_cross_template_independence() -> None:
    seeds = (0, 1, 2, 3)
    left = tuple(seed % 2 for seed in seeds)
    right = tuple(seed % 2 for seed in seeds)
    assert sum(left) == sum(right) == 2
    assert tuple(zip(left, right)) == ((0, 0), (1, 1), (0, 0), (1, 1))
    assert not any(a != b for a, b in zip(left, right))


def test_public_records_are_sealed_unpickleable_and_exact_type_only() -> None:
    bundle = design.cp61_whole_seed_mc_design_bundle()
    assert design.validate_cp61_whole_seed_mc_design_bundle(bundle) is bundle
    representatives = (
        bundle.stable_trace_projection_contract,
        bundle.ordered_rows[0],
        bundle.observable_estimands[0],
        bundle.multiplicity_and_precision,
        bundle.resource_budget,
        bundle,
    )
    for record in representatives:
        assert not hasattr(record, "__dict__")
        with pytest.raises(TypeError, match="module-created"):
            type(record)()
        with pytest.raises((TypeError, pickle.PicklingError)):
            pickle.dumps(record)
        with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
            setattr(record, "record_sha256", _ZERO_SHA256)
        with pytest.raises(TypeError, match="cannot be subclassed"):
            type("Hostile" + type(record).__name__, (type(record),), {})
    with pytest.raises(TypeError, match="cannot be subclassed"):
        make_dataclass(
            "HostileCP61Alien",
            (("record_sha256", str),),
            bases=(design._SealedRecord,),
            frozen=True,
            init=False,
            slots=True,
        )
    for alien in (None, True, 1, {}, (), _ProtocolBomb()):
        with pytest.raises(TypeError):
            design.cp61_canonical_json_bytes(alien)
        with pytest.raises(TypeError):
            design.validate_cp61_whole_seed_mc_design_bundle(alien)


def test_every_nested_record_digest_and_public_canonical_bytes_are_independent() -> None:
    bundle = design.cp61_whole_seed_mc_design_bundle()
    typed_records = (
        (
            (bundle.stable_trace_projection_contract,),
            "stable-trace-projection-contract",
        ),
        (bundle.ordered_rows, "mc-row-design"),
        (_all_estimands(bundle), "estimand"),
        ((bundle.multiplicity_and_precision,), "multiplicity-and-precision"),
        ((bundle.resource_budget,), "resource-budget"),
        ((bundle,), "whole-seed-mc-design-bundle"),
    )
    for records, kind in typed_records:
        for record in records:
            assert record.record_sha256 == _independent_record_digest(record, kind)
            assert len(record.record_sha256) == 64
            assert set(record.record_sha256) <= set("0123456789abcdef")

    representatives = (
        bundle.stable_trace_projection_contract,
        bundle.ordered_rows[0],
        bundle.observable_estimands[0],
        bundle.rejection_first_attempt_estimands[-1],
        bundle.selected_conditional_feature_estimands[-1],
        bundle.multiplicity_and_precision,
        bundle.resource_budget,
        bundle,
    )
    encoded_union = b""
    for record in representatives:
        encoded = design.cp61_canonical_json_bytes(record)
        encoded_union += encoded
        assert encoded == _independent_canonical_bytes(record)
        assert encoded == json.dumps(
            json.loads(encoded.decode("ascii")),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("ascii")
        assert b'"cp61_record_type"' in encoded
    assert b'"cp61_exact_integer_hex"' in encoded_union
    assert b'"cp61_exact_fraction_v1"' in encoded_union


def test_compact_row_and_estimand_semantic_digests_are_independently_exact() -> None:
    bundle = design.cp61_whole_seed_mc_design_bundle()
    assert (
        design.CP61_TEST28_COMPACT_ESTIMAND_PROJECTION_SEMANTICS
        == _COMPACT_ESTIMAND_SEMANTICS
    )
    for row in bundle.ordered_rows:
        payload = {
            "schema_version": row.schema_version,
            "row_ordinal": row.row_ordinal,
            "fixture_id": row.fixture_id,
            "strategy": row.strategy,
            "budget": row.budget,
            "stable_request_template_sha256": row.cp60_request_template_sha256,
            "observable_cell_labels": row.observable_cell_labels,
            "observable_estimand_ordinals": row.observable_estimand_ordinals,
            "first_attempt_estimand_ordinals": row.first_attempt_estimand_ordinals,
            "selected_feature_estimand_ordinals": (
                row.selected_feature_estimand_ordinals
            ),
            "selected_feature_ids": row.selected_feature_ids,
            "selected_feature_lower_bounds": row.selected_feature_lower_bounds,
            "selected_feature_upper_bounds": row.selected_feature_upper_bounds,
            "external_seed_count": row.external_seed_count,
            "deadline_seconds": row.deadline_seconds,
            "same_seed_ordinal_reuse_across_rows_required": (
                row.same_seed_ordinal_reuse_across_rows_required
            ),
            "cross_row_pairing_required_without_independence": (
                row.cross_row_pairing_required_without_independence
            ),
        }
        assert row.compact_row_semantic_sha256 == _independent_digest(
            "compact-row-semantic", payload
        )

    for estimand in _all_estimands(bundle):
        payload = {
            "schema_version": estimand.schema_version,
            "estimand_ordinal": estimand.estimand_ordinal,
            "estimand_id": estimand.estimand_id,
            "estimand_family": estimand.estimand_family,
            "row_ordinal": estimand.row_ordinal,
            "fixture_id": estimand.fixture_id,
            "strategy": estimand.strategy,
            "budget": estimand.budget,
            "observable_cell_label": estimand.observable_cell_label,
            "first_attempt_one_based": estimand.first_attempt_one_based,
            "feature_id": estimand.feature_id,
            "feature_lower_bound": estimand.feature_lower_bound,
            "feature_upper_bound": estimand.feature_upper_bound,
            "feature_range": estimand.feature_range,
            "target_feature_halfwidth": estimand.target_feature_halfwidth,
            "denominator_mode": estimand.denominator_mode,
            "minimum_denominator_count": estimand.minimum_denominator_count,
            "uncertainty_method": estimand.uncertainty_method,
            "deadline_scoped_observation": estimand.deadline_scoped_observation,
            "observed_before_deadline_only": (estimand.observed_before_deadline_only),
            "returned_before_deadline_only": (estimand.returned_before_deadline_only),
            "timeout_censored_at_deadline": estimand.timeout_censored_at_deadline,
            "validated_return_before_deadline_required": (
                estimand.validated_return_before_deadline_required
            ),
            "timeout_censored_is_semantic_nonreturn": (
                estimand.timeout_censored_is_semantic_nonreturn
            ),
            "conditional_on_selected": estimand.conditional_on_selected,
            "familywise_error_budget": estimand.familywise_error_budget,
            "per_estimator_error_budget": estimand.per_estimator_error_budget,
            "per_tail_error_budget": estimand.per_tail_error_budget,
            "compact_projection_semantics": _COMPACT_ESTIMAND_SEMANTICS,
        }
        assert estimand.compact_estimand_semantic_sha256 == _independent_digest(
            "compact-estimand-semantic", payload
        )


def test_stable_design_digest_binds_ancestry_and_every_top_level_policy() -> None:
    bundle = design.cp61_whole_seed_mc_design_bundle()
    semantic_field_names = tuple(
        item.name
        for item in fields(type(bundle))
        if item.name not in ("stable_design_semantic_sha256", "record_sha256")
    )

    def stable_digest(**changes):
        payload = {name: getattr(bundle, name) for name in semantic_field_names}
        assert set(changes) <= set(payload)
        payload.update(changes)
        return _independent_digest("stable-design-semantic", payload)

    assert stable_digest() == bundle.stable_design_semantic_sha256
    assert design.cp61_stable_design_semantic_sha256(bundle) == stable_digest()

    changed_rows = []
    for field_name in (
        "cp60_bundle_sha256",
        "cp60_definition_record_sha256",
        "cp58_feature_registry_sha256",
    ):
        changed_row = _forge(bundle.ordered_rows[0], **{field_name: _ZERO_SHA256})
        changed_rows.append((changed_row,) + bundle.ordered_rows[1:])
    for rows in changed_rows:
        assert stable_digest(ordered_rows=rows) != bundle.stable_design_semantic_sha256

    changed_feature = _forge(
        bundle.selected_conditional_feature_estimands[0],
        cp58_feature_definition_sha256=_ZERO_SHA256,
    )
    changed_features = (changed_feature,) + (
        bundle.selected_conditional_feature_estimands[1:]
    )
    assert stable_digest(selected_conditional_feature_estimands=changed_features) != (
        bundle.stable_design_semantic_sha256
    )

    policy_perturbations = (
        {"scope": "hostile-scope"},
        {"external_seed_draws_iid_uniform_uint64_with_replacement_required": False},
        {"same_seed_ordinal_reuse_across_all_rows_required": False},
        {"duplicate_seed_value_retention_required": False},
        {"duplicate_seed_value_retry_permitted": True},
        {"outcome_dropping_permitted": True},
        {"sample_topup_permitted": True},
        {"cross_row_outcomes_assumed_independent": True},
        {"timeout_censoring_retention_required": False},
        {"timeout_censored_identified_with_semantic_nonreturn": True},
        {"infrastructure_failure_invalidates_entire_mc_attempt": False},
        {"infrastructure_failure_folded_into_execution_failure": True},
        {"infrastructure_failure_folded_into_timeout_censoring": True},
        {"observable_cell_partition_requires_infrastructure_fidelity": False},
        {"current_fixed_hash_seed_plan_is_external_iid_seed_sample": True},
        {"requests_executed": True},
        {"intervals_computed": True},
        {"operational_predictions_derived": True},
        {"full_trace_law_estimated": True},
        {"formal_test_28_status": "CLOSED"},
        {"formal_test_28_closed": True},
    )
    for changes in policy_perturbations:
        assert stable_digest(**changes) != bundle.stable_design_semantic_sha256


def test_all_public_nested_validators_accept_only_their_exact_frozen_record() -> None:
    bundle = design.cp61_whole_seed_mc_design_bundle()
    cases = (
        (
            design.validate_cp61_stable_trace_projection_contract,
            bundle.stable_trace_projection_contract,
        ),
        (design.validate_cp61_mc_row_design, bundle.ordered_rows[-1]),
        (design.validate_cp61_estimand, bundle.observable_estimands[-1]),
        (
            design.validate_cp61_estimand,
            bundle.rejection_first_attempt_estimands[-1],
        ),
        (
            design.validate_cp61_estimand,
            bundle.selected_conditional_feature_estimands[-1],
        ),
        (
            design.validate_cp61_multiplicity_and_precision,
            bundle.multiplicity_and_precision,
        ),
        (design.validate_cp61_resource_budget, bundle.resource_budget),
        (design.validate_cp61_whole_seed_mc_design_bundle, bundle),
    )
    for validator, record in cases:
        assert validator(record) is record
        for alien in (None, True, 1, {}, (), _ProtocolBomb()):
            with pytest.raises(TypeError):
                validator(alien)


def test_bundle_tamper_is_rejected_even_when_public_shape_is_preserved() -> None:
    bundle = design.cp61_whole_seed_mc_design_bundle()
    for field_name, value in (
        ("schema_version", "hostile-schema"),
        ("formal_test_28_status", "CLOSED"),
        ("formal_test_28_closed", True),
        ("record_sha256", _ZERO_SHA256),
    ):
        forged = _forge(bundle, **{field_name: value})
        with pytest.raises(ValueError):
            design.validate_cp61_whole_seed_mc_design_bundle(forged)


def test_redigested_nested_and_semantic_tamper_is_still_rejected() -> None:
    bundle = design.cp61_whole_seed_mc_design_bundle()
    cases = (
        (
            bundle.stable_trace_projection_contract,
            "stable-trace-projection-contract",
            design.validate_cp61_stable_trace_projection_contract,
            {"full_stable_trace_projection_required": False},
        ),
        (
            bundle.ordered_rows[0],
            "mc-row-design",
            design.validate_cp61_mc_row_design,
            {"cp60_definition_record_sha256": _ZERO_SHA256},
        ),
        (
            bundle.ordered_rows[0],
            "mc-row-design",
            design.validate_cp61_mc_row_design,
            {"compact_row_semantic_sha256": _ZERO_SHA256},
        ),
        (
            bundle.observable_estimands[0],
            "estimand",
            design.validate_cp61_estimand,
            {"interval_computed": True},
        ),
        (
            bundle.selected_conditional_feature_estimands[0],
            "estimand",
            design.validate_cp61_estimand,
            {"cp58_feature_definition_sha256": _ZERO_SHA256},
        ),
        (
            bundle.selected_conditional_feature_estimands[0],
            "estimand",
            design.validate_cp61_estimand,
            {"compact_estimand_semantic_sha256": _ZERO_SHA256},
        ),
        (
            bundle.multiplicity_and_precision,
            "multiplicity-and-precision",
            design.validate_cp61_multiplicity_and_precision,
            {"future_n2048_intervals_computed": True},
        ),
        (
            bundle.resource_budget,
            "resource-budget",
            design.validate_cp61_resource_budget,
            {"execution_performed": True},
        ),
        (
            bundle,
            "whole-seed-mc-design-bundle",
            design.validate_cp61_whole_seed_mc_design_bundle,
            {"stable_design_semantic_sha256": _ZERO_SHA256},
        ),
    )
    for record, kind, validator, changes in cases:
        tampered = _redigest(_forge(record, **changes), kind)
        assert tampered.record_sha256 == _independent_record_digest(tampered, kind)
        with pytest.raises(ValueError):
            validator(tampered)
        with pytest.raises(ValueError):
            design.cp61_canonical_json_bytes(tampered)


def test_redigested_outer_bundle_rejects_redigested_nested_tamper() -> None:
    bundle = design.cp61_whole_seed_mc_design_bundle()
    bad_estimand = _redigest(
        _forge(bundle.observable_estimands[0], interval_computed=True),
        "estimand",
    )
    bad_group = (bad_estimand,) + bundle.observable_estimands[1:]
    bad_bundle = _redigest(
        _forge(bundle, observable_estimands=bad_group),
        "whole-seed-mc-design-bundle",
    )
    assert bad_estimand.record_sha256 == _independent_record_digest(
        bad_estimand, "estimand"
    )
    assert bad_bundle.record_sha256 == _independent_record_digest(
        bad_bundle, "whole-seed-mc-design-bundle"
    )
    with pytest.raises(ValueError):
        design.validate_cp61_whole_seed_mc_design_bundle(bad_bundle)


def test_bundle_rejects_alien_nested_types_without_protocol_coercion() -> None:
    bundle = design.cp61_whole_seed_mc_design_bundle()
    alien_cases = (
        {"stable_trace_projection_contract": bundle.ordered_rows[0]},
        {"ordered_rows": _TupleSubclass(bundle.ordered_rows)},
        {"ordered_rows": (bundle.observable_estimands[0],) + bundle.ordered_rows[1:]},
        {"observable_estimands": list(bundle.observable_estimands)},
        {
            "observable_estimands": (bundle.ordered_rows[0],)
            + bundle.observable_estimands[1:]
        },
        {"multiplicity_and_precision": bundle.resource_budget},
        {"resource_budget": bundle.multiplicity_and_precision},
        {"seed_ordinals": _ProtocolBomb()},
    )
    for changes in alien_cases:
        forged = _forge(bundle, **changes)
        with pytest.raises(TypeError):
            design.validate_cp61_whole_seed_mc_design_bundle(forged)


def test_canonical_preflight_rejects_scalar_tuple_depth_and_fraction_bombs() -> None:
    bundle = design.cp61_whole_seed_mc_design_bundle()
    too_deep = None
    for _ in range(34):
        too_deep = (too_deep,)
    huge_fraction = Fraction(1 << 16_384, 1)
    bad_precision = _forge(
        bundle.multiplicity_and_precision,
        familywise_error_budget=huge_fraction,
    )
    cases = (
        _forge(bundle, scope=_StrSubclass("alien")),
        _forge(bundle, external_seed_count=_IntSubclass(_N)),
        _forge(bundle, external_seed_count=1 << 16_384),
        _forge(bundle, seed_ordinals=tuple(range(4_097))),
        _forge(bundle, scope={str(index): None for index in range(4_097)}),
        _forge(bundle, scope=too_deep),
        _forge(bundle, multiplicity_and_precision=bad_precision),
    )
    for forged in cases:
        with pytest.raises((TypeError, ValueError)):
            design.validate_cp61_whole_seed_mc_design_bundle(forged)


def test_canonical_preflight_rejects_node_text_and_encoded_output_bombs() -> None:
    bundle = design.cp61_whole_seed_mc_design_bundle()
    node_bomb = tuple(tuple(None for _ in range(4_096)) for _ in range(33))
    with pytest.raises(ValueError, match="node bound"):
        design.validate_cp61_whole_seed_mc_design_bundle(
            _forge(bundle, seed_ordinals=node_bomb)
        )

    repeated = "x" * 4_096
    text_bomb = tuple(repeated for _ in range(2_048))
    with pytest.raises(ValueError, match="text payload"):
        design.validate_cp61_whole_seed_mc_design_bundle(
            _forge(bundle, seed_ordinals=text_bomb)
        )

    # NUL is one UTF-8 byte but six canonical JSON bytes.  This stays under
    # the aggregate input-text cap and must hit the separate output cap.
    escaped = "\x00" * 4_096
    output_bomb = tuple(escaped for _ in range(700))
    with pytest.raises(ValueError, match="output bound"):
        design.validate_cp61_whole_seed_mc_design_bundle(
            _forge(bundle, seed_ordinals=output_bomb)
        )


def test_source_ast_has_no_rng_execution_or_volatile_identity_route() -> None:
    source = Path(design.__file__).resolve().read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    }
    assert not any(
        name == forbidden or name.startswith(forbidden + ".")
        for name in imports
        for forbidden in (
            "numpy",
            "scipy",
            "torch",
            "random",
            "secrets",
            "subprocess",
            "heterodiff.processes",
        )
    )
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    called_attributes = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert not called_names.intersection(
        {
            "id",
            "repr",
            "hash",
            "open",
            "exec",
            "eval",
            "Philox",
            "Generator",
        }
    )
    assert not called_attributes.intersection(
        {
            "execute",
            "sample_configuration",
            "evaluate",
            "random",
            "random_raw",
            "standard_normal",
        }
    )


def test_public_exports_and_signatures_preserve_the_design_only_boundary() -> None:
    required = {
        "CP61StableTraceProjectionContractV1",
        "CP61MCRowDesignV1",
        "CP61EstimandV1",
        "CP61MultiplicityAndPrecisionV1",
        "CP61ResourceBudgetV1",
        "CP61WholeSeedMCDesignBundleV1",
        "cp61_exact_clopper_pearson_outward_calibration_interval",
        "cp61_stable_design_semantic_sha256",
        "cp61_whole_seed_mc_design_bundle",
        "cp61_canonical_json_bytes",
        "validate_cp61_stable_trace_projection_contract",
        "validate_cp61_mc_row_design",
        "validate_cp61_estimand",
        "validate_cp61_multiplicity_and_precision",
        "validate_cp61_resource_budget",
        "validate_cp61_whole_seed_mc_design_bundle",
    }
    assert type(design.__all__) is tuple
    assert len(design.__all__) == len(set(design.__all__))
    assert required <= set(design.__all__)
    assert all(hasattr(design, name) for name in design.__all__)
    assert not any(name.startswith("_") for name in design.__all__)
    assert not any(
        token in name.lower()
        for name in design.__all__
        for token in ("execute_request", "sample_seed", "rng", "top_up", "retry")
    )
    assert (
        tuple(inspect.signature(design.cp61_whole_seed_mc_design_bundle).parameters)
        == ()
    )
    assert tuple(
        inspect.signature(
            design.cp61_exact_clopper_pearson_outward_calibration_interval
        ).parameters
    ) == ("success_count", "trial_count")
    for validator in (
        design.cp61_canonical_json_bytes,
        design.validate_cp61_stable_trace_projection_contract,
        design.validate_cp61_mc_row_design,
        design.validate_cp61_estimand,
        design.validate_cp61_multiplicity_and_precision,
        design.validate_cp61_resource_budget,
        design.validate_cp61_whole_seed_mc_design_bundle,
        design.cp61_stable_design_semantic_sha256,
    ):
        assert tuple(inspect.signature(validator).parameters) == ("value",)


def test_clean_import_and_bundle_replay_load_no_operational_dependency() -> None:
    bundle = design.cp61_whole_seed_mc_design_bundle()
    expected = (
        bundle.record_sha256,
        bundle.stable_design_semantic_sha256,
        hashlib.sha256(design.cp61_canonical_json_bytes(bundle)).hexdigest(),
    )
    source_root = str(Path(__file__).resolve().parents[2] / "src")
    code = r"""
import builtins
import hashlib
import sys
real_import = builtins.__import__
forbidden = (
    "numpy", "scipy", "torch", "random", "secrets", "heterodiff.processes",
    "heterodiff.evaluation.mixed_initializer_test28_bounded_sir_diagnostics",
    "heterodiff.evaluation.mixed_initializer_test28_uniform_seed_pushforward",
)
def guarded(name, *args, **kwargs):
    if any(name == item or name.startswith(item + ".") for item in forbidden):
        raise AssertionError("operational dependency crossed CP61 boundary: " + name)
    return real_import(name, *args, **kwargs)
builtins.__import__ = guarded
from heterodiff.evaluation import mixed_initializer_test28_whole_seed_mc_design as module
bundle = module.cp61_whole_seed_mc_design_bundle()
module.validate_cp61_whole_seed_mc_design_bundle(bundle)
assert not any(name == item or name.startswith(item + ".") for name in sys.modules for item in forbidden)
print(bundle.record_sha256)
print(module.cp61_stable_design_semantic_sha256(bundle))
print(hashlib.sha256(module.cp61_canonical_json_bytes(bundle)).hexdigest())
"""
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
        assert tuple(completed.stdout.splitlines()) == expected
