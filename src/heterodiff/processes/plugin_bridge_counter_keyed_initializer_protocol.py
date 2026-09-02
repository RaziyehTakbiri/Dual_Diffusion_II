"""Certified stage and attempt allocation for general initializer execution.

Checkpoint twenty-six deliberately leaves ``stage_index`` and
``attempt_index`` uninterpreted.  This additive successor assigns disjoint
tag-7 stages to four future initializer strategies and materializes the exact
parent prefixes for one fixed, nonadaptive budget:

* stage 0: one finite-enumeration selection record;
* stage 1: chronological bounded-rejection attempts;
* stage 2: chronological fixed-budget SIR particles;
* stage 3: one SIR resampling record after every particle; and
* stage 4: one branch-free reference-candidate capsule.

A reference candidate, rejection attempt, or SIR particle owns a fixed tuple
of positive word blocks.  If that tuple has length ``B``, outer work item
``a`` and block ``b`` use the injective flattened attempt coordinate
``a * B + b``.  Thus a work item may use multiple parent streams without
exceeding the 4,096-word per-stream limit, while the complete plan remains
bounded by 64 records and 65,536 words.

The stated maxima of 64 rejection attempts and 63 SIR particles are absolute
single-block maxima; a multiblock work-item capsule reaches the 64-record cap
at a smaller outer-item budget.

The module allocates and validates raw-word prefix records; it does not
interpret a word.
In particular, it supplies no categorical, integer, Gaussian, acceptance,
weight, resampling, configuration, lineage, or initializer output law.  All
prefixes in a bounded rejection allocation are materialized up front.  Each
rejection work-item capsule must later be partitioned explicitly into proposal
and acceptance-decision subprefixes by a semantic successor.  A future layer
may inspect attempts in order and ignore the suffix after its first accepted
attempt, but this module neither computes acceptance nor certifies success.

Reissuing the same strategy at the same run and initialization coordinates
replays the same direct streams.  One canonical allocation contains no
duplicate address coordinates; the contract has no issuance registry and
makes no global uniqueness, independence, portability, or cryptographic claim.
"""

from __future__ import annotations

from dataclasses import dataclass
import platform
import sys
from typing import Dict, Mapping, Tuple

import numpy as np

try:
    from heterodiff.processes import (
        plugin_bridge_counter_keyed_global_initializer_control as _control,
    )
    from heterodiff.processes import (
        plugin_bridge_counter_keyed_lineage_contract as _lineage,
    )
    from heterodiff.processes import plugin_bridge_operational_thinning as _thinning
except ModuleNotFoundError as error:  # pragma: no cover - subprocess tested
    if error.name == "torch" or "optional PyTorch" in str(error):
        raise ModuleNotFoundError(
            "initializer protocol requires the optional PyTorch reference "
            "dependency; install the 'reference' extra"
        ) from error
    raise


PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_PROTOCOL_SCHEMA_VERSION = (
    "plugin-bridge-counter-keyed-initializer-protocol-v1"
)
PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_PROTOCOL_POLICY = (
    "exact-checkpoint26-owner-binding;disjoint-strategy-stage-allocation;"
    "enumeration-stage0-single-selection;rejection-stage1-ordered-attempts;"
    "sir-stage2-ordered-particles-stage3-single-resample;"
    "reference-stage4-single-candidate;fixed-multiblock-work-item-capsules;"
    "injective-outer-item-block-flattening;fixed-nonadaptive-budgets;"
    "complete-parent-prefix-materialization;"
    "canonical-plan-result-replay;within-canonical-plan-address-uniqueness;"
    "no-caller-rng;uninterpreted-raw64-words-v1"
)
PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_PROTOCOL_SCOPE = (
    "same-runtime-procedural-initializer-strategy-allocation;"
    "not-cardinality-type-event-coordinate-or-configuration-generation;"
    "not-uniform-integer-categorical-gaussian-or-acceptance-transform;"
    "not-enumeration-support-evaluation-or-normalization;"
    "not-rejection-predicate-success-failure-or-fallback;"
    "not-sir-weight-normalization-ess-or-resampling-law;"
    "not-reference-conditional-or-tilted-initializer-law;"
    "not-tag3-payload-coordination-or-cross-initialization-separation;"
    "not-accepted-configuration-to-lineage-mapping;"
    "not-global-run-id-or-initialization-index-uniqueness;"
    "not-global-one-shot-address-use-or-issuance-registry;"
    "not-statistical-independence-or-physical-randomness;"
    "not-brownian-drift-path-strang-liveness-or-full-sampler;"
    "not-analytic-target-or-stationarity;"
    "not-runtime-portable-or-cryptographic-authentication"
)

INITIALIZER_STRATEGY_ENUMERATION = "enumeration"
INITIALIZER_STRATEGY_REJECTION = "rejection"
INITIALIZER_STRATEGY_SIR = "sir"
INITIALIZER_STRATEGY_REFERENCE = "reference"
INITIALIZER_STRATEGIES = (
    INITIALIZER_STRATEGY_ENUMERATION,
    INITIALIZER_STRATEGY_REJECTION,
    INITIALIZER_STRATEGY_SIR,
    INITIALIZER_STRATEGY_REFERENCE,
)

INITIALIZER_STAGE_ENUMERATION_SELECTION = 0
INITIALIZER_STAGE_REJECTION_ATTEMPT = 1
INITIALIZER_STAGE_SIR_PARTICLE = 2
INITIALIZER_STAGE_SIR_RESAMPLE = 3
INITIALIZER_STAGE_REFERENCE_CANDIDATE = 4

INITIALIZER_ROLE_ENUMERATION_SELECTION = "enumeration_selection"
INITIALIZER_ROLE_REJECTION_ATTEMPT = "rejection_attempt"
INITIALIZER_ROLE_SIR_PARTICLE = "sir_particle"
INITIALIZER_ROLE_SIR_RESAMPLE = "sir_resample"
INITIALIZER_ROLE_REFERENCE_CANDIDATE = "reference_candidate"
INITIALIZER_STAGE_ROLES = (
    (
        INITIALIZER_STAGE_ENUMERATION_SELECTION,
        INITIALIZER_ROLE_ENUMERATION_SELECTION,
    ),
    (INITIALIZER_STAGE_REJECTION_ATTEMPT, INITIALIZER_ROLE_REJECTION_ATTEMPT),
    (INITIALIZER_STAGE_SIR_PARTICLE, INITIALIZER_ROLE_SIR_PARTICLE),
    (INITIALIZER_STAGE_SIR_RESAMPLE, INITIALIZER_ROLE_SIR_RESAMPLE),
    (
        INITIALIZER_STAGE_REFERENCE_CANDIDATE,
        INITIALIZER_ROLE_REFERENCE_CANDIDATE,
    ),
)

COUNTER_KEYED_INITIALIZER_PROTOCOL_MAX_REJECTION_ATTEMPTS = (
    _control.COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_STREAM_RECORDS
)
COUNTER_KEYED_INITIALIZER_PROTOCOL_MAX_SIR_PARTICLES = (
    _control.COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_STREAM_RECORDS - 1
)
_PARENT_MAXIMUM_WORDS_PER_STREAM = (
    _control.COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_RAW64_WORDS_PER_STREAM
)

_CERTIFICATE_TOKEN = object()
_ENTRY_TOKEN = object()
_RESULT_TOKEN = object()
_OWNER_TOKEN = object()
_ZERO_SHA256 = "0" * 64


class PluginBridgeCounterKeyedInitializerProtocolError(ArithmeticError):
    """Fail-closed checkpoint-twenty-seven protocol-allocation error."""


def _without(values: Mapping[str, object], *names: str) -> Mapping[str, object]:
    excluded = set(names)
    return {name: value for name, value in values.items() if name not in excluded}


def _exact_bool(value: object, *, name: str) -> bool:
    if type(value) is not bool:
        raise TypeError("%s must be an exact bool" % name)
    return value


def _exact_strategy(value: object) -> str:
    if type(value) is not str:
        raise TypeError("strategy must be exact text")
    if value not in INITIALIZER_STRATEGIES:
        raise ValueError("strategy is not one of the frozen initializer strategies")
    return value


def _exact_word_count(
    value: object,
    *,
    name: str,
    positive: bool,
) -> int:
    count = _lineage._exact_uint64(value, name=name)
    if positive and count == 0:
        raise ValueError("%s must be positive" % name)
    if (
        count
        > _control.COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_RAW64_WORDS_PER_STREAM
    ):
        raise ValueError("%s exceeds the per-stream word bound" % name)
    return count


def _preflight_work_item_word_blocks(value: object) -> Tuple[int, ...]:
    if type(value) is not tuple:
        raise TypeError("work_item_raw64_word_counts must be an exact tuple")
    if (
        len(value)
        > _control.COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_STREAM_RECORDS
    ):
        raise ValueError("work-item word-block tuple exceeds the parent record bound")
    return tuple(
        _exact_word_count(
            count,
            name="work_item_raw64_word_counts[%d]" % position,
            positive=True,
        )
        for position, count in enumerate(value)
    )


def _exact_strategy_tuple(
    value: object,
    *,
    name: str,
    expected_length: int,
) -> Tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError("%s must be an exact tuple" % name)
    if len(value) != expected_length:
        raise ValueError("%s has the wrong fixed length" % name)
    for position, strategy in enumerate(value):
        if type(strategy) is not str:
            raise TypeError("%s[%d] must be exact text" % (name, position))
    return value


def _exact_stage_role_tuple(
    value: object,
    *,
    name: str,
    expected_length: int,
) -> Tuple[Tuple[int, str], ...]:
    if type(value) is not tuple:
        raise TypeError("%s must be an exact tuple" % name)
    if len(value) != expected_length:
        raise ValueError("%s has the wrong fixed length" % name)
    checked = []
    for position, pair in enumerate(value):
        if type(pair) is not tuple or len(pair) != 2:
            raise TypeError(
                "%s[%d] must be an exact stage-role pair" % (name, position)
            )
        stage = _lineage._exact_uint64(
            pair[0],
            name="%s[%d].stage" % (name, position),
        )
        if type(pair[1]) is not str:
            raise TypeError("%s[%d].role must be exact text" % (name, position))
        checked.append((stage, pair[1]))
    return tuple(checked)


def _preflight_protocol_request(
    strategy: object,
    strategy_budget: object,
    work_item_raw64_word_counts: object,
    selection_raw64_word_count: object,
) -> Tuple[str, int, Tuple[int, ...], int, Tuple[Tuple[int, int, int], ...]]:
    checked_strategy = _exact_strategy(strategy)
    budget = _lineage._exact_uint64(strategy_budget, name="strategy_budget")
    work_item_blocks = _preflight_work_item_word_blocks(work_item_raw64_word_counts)
    selection_words = _exact_word_count(
        selection_raw64_word_count,
        name="selection_raw64_word_count",
        positive=False,
    )

    if checked_strategy == INITIALIZER_STRATEGY_ENUMERATION:
        if budget != 1:
            raise ValueError("enumeration requires the literal strategy budget one")
        if work_item_blocks:
            raise ValueError("enumeration has no work-item block allocation")
        if selection_words == 0:
            raise ValueError("enumeration requires a positive selection prefix")
        plan = (
            (
                INITIALIZER_STAGE_ENUMERATION_SELECTION,
                0,
                selection_words,
            ),
        )
    elif checked_strategy == INITIALIZER_STRATEGY_REJECTION:
        if budget == 0:
            raise ValueError("rejection requires at least one attempted proposal")
        if budget > COUNTER_KEYED_INITIALIZER_PROTOCOL_MAX_REJECTION_ATTEMPTS:
            raise ValueError("rejection attempt budget exceeds its maximum")
        if not work_item_blocks:
            raise ValueError("rejection requires at least one block per attempt")
        if selection_words != 0:
            raise ValueError("rejection has no separate selection-prefix allocation")
        plan = tuple(
            (
                INITIALIZER_STAGE_REJECTION_ATTEMPT,
                attempt * len(work_item_blocks) + block,
                count,
            )
            for attempt in range(budget)
            for block, count in enumerate(work_item_blocks)
        )
    elif checked_strategy == INITIALIZER_STRATEGY_SIR:
        if budget == 0:
            raise ValueError("SIR requires at least one particle")
        if budget > COUNTER_KEYED_INITIALIZER_PROTOCOL_MAX_SIR_PARTICLES:
            raise ValueError("SIR particle budget exceeds its maximum")
        if not work_item_blocks:
            raise ValueError("SIR requires at least one block per particle")
        if selection_words == 0:
            raise ValueError("SIR requires a positive resampling prefix")
        plan = tuple(
            (
                INITIALIZER_STAGE_SIR_PARTICLE,
                particle * len(work_item_blocks) + block,
                count,
            )
            for particle in range(budget)
            for block, count in enumerate(work_item_blocks)
        ) + ((INITIALIZER_STAGE_SIR_RESAMPLE, 0, selection_words),)
    else:
        if budget != 1:
            raise ValueError("reference requires the literal strategy budget one")
        if not work_item_blocks:
            raise ValueError("reference requires at least one candidate block")
        if selection_words != 0:
            raise ValueError("reference has no separate selection-prefix allocation")
        plan = tuple(
            (INITIALIZER_STAGE_REFERENCE_CANDIDATE, block, count)
            for block, count in enumerate(work_item_blocks)
        )

    if len(plan) > _control.COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_STREAM_RECORDS:
        raise ValueError("initializer protocol plan exceeds the parent record bound")
    total_words = sum(entry[2] for entry in plan)
    if (
        total_words
        > _control.COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_TOTAL_RAW64_WORDS
    ):
        raise ValueError("initializer protocol plan exceeds the aggregate word bound")
    if any(right[:2] <= left[:2] for left, right in zip(plan, plan[1:])):
        raise ValueError("initializer protocol plan is not strictly lexicographic")
    return checked_strategy, budget, work_item_blocks, selection_words, plan


def _runtime_sha256() -> str:
    expected_strategies = ("enumeration", "rejection", "sir", "reference")
    strategy_constants = (
        INITIALIZER_STRATEGY_ENUMERATION,
        INITIALIZER_STRATEGY_REJECTION,
        INITIALIZER_STRATEGY_SIR,
        INITIALIZER_STRATEGY_REFERENCE,
    )
    if (
        _exact_strategy_tuple(
            strategy_constants,
            name="strategy_constants",
            expected_length=4,
        )
        != expected_strategies
    ):
        raise ValueError("initializer protocol strategy constants changed")
    if (
        _exact_strategy_tuple(
            INITIALIZER_STRATEGIES,
            name="INITIALIZER_STRATEGIES",
            expected_length=4,
        )
        != expected_strategies
    ):
        raise ValueError("initializer protocol strategy tuple changed")
    stage_constants = (
        INITIALIZER_STAGE_ENUMERATION_SELECTION,
        INITIALIZER_STAGE_REJECTION_ATTEMPT,
        INITIALIZER_STAGE_SIR_PARTICLE,
        INITIALIZER_STAGE_SIR_RESAMPLE,
        INITIALIZER_STAGE_REFERENCE_CANDIDATE,
    )
    if any(type(stage) is not int for stage in stage_constants) or stage_constants != (
        0,
        1,
        2,
        3,
        4,
    ):
        raise ValueError("initializer protocol stage constants changed")
    role_constants = (
        INITIALIZER_ROLE_ENUMERATION_SELECTION,
        INITIALIZER_ROLE_REJECTION_ATTEMPT,
        INITIALIZER_ROLE_SIR_PARTICLE,
        INITIALIZER_ROLE_SIR_RESAMPLE,
        INITIALIZER_ROLE_REFERENCE_CANDIDATE,
    )
    if any(type(role) is not str for role in role_constants) or role_constants != (
        "enumeration_selection",
        "rejection_attempt",
        "sir_particle",
        "sir_resample",
        "reference_candidate",
    ):
        raise ValueError("initializer protocol role constants changed")
    expected_stage_roles = (
        (0, "enumeration_selection"),
        (1, "rejection_attempt"),
        (2, "sir_particle"),
        (3, "sir_resample"),
        (4, "reference_candidate"),
    )
    if (
        _exact_stage_role_tuple(
            INITIALIZER_STAGE_ROLES,
            name="INITIALIZER_STAGE_ROLES",
            expected_length=5,
        )
        != expected_stage_roles
    ):
        raise ValueError("initializer protocol stage-role map changed")
    if len({stage for stage, _ in INITIALIZER_STAGE_ROLES}) != len(
        INITIALIZER_STAGE_ROLES
    ):
        raise ValueError("initializer protocol stages are not distinct")
    return _thinning._semantic_digest(
        {
            "schema_version": (
                PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_PROTOCOL_SCHEMA_VERSION
            ),
            "policy": PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_PROTOCOL_POLICY,
            "scope": PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_PROTOCOL_SCOPE,
            "python": tuple(sys.version_info[:3]),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "numpy": np.__version__,
            "strategies": INITIALIZER_STRATEGIES,
            "stage_roles": INITIALIZER_STAGE_ROLES,
            "maximum_rejection_attempts": (
                COUNTER_KEYED_INITIALIZER_PROTOCOL_MAX_REJECTION_ATTEMPTS
            ),
            "maximum_sir_particles": (
                COUNTER_KEYED_INITIALIZER_PROTOCOL_MAX_SIR_PARTICLES
            ),
            "parent_maximum_records": (
                _control.COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_STREAM_RECORDS
            ),
            "parent_maximum_words_per_stream": (_PARENT_MAXIMUM_WORDS_PER_STREAM),
            "parent_maximum_total_words": (
                _control.COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_TOTAL_RAW64_WORDS
            ),
        }
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitializerProtocolCertificate:
    """Certificate for the checkpoint-twenty-seven allocation successor."""

    schema_version: str
    certificate_scope: str
    protocol_policy: str
    protocol_role_sha256: str
    process_parameter_sha256: str
    checkpoint26_certificate: _control.CounterKeyedGlobalInitializerControlCertificate
    checkpoint26_certificate_sha256: str
    checkpoint26_role_sha256: str
    checkpoint26_runtime_sha256: str
    checkpoint25_certificate_sha256: str
    protocol_runtime_sha256: str
    strategies: Tuple[str, ...]
    stage_roles: Tuple[Tuple[int, str], ...]
    maximum_stream_records: int
    maximum_raw64_words_per_stream: int
    maximum_total_raw64_words: int
    maximum_rejection_attempts: int
    maximum_sir_particles: int
    exact_checkpoint26_owner_binding_certified: bool
    disjoint_strategy_stage_semantics_certified: bool
    strategy_specific_attempt_semantics_certified: bool
    fixed_multiblock_work_item_allocation_certified: bool
    canonical_chronological_allocation_certified: bool
    fixed_nonadaptive_budget_preflight_certified: bool
    within_allocation_unique_addresses_certified: bool
    complete_parent_prefix_materialization_certified: bool
    exact_parent_result_replay_certified: bool
    no_caller_rng_certified: bool
    protocol_allocation_certified: bool
    actual_branch_decision_certified: bool
    rejection_predicate_certified: bool
    rejection_success_or_failure_certified: bool
    sir_weights_or_resampling_law_certified: bool
    enumeration_support_or_normalization_certified: bool
    finite_resolution_output_transform_certified: bool
    cardinality_law_certified: bool
    event_type_law_certified: bool
    coordinate_law_certified: bool
    initializer_output_law_certified: bool
    reference_initializer_law_certified: bool
    conditional_or_tilted_initializer_law_certified: bool
    accepted_configuration_to_lineage_mapping_certified: bool
    tag3_occurrence_payload_coordination_certified: bool
    tag3_cross_initialization_disjointness_certified: bool
    global_duplicate_address_use_prevention_certified: bool
    global_run_id_uniqueness_certified: bool
    statistical_independence_certified: bool
    physical_randomness_certified: bool
    brownian_stream_consumption_certified: bool
    brownian_additive_coupling_certified: bool
    continuous_drift_admissible: bool
    initializer_admissible: bool
    path_admissible: bool
    strang_sampler_admissible: bool
    full_sampler_admissible: bool
    analytic_target_preserved: bool
    rounded_stationarity_certified: bool
    sampler_liveness_certified: bool
    runtime_portable: bool
    cryptographic_authentication: bool
    passed: bool
    certificate_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("initializer protocol certificates cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError("initializer protocol certificates are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("initializer protocol certificate fields are incomplete")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])
        _validate_certificate(self)

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("initializer protocol certificates are not pickle objects")


def _certificate_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedInitializerProtocolCertificate.__annotations__)


def _certificate_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(values, "checkpoint26_certificate", "certificate_sha256")


def _validate_certificate(
    certificate: object,
) -> CounterKeyedInitializerProtocolCertificate:
    if type(certificate) is not CounterKeyedInitializerProtocolCertificate:
        raise TypeError("certificate has the wrong exact initializer protocol type")
    values = {name: getattr(certificate, name) for name in _certificate_fields()}
    expected_text = {
        "schema_version": (
            PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_PROTOCOL_SCHEMA_VERSION
        ),
        "certificate_scope": PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_PROTOCOL_SCOPE,
        "protocol_policy": PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_PROTOCOL_POLICY,
    }
    for name, expected in expected_text.items():
        if type(values[name]) is not str or values[name] != expected:
            raise ValueError("initializer protocol certificate %s differs" % name)
    _thinning._require_sha256(
        values["protocol_role_sha256"], name="certificate.protocol_role_sha256"
    )
    parent = _control._validate_certificate(values["checkpoint26_certificate"])
    _exact_strategy_tuple(
        values["strategies"],
        name="certificate.strategies",
        expected_length=4,
    )
    _exact_stage_role_tuple(
        values["stage_roles"],
        name="certificate.stage_roles",
        expected_length=5,
    )
    expected_scalars = {
        "process_parameter_sha256": parent.process_parameter_sha256,
        "checkpoint26_certificate_sha256": parent.certificate_sha256,
        "checkpoint26_role_sha256": parent.control_role_sha256,
        "checkpoint26_runtime_sha256": parent.control_runtime_sha256,
        "checkpoint25_certificate_sha256": parent.checkpoint25_certificate_sha256,
        "protocol_runtime_sha256": _runtime_sha256(),
        "strategies": INITIALIZER_STRATEGIES,
        "stage_roles": INITIALIZER_STAGE_ROLES,
        "maximum_stream_records": parent.maximum_stream_records,
        "maximum_raw64_words_per_stream": parent.maximum_raw64_words_per_stream,
        "maximum_total_raw64_words": parent.maximum_total_raw64_words,
        "maximum_rejection_attempts": (
            COUNTER_KEYED_INITIALIZER_PROTOCOL_MAX_REJECTION_ATTEMPTS
        ),
        "maximum_sir_particles": COUNTER_KEYED_INITIALIZER_PROTOCOL_MAX_SIR_PARTICLES,
    }
    for name, expected in expected_scalars.items():
        if type(values[name]) is not type(expected) or values[name] != expected:
            raise ValueError("initializer protocol certificate %s differs" % name)
    positive = (
        "exact_checkpoint26_owner_binding_certified",
        "disjoint_strategy_stage_semantics_certified",
        "strategy_specific_attempt_semantics_certified",
        "fixed_multiblock_work_item_allocation_certified",
        "canonical_chronological_allocation_certified",
        "fixed_nonadaptive_budget_preflight_certified",
        "within_allocation_unique_addresses_certified",
        "complete_parent_prefix_materialization_certified",
        "exact_parent_result_replay_certified",
        "no_caller_rng_certified",
        "protocol_allocation_certified",
        "passed",
    )
    negative = (
        "actual_branch_decision_certified",
        "rejection_predicate_certified",
        "rejection_success_or_failure_certified",
        "sir_weights_or_resampling_law_certified",
        "enumeration_support_or_normalization_certified",
        "finite_resolution_output_transform_certified",
        "cardinality_law_certified",
        "event_type_law_certified",
        "coordinate_law_certified",
        "initializer_output_law_certified",
        "reference_initializer_law_certified",
        "conditional_or_tilted_initializer_law_certified",
        "accepted_configuration_to_lineage_mapping_certified",
        "tag3_occurrence_payload_coordination_certified",
        "tag3_cross_initialization_disjointness_certified",
        "global_duplicate_address_use_prevention_certified",
        "global_run_id_uniqueness_certified",
        "statistical_independence_certified",
        "physical_randomness_certified",
        "brownian_stream_consumption_certified",
        "brownian_additive_coupling_certified",
        "continuous_drift_admissible",
        "initializer_admissible",
        "path_admissible",
        "strang_sampler_admissible",
        "full_sampler_admissible",
        "analytic_target_preserved",
        "rounded_stationarity_certified",
        "sampler_liveness_certified",
        "runtime_portable",
        "cryptographic_authentication",
    )
    for name in positive:
        if _exact_bool(values[name], name="certificate.%s" % name) is not True:
            raise ValueError("initializer protocol positive claim %s differs" % name)
    for name in negative:
        if _exact_bool(values[name], name="certificate.%s" % name) is not False:
            raise ValueError("initializer protocol negative claim %s differs" % name)
    for name in ("protocol_runtime_sha256", "certificate_sha256"):
        _thinning._require_sha256(values[name], name="certificate.%s" % name)
    expected_digest = _thinning._semantic_digest(_certificate_payload(values))
    if values["certificate_sha256"] != expected_digest:
        raise ValueError("initializer protocol certificate digest differs")
    return certificate


def _make_certificate(
    parent: _control.CounterKeyedGlobalInitializerControlCertificate,
    *,
    protocol_role_sha256: str,
) -> CounterKeyedInitializerProtocolCertificate:
    checked = _control._validate_certificate(parent)
    values: Dict[str, object] = {
        "schema_version": (
            PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_PROTOCOL_SCHEMA_VERSION
        ),
        "certificate_scope": PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_PROTOCOL_SCOPE,
        "protocol_policy": PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_PROTOCOL_POLICY,
        "protocol_role_sha256": protocol_role_sha256,
        "process_parameter_sha256": checked.process_parameter_sha256,
        "checkpoint26_certificate": parent,
        "checkpoint26_certificate_sha256": checked.certificate_sha256,
        "checkpoint26_role_sha256": checked.control_role_sha256,
        "checkpoint26_runtime_sha256": checked.control_runtime_sha256,
        "checkpoint25_certificate_sha256": checked.checkpoint25_certificate_sha256,
        "protocol_runtime_sha256": _runtime_sha256(),
        "strategies": INITIALIZER_STRATEGIES,
        "stage_roles": INITIALIZER_STAGE_ROLES,
        "maximum_stream_records": checked.maximum_stream_records,
        "maximum_raw64_words_per_stream": checked.maximum_raw64_words_per_stream,
        "maximum_total_raw64_words": checked.maximum_total_raw64_words,
        "maximum_rejection_attempts": (
            COUNTER_KEYED_INITIALIZER_PROTOCOL_MAX_REJECTION_ATTEMPTS
        ),
        "maximum_sir_particles": COUNTER_KEYED_INITIALIZER_PROTOCOL_MAX_SIR_PARTICLES,
        "certificate_sha256": _ZERO_SHA256,
    }
    positive = {
        "exact_checkpoint26_owner_binding_certified",
        "disjoint_strategy_stage_semantics_certified",
        "strategy_specific_attempt_semantics_certified",
        "fixed_multiblock_work_item_allocation_certified",
        "canonical_chronological_allocation_certified",
        "fixed_nonadaptive_budget_preflight_certified",
        "within_allocation_unique_addresses_certified",
        "complete_parent_prefix_materialization_certified",
        "exact_parent_result_replay_certified",
        "no_caller_rng_certified",
        "protocol_allocation_certified",
    }
    boolean_fields = tuple(
        name
        for name in CounterKeyedInitializerProtocolCertificate.__annotations__
        if name.endswith("certified") or name.endswith("admissible")
    )
    for name in boolean_fields:
        values[name] = name in positive
    for name in (
        "analytic_target_preserved",
        "runtime_portable",
        "cryptographic_authentication",
    ):
        values[name] = False
    values["passed"] = True
    values["certificate_sha256"] = _thinning._semantic_digest(
        _certificate_payload(values)
    )
    return CounterKeyedInitializerProtocolCertificate(
        **values, _construction_token=_CERTIFICATE_TOKEN
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitializerProtocolEntry:
    """One parent tag-7 prefix with its frozen protocol interpretation."""

    schema_version: str
    certificate_sha256: str
    strategy: str
    semantic_role: str
    plan_position: int
    chronological_index: int
    work_item_index: int
    block_index: int
    stage_index: int
    attempt_index: int
    raw64_word_count: int
    parent_consumption: _control.CounterKeyedGlobalInitializerControlConsumption
    parent_record_sha256: str
    raw64_words: Tuple[int, ...]
    prefix_materialized_without_semantic_resolution: bool
    entry_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("initializer protocol entries cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _ENTRY_TOKEN:
            raise TypeError("initializer protocol entries are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("initializer protocol entry fields are incomplete")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])
        _validate_entry_record(self)

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("initializer protocol entries are not pickle objects")


def _entry_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedInitializerProtocolEntry.__annotations__)


def _entry_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(values, "parent_consumption", "raw64_words", "entry_sha256")


def _expected_role(strategy: str, stage: int) -> str:
    if strategy == INITIALIZER_STRATEGY_ENUMERATION:
        if stage != INITIALIZER_STAGE_ENUMERATION_SELECTION:
            raise ValueError("enumeration entry uses another stage")
        return INITIALIZER_ROLE_ENUMERATION_SELECTION
    if strategy == INITIALIZER_STRATEGY_REJECTION:
        if stage != INITIALIZER_STAGE_REJECTION_ATTEMPT:
            raise ValueError("rejection entry uses another stage")
        return INITIALIZER_ROLE_REJECTION_ATTEMPT
    if strategy == INITIALIZER_STRATEGY_REFERENCE:
        if stage != INITIALIZER_STAGE_REFERENCE_CANDIDATE:
            raise ValueError("reference entry uses another stage")
        return INITIALIZER_ROLE_REFERENCE_CANDIDATE
    if stage == INITIALIZER_STAGE_SIR_PARTICLE:
        return INITIALIZER_ROLE_SIR_PARTICLE
    if stage == INITIALIZER_STAGE_SIR_RESAMPLE:
        return INITIALIZER_ROLE_SIR_RESAMPLE
    raise ValueError("SIR entry uses an unknown stage")


def _validate_entry_record(
    entry: object,
) -> CounterKeyedInitializerProtocolEntry:
    if type(entry) is not CounterKeyedInitializerProtocolEntry:
        raise TypeError("entry has the wrong exact initializer protocol type")
    values = {name: getattr(entry, name) for name in _entry_fields()}
    if (
        type(values["schema_version"]) is not str
        or values["schema_version"]
        != PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_PROTOCOL_SCHEMA_VERSION
    ):
        raise ValueError("initializer protocol entry schema differs")
    _thinning._require_sha256(
        values["certificate_sha256"], name="entry.certificate_sha256"
    )
    strategy = _exact_strategy(values["strategy"])
    role = values["semantic_role"]
    if type(role) is not str:
        raise TypeError("entry semantic_role must be exact text")
    position = _lineage._exact_uint64(values["plan_position"], name="entry.position")
    chronology = _lineage._exact_uint64(
        values["chronological_index"], name="entry.chronological_index"
    )
    work_item = _lineage._exact_uint64(
        values["work_item_index"], name="entry.work_item_index"
    )
    block = _lineage._exact_uint64(values["block_index"], name="entry.block_index")
    stage = _lineage._exact_uint64(values["stage_index"], name="entry.stage_index")
    attempt = _lineage._exact_uint64(
        values["attempt_index"], name="entry.attempt_index"
    )
    count = _exact_word_count(
        values["raw64_word_count"], name="entry.raw64_word_count", positive=True
    )
    if position >= _control.COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_STREAM_RECORDS:
        raise ValueError("initializer protocol entry position exceeds its bound")
    if (
        chronology
        >= _control.COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_STREAM_RECORDS
    ):
        raise ValueError("initializer protocol chronology exceeds its bound")
    if (
        work_item
        >= _control.COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_STREAM_RECORDS
        or block >= _control.COUNTER_KEYED_GLOBAL_INITIALIZER_CONTROL_MAX_STREAM_RECORDS
    ):
        raise ValueError("initializer protocol work-item coordinate exceeds its bound")
    if role != _expected_role(strategy, stage):
        raise ValueError("initializer protocol entry role differs")
    if strategy == INITIALIZER_STRATEGY_ENUMERATION:
        if attempt != 0 or chronology != 0 or work_item != 0 or block != 0:
            raise ValueError("enumeration entry chronology differs")
    elif strategy == INITIALIZER_STRATEGY_REJECTION:
        if chronology != attempt:
            raise ValueError("rejection attempt chronology differs")
    elif stage == INITIALIZER_STAGE_SIR_PARTICLE:
        if chronology != attempt:
            raise ValueError("SIR particle chronology differs")
    elif strategy == INITIALIZER_STRATEGY_REFERENCE:
        if work_item != 0 or block != attempt or chronology != attempt:
            raise ValueError("reference block chronology differs")
    elif attempt != 0 or block != 0:
        raise ValueError("SIR resample coordinate differs")
    parent = _control._validate_consumption_record(values["parent_consumption"])
    _thinning._require_sha256(
        values["parent_record_sha256"],
        name="entry.parent_record_sha256",
    )
    if values["parent_record_sha256"] != parent.record_sha256:
        raise ValueError("initializer protocol parent record digest differs")
    if (
        parent.position != position
        or parent.stage_index != stage
        or parent.attempt_index != attempt
        or parent.raw64_word_count != count
    ):
        raise ValueError("initializer protocol entry differs from its parent record")
    if values["raw64_words"] is not parent.raw64_words:
        raise ValueError("initializer protocol raw-word identity differs")
    if (
        _exact_bool(
            values["prefix_materialized_without_semantic_resolution"],
            name="entry.prefix_materialized_without_semantic_resolution",
        )
        is not True
    ):
        raise ValueError("initializer protocol prefix-materialization flag differs")
    _thinning._require_sha256(values["entry_sha256"], name="entry.entry_sha256")
    expected_digest = _thinning._semantic_digest(_entry_payload(values))
    if values["entry_sha256"] != expected_digest:
        raise ValueError("initializer protocol entry digest differs")
    return entry


def _make_entry(
    certificate: CounterKeyedInitializerProtocolCertificate,
    parent: _control.CounterKeyedGlobalInitializerControlConsumption,
    *,
    strategy: str,
    semantic_role: str,
    chronological_index: int,
    work_item_index: int,
    block_index: int,
) -> CounterKeyedInitializerProtocolEntry:
    checked_certificate = _validate_certificate(certificate)
    checked_parent = _control._validate_consumption_record(parent)
    values: Dict[str, object] = {
        "schema_version": (
            PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_PROTOCOL_SCHEMA_VERSION
        ),
        "certificate_sha256": checked_certificate.certificate_sha256,
        "strategy": strategy,
        "semantic_role": semantic_role,
        "plan_position": checked_parent.position,
        "chronological_index": chronological_index,
        "work_item_index": work_item_index,
        "block_index": block_index,
        "stage_index": checked_parent.stage_index,
        "attempt_index": checked_parent.attempt_index,
        "raw64_word_count": checked_parent.raw64_word_count,
        "parent_consumption": parent,
        "parent_record_sha256": checked_parent.record_sha256,
        "raw64_words": parent.raw64_words,
        "prefix_materialized_without_semantic_resolution": True,
        "entry_sha256": _ZERO_SHA256,
    }
    values["entry_sha256"] = _thinning._semantic_digest(_entry_payload(values))
    return CounterKeyedInitializerProtocolEntry(
        **values, _construction_token=_ENTRY_TOKEN
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedInitializerProtocolResult:
    """Complete fixed-budget initializer-protocol allocation."""

    schema_version: str
    certificate: CounterKeyedInitializerProtocolCertificate
    certificate_sha256: str
    strategy: str
    run_id: int
    initialization_index: int
    strategy_budget: int
    work_item_raw64_word_counts: Tuple[int, ...]
    work_item_block_count: int
    selection_raw64_word_count: int
    control_plan: Tuple[Tuple[int, int, int], ...]
    parent_control_result: _control.CounterKeyedGlobalInitializerControlResult
    parent_result_sha256: str
    entries: Tuple[CounterKeyedInitializerProtocolEntry, ...]
    entry_sha256s: Tuple[str, ...]
    active_stage_roles: Tuple[Tuple[int, str], ...]
    stream_record_count: int
    total_raw64_words: int
    fixed_nonadaptive_budget: bool
    complete_parent_prefix_materialization: bool
    canonical_chronological_allocation: bool
    no_caller_rng: bool
    result_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("initializer protocol results cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _RESULT_TOKEN:
            raise TypeError("initializer protocol results are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("initializer protocol result fields are incomplete")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])
        _validate_result_record(self)

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("initializer protocol results are not pickle objects")


def _result_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedInitializerProtocolResult.__annotations__)


def _result_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(
        values,
        "certificate",
        "parent_control_result",
        "entries",
        "result_sha256",
    )


def _active_stage_roles(strategy: str) -> Tuple[Tuple[int, str], ...]:
    if strategy == INITIALIZER_STRATEGY_ENUMERATION:
        return (INITIALIZER_STAGE_ROLES[0],)
    if strategy == INITIALIZER_STRATEGY_REJECTION:
        return (INITIALIZER_STAGE_ROLES[1],)
    if strategy == INITIALIZER_STRATEGY_SIR:
        return (INITIALIZER_STAGE_ROLES[2], INITIALIZER_STAGE_ROLES[3])
    return (INITIALIZER_STAGE_ROLES[4],)


def _validate_result_record(
    result: object,
) -> CounterKeyedInitializerProtocolResult:
    if type(result) is not CounterKeyedInitializerProtocolResult:
        raise TypeError("result has the wrong exact initializer protocol type")
    values = {name: getattr(result, name) for name in _result_fields()}
    if (
        type(values["schema_version"]) is not str
        or values["schema_version"]
        != PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_PROTOCOL_SCHEMA_VERSION
    ):
        raise ValueError("initializer protocol result schema differs")
    certificate = _validate_certificate(values["certificate"])
    _thinning._require_sha256(
        values["certificate_sha256"],
        name="result.certificate_sha256",
    )
    if values["certificate_sha256"] != certificate.certificate_sha256:
        raise ValueError("initializer protocol result certificate digest differs")
    run_id = _lineage._exact_uint64(values["run_id"], name="result.run_id")
    initialization_index = _lineage._exact_uint64(
        values["initialization_index"], name="result.initialization_index"
    )
    (
        strategy,
        budget,
        work_item_blocks,
        selection_words,
        plan,
    ) = _preflight_protocol_request(
        values["strategy"],
        values["strategy_budget"],
        values["work_item_raw64_word_counts"],
        values["selection_raw64_word_count"],
    )
    if type(values["control_plan"]) is not tuple:
        raise TypeError("initializer protocol result plan must be an exact tuple")
    checked_result_plan, _ = _control._preflight_control_plan(values["control_plan"])
    if checked_result_plan != plan:
        raise ValueError("initializer protocol result plan differs")
    parent = _control._validate_result_record(values["parent_control_result"])
    if values["control_plan"] is not parent.control_plan:
        raise ValueError("initializer protocol result plan identity differs")
    _thinning._require_sha256(
        values["parent_result_sha256"],
        name="result.parent_result_sha256",
    )
    if values["parent_result_sha256"] != parent.result_sha256:
        raise ValueError("initializer protocol parent-result digest differs")
    if (
        parent.run_id != run_id
        or parent.initialization_index != initialization_index
        or parent.control_plan != plan
    ):
        raise ValueError("initializer protocol parent-result coordinates differ")
    if parent.certificate_sha256 != certificate.checkpoint26_certificate_sha256:
        raise ValueError("initializer protocol parent certificate digest differs")
    if type(values["entries"]) is not tuple:
        raise TypeError("initializer protocol entries must be an exact tuple")
    if type(values["entry_sha256s"]) is not tuple:
        raise TypeError("initializer protocol entry digests must be an exact tuple")
    if len(values["entries"]) > certificate.maximum_stream_records:
        raise ValueError("initializer protocol entry tuple exceeds its bound")
    if len(values["entry_sha256s"]) != len(values["entries"]):
        raise ValueError("initializer protocol entry digest count differs")
    for position, digest in enumerate(values["entry_sha256s"]):
        _thinning._require_sha256(
            digest,
            name="result.entry_sha256s[%d]" % position,
        )
    entries = tuple(_validate_entry_record(entry) for entry in values["entries"])
    if len(entries) != len(plan) or len(entries) != len(parent.consumptions):
        raise ValueError("initializer protocol entry count differs")
    if values["entry_sha256s"] != tuple(entry.entry_sha256 for entry in entries):
        raise ValueError("initializer protocol entry digest sequence differs")
    for position, (entry, parent_record, plan_entry) in enumerate(
        zip(entries, parent.consumptions, plan)
    ):
        if entry.parent_consumption is not parent_record:
            raise ValueError("initializer protocol entry parent identity differs")
        if entry.certificate_sha256 != certificate.certificate_sha256:
            raise ValueError("initializer protocol entry certificate differs")
        if entry.strategy != strategy or entry.plan_position != position:
            raise ValueError("initializer protocol entry position differs")
        if (
            entry.stage_index,
            entry.attempt_index,
            entry.raw64_word_count,
        ) != plan_entry:
            raise ValueError("initializer protocol entry plan projection differs")
        if entry.chronological_index != position:
            raise ValueError("initializer protocol chronology differs")
        if strategy == INITIALIZER_STRATEGY_ENUMERATION:
            expected_work_item, expected_block = 0, 0
        elif strategy == INITIALIZER_STRATEGY_SIR and (
            entry.stage_index == INITIALIZER_STAGE_SIR_RESAMPLE
        ):
            expected_work_item, expected_block = budget, 0
        else:
            expected_work_item, expected_block = divmod(position, len(work_item_blocks))
        if (
            entry.work_item_index != expected_work_item
            or entry.block_index != expected_block
        ):
            raise ValueError("initializer protocol work-item/block mapping differs")
    active_roles = _active_stage_roles(strategy)
    checked_active_roles = _exact_stage_role_tuple(
        values["active_stage_roles"],
        name="result.active_stage_roles",
        expected_length=len(active_roles),
    )
    if checked_active_roles != active_roles:
        raise ValueError("initializer protocol active-stage roles differ")
    observed_stage_roles = []
    for entry in entries:
        stage_role = (entry.stage_index, entry.semantic_role)
        if not observed_stage_roles or observed_stage_roles[-1] != stage_role:
            observed_stage_roles.append(stage_role)
    if tuple(observed_stage_roles) != active_roles:
        raise ValueError(
            "initializer protocol active-stage roles differ from its entries"
        )
    expected_scalars = {
        "strategy_budget": budget,
        "work_item_block_count": len(work_item_blocks),
        "selection_raw64_word_count": selection_words,
        "stream_record_count": len(plan),
        "total_raw64_words": sum(item[2] for item in plan),
    }
    for name, expected in expected_scalars.items():
        if type(values[name]) is not int or values[name] != expected:
            raise ValueError("initializer protocol result %s differs" % name)
    if (
        type(values["work_item_raw64_word_counts"]) is not tuple
        or values["work_item_raw64_word_counts"] != work_item_blocks
    ):
        raise ValueError("initializer protocol work-item word blocks differ")
    for name in (
        "fixed_nonadaptive_budget",
        "complete_parent_prefix_materialization",
        "canonical_chronological_allocation",
        "no_caller_rng",
    ):
        if _exact_bool(values[name], name="result.%s" % name) is not True:
            raise ValueError("initializer protocol result flag %s differs" % name)
    _thinning._require_sha256(values["result_sha256"], name="result.result_sha256")
    expected_digest = _thinning._semantic_digest(_result_payload(values))
    if values["result_sha256"] != expected_digest:
        raise ValueError("initializer protocol result digest differs")
    return result


def _make_result(
    certificate: CounterKeyedInitializerProtocolCertificate,
    parent: _control.CounterKeyedGlobalInitializerControlResult,
    entries: Tuple[CounterKeyedInitializerProtocolEntry, ...],
    *,
    strategy: str,
    strategy_budget: int,
    work_item_raw64_word_counts: Tuple[int, ...],
    selection_raw64_word_count: int,
) -> CounterKeyedInitializerProtocolResult:
    checked_certificate = _validate_certificate(certificate)
    checked_parent = _control._validate_result_record(parent)
    plan = checked_parent.control_plan
    values: Dict[str, object] = {
        "schema_version": (
            PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_PROTOCOL_SCHEMA_VERSION
        ),
        "certificate": certificate,
        "certificate_sha256": checked_certificate.certificate_sha256,
        "strategy": strategy,
        "run_id": checked_parent.run_id,
        "initialization_index": checked_parent.initialization_index,
        "strategy_budget": strategy_budget,
        "work_item_raw64_word_counts": work_item_raw64_word_counts,
        "work_item_block_count": len(work_item_raw64_word_counts),
        "selection_raw64_word_count": selection_raw64_word_count,
        "control_plan": plan,
        "parent_control_result": parent,
        "parent_result_sha256": checked_parent.result_sha256,
        "entries": entries,
        "entry_sha256s": tuple(entry.entry_sha256 for entry in entries),
        "active_stage_roles": _active_stage_roles(strategy),
        "stream_record_count": len(plan),
        "total_raw64_words": sum(item[2] for item in plan),
        "fixed_nonadaptive_budget": True,
        "complete_parent_prefix_materialization": True,
        "canonical_chronological_allocation": True,
        "no_caller_rng": True,
        "result_sha256": _ZERO_SHA256,
    }
    values["result_sha256"] = _thinning._semantic_digest(_result_payload(values))
    return CounterKeyedInitializerProtocolResult(
        **values, _construction_token=_RESULT_TOKEN
    )


class CounterKeyedInitializerProtocolOwner:
    """Immutable owner of strategy-specific tag-7 protocol allocations."""

    __slots__ = (
        "_control_owner",
        "_certified_control_owner",
        "_protocol_role_sha256",
        "_certified_protocol_role_sha256",
        "_certificate",
        "_certified_certificate",
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CounterKeyedInitializerProtocolOwner cannot be subclassed")

    def __init__(
        self,
        control_owner: _control.CounterKeyedGlobalInitializerControlOwner,
        protocol_role_sha256: str,
        certificate: CounterKeyedInitializerProtocolCertificate,
        *,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _OWNER_TOKEN:
            raise TypeError("initializer protocol owners require certification")
        if (
            type(control_owner)
            is not _control.CounterKeyedGlobalInitializerControlOwner
        ):
            raise TypeError("control_owner has the wrong exact type")
        role = _thinning._require_sha256(
            protocol_role_sha256, name="protocol_role_sha256"
        )
        checked = _validate_certificate(certificate)
        if checked.protocol_role_sha256 != role:
            raise ValueError("initializer protocol role differs from certificate")
        object.__setattr__(self, "_control_owner", control_owner)
        object.__setattr__(self, "_certified_control_owner", control_owner)
        object.__setattr__(self, "_protocol_role_sha256", role)
        object.__setattr__(self, "_certified_protocol_role_sha256", role)
        object.__setattr__(self, "_certificate", checked)
        object.__setattr__(self, "_certified_certificate", checked)

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("initializer protocol owners are immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("initializer protocol owners are immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("initializer protocol owners are not pickle objects")

    @property
    def certificate(self) -> CounterKeyedInitializerProtocolCertificate:
        return self._certificate

    @property
    def control_owner(self) -> _control.CounterKeyedGlobalInitializerControlOwner:
        return self._control_owner

    def _require_live_binding(self) -> CounterKeyedInitializerProtocolCertificate:
        _thinning._require_binary64_environment()
        if type(self._control_owner) is not (
            _control.CounterKeyedGlobalInitializerControlOwner
        ):
            raise TypeError("initializer protocol parent owner has the wrong type")
        if self._control_owner is not self._certified_control_owner:
            raise ValueError("initializer protocol parent-owner binding changed")
        _thinning._require_sha256(
            self._protocol_role_sha256,
            name="owner.protocol_role_sha256",
        )
        if self._protocol_role_sha256 != self._certified_protocol_role_sha256:
            raise ValueError("initializer protocol certified role binding changed")
        if self._certificate is not self._certified_certificate:
            raise ValueError("initializer protocol certified certificate changed")
        parent = self._control_owner._require_live_binding()
        if self.certificate.checkpoint26_certificate is not parent:
            raise ValueError("initializer protocol parent certificate changed")
        if self.certificate.protocol_runtime_sha256 != _runtime_sha256():
            raise ValueError("live initializer protocol runtime differs")
        expected = _make_certificate(
            parent,
            protocol_role_sha256=self._protocol_role_sha256,
        )
        for name in _certificate_fields():
            actual_value = getattr(self.certificate, name)
            expected_value = getattr(expected, name)
            if name == "checkpoint26_certificate":
                if actual_value is not expected_value:
                    raise ValueError("initializer protocol parent certificate changed")
            elif not _thinning._field_matches(name, actual_value, expected_value):
                raise ValueError(
                    "initializer protocol certificate field %s differs" % name
                )
        _thinning._require_binary64_environment()
        return self.certificate

    def allocate(
        self,
        run_id: object,
        initialization_index: object,
        *,
        strategy: object,
        strategy_budget: object,
        work_item_raw64_word_counts: object,
        selection_raw64_word_count: object,
    ) -> CounterKeyedInitializerProtocolResult:
        """Allocate and materialize one complete fixed-budget protocol plan."""

        self._require_live_binding()
        checked_run = _lineage._exact_uint64(run_id, name="run_id")
        checked_initialization = _lineage._exact_uint64(
            initialization_index, name="initialization_index"
        )
        (
            checked_strategy,
            budget,
            work_item_blocks,
            selection_words,
            plan,
        ) = _preflight_protocol_request(
            strategy,
            strategy_budget,
            work_item_raw64_word_counts,
            selection_raw64_word_count,
        )
        parent = self.control_owner.consume(
            checked_run,
            checked_initialization,
            control_plan=plan,
        )
        entries = []
        for position, record in enumerate(parent.consumptions):
            role = _expected_role(checked_strategy, record.stage_index)
            if checked_strategy == INITIALIZER_STRATEGY_ENUMERATION:
                work_item, block = 0, 0
            elif checked_strategy == INITIALIZER_STRATEGY_SIR and (
                record.stage_index == INITIALIZER_STAGE_SIR_RESAMPLE
            ):
                work_item, block = budget, 0
            else:
                work_item, block = divmod(position, len(work_item_blocks))
            entries.append(
                _make_entry(
                    self.certificate,
                    record,
                    strategy=checked_strategy,
                    semantic_role=role,
                    chronological_index=position,
                    work_item_index=work_item,
                    block_index=block,
                )
            )
        result = _make_result(
            self.certificate,
            parent,
            tuple(entries),
            strategy=checked_strategy,
            strategy_budget=budget,
            work_item_raw64_word_counts=work_item_blocks,
            selection_raw64_word_count=selection_words,
        )
        self.validate_result(
            result,
            checked_run,
            checked_initialization,
            strategy=checked_strategy,
            strategy_budget=budget,
            work_item_raw64_word_counts=work_item_blocks,
            selection_raw64_word_count=selection_words,
        )
        return result

    def validate_result(
        self,
        result: CounterKeyedInitializerProtocolResult,
        run_id: object,
        initialization_index: object,
        *,
        strategy: object,
        strategy_budget: object,
        work_item_raw64_word_counts: object,
        selection_raw64_word_count: object,
    ) -> CounterKeyedInitializerProtocolResult:
        """Deeply validate one allocation and replay its exact parent result."""

        self._require_live_binding()
        checked_run = _lineage._exact_uint64(run_id, name="run_id")
        checked_initialization = _lineage._exact_uint64(
            initialization_index, name="initialization_index"
        )
        (
            checked_strategy,
            budget,
            work_item_blocks,
            selection_words,
            plan,
        ) = _preflight_protocol_request(
            strategy,
            strategy_budget,
            work_item_raw64_word_counts,
            selection_raw64_word_count,
        )
        if type(result) is not CounterKeyedInitializerProtocolResult:
            raise TypeError("result has the wrong exact initializer protocol type")
        if type(result.entries) is not tuple:
            raise TypeError("initializer protocol entries must be an exact tuple")
        if len(result.entries) > self.certificate.maximum_stream_records:
            raise ValueError("initializer protocol result exceeds its record bound")
        checked = _validate_result_record(result)
        result_fields = _result_fields()
        result_before = _control._capture_fields(result, result_fields)
        parent = checked.parent_control_result
        parent_fields = _control._result_fields()
        parent_before = _control._capture_fields(parent, parent_fields)
        entry_fields = _entry_fields()
        entry_befores = tuple(
            _control._capture_fields(entry, entry_fields) for entry in checked.entries
        )
        parent_record_fields = _control._record_fields()
        parent_record_befores = tuple(
            _control._capture_fields(record, parent_record_fields)
            for record in parent.consumptions
        )
        if checked.certificate is not self.certificate:
            raise ValueError("initializer protocol result belongs to another owner")
        if parent.certificate is not self.control_owner.certificate:
            raise ValueError("initializer protocol parent result belongs elsewhere")
        if (
            checked.run_id != checked_run
            or checked.initialization_index != checked_initialization
            or checked.strategy != checked_strategy
            or checked.strategy_budget != budget
            or checked.work_item_raw64_word_counts != work_item_blocks
            or checked.selection_raw64_word_count != selection_words
            or checked.control_plan != plan
        ):
            raise ValueError("initializer protocol request differs from result")
        self.control_owner.validate_result(
            parent,
            checked_run,
            checked_initialization,
            control_plan=plan,
        )
        for position, (entry, record) in enumerate(
            zip(checked.entries, parent.consumptions)
        ):
            _validate_entry_record(entry)
            if entry.parent_consumption is not record:
                raise ValueError(
                    "initializer protocol entry %d lost parent identity" % position
                )
        self._require_live_binding()
        _validate_result_record(result)
        _control._require_fields_unchanged(
            result,
            result_fields,
            result_before,
            identity_fields=(
                "certificate",
                "control_plan",
                "parent_control_result",
                "entries",
                "entry_sha256s",
            ),
            name="initializer protocol result",
        )
        _control._require_fields_unchanged(
            parent,
            parent_fields,
            parent_before,
            identity_fields=(
                "certificate",
                "control_plan",
                "consumptions",
                "consumption_sha256s",
            ),
            name="initializer protocol parent result",
        )
        for position, (entry, before, record, record_before) in enumerate(
            zip(
                result.entries,
                entry_befores,
                parent.consumptions,
                parent_record_befores,
            )
        ):
            _validate_entry_record(entry)
            _control._require_fields_unchanged(
                entry,
                entry_fields,
                before,
                identity_fields=("parent_consumption", "raw64_words"),
                name="initializer protocol entry %d" % position,
            )
            _control._require_fields_unchanged(
                record,
                parent_record_fields,
                record_before,
                identity_fields=(
                    "certificate",
                    "control_stream",
                    "stream_initial_state",
                    "raw64_words",
                    "stream_final_state",
                ),
                name="initializer protocol parent record %d" % position,
            )
            if entry.parent_consumption is not record:
                raise ValueError("initializer protocol parent identity changed")
        return result


def certify_plugin_bridge_counter_keyed_initializer_protocol(
    control_owner: _control.CounterKeyedGlobalInitializerControlOwner,
    *,
    protocol_policy: object,
    protocol_role_sha256: object,
) -> CounterKeyedInitializerProtocolOwner:
    """Certify the checkpoint-twenty-seven protocol-allocation successor."""

    if type(protocol_policy) is not str:
        raise TypeError("protocol_policy must be exact text")
    if protocol_policy != PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_PROTOCOL_POLICY:
        raise ValueError("only the exported initializer protocol is supported")
    role = _thinning._require_sha256(protocol_role_sha256, name="protocol_role_sha256")
    if type(control_owner) is not _control.CounterKeyedGlobalInitializerControlOwner:
        raise TypeError("control_owner has the wrong exact type")
    parent = control_owner._require_live_binding()
    certificate = _make_certificate(parent, protocol_role_sha256=role)
    owner = CounterKeyedInitializerProtocolOwner(
        control_owner,
        role,
        certificate,
        _construction_token=_OWNER_TOKEN,
    )
    owner._require_live_binding()
    return owner


def require_matching_plugin_bridge_counter_keyed_initializer_protocol(
    control_owner: _control.CounterKeyedGlobalInitializerControlOwner,
    owner: CounterKeyedInitializerProtocolOwner,
    *,
    protocol_policy: object,
    protocol_role_sha256: object,
) -> CounterKeyedInitializerProtocolOwner:
    """Require exact checkpoint-26 identity, role, policy, and live custody."""

    if type(protocol_policy) is not str:
        raise TypeError("protocol_policy must be exact text")
    if protocol_policy != PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_PROTOCOL_POLICY:
        raise ValueError("only the exported initializer protocol is supported")
    role = _thinning._require_sha256(protocol_role_sha256, name="protocol_role_sha256")
    if type(owner) is not CounterKeyedInitializerProtocolOwner:
        raise TypeError("owner has the wrong exact initializer protocol type")
    if owner.control_owner is not control_owner:
        raise ValueError("initializer protocol owner uses another checkpoint-26 owner")
    if owner.certificate.protocol_role_sha256 != role:
        raise ValueError("initializer protocol owner uses another role")
    owner._require_live_binding()
    return owner


def validate_plugin_bridge_counter_keyed_initializer_protocol_certificate(
    control_owner: _control.CounterKeyedGlobalInitializerControlOwner,
    owner: CounterKeyedInitializerProtocolOwner,
    *,
    protocol_policy: object,
    protocol_role_sha256: object,
) -> CounterKeyedInitializerProtocolCertificate:
    """Return the reconstructed live checkpoint-twenty-seven certificate."""

    return require_matching_plugin_bridge_counter_keyed_initializer_protocol(
        control_owner,
        owner,
        protocol_policy=protocol_policy,
        protocol_role_sha256=protocol_role_sha256,
    ).certificate


__all__ = [
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_PROTOCOL_SCHEMA_VERSION",
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_PROTOCOL_POLICY",
    "PLUGIN_BRIDGE_COUNTER_KEYED_INITIALIZER_PROTOCOL_SCOPE",
    "INITIALIZER_STRATEGY_ENUMERATION",
    "INITIALIZER_STRATEGY_REJECTION",
    "INITIALIZER_STRATEGY_SIR",
    "INITIALIZER_STRATEGY_REFERENCE",
    "INITIALIZER_STRATEGIES",
    "INITIALIZER_STAGE_ENUMERATION_SELECTION",
    "INITIALIZER_STAGE_REJECTION_ATTEMPT",
    "INITIALIZER_STAGE_SIR_PARTICLE",
    "INITIALIZER_STAGE_SIR_RESAMPLE",
    "INITIALIZER_STAGE_REFERENCE_CANDIDATE",
    "INITIALIZER_ROLE_ENUMERATION_SELECTION",
    "INITIALIZER_ROLE_REJECTION_ATTEMPT",
    "INITIALIZER_ROLE_SIR_PARTICLE",
    "INITIALIZER_ROLE_SIR_RESAMPLE",
    "INITIALIZER_ROLE_REFERENCE_CANDIDATE",
    "INITIALIZER_STAGE_ROLES",
    "COUNTER_KEYED_INITIALIZER_PROTOCOL_MAX_REJECTION_ATTEMPTS",
    "COUNTER_KEYED_INITIALIZER_PROTOCOL_MAX_SIR_PARTICLES",
    "CounterKeyedInitializerProtocolCertificate",
    "CounterKeyedInitializerProtocolEntry",
    "CounterKeyedInitializerProtocolResult",
    "CounterKeyedInitializerProtocolOwner",
    "PluginBridgeCounterKeyedInitializerProtocolError",
    "certify_plugin_bridge_counter_keyed_initializer_protocol",
    "require_matching_plugin_bridge_counter_keyed_initializer_protocol",
    "validate_plugin_bridge_counter_keyed_initializer_protocol_certificate",
]
