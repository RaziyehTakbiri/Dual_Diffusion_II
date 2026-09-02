"""Predeclared whole-seed Monte Carlo design for Formal Test 28.

The zero-argument bundle is declarative only.  It does not draw seeds, execute
requests, observe traces, construct the future ``n=2048`` intervals, or close
Formal Test 28.  A separately named, resource-capped ``n<=128`` helper merely
exercises the predeclared exact-rational interval arithmetic on calibration
inputs; it is not an observed or operational interval.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from fractions import Fraction
import hashlib
import json
from math import comb, factorial
from typing import Mapping, Optional, Tuple, cast


CP61_TEST28_WHOLE_SEED_MC_SCHEMA_VERSION = "cp61-test28-whole-seed-mc-design-v1"
CP61_TEST28_WHOLE_SEED_MC_SCOPE = (
    "prospective-external-iid-uniform-uint64-whole-seed-monte-carlo-with-"
    "replacement;paired-fixture-major-cp60-grid;bounded-external-deadline-"
    "with-timeout-censoring-distinct-from-semantic-nonreturn;predeclared-"
    "observable-first-attempt-and-selected-feature-estimands;familywise-"
    "exact-binomial-and-bounded-feature-uncertainty;stable-semantic-"
    "projection-with-raw-trace-retention;design-only-no-source-runtime-"
    "supervisor-sample-execution-interval-operational-power-confirmatory-"
    "manuscript-or-test28-closure-claim"
)
CP61_TEST28_FORMAL_TEST_28_STATUS = "OPEN"
CP61_TEST28_FIXTURE_IDS = ("T28-M1-Q", "T28-M2-Q")
CP61_TEST28_STRATEGIES = ("bounded-rejection", "fixed-budget-sir")
CP61_TEST28_REJECTION_BUDGET_GRID = (1, 4, 16, 64)
CP61_TEST28_SIR_BUDGET_GRID = (8, 32, 128, 512)
CP61_TEST28_ROW_COUNT = 16
CP61_TEST28_EXTERNAL_SEED_COUNT = 2_048
CP61_TEST28_PLAN_SEED_BITS = 64
CP61_TEST28_DEADLINE_SECONDS = 300
CP61_TEST28_OBSERVABLE_ESTIMAND_COUNT = 72
CP61_TEST28_REJECTION_FIRST_ATTEMPT_ESTIMAND_COUNT = 170
CP61_TEST28_SELECTED_FEATURE_ESTIMAND_COUNT = 312
CP61_TEST28_ESTIMAND_COUNT = 554
CP61_TEST28_BINOMIAL_ESTIMAND_COUNT = 242
CP61_TEST28_M1_FEATURE_COUNT = 6
CP61_TEST28_M2_FEATURE_COUNT = 33
CP61_TEST28_FAMILYWISE_ERROR_BUDGET = Fraction(1, 100)
CP61_TEST28_PER_ESTIMATOR_ERROR_BUDGET = Fraction(1, 55_400)
CP61_TEST28_PER_TAIL_ERROR_BUDGET = Fraction(1, 110_800)
CP61_TEST28_CP_BISECTION_STEPS = 256
CP61_TEST28_CP_CALIBRATION_MAX_TRIAL_COUNT = 128
CP61_TEST28_MINIMUM_SELECTED_COUNT = 1_040
CP61_TEST28_FEATURE_HALFWIDTH_RANGE_MULTIPLIER = Fraction(3, 40)
CP61_TEST28_HOEFFDING_EXPONENT = Fraction(117, 10)
CP61_TEST28_TAYLOR_MAXIMUM_DEGREE = 17
CP61_TEST28_TAYLOR_LOWER_BOUND = Fraction(
    428_914_006_377_131_589_846_189_933_005_011,
    3_753_164_800_000_000_000_000_000_000,
)
CP61_TEST28_TOTAL_REQUEST_COUNT = 32_768
CP61_TEST28_REJECTION_PROPOSAL_SLOT_COUNT = 348_160
CP61_TEST28_SIR_PROPOSAL_SLOT_COUNT = 2_785_280
CP61_TEST28_TOTAL_PROPOSAL_SLOT_COUNT = 3_133_440
CP61_TEST28_SIR_RESAMPLING_DRAW_COUNT = 16_384
CP61_TEST28_MAX_EVENT_OCCURRENCE_COUNT = 4_700_160
CP61_TEST28_MAX_COORDINATE_COUNT = 7_833_600
CP61_TEST28_CP58_SOURCE_SHA256 = (
    "24649278e40c49bb1c7eae0f3b00a3c5694020844b986aa836b98c02c3024822"
)
CP61_TEST28_CP60_SOURCE_SHA256 = (
    "493c4ad27a7b07aa6ad9f2894656a0dd37616f8cf54f010cd2050871783294a6"
)
CP61_TEST28_CP60_BUNDLE_SHA256 = (
    "ae105e4f9689dc6ee06fbaf1f2c697b08db2b1256225e5d348a5b82afcbd7d4a"
)
CP61_TEST28_M1_FEATURE_REGISTRY_SHA256 = (
    "314a54638d17f8dcb4b4313a92594306643254ab4a958aeb9d81efd5786a0406"
)
CP61_TEST28_M2_FEATURE_REGISTRY_SHA256 = (
    "e740e5927d2242aa0d945f4a252a638cae6aa4757f31ed24094c188b715929e8"
)
CP61_TEST28_REJECTION_OBSERVABLE_CELLS = (
    "returned-rejection-selected-before-deadline",
    "returned-rejection-exhausted-before-deadline",
    "preexecution-refusal-before-deadline",
    "execution-failure-before-deadline",
    "timeout-censored-at-deadline",
)
CP61_TEST28_SIR_OBSERVABLE_CELLS = (
    "returned-sir-selected-before-deadline",
    "preexecution-refusal-before-deadline",
    "execution-failure-before-deadline",
    "timeout-censored-at-deadline",
)
CP61_TEST28_STABLE_TRACE_PROJECTION_INCLUDED_SEMANTICS = (
    "stable-request-digest-and-fixture-strategy-budget-plan-seed",
    "stable-local-source-and-facade-provider-certificate-digests",
    "reference-and-source-parameter-digests",
    "role-context-and-stable-runtime-record",
    "derived-role-seeds-and-rng-state-hashes",
    "canonical-configuration-values-with-binary64-bytes",
    "independently-recomputed-provider-and-configuration-digests",
    "exact-q-delta-quota-certificate-decision-word-and-acceptance-records",
    "every-rejection-attempt-slot-or-complete-sir-cloud-score-weight-bytes-"
    "ess-and-resampling-record",
    "closed-outcome-status-and-failure-code",
)
CP61_TEST28_STABLE_TRACE_PROJECTION_EXCLUDED_CUSTODY = (
    "raw-runtime-identity-and-object-identity-fields",
    "address-bearing-representations-and-unbounded-exception-text",
    "plan-sha256",
    "kernel-owner-and-execution-certificate-sha256",
    "nested-scored-attempt-particle-and-result-hashes-that-inherit-runtime-" "identity",
)
CP61_TEST28_STABLE_TRACE_PROJECTION_FORMULA = (
    "project each future retained raw trace to every stable request, source, "
    "facade-provider, runtime, RNG-state, configuration-value, exact-score, "
    "quota/word/acceptance and complete strategy-trace semantic field plus the "
    "closed status/failure code; exclude only raw runtime/object identities,"
    " address-bearing repr, plan and owner/execution-certificate hashes, and "
    "nested/result hashes inheriting those identities; never discard raw trace"
)
CP61_TEST28_COMPACT_ESTIMAND_PROJECTION_SEMANTICS = (
    "fixture-id-strategy-budget-row-key",
    "deadline-scoped-observable-cell-tag-with-timeout-at-deadline",
    "optional-one-based-rejection-first-attempt",
    "optional-cp58-feature-id-bounds-and-exact-selected-feature-value",
)
CP61_TEST28_INFRASTRUCTURE_FAILURE_POLICY = (
    "any future supervisor, seed-source, durable-recording, or trace-custody "
    "infrastructure failure invalidates the entire Monte Carlo attempt before "
    "any interval;it is never an estimand cell, execution failure, timeout, "
    "dropped draw, retry, replacement, or top-up;the observable-cell partition "
    "is conditional on infrastructure fidelity"
)
CP61_TEST28_CP_INTERVAL_FORMULA = (
    "for X~Binomial(n,p), lower=0 when k=0;otherwise initialize lo=0,hi=1 "
    "and perform exactly 256 updates with mid=(lo+hi)/2 and exact-rational "
    "T=P_mid(X>=k):if T<delta set lo=mid,else including equality set hi=mid;"
    "publish lower=lo;upper=1 when k=n;otherwise initialize lo=0,hi=1 and "
    "perform exactly 256 updates with mid=(lo+hi)/2 and exact-rational "
    "C=P_mid(X<=k):if C>delta set lo=mid,else including equality set hi=mid;"
    "publish upper=hi"
)
CP61_TEST28_FEATURE_INTERVAL_FORMULA = (
    "when selected count K>=1040, clip sample-feature-mean plus-or-minus "
    "3/40 times the frozen feature range to that feature's exact bounds;"
    "otherwise publish no feature interval and retain insufficient-selection"
)
CP61_TEST28_HOEFFDING_EXPONENT_FORMULA = "2*Kmin*(3/40)^2=2*1040*9/1600=117/10"
CP61_TEST28_TAYLOR_LOWER_BOUND_FORMULA = (
    "sum_{j=0}^{17}(117/10)^j/j!="
    "428914006377131589846189933005011/"
    "3753164800000000000000000000>110800"
)

_ZERO_SHA256 = "0" * 64
_MAX_CANONICAL_NODES = 131_072
_MAX_CANONICAL_DEPTH = 32
_MAX_CANONICAL_TEXT_BYTES = 8_388_608
_MAX_CANONICAL_OUTPUT_BYTES = 16_777_216
_MAX_TEXT_BYTES = 4_096
_MAX_INTEGER_BITS = 16_384
_MAX_FRACTION_BITS = 16_384
_ALLOW_RECORD_CLASS_DEFINITION = True

_CP60_ROW_INVENTORY = (
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

_CP58_M1_FEATURES = (
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

_CP58_M2_FEATURES = (
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


class _SealedRecord:
    __slots__ = ()

    def __init_subclass__(cls, **kwargs: object) -> None:
        del cls, kwargs
        if not _ALLOW_RECORD_CLASS_DEFINITION:
            raise TypeError("the CP61 sealed-record base cannot be subclassed")

    def __init__(self, *args: object, **kwargs: object) -> None:
        del args, kwargs
        raise TypeError("CP61 records are module-created")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP61 records are not pickle objects")


@dataclass(frozen=True, eq=False, init=False, slots=True)
class CP61StableTraceProjectionContractV1(_SealedRecord):
    schema_version: str
    projection_id: str
    projection_formula: str
    included_semantics: Tuple[str, ...]
    excluded_volatile_custody: Tuple[str, ...]
    future_raw_trace_retention_required: bool
    raw_trace_digest_only_permitted: bool
    stable_projection_replaces_raw_trace: bool
    full_stable_trace_projection_required: bool
    stable_request_digest_retention_required: bool
    stable_facade_provider_certificate_digest_retention_required: bool
    stable_runtime_record_retention_required: bool
    plan_seed_and_derived_rng_state_retention_required: bool
    runtime_identifiers_in_semantic_projection: bool
    volatile_plan_certificate_nested_result_hashes_in_semantic_projection: bool
    compact_estimand_projection_is_full_stable_trace: bool
    full_trace_law_estimated: bool
    total_variation_estimated: bool
    projection_instantiated_on_observed_traces: bool
    cross_process_projection_parity_verified: bool
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP61StableTraceProjectionContractV1 cannot be subclassed")


@dataclass(frozen=True, eq=False, init=False, slots=True)
class CP61MCRowDesignV1(_SealedRecord):
    schema_version: str
    row_ordinal: int
    fixture_id: str
    strategy: str
    budget: int
    cp60_bundle_sha256: str
    cp60_request_template_sha256: str
    cp60_definition_record_sha256: str
    cp58_feature_registry_sha256: str
    stable_trace_projection_contract_sha256: str
    observable_cell_labels: Tuple[str, ...]
    observable_estimand_ordinals: Tuple[int, ...]
    first_attempt_estimand_ordinals: Tuple[int, ...]
    selected_feature_estimand_ordinals: Tuple[int, ...]
    selected_feature_ids: Tuple[str, ...]
    selected_feature_lower_bounds: Tuple[Fraction, ...]
    selected_feature_upper_bounds: Tuple[Fraction, ...]
    external_seed_count: int
    deadline_seconds: int
    same_seed_ordinal_reuse_across_rows_required: bool
    cross_row_pairing_required_without_independence: bool
    volatile_runtime_or_result_hashes_semantically_authoritative: bool
    compact_row_semantic_sha256: str
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP61MCRowDesignV1 cannot be subclassed")


@dataclass(frozen=True, eq=False, init=False, slots=True)
class CP61EstimandV1(_SealedRecord):
    schema_version: str
    estimand_ordinal: int
    estimand_id: str
    estimand_family: str
    row_ordinal: int
    fixture_id: str
    strategy: str
    budget: int
    observable_cell_label: Optional[str]
    first_attempt_one_based: Optional[int]
    feature_id: Optional[str]
    feature_lower_bound: Optional[Fraction]
    feature_upper_bound: Optional[Fraction]
    feature_range: Optional[Fraction]
    target_feature_halfwidth: Optional[Fraction]
    cp60_definition_record_sha256: str
    cp58_feature_registry_sha256: Optional[str]
    cp58_feature_definition_sha256: Optional[str]
    denominator_mode: str
    minimum_denominator_count: int
    uncertainty_method: str
    deadline_scoped_observation: bool
    observed_before_deadline_only: bool
    returned_before_deadline_only: bool
    timeout_censored_at_deadline: bool
    validated_return_before_deadline_required: bool
    timeout_censored_is_semantic_nonreturn: bool
    conditional_on_selected: bool
    familywise_error_budget: Fraction
    per_estimator_error_budget: Fraction
    per_tail_error_budget: Fraction
    stable_trace_projection_contract_sha256: str
    estimate_observed: bool
    interval_computed: bool
    compact_estimand_semantic_sha256: str
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP61EstimandV1 cannot be subclassed")


@dataclass(frozen=True, eq=False, init=False, slots=True)
class CP61MultiplicityAndPrecisionV1(_SealedRecord):
    schema_version: str
    estimand_count: int
    binomial_estimand_count: int
    selected_feature_estimand_count: int
    familywise_error_budget: Fraction
    per_estimator_error_budget: Fraction
    per_tail_error_budget: Fraction
    bonferroni_estimator_sum: Fraction
    bonferroni_tail_sum: Fraction
    clopper_pearson_interval_formula: str
    clopper_pearson_bisection_steps: int
    public_cp_calibration_max_trial_count: int
    clopper_pearson_exact_rational_tail_evaluation: bool
    clopper_pearson_outward_rounding: bool
    zero_success_upper_endpoint_strictly_positive: bool
    all_success_lower_endpoint_strictly_less_than_one: bool
    minimum_selected_count: int
    feature_halfwidth_formula: str
    feature_halfwidth_range_multiplier: Fraction
    hoeffding_exponent_formula: str
    hoeffding_exponent_at_minimum_count: Fraction
    taylor_lower_bound_formula: str
    taylor_maximum_degree: int
    exp_exponent_taylor_lower_bound: Fraction
    reciprocal_per_tail_error_budget: int
    taylor_lower_bound_exceeds_reciprocal_tail_budget: bool
    bounded_feature_one_sided_tail_bound_strictly_below_per_tail_budget: bool
    bounded_feature_two_sided_failure_strictly_below_per_estimator_budget: bool
    below_minimum_selected_count_produces_no_interval: bool
    future_interval_algorithm_predeclared: bool
    future_n2048_intervals_computed: bool
    intervals_computed: bool
    simultaneous_coverage_realized: bool
    power_guarantee_claimed: bool
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP61MultiplicityAndPrecisionV1 cannot be subclassed")


@dataclass(frozen=True, eq=False, init=False, slots=True)
class CP61ResourceBudgetV1(_SealedRecord):
    schema_version: str
    external_seed_count: int
    row_count: int
    total_request_count: int
    rejection_proposal_slot_count: int
    sir_proposal_slot_count: int
    total_proposal_slot_count: int
    sir_resampling_draw_count: int
    maximum_event_occurrence_count: int
    maximum_coordinate_count: int
    request_count_formula: str
    proposal_slot_count_formula: str
    event_occurrence_count_formula: str
    coordinate_count_formula: str
    resource_caps_predeclared: bool
    total_request_count_is_scheduled: bool
    proposal_slot_counts_are_planned_maxima_not_observed: bool
    sir_resampling_draw_count_is_planned_maximum_not_observed: bool
    event_and_coordinate_counts_are_planned_maxima_not_observed: bool
    resources_allocated: bool
    execution_performed: bool
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP61ResourceBudgetV1 cannot be subclassed")


@dataclass(frozen=True, eq=False, init=False, slots=True)
class CP61WholeSeedMCDesignBundleV1(_SealedRecord):
    schema_version: str
    scope: str
    cp58_source_sha256: str
    cp60_source_sha256: str
    cp60_bundle_sha256: str
    m1_feature_registry_sha256: str
    m2_feature_registry_sha256: str
    stable_trace_projection_contract: CP61StableTraceProjectionContractV1
    ordered_rows: Tuple[CP61MCRowDesignV1, ...]
    observable_estimands: Tuple[CP61EstimandV1, ...]
    rejection_first_attempt_estimands: Tuple[CP61EstimandV1, ...]
    selected_conditional_feature_estimands: Tuple[CP61EstimandV1, ...]
    multiplicity_and_precision: CP61MultiplicityAndPrecisionV1
    resource_budget: CP61ResourceBudgetV1
    fixture_ids: Tuple[str, ...]
    rejection_budget_grid: Tuple[int, ...]
    sir_budget_grid: Tuple[int, ...]
    seed_ordinals: Tuple[int, ...]
    external_seed_count: int
    external_seed_bits: int
    external_seed_sampling_mode: str
    same_seed_ordinal_reuse_across_all_rows_required: bool
    external_seed_draws_iid_uniform_uint64_with_replacement_required: bool
    duplicate_seed_value_retention_required: bool
    duplicate_seed_value_retry_permitted: bool
    outcome_dropping_permitted: bool
    sample_topup_permitted: bool
    cross_row_outcomes_assumed_independent: bool
    deadline_seconds: int
    timeout_censoring_retention_required: bool
    timeout_censored_identified_with_semantic_nonreturn: bool
    predeclared_design_only: bool
    predecessor_inventories_hardcoded: bool
    predecessor_source_and_record_hashes_are_frozen_custody_bindings: bool
    cp58_or_cp60_imported_or_loaded_by_builder: bool
    live_predecessor_parity_verified_by_builder: bool
    infrastructure_failure_policy: str
    infrastructure_failure_invalidates_entire_mc_attempt: bool
    infrastructure_failure_is_estimand_cell: bool
    infrastructure_failure_folded_into_execution_failure: bool
    infrastructure_failure_folded_into_timeout_censoring: bool
    infrastructure_failure_draw_retried_replaced_or_topped_up: bool
    observable_cell_partition_requires_infrastructure_fidelity: bool
    infrastructure_fidelity_verified: bool
    requests_fully_bound: bool
    runtime_fully_bound: bool
    source_capsule_fully_bound: bool
    external_supervisor_fully_bound: bool
    external_seed_source_verified: bool
    cross_ordinal_iid_uniformity_verified: bool
    current_fixed_hash_seed_plan_is_external_iid_seed_sample: bool
    seed_sample_recorded: bool
    raw_trace_sample_recorded: bool
    requests_executed: bool
    intervals_computed: bool
    operational_predictions_derived: bool
    full_trace_law_estimated: bool
    total_variation_estimated: bool
    power_guarantee_claimed: bool
    confirmatory_evidence: bool
    manuscript_claim_promoted: bool
    formal_test_28_status: str
    formal_test_28_closed: bool
    stable_design_semantic_digest_binds_predecessor_sources_and_registries: bool
    stable_design_semantic_digest_excludes_volatile_identity_hashes: bool
    stable_design_semantic_digest_is_full_trace_law_digest: bool
    stable_design_semantic_sha256: str
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP61WholeSeedMCDesignBundleV1 cannot be subclassed")


_ALLOW_RECORD_CLASS_DEFINITION = False
_RECORD_TYPE_TAGS = {
    CP61StableTraceProjectionContractV1: "stable-trace-projection-contract-v1",
    CP61MCRowDesignV1: "mc-row-design-v1",
    CP61EstimandV1: "estimand-v1",
    CP61MultiplicityAndPrecisionV1: "multiplicity-and-precision-v1",
    CP61ResourceBudgetV1: "resource-budget-v1",
    CP61WholeSeedMCDesignBundleV1: "whole-seed-mc-design-bundle-v1",
}


def _seal(cls: type, values: Mapping[str, object]) -> object:
    if set(values) != {item.name for item in fields(cls)}:
        raise TypeError("sealed CP61 record field set differs")
    result = object.__new__(cls)
    for name, value in values.items():
        object.__setattr__(result, name, value)
    return result


def _text(value: object, name: str, maximum: int = _MAX_TEXT_BYTES) -> str:
    if type(value) is not str:
        raise TypeError(name + " must be exact text")
    if not value or len(value) > maximum:
        raise ValueError(name + " must be bounded nonempty text")
    if len(value.encode("utf-8")) > maximum:
        raise ValueError(name + " must be bounded nonempty text")
    return value


def _sha256(value: object, name: str) -> str:
    checked = _text(value, name, 64)
    if len(checked) != 64 or any(c not in "0123456789abcdef" for c in checked):
        raise ValueError(name + " must be lowercase SHA-256 text")
    return checked


def _integer(value: object, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int:
        raise TypeError(name + " must be an exact integer")
    if value < minimum or value > maximum:
        raise ValueError(name + " is outside its frozen range")
    return value


def _fraction(value: object, name: str) -> Fraction:
    if type(value) is not Fraction:
        raise TypeError(name + " must be an exact Fraction")
    if (
        value.numerator.bit_length() > _MAX_FRACTION_BITS
        or value.denominator.bit_length() > _MAX_FRACTION_BITS
    ):
        raise ValueError(name + " exceeds the exact arithmetic bit bound")
    return value


def _exact_tuple(
    value: object, name: str, minimum: int = 0, maximum: int = 4_096
) -> tuple:
    if type(value) is not tuple:
        raise TypeError(name + " must be an exact tuple")
    if len(value) < minimum or len(value) > maximum:
        raise ValueError(name + " has an invalid bounded length")
    return value


def _canonical(value: object, *, depth: int = 0) -> object:
    if depth > _MAX_CANONICAL_DEPTH:
        raise ValueError("canonical value exceeds the depth bound")
    if value is None or type(value) is bool:
        return value
    if type(value) is str:
        if len(value) > _MAX_TEXT_BYTES:
            raise ValueError("canonical text exceeds the character bound")
        if len(value.encode("utf-8")) > _MAX_TEXT_BYTES:
            raise ValueError("canonical text exceeds the byte bound")
        return value
    if type(value) is int:
        if value.bit_length() > _MAX_INTEGER_BITS:
            raise ValueError("canonical integer exceeds the bit bound")
        return {
            "cp61_exact_integer_hex": ("-" if value < 0 else "+")
            + format(abs(value), "x")
        }
    if type(value) is Fraction:
        _fraction(value, "canonical Fraction")
        return {
            "cp61_exact_fraction_v1": {
                "numerator": _canonical(value.numerator, depth=depth + 1),
                "denominator": _canonical(value.denominator, depth=depth + 1),
            }
        }
    if type(value) is tuple:
        if len(value) > 4_096:
            raise ValueError("canonical tuple exceeds the item bound")
        return [_canonical(item, depth=depth + 1) for item in value]
    if type(value) is dict:
        if len(value) > 4_096:
            raise ValueError("canonical mapping exceeds the item bound")
        if not all(type(key) is str for key in value):
            raise TypeError("canonical mapping keys must be exact text")
        return {key: _canonical(value[key], depth=depth + 1) for key in sorted(value)}
    record_type = type(value)
    if record_type in _RECORD_TYPE_TAGS:
        return {
            "cp61_record_type": _RECORD_TYPE_TAGS[record_type],
            "fields": {
                item.name: _canonical(getattr(value, item.name), depth=depth + 1)
                for item in fields(record_type)
            },
        }
    raise TypeError("unsupported CP61 canonical value")


def _preflight_canonical(value: object) -> None:
    stack = [(value, 0)]
    nodes = 0
    text_bytes = 0
    while stack:
        current, depth = stack.pop()
        nodes += 1
        if nodes > _MAX_CANONICAL_NODES:
            raise ValueError("canonical value exceeds the node bound")
        if depth > _MAX_CANONICAL_DEPTH:
            raise ValueError("canonical value exceeds the depth bound")
        if current is None or type(current) is bool:
            continue
        if type(current) is str:
            if len(current) > _MAX_CANONICAL_TEXT_BYTES:
                raise ValueError("canonical text payload exceeds its bound")
            text_bytes += len(current.encode("utf-8"))
        elif type(current) is int:
            if current.bit_length() > _MAX_INTEGER_BITS:
                raise ValueError("canonical integer exceeds the bit bound")
        elif type(current) is Fraction:
            _fraction(current, "canonical Fraction")
        elif type(current) is tuple:
            if len(current) > 4_096:
                raise ValueError("canonical tuple exceeds the item bound")
            stack.extend((item, depth + 1) for item in current)
        elif type(current) is dict:
            if len(current) > 4_096:
                raise ValueError("canonical mapping exceeds the item bound")
            for key, item in current.items():
                if type(key) is not str:
                    raise TypeError("canonical mapping keys must be exact text")
                if len(key) > _MAX_TEXT_BYTES:
                    raise ValueError("canonical mapping key exceeds its bound")
                text_bytes += len(key.encode("utf-8"))
                stack.append((item, depth + 1))
        elif type(current) in _RECORD_TYPE_TAGS:
            children = []
            for item in fields(type(current)):
                try:
                    child = getattr(current, item.name)
                except AttributeError as error:
                    raise TypeError("CP61 record is missing a sealed field") from error
                children.append((child, depth + 1))
            stack.extend(children)
        else:
            raise TypeError("unsupported CP61 canonical value")
        if text_bytes > _MAX_CANONICAL_TEXT_BYTES:
            raise ValueError("canonical text payload exceeds its bound")


def _canonical_bytes(value: object) -> bytes:
    _preflight_canonical(value)
    result = json.dumps(
        _canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    if len(result) > _MAX_CANONICAL_OUTPUT_BYTES:
        raise ValueError("canonical JSON exceeds the output bound")
    return result


def _digest(kind: str, values: Mapping[str, object]) -> str:
    payload = dict(values)
    if "record_sha256" in payload:
        payload["record_sha256"] = _ZERO_SHA256
    return hashlib.sha256(
        b"cp61-test28-whole-seed-mc-design-v1\x00"
        + _text(kind, "digest domain", 96).encode("ascii")
        + b"\x00"
        + _canonical_bytes(payload)
    ).hexdigest()


def _binomial_tail_numerator(
    numerator: int,
    denominator: int,
    trial_count: int,
    start: int,
    stop: int,
) -> int:
    complement = denominator - numerator
    term = (
        comb(trial_count, start)
        * numerator**start
        * complement ** (trial_count - start)
    )
    total = term
    for count in range(start, stop):
        dividend = term * (trial_count - count) * numerator
        divisor = (count + 1) * complement
        term, remainder = divmod(dividend, divisor)
        if remainder:
            raise AssertionError("exact binomial adjacent-term recurrence failed")
        total += term
    return total


def _tail_compare_delta(
    probability: Fraction,
    trial_count: int,
    start: int,
    stop: int,
) -> int:
    tail_numerator = _binomial_tail_numerator(
        probability.numerator,
        probability.denominator,
        trial_count,
        start,
        stop,
    )
    left = tail_numerator * CP61_TEST28_PER_TAIL_ERROR_BUDGET.denominator
    right = (
        CP61_TEST28_PER_TAIL_ERROR_BUDGET.numerator
        * probability.denominator**trial_count
    )
    return (left > right) - (left < right)


def cp61_exact_clopper_pearson_outward_calibration_interval(
    success_count: object, trial_count: object
) -> Tuple[Fraction, Fraction]:
    """Exercise the exact CP algorithm on a bounded calibration problem."""

    n = _integer(
        trial_count,
        "trial_count",
        1,
        CP61_TEST28_CP_CALIBRATION_MAX_TRIAL_COUNT,
    )
    k = _integer(success_count, "success_count", 0, n)
    if k == 0:
        lower = Fraction(0, 1)
    else:
        lo, hi = Fraction(0, 1), Fraction(1, 1)
        for _ in range(CP61_TEST28_CP_BISECTION_STEPS):
            mid = (lo + hi) / 2
            if _tail_compare_delta(mid, n, k, n) < 0:
                lo = mid
            else:
                hi = mid
        lower = lo
    if k == n:
        upper = Fraction(1, 1)
    else:
        lo, hi = Fraction(0, 1), Fraction(1, 1)
        for _ in range(CP61_TEST28_CP_BISECTION_STEPS):
            mid = (lo + hi) / 2
            if _tail_compare_delta(mid, n, 0, k) > 0:
                lo = mid
            else:
                hi = mid
        upper = hi
    return lower, upper


def _make_record(cls: type, kind: str, values: Mapping[str, object]) -> object:
    payload = dict(values)
    payload["record_sha256"] = _ZERO_SHA256
    payload["record_sha256"] = _digest(kind, payload)
    return _seal(cls, payload)


def _build_stable_trace_projection_contract() -> CP61StableTraceProjectionContractV1:
    values = {
        "schema_version": CP61_TEST28_WHOLE_SEED_MC_SCHEMA_VERSION,
        "projection_id": "cp61-future-full-stable-whole-seed-trace-v1",
        "projection_formula": CP61_TEST28_STABLE_TRACE_PROJECTION_FORMULA,
        "included_semantics": (CP61_TEST28_STABLE_TRACE_PROJECTION_INCLUDED_SEMANTICS),
        "excluded_volatile_custody": (
            CP61_TEST28_STABLE_TRACE_PROJECTION_EXCLUDED_CUSTODY
        ),
        "future_raw_trace_retention_required": True,
        "raw_trace_digest_only_permitted": False,
        "stable_projection_replaces_raw_trace": False,
        "full_stable_trace_projection_required": True,
        "stable_request_digest_retention_required": True,
        "stable_facade_provider_certificate_digest_retention_required": True,
        "stable_runtime_record_retention_required": True,
        "plan_seed_and_derived_rng_state_retention_required": True,
        "runtime_identifiers_in_semantic_projection": False,
        "volatile_plan_certificate_nested_result_hashes_in_semantic_projection": (
            False
        ),
        "compact_estimand_projection_is_full_stable_trace": False,
        "full_trace_law_estimated": False,
        "total_variation_estimated": False,
        "projection_instantiated_on_observed_traces": False,
        "cross_process_projection_parity_verified": False,
    }
    return cast(
        CP61StableTraceProjectionContractV1,
        _make_record(
            CP61StableTraceProjectionContractV1,
            "stable-trace-projection-contract",
            values,
        ),
    )


def _build_multiplicity_and_precision() -> CP61MultiplicityAndPrecisionV1:
    exponent = (
        2
        * CP61_TEST28_MINIMUM_SELECTED_COUNT
        * CP61_TEST28_FEATURE_HALFWIDTH_RANGE_MULTIPLIER**2
    )
    taylor = sum(
        (
            exponent**degree / factorial(degree)
            for degree in range(CP61_TEST28_TAYLOR_MAXIMUM_DEGREE + 1)
        ),
        Fraction(0, 1),
    )
    if (
        exponent != CP61_TEST28_HOEFFDING_EXPONENT
        or taylor != CP61_TEST28_TAYLOR_LOWER_BOUND
        or taylor <= 110_800
        or CP61_TEST28_ESTIMAND_COUNT * CP61_TEST28_PER_ESTIMATOR_ERROR_BUDGET
        != CP61_TEST28_FAMILYWISE_ERROR_BUDGET
        or 2 * CP61_TEST28_ESTIMAND_COUNT * CP61_TEST28_PER_TAIL_ERROR_BUDGET
        != CP61_TEST28_FAMILYWISE_ERROR_BUDGET
    ):
        raise AssertionError("frozen Taylor lower-bound arithmetic differs")
    values = {
        "schema_version": CP61_TEST28_WHOLE_SEED_MC_SCHEMA_VERSION,
        "estimand_count": CP61_TEST28_ESTIMAND_COUNT,
        "binomial_estimand_count": CP61_TEST28_BINOMIAL_ESTIMAND_COUNT,
        "selected_feature_estimand_count": (
            CP61_TEST28_SELECTED_FEATURE_ESTIMAND_COUNT
        ),
        "familywise_error_budget": CP61_TEST28_FAMILYWISE_ERROR_BUDGET,
        "per_estimator_error_budget": CP61_TEST28_PER_ESTIMATOR_ERROR_BUDGET,
        "per_tail_error_budget": CP61_TEST28_PER_TAIL_ERROR_BUDGET,
        "bonferroni_estimator_sum": (
            CP61_TEST28_ESTIMAND_COUNT * CP61_TEST28_PER_ESTIMATOR_ERROR_BUDGET
        ),
        "bonferroni_tail_sum": (
            2 * CP61_TEST28_ESTIMAND_COUNT * CP61_TEST28_PER_TAIL_ERROR_BUDGET
        ),
        "clopper_pearson_interval_formula": CP61_TEST28_CP_INTERVAL_FORMULA,
        "clopper_pearson_bisection_steps": CP61_TEST28_CP_BISECTION_STEPS,
        "public_cp_calibration_max_trial_count": (
            CP61_TEST28_CP_CALIBRATION_MAX_TRIAL_COUNT
        ),
        "clopper_pearson_exact_rational_tail_evaluation": True,
        "clopper_pearson_outward_rounding": True,
        "zero_success_upper_endpoint_strictly_positive": True,
        "all_success_lower_endpoint_strictly_less_than_one": True,
        "minimum_selected_count": CP61_TEST28_MINIMUM_SELECTED_COUNT,
        "feature_halfwidth_formula": CP61_TEST28_FEATURE_INTERVAL_FORMULA,
        "feature_halfwidth_range_multiplier": (
            CP61_TEST28_FEATURE_HALFWIDTH_RANGE_MULTIPLIER
        ),
        "hoeffding_exponent_formula": CP61_TEST28_HOEFFDING_EXPONENT_FORMULA,
        "hoeffding_exponent_at_minimum_count": exponent,
        "taylor_lower_bound_formula": CP61_TEST28_TAYLOR_LOWER_BOUND_FORMULA,
        "taylor_maximum_degree": CP61_TEST28_TAYLOR_MAXIMUM_DEGREE,
        "exp_exponent_taylor_lower_bound": taylor,
        "reciprocal_per_tail_error_budget": 110_800,
        "taylor_lower_bound_exceeds_reciprocal_tail_budget": True,
        "bounded_feature_one_sided_tail_bound_strictly_below_per_tail_budget": (True),
        "bounded_feature_two_sided_failure_strictly_below_per_estimator_budget": (True),
        "below_minimum_selected_count_produces_no_interval": True,
        "future_interval_algorithm_predeclared": True,
        "future_n2048_intervals_computed": False,
        "intervals_computed": False,
        "simultaneous_coverage_realized": False,
        "power_guarantee_claimed": False,
    }
    return cast(
        CP61MultiplicityAndPrecisionV1,
        _make_record(
            CP61MultiplicityAndPrecisionV1, "multiplicity-and-precision", values
        ),
    )


def _build_resource_budget() -> CP61ResourceBudgetV1:
    requests = CP61_TEST28_EXTERNAL_SEED_COUNT * CP61_TEST28_ROW_COUNT
    rejection_slots = (
        CP61_TEST28_EXTERNAL_SEED_COUNT
        * len(CP61_TEST28_FIXTURE_IDS)
        * sum(CP61_TEST28_REJECTION_BUDGET_GRID)
    )
    sir_slots = (
        CP61_TEST28_EXTERNAL_SEED_COUNT
        * len(CP61_TEST28_FIXTURE_IDS)
        * sum(CP61_TEST28_SIR_BUDGET_GRID)
    )
    resampling_draws = CP61_TEST28_EXTERNAL_SEED_COUNT * 8
    slots_per_fixture = sum(CP61_TEST28_REJECTION_BUDGET_GRID) + sum(
        CP61_TEST28_SIR_BUDGET_GRID
    )
    event_occurrences = CP61_TEST28_EXTERNAL_SEED_COUNT * slots_per_fixture * (1 + 2)
    coordinates = CP61_TEST28_EXTERNAL_SEED_COUNT * slots_per_fixture * (1 + 4)
    if (
        requests != CP61_TEST28_TOTAL_REQUEST_COUNT
        or rejection_slots != CP61_TEST28_REJECTION_PROPOSAL_SLOT_COUNT
        or sir_slots != CP61_TEST28_SIR_PROPOSAL_SLOT_COUNT
        or rejection_slots + sir_slots != CP61_TEST28_TOTAL_PROPOSAL_SLOT_COUNT
        or resampling_draws != CP61_TEST28_SIR_RESAMPLING_DRAW_COUNT
        or event_occurrences != CP61_TEST28_MAX_EVENT_OCCURRENCE_COUNT
        or coordinates != CP61_TEST28_MAX_COORDINATE_COUNT
    ):
        raise AssertionError("frozen proposal-slot resource arithmetic differs")
    values = {
        "schema_version": CP61_TEST28_WHOLE_SEED_MC_SCHEMA_VERSION,
        "external_seed_count": CP61_TEST28_EXTERNAL_SEED_COUNT,
        "row_count": CP61_TEST28_ROW_COUNT,
        "total_request_count": requests,
        "rejection_proposal_slot_count": rejection_slots,
        "sir_proposal_slot_count": sir_slots,
        "total_proposal_slot_count": rejection_slots + sir_slots,
        "sir_resampling_draw_count": resampling_draws,
        "maximum_event_occurrence_count": event_occurrences,
        "maximum_coordinate_count": coordinates,
        "request_count_formula": "2048 external seed ordinals times 16 rows",
        "proposal_slot_count_formula": (
            "2048 times 2 fixtures times (1+4+16+64) rejection slots plus "
            "2048 times 2 fixtures times (8+32+128+512) SIR slots"
        ),
        "event_occurrence_count_formula": (
            "proposal slots weighted by fixture count caps M1=1 and M2=2"
        ),
        "coordinate_count_formula": (
            "proposal slots weighted by maximum coordinates per configuration "
            "M1=1 and M2=4"
        ),
        "resource_caps_predeclared": True,
        "total_request_count_is_scheduled": True,
        "proposal_slot_counts_are_planned_maxima_not_observed": True,
        "sir_resampling_draw_count_is_planned_maximum_not_observed": True,
        "event_and_coordinate_counts_are_planned_maxima_not_observed": True,
        "resources_allocated": False,
        "execution_performed": False,
    }
    return cast(
        CP61ResourceBudgetV1,
        _make_record(CP61ResourceBudgetV1, "resource-budget", values),
    )


def _row_key(row_ordinal: int, fixture_id: str, strategy: str, budget: int) -> str:
    return "row-%02d/%s/%s/budget-%d" % (
        row_ordinal,
        fixture_id,
        strategy,
        budget,
    )


def _feature_inventory(fixture_id: str) -> tuple:
    if fixture_id == "T28-M1-Q":
        raw = _CP58_M1_FEATURES
        registry_sha256 = CP61_TEST28_M1_FEATURE_REGISTRY_SHA256
    elif fixture_id == "T28-M2-Q":
        raw = _CP58_M2_FEATURES
        registry_sha256 = CP61_TEST28_M2_FEATURE_REGISTRY_SHA256
    else:
        raise AssertionError("frozen feature fixture differs")
    return registry_sha256, tuple(
        (feature_id, Fraction(lower, 1), Fraction(upper, 1), feature_sha256)
        for feature_id, lower, upper, feature_sha256 in raw
    )


def _estimand_compact_payload(value: CP61EstimandV1) -> dict:
    return {
        "schema_version": value.schema_version,
        "estimand_ordinal": value.estimand_ordinal,
        "estimand_id": value.estimand_id,
        "estimand_family": value.estimand_family,
        "row_ordinal": value.row_ordinal,
        "fixture_id": value.fixture_id,
        "strategy": value.strategy,
        "budget": value.budget,
        "observable_cell_label": value.observable_cell_label,
        "first_attempt_one_based": value.first_attempt_one_based,
        "feature_id": value.feature_id,
        "feature_lower_bound": value.feature_lower_bound,
        "feature_upper_bound": value.feature_upper_bound,
        "feature_range": value.feature_range,
        "target_feature_halfwidth": value.target_feature_halfwidth,
        "denominator_mode": value.denominator_mode,
        "minimum_denominator_count": value.minimum_denominator_count,
        "uncertainty_method": value.uncertainty_method,
        "deadline_scoped_observation": value.deadline_scoped_observation,
        "observed_before_deadline_only": value.observed_before_deadline_only,
        "returned_before_deadline_only": value.returned_before_deadline_only,
        "timeout_censored_at_deadline": value.timeout_censored_at_deadline,
        "validated_return_before_deadline_required": (
            value.validated_return_before_deadline_required
        ),
        "timeout_censored_is_semantic_nonreturn": (
            value.timeout_censored_is_semantic_nonreturn
        ),
        "conditional_on_selected": value.conditional_on_selected,
        "familywise_error_budget": value.familywise_error_budget,
        "per_estimator_error_budget": value.per_estimator_error_budget,
        "per_tail_error_budget": value.per_tail_error_budget,
        "compact_projection_semantics": (
            CP61_TEST28_COMPACT_ESTIMAND_PROJECTION_SEMANTICS
        ),
    }


def _build_estimand(
    *,
    ordinal: int,
    row_ordinal: int,
    row_data: tuple,
    projection_sha256: str,
    family: str,
    observable_cell: Optional[str] = None,
    first_attempt: Optional[int] = None,
    feature: Optional[tuple] = None,
) -> CP61EstimandV1:
    fixture_id, strategy, budget, _, definition_sha256 = row_data
    row_key = _row_key(row_ordinal, fixture_id, strategy, budget)
    if family == "observable-cell":
        if observable_cell is None or first_attempt is not None or feature is not None:
            raise AssertionError("observable estimand shape differs")
        suffix = observable_cell
        feature_id = None
        lower = upper = feature_range = halfwidth = None
        registry_sha256 = feature_sha256 = None
        denominator_mode = "all-2048-external-seed-ordinals"
        minimum_count = CP61_TEST28_EXTERNAL_SEED_COUNT
        uncertainty = "clopper-pearson-exact-rational-outward-bisection"
        conditional = False
        id_family = "observable"
    elif family == "rejection-first-attempt":
        if first_attempt is None or observable_cell is not None or feature is not None:
            raise AssertionError("first-attempt estimand shape differs")
        suffix = "attempt-%d" % first_attempt
        feature_id = None
        lower = upper = feature_range = halfwidth = None
        registry_sha256 = feature_sha256 = None
        denominator_mode = "all-2048-external-seed-ordinals"
        minimum_count = CP61_TEST28_EXTERNAL_SEED_COUNT
        uncertainty = "clopper-pearson-exact-rational-outward-bisection"
        conditional = False
    elif family == "selected-conditional-feature":
        if feature is None or observable_cell is not None or first_attempt is not None:
            raise AssertionError("selected-feature estimand shape differs")
        feature_id, lower, upper, feature_sha256 = feature
        registry_sha256, _ = _feature_inventory(fixture_id)
        feature_range = upper - lower
        halfwidth = feature_range * CP61_TEST28_FEATURE_HALFWIDTH_RANGE_MULTIPLIER
        suffix = feature_id
        id_family = "selected-feature"
        denominator_mode = "predeadline-selected-count-in-this-row"
        minimum_count = CP61_TEST28_MINIMUM_SELECTED_COUNT
        uncertainty = "bounded-feature-hoeffding-fixed-range-halfwidth"
        conditional = True
    else:
        raise AssertionError("unknown frozen CP61 estimand family")
    if family == "rejection-first-attempt":
        id_family = family
    estimand_id = "cp61/%s/%s/%s" % (id_family, row_key, suffix)
    is_timeout = observable_cell == "timeout-censored-at-deadline"
    validated_return = family in (
        "rejection-first-attempt",
        "selected-conditional-feature",
    ) or observable_cell in (
        "returned-rejection-selected-before-deadline",
        "returned-rejection-exhausted-before-deadline",
        "returned-sir-selected-before-deadline",
    )
    observed_before_deadline = not is_timeout
    if is_timeout and (observed_before_deadline or validated_return):
        raise AssertionError("timeout endpoint semantics differ")
    if observable_cell in (
        "preexecution-refusal-before-deadline",
        "execution-failure-before-deadline",
    ) and (not observed_before_deadline or validated_return):
        raise AssertionError("before-deadline nonreturn semantics differ")
    if observable_cell in (
        "returned-rejection-selected-before-deadline",
        "returned-rejection-exhausted-before-deadline",
        "returned-sir-selected-before-deadline",
    ) and (not observed_before_deadline or not validated_return):
        raise AssertionError("before-deadline validated-return semantics differ")
    values = {
        "schema_version": CP61_TEST28_WHOLE_SEED_MC_SCHEMA_VERSION,
        "estimand_ordinal": ordinal,
        "estimand_id": estimand_id,
        "estimand_family": family,
        "row_ordinal": row_ordinal,
        "fixture_id": fixture_id,
        "strategy": strategy,
        "budget": budget,
        "observable_cell_label": observable_cell,
        "first_attempt_one_based": first_attempt,
        "feature_id": feature_id,
        "feature_lower_bound": lower,
        "feature_upper_bound": upper,
        "feature_range": feature_range,
        "target_feature_halfwidth": halfwidth,
        "cp60_definition_record_sha256": definition_sha256,
        "cp58_feature_registry_sha256": registry_sha256,
        "cp58_feature_definition_sha256": feature_sha256,
        "denominator_mode": denominator_mode,
        "minimum_denominator_count": minimum_count,
        "uncertainty_method": uncertainty,
        "deadline_scoped_observation": True,
        "observed_before_deadline_only": observed_before_deadline,
        "returned_before_deadline_only": validated_return,
        "timeout_censored_at_deadline": is_timeout,
        "validated_return_before_deadline_required": validated_return,
        "timeout_censored_is_semantic_nonreturn": False,
        "conditional_on_selected": conditional,
        "familywise_error_budget": CP61_TEST28_FAMILYWISE_ERROR_BUDGET,
        "per_estimator_error_budget": CP61_TEST28_PER_ESTIMATOR_ERROR_BUDGET,
        "per_tail_error_budget": CP61_TEST28_PER_TAIL_ERROR_BUDGET,
        "stable_trace_projection_contract_sha256": projection_sha256,
        "estimate_observed": False,
        "interval_computed": False,
        "compact_estimand_semantic_sha256": _ZERO_SHA256,
    }
    provisional = cast(
        CP61EstimandV1,
        _seal(CP61EstimandV1, {**values, "record_sha256": _ZERO_SHA256}),
    )
    values["compact_estimand_semantic_sha256"] = _digest(
        "compact-estimand-semantic", _estimand_compact_payload(provisional)
    )
    return cast(
        CP61EstimandV1,
        _make_record(CP61EstimandV1, "estimand", values),
    )


def _build_estimands(
    projection_sha256: str,
) -> Tuple[tuple, tuple, tuple]:
    observable = []
    ordinal = 1
    for row_ordinal, row_data in enumerate(_CP60_ROW_INVENTORY, 1):
        strategy = row_data[1]
        cells = (
            CP61_TEST28_REJECTION_OBSERVABLE_CELLS
            if strategy == "bounded-rejection"
            else CP61_TEST28_SIR_OBSERVABLE_CELLS
        )
        for cell in cells:
            observable.append(
                _build_estimand(
                    ordinal=ordinal,
                    row_ordinal=row_ordinal,
                    row_data=row_data,
                    projection_sha256=projection_sha256,
                    family="observable-cell",
                    observable_cell=cell,
                )
            )
            ordinal += 1
    first_attempt = []
    for row_ordinal, row_data in enumerate(_CP60_ROW_INVENTORY, 1):
        if row_data[1] != "bounded-rejection":
            continue
        for attempt in range(1, row_data[2] + 1):
            first_attempt.append(
                _build_estimand(
                    ordinal=ordinal,
                    row_ordinal=row_ordinal,
                    row_data=row_data,
                    projection_sha256=projection_sha256,
                    family="rejection-first-attempt",
                    first_attempt=attempt,
                )
            )
            ordinal += 1
    selected_features = []
    for row_ordinal, row_data in enumerate(_CP60_ROW_INVENTORY, 1):
        _, features_ = _feature_inventory(row_data[0])
        for feature in features_:
            selected_features.append(
                _build_estimand(
                    ordinal=ordinal,
                    row_ordinal=row_ordinal,
                    row_data=row_data,
                    projection_sha256=projection_sha256,
                    family="selected-conditional-feature",
                    feature=feature,
                )
            )
            ordinal += 1
    if (
        len(observable) != CP61_TEST28_OBSERVABLE_ESTIMAND_COUNT
        or len(first_attempt) != CP61_TEST28_REJECTION_FIRST_ATTEMPT_ESTIMAND_COUNT
        or len(observable) + len(first_attempt) != CP61_TEST28_BINOMIAL_ESTIMAND_COUNT
        or len(selected_features) != CP61_TEST28_SELECTED_FEATURE_ESTIMAND_COUNT
        or ordinal != CP61_TEST28_ESTIMAND_COUNT + 1
    ):
        raise AssertionError("frozen CP61 estimand count arithmetic differs")
    return tuple(observable), tuple(first_attempt), tuple(selected_features)


def _row_compact_payload(value: CP61MCRowDesignV1) -> dict:
    return {
        "schema_version": value.schema_version,
        "row_ordinal": value.row_ordinal,
        "fixture_id": value.fixture_id,
        "strategy": value.strategy,
        "budget": value.budget,
        "stable_request_template_sha256": value.cp60_request_template_sha256,
        "observable_cell_labels": value.observable_cell_labels,
        "observable_estimand_ordinals": value.observable_estimand_ordinals,
        "first_attempt_estimand_ordinals": value.first_attempt_estimand_ordinals,
        "selected_feature_estimand_ordinals": (
            value.selected_feature_estimand_ordinals
        ),
        "selected_feature_ids": value.selected_feature_ids,
        "selected_feature_lower_bounds": value.selected_feature_lower_bounds,
        "selected_feature_upper_bounds": value.selected_feature_upper_bounds,
        "external_seed_count": value.external_seed_count,
        "deadline_seconds": value.deadline_seconds,
        "same_seed_ordinal_reuse_across_rows_required": (
            value.same_seed_ordinal_reuse_across_rows_required
        ),
        "cross_row_pairing_required_without_independence": (
            value.cross_row_pairing_required_without_independence
        ),
    }


def _estimand_ordinals_for_row(estimands: tuple, row_ordinal: int) -> tuple:
    return tuple(
        estimand.estimand_ordinal
        for estimand in estimands
        if estimand.row_ordinal == row_ordinal
    )


def _build_rows(
    projection_sha256: str,
    observable: tuple,
    first_attempt: tuple,
    selected_features: tuple,
) -> tuple:
    rows = []
    for row_ordinal, row_data in enumerate(_CP60_ROW_INVENTORY, 1):
        fixture_id, strategy, budget, request_sha256, definition_sha256 = row_data
        registry_sha256, features_ = _feature_inventory(fixture_id)
        cells = (
            CP61_TEST28_REJECTION_OBSERVABLE_CELLS
            if strategy == "bounded-rejection"
            else CP61_TEST28_SIR_OBSERVABLE_CELLS
        )
        values = {
            "schema_version": CP61_TEST28_WHOLE_SEED_MC_SCHEMA_VERSION,
            "row_ordinal": row_ordinal,
            "fixture_id": fixture_id,
            "strategy": strategy,
            "budget": budget,
            "cp60_bundle_sha256": CP61_TEST28_CP60_BUNDLE_SHA256,
            "cp60_request_template_sha256": request_sha256,
            "cp60_definition_record_sha256": definition_sha256,
            "cp58_feature_registry_sha256": registry_sha256,
            "stable_trace_projection_contract_sha256": projection_sha256,
            "observable_cell_labels": cells,
            "observable_estimand_ordinals": _estimand_ordinals_for_row(
                observable, row_ordinal
            ),
            "first_attempt_estimand_ordinals": _estimand_ordinals_for_row(
                first_attempt, row_ordinal
            ),
            "selected_feature_estimand_ordinals": _estimand_ordinals_for_row(
                selected_features, row_ordinal
            ),
            "selected_feature_ids": tuple(item[0] for item in features_),
            "selected_feature_lower_bounds": tuple(item[1] for item in features_),
            "selected_feature_upper_bounds": tuple(item[2] for item in features_),
            "external_seed_count": CP61_TEST28_EXTERNAL_SEED_COUNT,
            "deadline_seconds": CP61_TEST28_DEADLINE_SECONDS,
            "same_seed_ordinal_reuse_across_rows_required": True,
            "cross_row_pairing_required_without_independence": True,
            "volatile_runtime_or_result_hashes_semantically_authoritative": False,
            "compact_row_semantic_sha256": _ZERO_SHA256,
        }
        provisional = cast(
            CP61MCRowDesignV1,
            _seal(CP61MCRowDesignV1, {**values, "record_sha256": _ZERO_SHA256}),
        )
        values["compact_row_semantic_sha256"] = _digest(
            "compact-row-semantic", _row_compact_payload(provisional)
        )
        rows.append(
            cast(
                CP61MCRowDesignV1,
                _make_record(CP61MCRowDesignV1, "mc-row-design", values),
            )
        )
    return tuple(rows)


def _stable_design_semantic_sha256(values: Mapping[str, object]) -> str:
    semantic_fields = tuple(
        item.name
        for item in fields(CP61WholeSeedMCDesignBundleV1)
        if item.name not in ("stable_design_semantic_sha256", "record_sha256")
    )
    expected_fields = set(semantic_fields) | {"stable_design_semantic_sha256"}
    if set(values) != expected_fields:
        raise TypeError("stable design semantic field set differs")
    payload = {name: values[name] for name in semantic_fields}
    return _digest("stable-design-semantic", payload)


def cp61_whole_seed_mc_design_bundle() -> CP61WholeSeedMCDesignBundleV1:
    """Return the zero-import, zero-execution frozen prospective CP61 design."""

    projection = _build_stable_trace_projection_contract()
    observable, first_attempt, selected_features = _build_estimands(
        projection.record_sha256
    )
    rows = _build_rows(
        projection.record_sha256,
        observable,
        first_attempt,
        selected_features,
    )
    multiplicity = _build_multiplicity_and_precision()
    resources = _build_resource_budget()
    values = {
        "schema_version": CP61_TEST28_WHOLE_SEED_MC_SCHEMA_VERSION,
        "scope": CP61_TEST28_WHOLE_SEED_MC_SCOPE,
        "cp58_source_sha256": CP61_TEST28_CP58_SOURCE_SHA256,
        "cp60_source_sha256": CP61_TEST28_CP60_SOURCE_SHA256,
        "cp60_bundle_sha256": CP61_TEST28_CP60_BUNDLE_SHA256,
        "m1_feature_registry_sha256": CP61_TEST28_M1_FEATURE_REGISTRY_SHA256,
        "m2_feature_registry_sha256": CP61_TEST28_M2_FEATURE_REGISTRY_SHA256,
        "stable_trace_projection_contract": projection,
        "ordered_rows": rows,
        "observable_estimands": observable,
        "rejection_first_attempt_estimands": first_attempt,
        "selected_conditional_feature_estimands": selected_features,
        "multiplicity_and_precision": multiplicity,
        "resource_budget": resources,
        "fixture_ids": CP61_TEST28_FIXTURE_IDS,
        "rejection_budget_grid": CP61_TEST28_REJECTION_BUDGET_GRID,
        "sir_budget_grid": CP61_TEST28_SIR_BUDGET_GRID,
        "seed_ordinals": tuple(range(1, CP61_TEST28_EXTERNAL_SEED_COUNT + 1)),
        "external_seed_count": CP61_TEST28_EXTERNAL_SEED_COUNT,
        "external_seed_bits": CP61_TEST28_PLAN_SEED_BITS,
        "external_seed_sampling_mode": (
            "future-external-iid-uniform-uint64-with-replacement"
        ),
        "same_seed_ordinal_reuse_across_all_rows_required": True,
        "external_seed_draws_iid_uniform_uint64_with_replacement_required": True,
        "duplicate_seed_value_retention_required": True,
        "duplicate_seed_value_retry_permitted": False,
        "outcome_dropping_permitted": False,
        "sample_topup_permitted": False,
        "cross_row_outcomes_assumed_independent": False,
        "deadline_seconds": CP61_TEST28_DEADLINE_SECONDS,
        "timeout_censoring_retention_required": True,
        "timeout_censored_identified_with_semantic_nonreturn": False,
        "predeclared_design_only": True,
        "predecessor_inventories_hardcoded": True,
        "predecessor_source_and_record_hashes_are_frozen_custody_bindings": True,
        "cp58_or_cp60_imported_or_loaded_by_builder": False,
        "live_predecessor_parity_verified_by_builder": False,
        "infrastructure_failure_policy": CP61_TEST28_INFRASTRUCTURE_FAILURE_POLICY,
        "infrastructure_failure_invalidates_entire_mc_attempt": True,
        "infrastructure_failure_is_estimand_cell": False,
        "infrastructure_failure_folded_into_execution_failure": False,
        "infrastructure_failure_folded_into_timeout_censoring": False,
        "infrastructure_failure_draw_retried_replaced_or_topped_up": False,
        "observable_cell_partition_requires_infrastructure_fidelity": True,
        "infrastructure_fidelity_verified": False,
        "requests_fully_bound": False,
        "runtime_fully_bound": False,
        "source_capsule_fully_bound": False,
        "external_supervisor_fully_bound": False,
        "external_seed_source_verified": False,
        "cross_ordinal_iid_uniformity_verified": False,
        "current_fixed_hash_seed_plan_is_external_iid_seed_sample": False,
        "seed_sample_recorded": False,
        "raw_trace_sample_recorded": False,
        "requests_executed": False,
        "intervals_computed": False,
        "operational_predictions_derived": False,
        "full_trace_law_estimated": False,
        "total_variation_estimated": False,
        "power_guarantee_claimed": False,
        "confirmatory_evidence": False,
        "manuscript_claim_promoted": False,
        "formal_test_28_status": CP61_TEST28_FORMAL_TEST_28_STATUS,
        "formal_test_28_closed": False,
        "stable_design_semantic_digest_binds_predecessor_sources_and_registries": (
            True
        ),
        "stable_design_semantic_digest_excludes_volatile_identity_hashes": True,
        "stable_design_semantic_digest_is_full_trace_law_digest": False,
        "stable_design_semantic_sha256": _ZERO_SHA256,
    }
    values["stable_design_semantic_sha256"] = _stable_design_semantic_sha256(values)
    return cast(
        CP61WholeSeedMCDesignBundleV1,
        _make_record(
            CP61WholeSeedMCDesignBundleV1,
            "whole-seed-mc-design-bundle",
            values,
        ),
    )


def _validate_record_digest(value: object, cls: type, kind: str) -> None:
    if type(value) is not cls:
        raise TypeError("CP61 record has the wrong exact concrete type")
    actual = _sha256(getattr(value, "record_sha256"), "CP61 record SHA-256")
    payload = {item.name: getattr(value, item.name) for item in fields(cls)}
    if actual != _digest(kind, payload):
        raise ValueError("CP61 record digest differs")


def _same_record(value: object, expected: object) -> bool:
    return _canonical_bytes(value) == _canonical_bytes(expected)


def validate_cp61_stable_trace_projection_contract(
    value: object,
) -> CP61StableTraceProjectionContractV1:
    if type(value) is not CP61StableTraceProjectionContractV1:
        raise TypeError("stable trace projection contract has the wrong exact type")
    _preflight_canonical(value)
    _validate_record_digest(
        value,
        CP61StableTraceProjectionContractV1,
        "stable-trace-projection-contract",
    )
    expected = _build_stable_trace_projection_contract()
    if not _same_record(value, expected):
        raise ValueError("stable trace projection contract differs")
    return value


def validate_cp61_mc_row_design(value: object) -> CP61MCRowDesignV1:
    if type(value) is not CP61MCRowDesignV1:
        raise TypeError("MC row design has the wrong exact type")
    _preflight_canonical(value)
    ordinal = _integer(value.row_ordinal, "row ordinal", 1, CP61_TEST28_ROW_COUNT)
    _validate_record_digest(value, CP61MCRowDesignV1, "mc-row-design")
    expected = cp61_whole_seed_mc_design_bundle().ordered_rows[ordinal - 1]
    if not _same_record(value, expected):
        raise ValueError("MC row design differs from frozen replay")
    return value


def validate_cp61_estimand(value: object) -> CP61EstimandV1:
    if type(value) is not CP61EstimandV1:
        raise TypeError("estimand has the wrong exact type")
    _preflight_canonical(value)
    ordinal = _integer(
        value.estimand_ordinal,
        "estimand ordinal",
        1,
        CP61_TEST28_ESTIMAND_COUNT,
    )
    _validate_record_digest(value, CP61EstimandV1, "estimand")
    bundle = cp61_whole_seed_mc_design_bundle()
    ordered = (
        bundle.observable_estimands
        + bundle.rejection_first_attempt_estimands
        + bundle.selected_conditional_feature_estimands
    )
    if not _same_record(value, ordered[ordinal - 1]):
        raise ValueError("estimand differs from frozen replay")
    return value


def validate_cp61_multiplicity_and_precision(
    value: object,
) -> CP61MultiplicityAndPrecisionV1:
    if type(value) is not CP61MultiplicityAndPrecisionV1:
        raise TypeError("multiplicity record has the wrong exact type")
    _preflight_canonical(value)
    _validate_record_digest(
        value, CP61MultiplicityAndPrecisionV1, "multiplicity-and-precision"
    )
    expected = _build_multiplicity_and_precision()
    if not _same_record(value, expected):
        raise ValueError("multiplicity record differs from frozen replay")
    return value


def validate_cp61_resource_budget(value: object) -> CP61ResourceBudgetV1:
    if type(value) is not CP61ResourceBudgetV1:
        raise TypeError("resource budget has the wrong exact type")
    _preflight_canonical(value)
    _validate_record_digest(value, CP61ResourceBudgetV1, "resource-budget")
    expected = _build_resource_budget()
    if not _same_record(value, expected):
        raise ValueError("resource budget differs from frozen replay")
    return value


def validate_cp61_whole_seed_mc_design_bundle(
    value: object,
) -> CP61WholeSeedMCDesignBundleV1:
    """Replay and validate the sealed zero-execution CP61 design."""

    if type(value) is not CP61WholeSeedMCDesignBundleV1:
        raise TypeError("CP61 design bundle has the wrong exact type")
    _preflight_canonical(value)
    if type(value.stable_trace_projection_contract) is not (
        CP61StableTraceProjectionContractV1
    ):
        raise TypeError("bundle projection contract has the wrong exact type")
    if type(value.ordered_rows) is not tuple or len(value.ordered_rows) != 16:
        raise TypeError("bundle rows have the wrong exact structure")
    group_contracts = (
        (value.observable_estimands, CP61_TEST28_OBSERVABLE_ESTIMAND_COUNT),
        (
            value.rejection_first_attempt_estimands,
            CP61_TEST28_REJECTION_FIRST_ATTEMPT_ESTIMAND_COUNT,
        ),
        (
            value.selected_conditional_feature_estimands,
            CP61_TEST28_SELECTED_FEATURE_ESTIMAND_COUNT,
        ),
    )
    for group, expected_count in group_contracts:
        if type(group) is not tuple or len(group) != expected_count:
            raise TypeError("bundle estimand group has the wrong exact structure")
        if any(type(item) is not CP61EstimandV1 for item in group):
            raise TypeError("bundle estimand child has the wrong exact type")
    if any(type(item) is not CP61MCRowDesignV1 for item in value.ordered_rows):
        raise TypeError("bundle row child has the wrong exact type")
    if type(value.multiplicity_and_precision) is not CP61MultiplicityAndPrecisionV1:
        raise TypeError("bundle multiplicity child has the wrong exact type")
    if type(value.resource_budget) is not CP61ResourceBudgetV1:
        raise TypeError("bundle resource child has the wrong exact type")
    _validate_record_digest(
        value.stable_trace_projection_contract,
        CP61StableTraceProjectionContractV1,
        "stable-trace-projection-contract",
    )
    for row in value.ordered_rows:
        _validate_record_digest(row, CP61MCRowDesignV1, "mc-row-design")
    for group, _ in group_contracts:
        for estimand in group:
            _validate_record_digest(estimand, CP61EstimandV1, "estimand")
    _validate_record_digest(
        value.multiplicity_and_precision,
        CP61MultiplicityAndPrecisionV1,
        "multiplicity-and-precision",
    )
    _validate_record_digest(
        value.resource_budget, CP61ResourceBudgetV1, "resource-budget"
    )
    _validate_record_digest(
        value,
        CP61WholeSeedMCDesignBundleV1,
        "whole-seed-mc-design-bundle",
    )
    expected = cp61_whole_seed_mc_design_bundle()
    if not _same_record(value, expected):
        raise ValueError("CP61 design bundle differs from frozen replay")
    return value


def cp61_canonical_json_bytes(value: object) -> bytes:
    """Return tagged canonical JSON for one exact validated public record."""

    if type(value) is CP61StableTraceProjectionContractV1:
        checked = validate_cp61_stable_trace_projection_contract(value)
    elif type(value) is CP61MCRowDesignV1:
        checked = validate_cp61_mc_row_design(value)
    elif type(value) is CP61EstimandV1:
        checked = validate_cp61_estimand(value)
    elif type(value) is CP61MultiplicityAndPrecisionV1:
        checked = validate_cp61_multiplicity_and_precision(value)
    elif type(value) is CP61ResourceBudgetV1:
        checked = validate_cp61_resource_budget(value)
    elif type(value) is CP61WholeSeedMCDesignBundleV1:
        checked = validate_cp61_whole_seed_mc_design_bundle(value)
    else:
        raise TypeError("canonical encoding accepts exact public CP61 records only")
    return _canonical_bytes(checked)


def cp61_stable_design_semantic_sha256(value: object) -> str:
    """Return the validated design-semantic digest without volatile custody."""

    return validate_cp61_whole_seed_mc_design_bundle(
        value
    ).stable_design_semantic_sha256


__all__ = (
    "CP61_TEST28_BINOMIAL_ESTIMAND_COUNT",
    "CP61_TEST28_COMPACT_ESTIMAND_PROJECTION_SEMANTICS",
    "CP61_TEST28_CP58_SOURCE_SHA256",
    "CP61_TEST28_CP60_BUNDLE_SHA256",
    "CP61_TEST28_CP60_SOURCE_SHA256",
    "CP61_TEST28_CP_BISECTION_STEPS",
    "CP61_TEST28_CP_CALIBRATION_MAX_TRIAL_COUNT",
    "CP61_TEST28_CP_INTERVAL_FORMULA",
    "CP61_TEST28_DEADLINE_SECONDS",
    "CP61_TEST28_ESTIMAND_COUNT",
    "CP61_TEST28_EXTERNAL_SEED_COUNT",
    "CP61_TEST28_FAMILYWISE_ERROR_BUDGET",
    "CP61_TEST28_FEATURE_HALFWIDTH_RANGE_MULTIPLIER",
    "CP61_TEST28_FIXTURE_IDS",
    "CP61_TEST28_FORMAL_TEST_28_STATUS",
    "CP61_TEST28_HOEFFDING_EXPONENT",
    "CP61_TEST28_HOEFFDING_EXPONENT_FORMULA",
    "CP61_TEST28_INFRASTRUCTURE_FAILURE_POLICY",
    "CP61_TEST28_M1_FEATURE_COUNT",
    "CP61_TEST28_M1_FEATURE_REGISTRY_SHA256",
    "CP61_TEST28_M2_FEATURE_COUNT",
    "CP61_TEST28_M2_FEATURE_REGISTRY_SHA256",
    "CP61_TEST28_MAX_COORDINATE_COUNT",
    "CP61_TEST28_MAX_EVENT_OCCURRENCE_COUNT",
    "CP61_TEST28_MINIMUM_SELECTED_COUNT",
    "CP61_TEST28_OBSERVABLE_ESTIMAND_COUNT",
    "CP61_TEST28_PER_ESTIMATOR_ERROR_BUDGET",
    "CP61_TEST28_PER_TAIL_ERROR_BUDGET",
    "CP61_TEST28_PLAN_SEED_BITS",
    "CP61_TEST28_REJECTION_BUDGET_GRID",
    "CP61_TEST28_REJECTION_FIRST_ATTEMPT_ESTIMAND_COUNT",
    "CP61_TEST28_REJECTION_OBSERVABLE_CELLS",
    "CP61_TEST28_REJECTION_PROPOSAL_SLOT_COUNT",
    "CP61_TEST28_ROW_COUNT",
    "CP61_TEST28_SELECTED_FEATURE_ESTIMAND_COUNT",
    "CP61_TEST28_SIR_BUDGET_GRID",
    "CP61_TEST28_SIR_OBSERVABLE_CELLS",
    "CP61_TEST28_SIR_PROPOSAL_SLOT_COUNT",
    "CP61_TEST28_SIR_RESAMPLING_DRAW_COUNT",
    "CP61_TEST28_STABLE_TRACE_PROJECTION_EXCLUDED_CUSTODY",
    "CP61_TEST28_STABLE_TRACE_PROJECTION_FORMULA",
    "CP61_TEST28_STABLE_TRACE_PROJECTION_INCLUDED_SEMANTICS",
    "CP61_TEST28_STRATEGIES",
    "CP61_TEST28_TAYLOR_LOWER_BOUND",
    "CP61_TEST28_TAYLOR_LOWER_BOUND_FORMULA",
    "CP61_TEST28_TAYLOR_MAXIMUM_DEGREE",
    "CP61_TEST28_TOTAL_PROPOSAL_SLOT_COUNT",
    "CP61_TEST28_TOTAL_REQUEST_COUNT",
    "CP61_TEST28_WHOLE_SEED_MC_SCHEMA_VERSION",
    "CP61_TEST28_WHOLE_SEED_MC_SCOPE",
    "CP61EstimandV1",
    "CP61MCRowDesignV1",
    "CP61MultiplicityAndPrecisionV1",
    "CP61ResourceBudgetV1",
    "CP61StableTraceProjectionContractV1",
    "CP61WholeSeedMCDesignBundleV1",
    "cp61_canonical_json_bytes",
    "cp61_exact_clopper_pearson_outward_calibration_interval",
    "cp61_stable_design_semantic_sha256",
    "cp61_whole_seed_mc_design_bundle",
    "validate_cp61_estimand",
    "validate_cp61_mc_row_design",
    "validate_cp61_multiplicity_and_precision",
    "validate_cp61_resource_budget",
    "validate_cp61_stable_trace_projection_contract",
    "validate_cp61_whole_seed_mc_design_bundle",
)
