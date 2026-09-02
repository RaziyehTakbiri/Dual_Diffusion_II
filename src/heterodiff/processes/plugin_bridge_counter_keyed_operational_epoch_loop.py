"""Counter-keyed operational epochs over the frozen thinning parents.

Checkpoint twenty-three cannot drive an adaptive checkpoint-nineteen loop with
its ``jump_proposal`` and ``terminal_wait`` domains alone.  A waiting draw must
choose its stream before it reveals whether a proposal is due, while the
former domain is restricted to an actual proposal and the latter to a terminal
wait.  This successor therefore leaves checkpoint twenty-three unchanged and
adds one disjoint direct domain, ``operational_epoch`` (tag 6).

At an active boundary, one epoch stream owns the complete checkpoint-nineteen
wait -> checkpoint-twenty-one evidenced route -> potential/rate -> acceptance
sequence.  The same epoch may instead end with an active right-endpoint wait.
A deterministic structural-zero or zero-duration terminal uses the frozen
checkpoint-twenty-three ``terminal_wait`` receipt and consumes no words.

The aggregate is intentionally distinct from checkpoints twenty through
twenty-three: those aggregates certify one sequential caller stream or a
post-hoc keyed-false parent result.  This module accepts no caller RNG.  It
retains exact checkpoint-twenty proposal iterations, checkpoint-twenty-one
route evidence, and checkpoint-twenty-three lineage transitions, and replays
every address-local stream in the same runtime.  It is not an exact analytic
path law, an independence claim, a drift or initializer, or a full sampler.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import platform
import sys
from typing import Dict, Mapping, Optional, Tuple

import numpy as np

try:
    from heterodiff.processes import (
        plugin_bridge_continuous_route_evidence as _route_evidence,
    )
    from heterodiff.processes import (
        plugin_bridge_counter_keyed_lineage_contract as _lineage,
    )
    from heterodiff.processes import (
        plugin_bridge_operational_thinning as _thinning,
    )
    from heterodiff.processes import (
        plugin_bridge_operational_thinning_loop as _loop,
    )
    from heterodiff.processes import (
        plugin_bridge_operational_thinning_loop_route_evidence as _loop_route,
    )
except ModuleNotFoundError as error:  # pragma: no cover - subprocess tested
    if error.name == "torch" or "optional PyTorch" in str(error):
        raise ModuleNotFoundError(
            "counter-keyed operational epoch loops require the optional "
            "PyTorch reference dependency; install the 'reference' extra"
        ) from error
    raise
from heterodiff.processes import plugin_bridge_sampler as _sampler
from heterodiff.processes.plugin_bridge_sampler import ReferenceCandidateIntensity
from heterodiff.processes.reversible_hybrid_reference import (
    HybridJumpKind,
    HybridJumpRates,
    HybridReferenceJumpProposal,
    MAX_HYBRID_STATE_COORDINATES,
)
from heterodiff.theory.configuration_reference import (
    MAX_CONFIGURATION_CARDINALITY,
    MAX_TRANSFORMED_COORDINATE_DIMENSION,
    TransformedConfiguration,
    TransformedEvent,
)


PLUGIN_BRIDGE_COUNTER_KEYED_OPERATIONAL_EPOCH_LOOP_SCHEMA_VERSION = (
    "plugin-bridge-counter-keyed-operational-epoch-loop-v1"
)
PLUGIN_BRIDGE_COUNTER_KEYED_OPERATIONAL_EPOCH_LOOP_POLICY = (
    "exact-checkpoint23-owner-binding;direct-operational-epoch-tag6;"
    "active-boundary-wait-route-accept-or-terminal;"
    "deterministic-checkpoint23-terminal-wait-zero-word;"
    "checkpoint20-iteration-checkpoint21-route-evidence;"
    "checkpoint23-inline-lineage-transition;accepted-parent-refresh;"
    "rejection-parent-identity-reuse;bounded-cap-refusal;"
    "same-runtime-address-local-replay;recorded-no-upper-counter-carry;"
    "no-caller-rng;legacy-jump-proposal-unconsumed-v1"
)
PLUGIN_BRIDGE_COUNTER_KEYED_OPERATIONAL_EPOCH_LOOP_SCOPE = (
    "checkpoint17-operational-surrogate-target;"
    "bounded-successful-return-operational-epoch-transcript;"
    "direct-run-domain-step-completed-proposals-addresses;"
    "active-tag6-wait-route-accept-or-right-endpoint-terminal;"
    "deterministic-tag2-terminal-invocation-with-zero-raw-words;"
    "complete-route-evidence-and-live-lineage-per-proposal;"
    "not-checkpoint23-jump-proposal-stream-consumption;"
    "not-checkpoint22-proposal-keyed-execution;"
    "not-cross-epoch-sequential-stream;not-statistical-independence;"
    "not-physical-randomness;not-exact-categorical-integer-or-gaussian-law;"
    "not-analytic-output-law;not-unconditional-completion;not-liveness;"
    "not-exact-real-time-poisson-or-ctmc;not-exact-frozen-jump-law;"
    "not-analytic-or-conditional-target;not-stationarity;"
    "not-initializer-or-brownian-consumption;not-brownian-coupling;"
    "not-drift;not-path;not-strang;not-full-sampler;"
    "not-runtime-portable;not-cryptographic-authentication"
)

COUNTER_KEY_DOMAIN_OPERATIONAL_EPOCH = "operational_epoch"
COUNTER_KEY_DOMAIN_TAG_OPERATIONAL_EPOCH = 6
COUNTER_KEYED_OPERATIONAL_EPOCH_ADDRESS_LAYOUT = (
    "key=(run_id,6);counter=(0,step_index,0,completed_proposals)"
)

COUNTER_KEYED_OPERATIONAL_EPOCH_MAX_PROPOSALS = (
    _loop.OPERATIONAL_THINNING_LOOP_MAX_PROPOSALS
)
COUNTER_KEYED_OPERATIONAL_EPOCH_MAX_STREAM_RECORDS = (
    COUNTER_KEYED_OPERATIONAL_EPOCH_MAX_PROPOSALS + 1
)
_MAX_ACCEPTANCE_WORDS = _thinning.OPERATIONAL_THINNING_MAX_BERNOULLI_TRIALS * math.ceil(
    _thinning.OPERATIONAL_THINNING_MAX_RATIO_BITS
    / _thinning.OPERATIONAL_THINNING_RAW_WORD_BITS
)
COUNTER_KEYED_OPERATIONAL_EPOCH_MAX_RECORDED_RAW64_WORDS = (
    COUNTER_KEYED_OPERATIONAL_EPOCH_MAX_PROPOSALS
    * (_thinning.OPERATIONAL_THINNING_MAX_WAITING_RAW64_WORDS + _MAX_ACCEPTANCE_WORDS)
)

_TERMINAL_ACTIVE_EPOCH = "active_operational_epoch_right_endpoint"
_TERMINAL_DETERMINISTIC_WAIT = "deterministic_checkpoint23_terminal_wait"
_TERMINAL_MODES = (_TERMINAL_ACTIVE_EPOCH, _TERMINAL_DETERMINISTIC_WAIT)
_STOP_REFERENCE_ZERO = "reference_intensity_zero"
_STOP_RIGHT_ENDPOINT = "right_endpoint_exhausted"

_CERTIFICATE_TOKEN = object()
_ADDRESS_TOKEN = object()
_STREAM_TOKEN = object()
_PROPOSAL_TOKEN = object()
_TERMINAL_TOKEN = object()
_RESULT_TOKEN = object()
_OWNER_TOKEN = object()
_ZERO_SHA256 = "0" * 64


class PluginBridgeCounterKeyedOperationalEpochLoopError(ArithmeticError):
    """Raised when an address-local epoch transcript cannot be certified."""


def _without(values: Mapping[str, object], *names: str) -> Mapping[str, object]:
    omitted = set(names)
    return {name: value for name, value in values.items() if name not in omitted}


def _exact_bool(value: object, *, name: str) -> bool:
    if type(value) is not bool:
        raise TypeError("%s must be boolean" % name)
    return value


def _exact_nonnegative_integer(value: object, *, name: str) -> int:
    return _loop._exact_nonnegative_integer(value, name=name)


def _proposal_budget(value: object) -> int:
    return _loop._proposal_budget(value)


def _clock_float(value: object, *, name: str) -> float:
    return _loop._clock_float(value, name=name)


def _same_float(left: object, right: object) -> bool:
    return _thinning._same_float(left, right)


def _snapshot_matches(
    left: _route_evidence.PhiloxRouteStateSnapshot,
    right: _route_evidence.PhiloxRouteStateSnapshot,
) -> bool:
    checked_left = _route_evidence._validate_snapshot(left)
    checked_right = _route_evidence._validate_snapshot(right)
    return all(
        getattr(checked_left, name) == getattr(checked_right, name)
        for name in _route_evidence._snapshot_fields()
    )


def _same_configuration_event_identities(left: object, right: object) -> bool:
    if type(left) is not tuple or type(right) is not tuple:
        return False
    return len(left) == len(right) and all(
        left_event is right_event for left_event, right_event in zip(left, right)
    )


def _require_no_recorded_counter_carry(
    initial: _route_evidence.PhiloxRouteStateSnapshot,
    final: _route_evidence.PhiloxRouteStateSnapshot,
) -> None:
    checked_initial = _route_evidence._validate_snapshot(initial)
    checked_final = _route_evidence._validate_snapshot(final)
    if checked_final.key != checked_initial.key:
        raise PluginBridgeCounterKeyedOperationalEpochLoopError(
            "an operational epoch changed its Philox key"
        )
    if checked_final.counter[1:] != checked_initial.counter[1:]:
        raise PluginBridgeCounterKeyedOperationalEpochLoopError(
            "an operational epoch carried into an address counter limb"
        )


def _preflight_raw_words(words: object, *, maximum: int, name: str) -> None:
    if type(words) is not tuple:
        raise TypeError("%s must be an exact tuple" % name)
    if len(words) > maximum:
        raise ValueError("%s exceeds its resource bound" % name)


def _canonical_record_context(
    context: object,
    *,
    dimension: int,
    name: str,
) -> Tuple[float, ...]:
    if type(context) is not tuple:
        raise TypeError("%s must be an exact tuple" % name)
    if len(context) != dimension:
        raise ValueError("%s dimension differs" % name)
    checked = _loop._validated_context(
        context,
        dimension=dimension,
        name=name,
    )
    for supplied, canonical in zip(context, checked):
        if type(supplied) is not float:
            raise TypeError("%s entries must be exact floats" % name)
        if not _same_float(supplied, canonical):
            raise ValueError("%s entries must be canonical float64 values" % name)
    return checked


def _preflight_configuration_resources(configuration: object, *, name: str) -> None:
    if type(configuration) is not tuple:
        raise TypeError("%s must be an exact tuple" % name)
    if len(configuration) > MAX_CONFIGURATION_CARDINALITY:
        raise ValueError("%s exceeds its cardinality bound" % name)
    coordinate_count = 0
    for index, event in enumerate(configuration):
        if type(event) is not TransformedEvent:
            raise TypeError("%s event %d has the wrong exact type" % (name, index))
        if type(event.coordinates) is not tuple:
            raise TypeError("%s event %d coordinates must be a tuple" % (name, index))
        if len(event.coordinates) > MAX_TRANSFORMED_COORDINATE_DIMENSION:
            raise ValueError(
                "%s event %d coordinates exceed their bound" % (name, index)
            )
        coordinate_count += len(event.coordinates)
        if coordinate_count > MAX_HYBRID_STATE_COORDINATES:
            raise ValueError("%s coordinates exceed their aggregate bound" % name)


def _preflight_route_candidate(route: object, *, name: str) -> None:
    if type(route) is not _thinning.OperationalReferenceRouteDraw:
        raise TypeError("%s has the wrong exact type" % name)
    candidate = route.candidate
    if type(candidate) is not _thinning.ProcessValidReferenceJump:
        raise TypeError("%s candidate has the wrong exact type" % name)
    if type(candidate.schema_version) is not str:
        raise TypeError("%s candidate schema must be exact text" % name)
    if type(candidate.contract_scope) is not str:
        raise TypeError("%s candidate scope must be exact text" % name)
    if candidate.schema_version != _sampler.PLUGIN_BRIDGE_REFERENCE_PROPOSAL_SCHEMA:
        raise ValueError("%s candidate schema differs" % name)
    if candidate.contract_scope != _sampler.PLUGIN_BRIDGE_REFERENCE_PROPOSAL_SCOPE:
        raise ValueError("%s candidate scope differs" % name)
    proposal = candidate.proposal
    if type(proposal) is not HybridReferenceJumpProposal:
        raise TypeError("%s proposal has the wrong exact type" % name)
    _preflight_configuration_resources(
        proposal.source_configuration,
        name="%s proposal source configuration" % name,
    )
    _preflight_configuration_resources(
        proposal.destination_configuration,
        name="%s proposal destination configuration" % name,
    )
    for event_name, event in (
        ("source event", proposal.source_event),
        ("destination event", proposal.destination_event),
    ):
        if event is not None:
            _preflight_configuration_resources(
                (event,),
                name="%s proposal %s" % (name, event_name),
            )
    if type(proposal.kind) is not HybridJumpKind:
        raise TypeError("%s proposal kind has the wrong exact type" % name)
    if type(proposal.base_rates) is not HybridJumpRates:
        raise TypeError("%s proposal rates have the wrong exact type" % name)
    for field in ("birth", "death", "replacement", "total"):
        if type(getattr(proposal.base_rates, field)) is not float:
            raise TypeError(
                "%s proposal rate %s must be an exact float" % (name, field)
            )
    source_index = proposal.source_occurrence_index
    if source_index is not None:
        if type(source_index) is not int:
            raise TypeError("%s proposal source index must be an exact integer" % name)
        if not 0 <= source_index < len(proposal.source_configuration):
            raise ValueError("%s proposal source index exceeds its bound" % name)
    _sampler._require_exact_candidate_representation(candidate)
    multiplicity = candidate.factorization.source_event_multiplicity
    if not 1 <= multiplicity <= max(1, len(proposal.source_configuration)):
        raise ValueError("%s proposal source multiplicity exceeds its bound" % name)


def _preflight_route_evidence_resources(evidence: object) -> None:
    if type(evidence) is not _route_evidence.OperationalReferenceRouteEvidence:
        raise TypeError("route evidence has the wrong exact type")
    _preflight_route_candidate(evidence.route_draw, name="evidence route draw")


def _preflight_iteration_resources(iteration: object) -> None:
    if type(iteration) is not _loop.OperationalProposalIteration:
        raise TypeError("iteration has the wrong exact type")
    waiting = iteration.waiting_draw
    decision = iteration.decision
    if type(waiting) is not _thinning.OperationalWaitingTimeDraw:
        raise TypeError("iteration waiting draw has the wrong exact type")
    if type(decision) is not _thinning.OperationalAcceptanceDecision:
        raise TypeError("iteration decision has the wrong exact type")
    _preflight_route_candidate(iteration.route_draw, name="iteration route draw")
    _preflight_raw_words(
        waiting.raw_words,
        maximum=_thinning.OPERATIONAL_THINNING_MAX_WAITING_RAW64_WORDS,
        name="iteration waiting raw words",
    )
    _preflight_raw_words(
        decision.raw_words,
        maximum=_MAX_ACCEPTANCE_WORDS,
        name="iteration acceptance raw words",
    )


def _preflight_lineage_state_resources(state: object, *, name: str) -> None:
    if type(state) is not _lineage.OperationalLineageState:
        raise TypeError("%s has the wrong exact type" % name)
    if type(state.occurrences) is not tuple:
        raise TypeError("%s occurrences must be an exact tuple" % name)
    if type(state.retired_identifiers) is not tuple:
        raise TypeError("%s retired identifiers must be an exact tuple" % name)
    if type(state.model_configuration) is not tuple:
        raise TypeError("%s model configuration must be an exact tuple" % name)
    if len(state.occurrences) > _lineage.MAX_CONFIGURATION_CARDINALITY:
        raise ValueError("%s live occurrences exceed their bound" % name)
    if (
        len(state.occurrences) + len(state.retired_identifiers)
        > _lineage.MAX_OPERATIONAL_LINEAGE_IDENTIFIERS
    ):
        raise ValueError("%s identifier ledger exceeds its bound" % name)
    if len(state.model_configuration) != len(state.occurrences):
        raise ValueError("%s model projection length differs" % name)
    for index, (event, occurrence) in enumerate(
        zip(state.model_configuration, state.occurrences)
    ):
        if type(occurrence) is not _lineage.OperationalLineagedOccurrence:
            raise TypeError("%s occurrence %d has the wrong exact type" % (name, index))
        if event is not occurrence.event:
            raise ValueError("%s model projection event identity differs" % name)


def _runtime_sha256() -> str:
    if COUNTER_KEY_DOMAIN_TAG_OPERATIONAL_EPOCH in tuple(
        _lineage.COUNTER_KEY_DOMAIN_TAGS.values()
    ):
        raise ValueError("the operational-epoch tag collides with checkpoint 23")
    if COUNTER_KEYED_OPERATIONAL_EPOCH_MAX_PROPOSALS != 64:
        raise ValueError("the operational-epoch proposal maximum changed")
    probe = np.random.Generator(
        np.random.Philox(
            key=np.asarray(
                (7, COUNTER_KEY_DOMAIN_TAG_OPERATIONAL_EPOCH), dtype=np.uint64
            ),
            counter=np.asarray((0, 11, 0, 13), dtype=np.uint64),
        )
    )
    snapshot = _route_evidence._capture_philox_state(probe)
    return _thinning._semantic_digest(
        {
            "domain": "plugin-bridge-counter-keyed-operational-epoch-runtime-v1",
            "python_implementation": sys.implementation.name,
            "python_version": platform.python_version(),
            "platform_system": platform.system(),
            "platform_machine": platform.machine(),
            "numpy_version": np.__version__,
            "philox_type_module": np.random.Philox.__module__,
            "philox_type_name": np.random.Philox.__name__,
            "probe_snapshot_sha256": snapshot.snapshot_sha256,
            "snapshot_schema": (
                _route_evidence.PLUGIN_BRIDGE_PHILOX_ROUTE_STATE_SCHEMA_VERSION
            ),
            "policy": PLUGIN_BRIDGE_COUNTER_KEYED_OPERATIONAL_EPOCH_LOOP_POLICY,
            "scope": PLUGIN_BRIDGE_COUNTER_KEYED_OPERATIONAL_EPOCH_LOOP_SCOPE,
            "address_layout": COUNTER_KEYED_OPERATIONAL_EPOCH_ADDRESS_LAYOUT,
            "operational_epoch_domain": COUNTER_KEY_DOMAIN_OPERATIONAL_EPOCH,
            "operational_epoch_tag": COUNTER_KEY_DOMAIN_TAG_OPERATIONAL_EPOCH,
            "checkpoint23_domain_tags": tuple(_lineage.COUNTER_KEY_DOMAIN_TAGS.items()),
            "terminal_modes": _TERMINAL_MODES,
            "stop_precedence": (
                _STOP_REFERENCE_ZERO,
                _STOP_RIGHT_ENDPOINT,
                "deterministic-terminal-before-active-cap",
            ),
            "maximum_proposals": COUNTER_KEYED_OPERATIONAL_EPOCH_MAX_PROPOSALS,
            "maximum_stream_records": (
                COUNTER_KEYED_OPERATIONAL_EPOCH_MAX_STREAM_RECORDS
            ),
            "maximum_recorded_raw64_words": (
                COUNTER_KEYED_OPERATIONAL_EPOCH_MAX_RECORDED_RAW64_WORDS
            ),
            "recorded_no_upper_counter_carry": True,
            "binary64_probe": _thinning._require_binary64_environment(),
        }
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedOperationalEpochLoopCertificate:
    """Transitive certificate for the checkpoint-twenty-four coordinator."""

    schema_version: str
    certificate_scope: str
    epoch_policy: str
    epoch_role_sha256: str
    process_parameter_sha256: str
    checkpoint23_certificate_sha256: str
    checkpoint23_role_sha256: str
    checkpoint23_runtime_sha256: str
    checkpoint22_certificate_sha256: str
    loop_certificate_sha256: str
    route_evidence_certificate_sha256: str
    thinning_certificate_sha256: str
    rate_certificate_sha256: str
    epoch_runtime_sha256: str
    philox_snapshot_schema_version: str
    rng_bit_generator: str
    address_layout: str
    operational_epoch_domain: str
    operational_epoch_domain_tag: int
    maximum_uint64: int
    maximum_proposals: int
    maximum_stream_records: int
    maximum_recorded_raw64_words: int
    maximum_lineage_identifiers: int
    maximum_live_coordinates: int
    base_context_dimension: int
    residual_context_dimension: int
    exact_checkpoint23_owner_binding_certified: bool
    direct_unhashed_operational_epoch_address_certified: bool
    disjoint_checkpoint23_domain_tag_certified: bool
    same_runtime_epoch_reconstruction_certified: bool
    actual_operational_epoch_consumption_certified: bool
    active_wait_route_accept_same_stream_certified: bool
    active_epoch_terminal_certified: bool
    deterministic_checkpoint23_terminal_wait_certified: bool
    deterministic_terminal_before_cap_certified: bool
    complete_route_evidence_per_proposal_certified: bool
    accepted_state_refresh_certified: bool
    rejection_parent_identity_reuse_certified: bool
    live_lineage_transition_per_proposal_certified: bool
    terminal_exact_lineage_state_reuse_certified: bool
    bounded_successful_interval_completion_certified: bool
    same_runtime_address_local_replay_certified: bool
    no_caller_rng_certified: bool
    recorded_upper_counter_limb_preservation_certified: bool
    identifier_excluded_from_model_projection_certified: bool
    checkpoint23_jump_proposal_stream_consumption_certified: bool
    checkpoint22_proposal_keyed_execution_certified: bool
    checkpoint22_stream_consumption_certified: bool
    cross_epoch_sequential_stream_certified: bool
    statistical_independence_certified: bool
    physical_randomness_certified: bool
    global_run_id_uniqueness_certified: bool
    duplicate_address_use_prevention_certified: bool
    lineage_fork_prevention_certified: bool
    exact_categorical_law_certified: bool
    exact_integer_law_certified: bool
    exact_gaussian_law_certified: bool
    analytic_output_law_certified: bool
    exact_active_controlled_total_exit_computed: bool
    analytic_target_preserved: bool
    conditional_posterior_or_doob_target: bool
    rounded_stationarity_certified: bool
    unconditional_local_completion_certified: bool
    unconditional_exact_frozen_jump_law_certified: bool
    exact_real_time_poisson_or_ctmc_path: bool
    sampler_liveness_certified: bool
    occurrence_stream_consumption_certified: bool
    initializer_stream_consumption_certified: bool
    brownian_stream_consumption_certified: bool
    brownian_additive_coupling_certified: bool
    continuous_drift_admissible: bool
    initializer_admissible: bool
    path_admissible: bool
    strang_sampler_admissible: bool
    full_sampler_admissible: bool
    runtime_portable: bool
    cryptographic_authentication: bool
    passed: bool
    certificate_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError(
            "CounterKeyedOperationalEpochLoopCertificate cannot be subclassed"
        )

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError("operational epoch certificates are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("operational epoch certificate fields are incomplete")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])
        _validate_certificate(self)

    def parameter_key(self) -> Tuple[object, ...]:
        return (
            "plugin-bridge-counter-keyed-operational-epoch-loop-certificate-v1",
            self.certificate_sha256,
        )

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("operational epoch certificates are not pickle objects")


def _certificate_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedOperationalEpochLoopCertificate.__annotations__)


def _certificate_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return _without(values, "certificate_sha256")


def _validate_certificate(
    certificate: object,
) -> CounterKeyedOperationalEpochLoopCertificate:
    if type(certificate) is not CounterKeyedOperationalEpochLoopCertificate:
        raise TypeError(
            "certificate must be an exact CounterKeyedOperationalEpochLoopCertificate"
        )
    expected_text = {
        "schema_version": (
            PLUGIN_BRIDGE_COUNTER_KEYED_OPERATIONAL_EPOCH_LOOP_SCHEMA_VERSION
        ),
        "certificate_scope": (PLUGIN_BRIDGE_COUNTER_KEYED_OPERATIONAL_EPOCH_LOOP_SCOPE),
        "epoch_policy": PLUGIN_BRIDGE_COUNTER_KEYED_OPERATIONAL_EPOCH_LOOP_POLICY,
        "philox_snapshot_schema_version": (
            _route_evidence.PLUGIN_BRIDGE_PHILOX_ROUTE_STATE_SCHEMA_VERSION
        ),
        "rng_bit_generator": "numpy.random.Philox",
        "address_layout": COUNTER_KEYED_OPERATIONAL_EPOCH_ADDRESS_LAYOUT,
        "operational_epoch_domain": COUNTER_KEY_DOMAIN_OPERATIONAL_EPOCH,
    }
    for name, expected in expected_text.items():
        if getattr(certificate, name) != expected:
            raise ValueError("operational epoch certificate %s differs" % name)
    for name in (
        "epoch_role_sha256",
        "process_parameter_sha256",
        "checkpoint23_certificate_sha256",
        "checkpoint23_role_sha256",
        "checkpoint23_runtime_sha256",
        "checkpoint22_certificate_sha256",
        "loop_certificate_sha256",
        "route_evidence_certificate_sha256",
        "thinning_certificate_sha256",
        "rate_certificate_sha256",
        "epoch_runtime_sha256",
        "certificate_sha256",
    ):
        _thinning._require_sha256(
            getattr(certificate, name), name="certificate.%s" % name
        )
    expected_integers = {
        "operational_epoch_domain_tag": COUNTER_KEY_DOMAIN_TAG_OPERATIONAL_EPOCH,
        "maximum_uint64": _lineage.MAX_UINT64,
        "maximum_proposals": COUNTER_KEYED_OPERATIONAL_EPOCH_MAX_PROPOSALS,
        "maximum_stream_records": COUNTER_KEYED_OPERATIONAL_EPOCH_MAX_STREAM_RECORDS,
        "maximum_recorded_raw64_words": (
            COUNTER_KEYED_OPERATIONAL_EPOCH_MAX_RECORDED_RAW64_WORDS
        ),
        "maximum_lineage_identifiers": (_lineage.MAX_OPERATIONAL_LINEAGE_IDENTIFIERS),
        "maximum_live_coordinates": _lineage.MAX_HYBRID_STATE_COORDINATES,
    }
    for name, expected in expected_integers.items():
        value = getattr(certificate, name)
        if type(value) is not int or isinstance(value, bool) or value != expected:
            raise ValueError("operational epoch certificate %s differs" % name)
    for name in ("base_context_dimension", "residual_context_dimension"):
        value = getattr(certificate, name)
        if type(value) is not int or isinstance(value, bool):
            raise TypeError("certificate.%s must be an exact integer" % name)
        if value < 0 or value > _loop._potential._MAX_CONTEXT_DIMENSION:
            raise ValueError("operational epoch certificate %s is invalid" % name)
    true_flags = (
        "exact_checkpoint23_owner_binding_certified",
        "direct_unhashed_operational_epoch_address_certified",
        "disjoint_checkpoint23_domain_tag_certified",
        "same_runtime_epoch_reconstruction_certified",
        "actual_operational_epoch_consumption_certified",
        "active_wait_route_accept_same_stream_certified",
        "active_epoch_terminal_certified",
        "deterministic_checkpoint23_terminal_wait_certified",
        "deterministic_terminal_before_cap_certified",
        "complete_route_evidence_per_proposal_certified",
        "accepted_state_refresh_certified",
        "rejection_parent_identity_reuse_certified",
        "live_lineage_transition_per_proposal_certified",
        "terminal_exact_lineage_state_reuse_certified",
        "bounded_successful_interval_completion_certified",
        "same_runtime_address_local_replay_certified",
        "no_caller_rng_certified",
        "recorded_upper_counter_limb_preservation_certified",
        "identifier_excluded_from_model_projection_certified",
        "passed",
    )
    false_flags = (
        "checkpoint23_jump_proposal_stream_consumption_certified",
        "checkpoint22_proposal_keyed_execution_certified",
        "checkpoint22_stream_consumption_certified",
        "cross_epoch_sequential_stream_certified",
        "statistical_independence_certified",
        "physical_randomness_certified",
        "global_run_id_uniqueness_certified",
        "duplicate_address_use_prevention_certified",
        "lineage_fork_prevention_certified",
        "exact_categorical_law_certified",
        "exact_integer_law_certified",
        "exact_gaussian_law_certified",
        "analytic_output_law_certified",
        "exact_active_controlled_total_exit_computed",
        "analytic_target_preserved",
        "conditional_posterior_or_doob_target",
        "rounded_stationarity_certified",
        "unconditional_local_completion_certified",
        "unconditional_exact_frozen_jump_law_certified",
        "exact_real_time_poisson_or_ctmc_path",
        "sampler_liveness_certified",
        "occurrence_stream_consumption_certified",
        "initializer_stream_consumption_certified",
        "brownian_stream_consumption_certified",
        "brownian_additive_coupling_certified",
        "continuous_drift_admissible",
        "initializer_admissible",
        "path_admissible",
        "strang_sampler_admissible",
        "full_sampler_admissible",
        "runtime_portable",
        "cryptographic_authentication",
    )
    for name in true_flags + false_flags:
        if type(getattr(certificate, name)) is not bool:
            raise TypeError("certificate.%s must be boolean" % name)
    if any(not getattr(certificate, name) for name in true_flags):
        raise ValueError("operational epoch positive flags are inconsistent")
    if any(getattr(certificate, name) for name in false_flags):
        raise ValueError("operational epoch negative flags are inconsistent")
    values = {name: getattr(certificate, name) for name in _certificate_fields()}
    expected_digest = _thinning._semantic_digest(_certificate_payload(values))
    if certificate.certificate_sha256 != expected_digest:
        raise ValueError("operational epoch certificate digest differs")
    return certificate


def _make_certificate(
    checkpoint23: _lineage.CounterKeyedLineageCertificate,
    loop_certificate: _loop.OperationalThinningLoopCertificate,
    *,
    epoch_role_sha256: str,
) -> CounterKeyedOperationalEpochLoopCertificate:
    checked = _lineage._validate_certificate(checkpoint23)
    checked_loop = _loop._validate_certificate(loop_certificate)
    if checked_loop.certificate_sha256 != checked.loop_certificate_sha256:
        raise ValueError("checkpoint 23 and loop certificates differ")
    values: Dict[str, object] = {
        "schema_version": (
            PLUGIN_BRIDGE_COUNTER_KEYED_OPERATIONAL_EPOCH_LOOP_SCHEMA_VERSION
        ),
        "certificate_scope": (PLUGIN_BRIDGE_COUNTER_KEYED_OPERATIONAL_EPOCH_LOOP_SCOPE),
        "epoch_policy": PLUGIN_BRIDGE_COUNTER_KEYED_OPERATIONAL_EPOCH_LOOP_POLICY,
        "epoch_role_sha256": epoch_role_sha256,
        "process_parameter_sha256": checked.process_parameter_sha256,
        "checkpoint23_certificate_sha256": checked.certificate_sha256,
        "checkpoint23_role_sha256": checked.contract_role_sha256,
        "checkpoint23_runtime_sha256": checked.contract_runtime_sha256,
        "checkpoint22_certificate_sha256": checked.parent_certificate_sha256,
        "loop_certificate_sha256": checked.loop_certificate_sha256,
        "route_evidence_certificate_sha256": (
            checked.route_evidence_certificate_sha256
        ),
        "thinning_certificate_sha256": checked.thinning_certificate_sha256,
        "rate_certificate_sha256": checked.rate_certificate_sha256,
        "epoch_runtime_sha256": _runtime_sha256(),
        "philox_snapshot_schema_version": (
            _route_evidence.PLUGIN_BRIDGE_PHILOX_ROUTE_STATE_SCHEMA_VERSION
        ),
        "rng_bit_generator": "numpy.random.Philox",
        "address_layout": COUNTER_KEYED_OPERATIONAL_EPOCH_ADDRESS_LAYOUT,
        "operational_epoch_domain": COUNTER_KEY_DOMAIN_OPERATIONAL_EPOCH,
        "operational_epoch_domain_tag": COUNTER_KEY_DOMAIN_TAG_OPERATIONAL_EPOCH,
        "maximum_uint64": _lineage.MAX_UINT64,
        "maximum_proposals": COUNTER_KEYED_OPERATIONAL_EPOCH_MAX_PROPOSALS,
        "maximum_stream_records": COUNTER_KEYED_OPERATIONAL_EPOCH_MAX_STREAM_RECORDS,
        "maximum_recorded_raw64_words": (
            COUNTER_KEYED_OPERATIONAL_EPOCH_MAX_RECORDED_RAW64_WORDS
        ),
        "maximum_lineage_identifiers": (_lineage.MAX_OPERATIONAL_LINEAGE_IDENTIFIERS),
        "maximum_live_coordinates": _lineage.MAX_HYBRID_STATE_COORDINATES,
        "base_context_dimension": checked_loop.base_context_dimension,
        "residual_context_dimension": checked_loop.residual_context_dimension,
        "exact_checkpoint23_owner_binding_certified": True,
        "direct_unhashed_operational_epoch_address_certified": True,
        "disjoint_checkpoint23_domain_tag_certified": True,
        "same_runtime_epoch_reconstruction_certified": True,
        "actual_operational_epoch_consumption_certified": True,
        "active_wait_route_accept_same_stream_certified": True,
        "active_epoch_terminal_certified": True,
        "deterministic_checkpoint23_terminal_wait_certified": True,
        "deterministic_terminal_before_cap_certified": True,
        "complete_route_evidence_per_proposal_certified": True,
        "accepted_state_refresh_certified": True,
        "rejection_parent_identity_reuse_certified": True,
        "live_lineage_transition_per_proposal_certified": True,
        "terminal_exact_lineage_state_reuse_certified": True,
        "bounded_successful_interval_completion_certified": True,
        "same_runtime_address_local_replay_certified": True,
        "no_caller_rng_certified": True,
        "recorded_upper_counter_limb_preservation_certified": True,
        "identifier_excluded_from_model_projection_certified": True,
        "checkpoint23_jump_proposal_stream_consumption_certified": False,
        "checkpoint22_proposal_keyed_execution_certified": False,
        "checkpoint22_stream_consumption_certified": False,
        "cross_epoch_sequential_stream_certified": False,
        "statistical_independence_certified": False,
        "physical_randomness_certified": False,
        "global_run_id_uniqueness_certified": False,
        "duplicate_address_use_prevention_certified": False,
        "lineage_fork_prevention_certified": False,
        "exact_categorical_law_certified": False,
        "exact_integer_law_certified": False,
        "exact_gaussian_law_certified": False,
        "analytic_output_law_certified": False,
        "exact_active_controlled_total_exit_computed": False,
        "analytic_target_preserved": False,
        "conditional_posterior_or_doob_target": False,
        "rounded_stationarity_certified": False,
        "unconditional_local_completion_certified": False,
        "unconditional_exact_frozen_jump_law_certified": False,
        "exact_real_time_poisson_or_ctmc_path": False,
        "sampler_liveness_certified": False,
        "occurrence_stream_consumption_certified": False,
        "initializer_stream_consumption_certified": False,
        "brownian_stream_consumption_certified": False,
        "brownian_additive_coupling_certified": False,
        "continuous_drift_admissible": False,
        "initializer_admissible": False,
        "path_admissible": False,
        "strang_sampler_admissible": False,
        "full_sampler_admissible": False,
        "runtime_portable": False,
        "cryptographic_authentication": False,
        "passed": True,
        "certificate_sha256": _ZERO_SHA256,
    }
    values["certificate_sha256"] = _thinning._semantic_digest(
        _certificate_payload(values)
    )
    return CounterKeyedOperationalEpochLoopCertificate(
        **values, _construction_token=_CERTIFICATE_TOKEN
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedOperationalEpochAddress:
    """One direct tag-6 address for an active operational boundary."""

    schema_version: str
    certificate_sha256: str
    domain: str
    domain_tag: int
    run_id: int
    step_index: int
    occurrence_serial: int
    completed_proposals: int
    philox_key: Tuple[int, int]
    philox_counter: Tuple[int, int, int, int]
    address_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CounterKeyedOperationalEpochAddress cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _ADDRESS_TOKEN:
            raise TypeError("operational epoch addresses are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("operational epoch address fields are incomplete")
        if values["schema_version"] != (
            PLUGIN_BRIDGE_COUNTER_KEYED_OPERATIONAL_EPOCH_LOOP_SCHEMA_VERSION
        ):
            raise ValueError("operational epoch address schema differs")
        _thinning._require_sha256(
            values["certificate_sha256"], name="address.certificate_sha256"
        )
        if values["domain"] != COUNTER_KEY_DOMAIN_OPERATIONAL_EPOCH:
            raise ValueError("operational epoch address domain differs")
        domain_tag = _lineage._exact_uint64(
            values["domain_tag"], name="address.domain_tag"
        )
        if domain_tag != COUNTER_KEY_DOMAIN_TAG_OPERATIONAL_EPOCH:
            raise ValueError("operational epoch address tag differs")
        run_id = _lineage._exact_uint64(values["run_id"], name="address.run_id")
        step = _lineage._exact_uint64(values["step_index"], name="address.step_index")
        occurrence = _lineage._exact_uint64(
            values["occurrence_serial"], name="address.occurrence_serial"
        )
        completed = _lineage._exact_uint64(
            values["completed_proposals"],
            name="address.completed_proposals",
        )
        if occurrence != 0:
            raise ValueError("operational epoch occurrence serial must be zero")
        if completed >= COUNTER_KEYED_OPERATIONAL_EPOCH_MAX_PROPOSALS:
            raise ValueError("operational epoch index exceeds its range")
        expected_key = (run_id, COUNTER_KEY_DOMAIN_TAG_OPERATIONAL_EPOCH)
        expected_counter = (0, step, 0, completed)
        if type(values["philox_key"]) is not tuple:
            raise TypeError("address.philox_key must be an exact tuple")
        if type(values["philox_counter"]) is not tuple:
            raise TypeError("address.philox_counter must be an exact tuple")
        if values["philox_key"] != expected_key:
            raise ValueError("operational epoch key differs from its address")
        if values["philox_counter"] != expected_counter:
            raise ValueError("operational epoch counter differs from its address")
        for index, word in enumerate(values["philox_key"]):
            _lineage._exact_uint64(word, name="address.philox_key[%d]" % index)
        for index, word in enumerate(values["philox_counter"]):
            _lineage._exact_uint64(word, name="address.philox_counter[%d]" % index)
        _thinning._require_sha256(
            values["address_sha256"], name="address.address_sha256"
        )
        expected_digest = _thinning._semantic_digest(_without(values, "address_sha256"))
        if values["address_sha256"] != expected_digest:
            raise ValueError("operational epoch address digest differs")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("operational epoch addresses are not pickle objects")


def _address_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedOperationalEpochAddress.__annotations__)


def _validate_address(address: object) -> CounterKeyedOperationalEpochAddress:
    if type(address) is not CounterKeyedOperationalEpochAddress:
        raise TypeError("address must be an exact CounterKeyedOperationalEpochAddress")
    return CounterKeyedOperationalEpochAddress(
        **{name: getattr(address, name) for name in _address_fields()},
        _construction_token=_ADDRESS_TOKEN,
    )


def _make_address(
    certificate: CounterKeyedOperationalEpochLoopCertificate,
    *,
    run_id: int,
    step_index: int,
    completed_proposals: int,
) -> CounterKeyedOperationalEpochAddress:
    checked = _validate_certificate(certificate)
    values: Dict[str, object] = {
        "schema_version": (
            PLUGIN_BRIDGE_COUNTER_KEYED_OPERATIONAL_EPOCH_LOOP_SCHEMA_VERSION
        ),
        "certificate_sha256": checked.certificate_sha256,
        "domain": COUNTER_KEY_DOMAIN_OPERATIONAL_EPOCH,
        "domain_tag": COUNTER_KEY_DOMAIN_TAG_OPERATIONAL_EPOCH,
        "run_id": run_id,
        "step_index": step_index,
        "occurrence_serial": 0,
        "completed_proposals": completed_proposals,
        "philox_key": (run_id, COUNTER_KEY_DOMAIN_TAG_OPERATIONAL_EPOCH),
        "philox_counter": (0, step_index, 0, completed_proposals),
        "address_sha256": _ZERO_SHA256,
    }
    values["address_sha256"] = _thinning._semantic_digest(
        _without(values, "address_sha256")
    )
    return CounterKeyedOperationalEpochAddress(
        **values, _construction_token=_ADDRESS_TOKEN
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedOperationalEpochStream:
    """Initially unused same-runtime Philox receipt for one active epoch."""

    certificate: CounterKeyedOperationalEpochLoopCertificate
    certificate_sha256: str
    address: CounterKeyedOperationalEpochAddress
    address_sha256: str
    initial_state: _route_evidence.PhiloxRouteStateSnapshot
    initial_snapshot_sha256: str
    initial_state_sha256: str
    buffer_is_zero: bool
    uint32_cache_is_zero: bool
    same_runtime_only: bool
    stream_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CounterKeyedOperationalEpochStream cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _STREAM_TOKEN:
            raise TypeError("operational epoch streams are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("operational epoch stream fields are incomplete")
        certificate = _validate_certificate(values["certificate"])
        if values["certificate_sha256"] != certificate.certificate_sha256:
            raise ValueError("operational epoch stream certificate differs")
        address = _validate_address(values["address"])
        if address.certificate_sha256 != certificate.certificate_sha256:
            raise ValueError("operational epoch address has another certificate")
        if values["address_sha256"] != address.address_sha256:
            raise ValueError("operational epoch address digest differs")
        snapshot = _route_evidence._validate_snapshot(values["initial_state"])
        if values["initial_snapshot_sha256"] != snapshot.snapshot_sha256:
            raise ValueError("operational epoch initial snapshot digest differs")
        if values["initial_state_sha256"] != snapshot.state_sha256:
            raise ValueError("operational epoch initial state digest differs")
        if snapshot.key != address.philox_key:
            raise ValueError("operational epoch initial key differs")
        if snapshot.counter != address.philox_counter:
            raise ValueError("operational epoch initial counter differs")
        if snapshot.buffer != (0, 0, 0, 0) or snapshot.buffer_pos != 4:
            raise ValueError("operational epoch initial buffer is not empty")
        if snapshot.has_uint32 != 0 or snapshot.uinteger != 0:
            raise ValueError("operational epoch initial uint32 cache is not empty")
        expected_flags = {
            "buffer_is_zero": True,
            "uint32_cache_is_zero": True,
            "same_runtime_only": True,
        }
        for name, expected in expected_flags.items():
            if _exact_bool(values[name], name="stream.%s" % name) is not expected:
                raise ValueError("operational epoch stream %s differs" % name)
        for name in (
            "certificate_sha256",
            "address_sha256",
            "initial_snapshot_sha256",
            "initial_state_sha256",
            "stream_sha256",
        ):
            _thinning._require_sha256(values[name], name="stream.%s" % name)
        expected_digest = _thinning._semantic_digest(
            _without(
                values,
                "certificate",
                "address",
                "initial_state",
                "stream_sha256",
            )
        )
        if values["stream_sha256"] != expected_digest:
            raise ValueError("operational epoch stream digest differs")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("operational epoch streams are not pickle objects")


def _stream_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedOperationalEpochStream.__annotations__)


def _validate_stream_record(stream: object) -> CounterKeyedOperationalEpochStream:
    if type(stream) is not CounterKeyedOperationalEpochStream:
        raise TypeError("stream must be an exact CounterKeyedOperationalEpochStream")
    return CounterKeyedOperationalEpochStream(
        **{name: getattr(stream, name) for name in _stream_fields()},
        _construction_token=_STREAM_TOKEN,
    )


def _make_stream(
    certificate: CounterKeyedOperationalEpochLoopCertificate,
    address: CounterKeyedOperationalEpochAddress,
) -> CounterKeyedOperationalEpochStream:
    checked_certificate = _validate_certificate(certificate)
    checked_address = _validate_address(address)
    bit_generator = np.random.Philox(
        key=np.asarray(checked_address.philox_key, dtype=np.uint64),
        counter=np.asarray(checked_address.philox_counter, dtype=np.uint64),
    )
    snapshot = _route_evidence._capture_philox_state(np.random.Generator(bit_generator))
    values: Dict[str, object] = {
        "certificate": checked_certificate,
        "certificate_sha256": checked_certificate.certificate_sha256,
        "address": checked_address,
        "address_sha256": checked_address.address_sha256,
        "initial_state": snapshot,
        "initial_snapshot_sha256": snapshot.snapshot_sha256,
        "initial_state_sha256": snapshot.state_sha256,
        "buffer_is_zero": True,
        "uint32_cache_is_zero": True,
        "same_runtime_only": True,
        "stream_sha256": _ZERO_SHA256,
    }
    values["stream_sha256"] = _thinning._semantic_digest(
        _without(
            values,
            "certificate",
            "address",
            "initial_state",
            "stream_sha256",
        )
    )
    return CounterKeyedOperationalEpochStream(
        **values, _construction_token=_STREAM_TOKEN
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedOperationalEpochProposal:
    """One actual proposal executed from one direct tag-6 epoch stream."""

    certificate: CounterKeyedOperationalEpochLoopCertificate
    certificate_sha256: str
    run_id: int
    step_index: int
    proposal_index: int
    epoch_stream: CounterKeyedOperationalEpochStream
    epoch_stream_sha256: str
    epoch_address_sha256: str
    iteration: _loop.OperationalProposalIteration
    iteration_sha256: str
    route_evidence: _route_evidence.OperationalReferenceRouteEvidence
    route_evidence_sha256: str
    lineage_transition: _lineage.OperationalLineageTransition
    lineage_transition_sha256: str
    stream_final_state: _route_evidence.PhiloxRouteStateSnapshot
    stream_final_snapshot_sha256: str
    stream_final_state_sha256: str
    pre_lineage_state_sha256: str
    post_lineage_state_sha256: str
    accepted: bool
    same_stream_wait_route_accept: bool
    operational_epoch_stream_consumed: bool
    recorded_upper_counter_limbs_unchanged: bool
    proposal_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CounterKeyedOperationalEpochProposal cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _PROPOSAL_TOKEN:
            raise TypeError("operational epoch proposals are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("operational epoch proposal fields are incomplete")
        certificate = _validate_certificate(values["certificate"])
        if values["certificate_sha256"] != certificate.certificate_sha256:
            raise ValueError("operational epoch proposal certificate differs")
        run_id = _lineage._exact_uint64(values["run_id"], name="proposal.run_id")
        step_index = _lineage._exact_uint64(
            values["step_index"], name="proposal.step_index"
        )
        proposal_index = _lineage._exact_uint64(
            values["proposal_index"], name="proposal.proposal_index"
        )
        if proposal_index >= COUNTER_KEYED_OPERATIONAL_EPOCH_MAX_PROPOSALS:
            raise ValueError("operational epoch proposal index exceeds its range")
        stream = _validate_stream_record(values["epoch_stream"])
        if stream.certificate is not certificate:
            raise ValueError("operational epoch proposal stream has another owner")
        if values["epoch_stream_sha256"] != stream.stream_sha256:
            raise ValueError("operational epoch proposal stream digest differs")
        if values["epoch_address_sha256"] != stream.address_sha256:
            raise ValueError("operational epoch proposal address digest differs")
        address = stream.address
        if (
            address.run_id != run_id
            or address.step_index != step_index
            or address.completed_proposals != proposal_index
        ):
            raise ValueError("operational epoch proposal address differs")
        iteration = values["iteration"]
        _preflight_iteration_resources(iteration)
        _loop.OperationalProposalIteration(
            **{name: getattr(iteration, name) for name in _loop._iteration_fields()},
            _construction_token=_loop._ITERATION_TOKEN,
        )
        if iteration.certificate_sha256 != certificate.loop_certificate_sha256:
            raise ValueError("operational epoch iteration has another certificate")
        if values["iteration_sha256"] != iteration.iteration_sha256:
            raise ValueError("operational epoch iteration digest differs")
        if iteration.proposal_index != proposal_index:
            raise ValueError("operational epoch iteration index differs")
        supplied_evidence = values["route_evidence"]
        _preflight_route_evidence_resources(supplied_evidence)
        evidence = _loop_route._validate_route_evidence_record(supplied_evidence)
        if evidence.certificate_sha256 != (
            certificate.route_evidence_certificate_sha256
        ):
            raise ValueError("operational epoch evidence has another certificate")
        if values["route_evidence_sha256"] != evidence.evidence_sha256:
            raise ValueError("operational epoch evidence digest differs")
        _loop_route._require_iteration_evidence_binding(iteration, evidence)
        if evidence.route_draw is not iteration.route_draw:
            raise ValueError("proposal evidence does not own the exact route record")
        transition = values["lineage_transition"]
        if type(transition) is not _lineage.OperationalLineageTransition:
            raise TypeError("proposal lineage transition has the wrong exact type")
        if transition.parent_iteration is not iteration:
            raise ValueError("proposal transition has another parent iteration")
        if transition.parent_route_evidence is not supplied_evidence:
            raise ValueError("proposal transition has another route evidence")
        _preflight_lineage_state_resources(
            transition.pre_state, name="proposal transition pre-state"
        )
        _preflight_lineage_state_resources(
            transition.post_state, name="proposal transition post-state"
        )
        checked_transition = _lineage._validate_transition(transition)
        if checked_transition.certificate_sha256 != (
            certificate.checkpoint23_certificate_sha256
        ):
            raise ValueError("proposal transition has another certificate")
        if values["lineage_transition_sha256"] != (
            checked_transition.transition_sha256
        ):
            raise ValueError("proposal lineage transition digest differs")
        if (
            checked_transition.run_id != run_id
            or checked_transition.step_index != step_index
            or checked_transition.proposal_index != proposal_index
        ):
            raise ValueError("proposal lineage transition address differs")
        final_state = _route_evidence._validate_snapshot(values["stream_final_state"])
        if values["stream_final_snapshot_sha256"] != final_state.snapshot_sha256:
            raise ValueError("proposal final snapshot digest differs")
        if values["stream_final_state_sha256"] != final_state.state_sha256:
            raise ValueError("proposal final state digest differs")
        if stream.initial_state_sha256 != iteration.rng_state_before_sha256:
            raise ValueError("proposal did not begin at its direct stream")
        if final_state.state_sha256 != iteration.rng_state_after_sha256:
            raise ValueError("proposal final stream differs from its iteration")
        _require_no_recorded_counter_carry(stream.initial_state, final_state)
        if values["pre_lineage_state_sha256"] != (checked_transition.pre_state_sha256):
            raise ValueError("proposal pre-lineage digest differs")
        if values["post_lineage_state_sha256"] != (
            checked_transition.post_state_sha256
        ):
            raise ValueError("proposal post-lineage digest differs")
        expected_flags = {
            "accepted": iteration.accepted,
            "same_stream_wait_route_accept": True,
            "operational_epoch_stream_consumed": True,
            "recorded_upper_counter_limbs_unchanged": True,
        }
        for name, expected in expected_flags.items():
            if _exact_bool(values[name], name="proposal.%s" % name) is not expected:
                raise ValueError("operational epoch proposal %s differs" % name)
        for name in (
            "certificate_sha256",
            "epoch_stream_sha256",
            "epoch_address_sha256",
            "iteration_sha256",
            "route_evidence_sha256",
            "lineage_transition_sha256",
            "stream_final_snapshot_sha256",
            "stream_final_state_sha256",
            "pre_lineage_state_sha256",
            "post_lineage_state_sha256",
            "proposal_sha256",
        ):
            _thinning._require_sha256(values[name], name="proposal.%s" % name)
        expected_digest = _thinning._semantic_digest(
            _without(
                values,
                "certificate",
                "epoch_stream",
                "iteration",
                "route_evidence",
                "lineage_transition",
                "stream_final_state",
                "proposal_sha256",
            )
        )
        if values["proposal_sha256"] != expected_digest:
            raise ValueError("operational epoch proposal digest differs")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("operational epoch proposals are not pickle objects")


def _proposal_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedOperationalEpochProposal.__annotations__)


def _validate_proposal_record(
    proposal: object,
) -> CounterKeyedOperationalEpochProposal:
    if type(proposal) is not CounterKeyedOperationalEpochProposal:
        raise TypeError(
            "proposal must be an exact CounterKeyedOperationalEpochProposal"
        )
    return CounterKeyedOperationalEpochProposal(
        **{name: getattr(proposal, name) for name in _proposal_fields()},
        _construction_token=_PROPOSAL_TOKEN,
    )


def _make_proposal(
    certificate: CounterKeyedOperationalEpochLoopCertificate,
    stream: CounterKeyedOperationalEpochStream,
    iteration: _loop.OperationalProposalIteration,
    evidence: _route_evidence.OperationalReferenceRouteEvidence,
    transition: _lineage.OperationalLineageTransition,
    final_state: _route_evidence.PhiloxRouteStateSnapshot,
    *,
    run_id: int,
    step_index: int,
) -> CounterKeyedOperationalEpochProposal:
    values: Dict[str, object] = {
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "run_id": run_id,
        "step_index": step_index,
        "proposal_index": iteration.proposal_index,
        "epoch_stream": stream,
        "epoch_stream_sha256": stream.stream_sha256,
        "epoch_address_sha256": stream.address_sha256,
        "iteration": iteration,
        "iteration_sha256": iteration.iteration_sha256,
        "route_evidence": evidence,
        "route_evidence_sha256": evidence.evidence_sha256,
        "lineage_transition": transition,
        "lineage_transition_sha256": transition.transition_sha256,
        "stream_final_state": final_state,
        "stream_final_snapshot_sha256": final_state.snapshot_sha256,
        "stream_final_state_sha256": final_state.state_sha256,
        "pre_lineage_state_sha256": transition.pre_state_sha256,
        "post_lineage_state_sha256": transition.post_state_sha256,
        "accepted": iteration.accepted,
        "same_stream_wait_route_accept": True,
        "operational_epoch_stream_consumed": True,
        "recorded_upper_counter_limbs_unchanged": True,
        "proposal_sha256": _ZERO_SHA256,
    }
    values["proposal_sha256"] = _thinning._semantic_digest(
        _without(
            values,
            "certificate",
            "epoch_stream",
            "iteration",
            "route_evidence",
            "lineage_transition",
            "stream_final_state",
            "proposal_sha256",
        )
    )
    return CounterKeyedOperationalEpochProposal(
        **values, _construction_token=_PROPOSAL_TOKEN
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedOperationalEpochTerminal:
    """The unique terminal wait for one successful keyed epoch result."""

    certificate: CounterKeyedOperationalEpochLoopCertificate
    certificate_sha256: str
    run_id: int
    step_index: int
    completed_proposals: int
    terminal_mode: str
    operational_epoch_stream: Optional[CounterKeyedOperationalEpochStream]
    operational_epoch_stream_sha256: Optional[str]
    checkpoint23_terminal_wait_stream: Optional[_lineage.CounterKeyedPhiloxStream]
    checkpoint23_terminal_wait_stream_sha256: Optional[str]
    waiting_draw: _thinning.OperationalWaitingTimeDraw
    waiting_draw_sha256: str
    stream_final_state: _route_evidence.PhiloxRouteStateSnapshot
    stream_final_snapshot_sha256: str
    stream_final_state_sha256: str
    stop_reason: str
    active_terminal: bool
    deterministic_terminal: bool
    reference_intensity_zero: bool
    zero_duration: bool
    right_endpoint_exhausted: bool
    operational_epoch_stream_consumed: bool
    checkpoint23_terminal_wait_invoked: bool
    checkpoint23_terminal_wait_raw_words_consumed: bool
    no_route_or_acceptance: bool
    recorded_upper_counter_limbs_unchanged: bool
    terminal_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CounterKeyedOperationalEpochTerminal cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _TERMINAL_TOKEN:
            raise TypeError("operational epoch terminals are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("operational epoch terminal fields are incomplete")
        certificate = _validate_certificate(values["certificate"])
        if values["certificate_sha256"] != certificate.certificate_sha256:
            raise ValueError("operational epoch terminal certificate differs")
        run_id = _lineage._exact_uint64(values["run_id"], name="terminal.run_id")
        step_index = _lineage._exact_uint64(
            values["step_index"], name="terminal.step_index"
        )
        completed = _lineage._exact_uint64(
            values["completed_proposals"],
            name="terminal.completed_proposals",
        )
        if completed > COUNTER_KEYED_OPERATIONAL_EPOCH_MAX_PROPOSALS:
            raise ValueError("terminal completed-proposal count exceeds its range")
        mode = values["terminal_mode"]
        if type(mode) is not str or mode not in _TERMINAL_MODES:
            raise ValueError("operational epoch terminal mode is unknown")
        waiting = values["waiting_draw"]
        if type(waiting) is not _thinning.OperationalWaitingTimeDraw:
            raise TypeError("terminal waiting draw has the wrong exact type")
        _preflight_raw_words(
            waiting.raw_words,
            maximum=_thinning.OPERATIONAL_THINNING_MAX_WAITING_RAW64_WORDS,
            name="terminal waiting raw words",
        )
        _thinning.OperationalWaitingTimeDraw(
            **{name: getattr(waiting, name) for name in _thinning._waiting_fields()},
            _construction_token=_thinning._WAITING_TOKEN,
        )
        if waiting.certificate_sha256 != certificate.thinning_certificate_sha256:
            raise ValueError("terminal waiting draw has another certificate")
        if waiting.candidate_due:
            raise ValueError("terminal waiting draw admitted a proposal")
        if values["waiting_draw_sha256"] != waiting.waiting_draw_sha256:
            raise ValueError("terminal waiting draw digest differs")
        final_state = _route_evidence._validate_snapshot(values["stream_final_state"])
        if values["stream_final_snapshot_sha256"] != final_state.snapshot_sha256:
            raise ValueError("terminal final snapshot digest differs")
        if values["stream_final_state_sha256"] != final_state.state_sha256:
            raise ValueError("terminal final state digest differs")
        epoch_stream = values["operational_epoch_stream"]
        terminal_stream = values["checkpoint23_terminal_wait_stream"]
        if mode == _TERMINAL_ACTIVE_EPOCH:
            if completed >= COUNTER_KEYED_OPERATIONAL_EPOCH_MAX_PROPOSALS:
                raise ValueError("an active terminal cannot occur at the epoch cap")
            checked_epoch = _validate_stream_record(epoch_stream)
            if checked_epoch.certificate is not certificate:
                raise ValueError("active terminal epoch stream has another owner")
            if terminal_stream is not None:
                raise ValueError("active terminal also supplied a tag-2 stream")
            if values["operational_epoch_stream_sha256"] != (
                checked_epoch.stream_sha256
            ):
                raise ValueError("active terminal epoch-stream digest differs")
            if values["checkpoint23_terminal_wait_stream_sha256"] is not None:
                raise ValueError("active terminal supplied a tag-2 stream digest")
            if (
                checked_epoch.address.run_id != run_id
                or checked_epoch.address.step_index != step_index
                or checked_epoch.address.completed_proposals != completed
            ):
                raise ValueError("active terminal epoch address differs")
            initial_state = checked_epoch.initial_state
            if waiting.raw_words_consumed == 0:
                raise ValueError("active terminal did not consume waiting words")
            if waiting.reference_intensity_zero or waiting.zero_duration:
                raise ValueError("active terminal was deterministically known")
        else:
            if epoch_stream is not None:
                raise ValueError("deterministic terminal supplied a tag-6 stream")
            if values["operational_epoch_stream_sha256"] is not None:
                raise ValueError("deterministic terminal supplied a tag-6 digest")
            checked_terminal = _lineage._validate_stream_record(terminal_stream)
            if checked_terminal.certificate_sha256 != (
                certificate.checkpoint23_certificate_sha256
            ):
                raise ValueError("deterministic terminal has another certificate")
            address = checked_terminal.address
            if (
                address.domain != _lineage.COUNTER_KEY_DOMAIN_TERMINAL_WAIT
                or address.run_id != run_id
                or address.step_index != step_index
                or address.proposal_index != completed
            ):
                raise ValueError("deterministic terminal tag-2 address differs")
            if values["checkpoint23_terminal_wait_stream_sha256"] != (
                checked_terminal.stream_sha256
            ):
                raise ValueError("deterministic terminal stream digest differs")
            initial_state = checked_terminal.initial_state
            if waiting.raw_words != () or waiting.raw_words_consumed != 0:
                raise ValueError("deterministic terminal consumed raw words")
            if not (waiting.reference_intensity_zero or waiting.zero_duration):
                raise ValueError("deterministic terminal was not known pre-draw")
            if not _snapshot_matches(initial_state, final_state):
                raise ValueError("deterministic terminal changed its Philox state")
        if initial_state.state_sha256 != waiting.rng_state_before_sha256:
            raise ValueError("terminal wait did not begin at its direct stream")
        if final_state.state_sha256 != waiting.rng_state_after_sha256:
            raise ValueError("terminal wait ended at another stream state")
        _require_no_recorded_counter_carry(initial_state, final_state)
        expected_reason = (
            _STOP_REFERENCE_ZERO
            if waiting.reference_intensity_zero
            else _STOP_RIGHT_ENDPOINT
        )
        if values["stop_reason"] != expected_reason:
            raise ValueError("terminal stop reason differs")
        expected_flags = {
            "active_terminal": mode == _TERMINAL_ACTIVE_EPOCH,
            "deterministic_terminal": mode == _TERMINAL_DETERMINISTIC_WAIT,
            "reference_intensity_zero": waiting.reference_intensity_zero,
            "zero_duration": waiting.zero_duration,
            "right_endpoint_exhausted": expected_reason == _STOP_RIGHT_ENDPOINT,
            "operational_epoch_stream_consumed": (mode == _TERMINAL_ACTIVE_EPOCH),
            "checkpoint23_terminal_wait_invoked": (
                mode == _TERMINAL_DETERMINISTIC_WAIT
            ),
            "checkpoint23_terminal_wait_raw_words_consumed": False,
            "no_route_or_acceptance": True,
            "recorded_upper_counter_limbs_unchanged": True,
        }
        for name, expected in expected_flags.items():
            if _exact_bool(values[name], name="terminal.%s" % name) is not expected:
                raise ValueError("operational epoch terminal %s differs" % name)
        for name in (
            "certificate_sha256",
            "waiting_draw_sha256",
            "stream_final_snapshot_sha256",
            "stream_final_state_sha256",
            "terminal_sha256",
        ):
            _thinning._require_sha256(values[name], name="terminal.%s" % name)
        for name in (
            "operational_epoch_stream_sha256",
            "checkpoint23_terminal_wait_stream_sha256",
        ):
            if values[name] is not None:
                _thinning._require_sha256(values[name], name="terminal.%s" % name)
        expected_digest = _thinning._semantic_digest(
            _without(
                values,
                "certificate",
                "operational_epoch_stream",
                "checkpoint23_terminal_wait_stream",
                "waiting_draw",
                "stream_final_state",
                "terminal_sha256",
            )
        )
        if values["terminal_sha256"] != expected_digest:
            raise ValueError("operational epoch terminal digest differs")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("operational epoch terminals are not pickle objects")


def _terminal_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedOperationalEpochTerminal.__annotations__)


def _validate_terminal_record(
    terminal: object,
) -> CounterKeyedOperationalEpochTerminal:
    if type(terminal) is not CounterKeyedOperationalEpochTerminal:
        raise TypeError(
            "terminal must be an exact CounterKeyedOperationalEpochTerminal"
        )
    return CounterKeyedOperationalEpochTerminal(
        **{name: getattr(terminal, name) for name in _terminal_fields()},
        _construction_token=_TERMINAL_TOKEN,
    )


def _make_terminal(
    certificate: CounterKeyedOperationalEpochLoopCertificate,
    *,
    run_id: int,
    step_index: int,
    completed_proposals: int,
    terminal_mode: str,
    operational_epoch_stream: Optional[CounterKeyedOperationalEpochStream],
    checkpoint23_terminal_wait_stream: Optional[_lineage.CounterKeyedPhiloxStream],
    waiting_draw: _thinning.OperationalWaitingTimeDraw,
    final_state: _route_evidence.PhiloxRouteStateSnapshot,
) -> CounterKeyedOperationalEpochTerminal:
    stop_reason = (
        _STOP_REFERENCE_ZERO
        if waiting_draw.reference_intensity_zero
        else _STOP_RIGHT_ENDPOINT
    )
    values: Dict[str, object] = {
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "run_id": run_id,
        "step_index": step_index,
        "completed_proposals": completed_proposals,
        "terminal_mode": terminal_mode,
        "operational_epoch_stream": operational_epoch_stream,
        "operational_epoch_stream_sha256": (
            None
            if operational_epoch_stream is None
            else operational_epoch_stream.stream_sha256
        ),
        "checkpoint23_terminal_wait_stream": checkpoint23_terminal_wait_stream,
        "checkpoint23_terminal_wait_stream_sha256": (
            None
            if checkpoint23_terminal_wait_stream is None
            else checkpoint23_terminal_wait_stream.stream_sha256
        ),
        "waiting_draw": waiting_draw,
        "waiting_draw_sha256": waiting_draw.waiting_draw_sha256,
        "stream_final_state": final_state,
        "stream_final_snapshot_sha256": final_state.snapshot_sha256,
        "stream_final_state_sha256": final_state.state_sha256,
        "stop_reason": stop_reason,
        "active_terminal": terminal_mode == _TERMINAL_ACTIVE_EPOCH,
        "deterministic_terminal": terminal_mode == _TERMINAL_DETERMINISTIC_WAIT,
        "reference_intensity_zero": waiting_draw.reference_intensity_zero,
        "zero_duration": waiting_draw.zero_duration,
        "right_endpoint_exhausted": stop_reason == _STOP_RIGHT_ENDPOINT,
        "operational_epoch_stream_consumed": (terminal_mode == _TERMINAL_ACTIVE_EPOCH),
        "checkpoint23_terminal_wait_invoked": (
            terminal_mode == _TERMINAL_DETERMINISTIC_WAIT
        ),
        "checkpoint23_terminal_wait_raw_words_consumed": False,
        "no_route_or_acceptance": True,
        "recorded_upper_counter_limbs_unchanged": True,
        "terminal_sha256": _ZERO_SHA256,
    }
    values["terminal_sha256"] = _thinning._semantic_digest(
        _without(
            values,
            "certificate",
            "operational_epoch_stream",
            "checkpoint23_terminal_wait_stream",
            "waiting_draw",
            "stream_final_state",
            "terminal_sha256",
        )
    )
    return CounterKeyedOperationalEpochTerminal(
        **values, _construction_token=_TERMINAL_TOKEN
    )


def _configuration_payload(
    configuration: TransformedConfiguration,
) -> Tuple[Tuple[int, Tuple[float, ...]], ...]:
    return tuple(
        (event.event_type, tuple(event.coordinates)) for event in configuration
    )


@dataclass(frozen=True, eq=False, init=False)
class CounterKeyedOperationalEpochLoopResult:
    """One bounded successful address-local epoch transcript with lineage."""

    certificate: CounterKeyedOperationalEpochLoopCertificate
    certificate_sha256: str
    run_id: int
    step_index: int
    initial_intensity: ReferenceCandidateIntensity
    initial_intensity_sha256: str
    initial_envelope: _loop.TotalizedJumpRateEnvelope
    initial_envelope_sha256: str
    initial_lineage_state: _lineage.OperationalLineageState
    initial_lineage_state_sha256: str
    base_context: Tuple[float, ...]
    base_context_sha256: str
    residual_context: Tuple[float, ...]
    residual_context_sha256: str
    frozen_reverse_time: float
    frozen_direct_time: float
    clock_start: float
    right_endpoint: float
    proposal_budget: int
    proposals: Tuple[CounterKeyedOperationalEpochProposal, ...]
    proposal_sha256s: Tuple[str, ...]
    iteration_sha256s: Tuple[str, ...]
    route_evidence_sha256s: Tuple[str, ...]
    lineage_transition_sha256s: Tuple[str, ...]
    terminal: CounterKeyedOperationalEpochTerminal
    terminal_sha256: str
    stop_reason: str
    proposal_count: int
    accepted_count: int
    rejected_count: int
    created_lineage_count: int
    destroyed_lineage_count: int
    operational_epoch_stream_count: int
    checkpoint23_terminal_wait_invocation_count: int
    checkpoint23_jump_proposal_stream_count: int
    recorded_raw64_word_count: int
    final_clock_cursor: float
    final_intensity: ReferenceCandidateIntensity
    final_intensity_sha256: str
    final_envelope: _loop.TotalizedJumpRateEnvelope
    final_envelope_sha256: str
    final_lineage_state: _lineage.OperationalLineageState
    final_lineage_state_sha256: str
    final_configuration: TransformedConfiguration
    final_model_state_sha256: str
    successful_local_interval_completion: bool
    reference_intensity_zero: bool
    right_endpoint_exhausted: bool
    all_within_result_epoch_addresses_unique: bool
    actual_operational_epoch_consumption: bool
    checkpoint23_jump_proposal_streams_consumed: bool
    checkpoint22_execution_was_proposal_keyed: bool
    terminal_reused_exact_lineage_state: bool
    identifiers_absent_from_model_projection: bool
    no_caller_rng: bool
    result_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CounterKeyedOperationalEpochLoopResult cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _RESULT_TOKEN:
            raise TypeError("operational epoch loop results are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("operational epoch loop result fields are incomplete")
        certificate = _validate_certificate(values["certificate"])
        if values["certificate_sha256"] != certificate.certificate_sha256:
            raise ValueError("operational epoch loop result certificate differs")
        run_id = _lineage._exact_uint64(values["run_id"], name="result.run_id")
        step_index = _lineage._exact_uint64(
            values["step_index"], name="result.step_index"
        )
        exact_parent_types = (
            ("initial_intensity", ReferenceCandidateIntensity),
            ("initial_envelope", _loop.TotalizedJumpRateEnvelope),
            ("final_intensity", ReferenceCandidateIntensity),
            ("final_envelope", _loop.TotalizedJumpRateEnvelope),
        )
        for name, expected in exact_parent_types:
            if type(values[name]) is not expected:
                raise TypeError("result %s has the wrong exact type" % name)
        initial_intensity = values["initial_intensity"]
        initial_envelope = values["initial_envelope"]
        expected_parent_digests = {
            "initial_intensity_sha256": _thinning._intensity_sha256(initial_intensity),
            "initial_envelope_sha256": initial_envelope.envelope_sha256,
            "final_intensity_sha256": _thinning._intensity_sha256(
                values["final_intensity"]
            ),
            "final_envelope_sha256": values["final_envelope"].envelope_sha256,
        }
        for name, expected in expected_parent_digests.items():
            if values[name] != expected:
                raise ValueError("operational epoch result %s differs" % name)
        _canonical_record_context(
            values["base_context"],
            dimension=certificate.base_context_dimension,
            name="result base_context",
        )
        _canonical_record_context(
            values["residual_context"],
            dimension=certificate.residual_context_dimension,
            name="result residual_context",
        )
        if values["base_context_sha256"] != _loop._context_sha256(
            values["base_context"], role="base"
        ):
            raise ValueError("operational epoch result base-context digest differs")
        if values["residual_context_sha256"] != _loop._context_sha256(
            values["residual_context"], role="residual"
        ):
            raise ValueError("operational epoch result residual-context digest differs")
        for name in (
            "frozen_reverse_time",
            "frozen_direct_time",
            "clock_start",
            "right_endpoint",
            "final_clock_cursor",
        ):
            _clock_float(values[name], name="result.%s" % name)
        if values["right_endpoint"] < values["clock_start"]:
            raise ValueError("operational epoch right endpoint precedes its start")
        if not _same_float(
            values["frozen_reverse_time"], initial_intensity.reverse_time
        ):
            raise ValueError("operational epoch frozen reverse time differs")
        if not _same_float(values["frozen_direct_time"], initial_intensity.direct_time):
            raise ValueError("operational epoch frozen direct time differs")
        budget = _proposal_budget(values["proposal_budget"])
        _preflight_lineage_state_resources(
            values["initial_lineage_state"], name="result initial lineage state"
        )
        _preflight_lineage_state_resources(
            values["final_lineage_state"], name="result final lineage state"
        )
        initial_lineage = _lineage._validate_state(values["initial_lineage_state"])
        final_lineage = _lineage._validate_state(values["final_lineage_state"])
        if initial_lineage.certificate_sha256 != (
            certificate.checkpoint23_certificate_sha256
        ):
            raise ValueError("result initial lineage has another certificate")
        if final_lineage.certificate_sha256 != (
            certificate.checkpoint23_certificate_sha256
        ):
            raise ValueError("result final lineage has another certificate")
        if initial_lineage.run_id != run_id or final_lineage.run_id != run_id:
            raise ValueError("operational epoch result lineage uses another run")
        if values["initial_lineage_state_sha256"] != initial_lineage.state_sha256:
            raise ValueError("result initial lineage digest differs")
        if values["final_lineage_state_sha256"] != final_lineage.state_sha256:
            raise ValueError("result final lineage digest differs")
        if not _same_configuration_event_identities(
            initial_lineage.model_configuration,
            initial_intensity.source_configuration,
        ):
            raise ValueError("result initial lineage projection differs")
        if type(values["proposals"]) is not tuple:
            raise TypeError("result proposals must be an exact tuple")
        if type(values["proposal_sha256s"]) is not tuple:
            raise TypeError("result proposal digests must be an exact tuple")
        proposals_value = values["proposals"]
        if len(proposals_value) > budget or len(proposals_value) > (
            COUNTER_KEYED_OPERATIONAL_EPOCH_MAX_PROPOSALS
        ):
            raise ValueError("operational epoch proposal tuple exceeds its bound")
        for proposal in proposals_value:
            if type(proposal) is not CounterKeyedOperationalEpochProposal:
                raise TypeError("result proposal has the wrong exact type")
            _preflight_iteration_resources(proposal.iteration)
            _preflight_lineage_state_resources(
                proposal.lineage_transition.pre_state,
                name="result proposal transition pre-state",
            )
            _preflight_lineage_state_resources(
                proposal.lineage_transition.post_state,
                name="result proposal transition post-state",
            )
        proposals = tuple(
            _validate_proposal_record(proposal) for proposal in proposals_value
        )
        expected_digest_sequences = {
            "proposal_sha256s": tuple(
                proposal.proposal_sha256 for proposal in proposals
            ),
            "iteration_sha256s": tuple(
                proposal.iteration_sha256 for proposal in proposals
            ),
            "route_evidence_sha256s": tuple(
                proposal.route_evidence_sha256 for proposal in proposals
            ),
            "lineage_transition_sha256s": tuple(
                proposal.lineage_transition_sha256 for proposal in proposals
            ),
        }
        for name, expected in expected_digest_sequences.items():
            if type(values[name]) is not tuple or values[name] != expected:
                raise ValueError("operational epoch result %s differs" % name)
        current_intensity = initial_intensity
        current_envelope = initial_envelope
        current_lineage = values["initial_lineage_state"]
        current_cursor = values["clock_start"]
        seen_intensities = [current_intensity]
        seen_envelopes = [current_envelope]
        accepted_count = 0
        created_count = 0
        destroyed_count = 0
        raw_word_count = 0
        address_sha256s = []
        for index, proposal in enumerate(proposals):
            iteration = proposal.iteration
            transition = proposal.lineage_transition
            if proposal.certificate is not certificate:
                raise ValueError("result proposal has another certificate object")
            if (
                proposal.run_id != run_id
                or proposal.step_index != step_index
                or proposal.proposal_index != index
            ):
                raise ValueError(
                    "operational epoch proposal indices are not contiguous"
                )
            if iteration.pre_intensity is not current_intensity:
                raise ValueError("operational epoch intensity identity chain differs")
            if iteration.pre_envelope is not current_envelope:
                raise ValueError("operational epoch envelope identity chain differs")
            if transition.pre_state is not current_lineage:
                raise ValueError("operational epoch lineage identity chain differs")
            if not _same_float(iteration.clock_start, current_cursor):
                raise ValueError("operational epoch clock chain differs")
            if not _same_float(
                iteration.waiting_draw.right_endpoint, values["right_endpoint"]
            ):
                raise ValueError("operational epoch proposal endpoint differs")
            if iteration.base_context_sha256 != values["base_context_sha256"]:
                raise ValueError("operational epoch proposal base context differs")
            if iteration.residual_context_sha256 != (values["residual_context_sha256"]):
                raise ValueError("operational epoch proposal residual context differs")
            if not _same_configuration_event_identities(
                current_lineage.model_configuration,
                iteration.pre_intensity.source_configuration,
            ):
                raise ValueError("proposal lineage/model projection differs")
            if not _same_configuration_event_identities(
                transition.post_state.model_configuration,
                iteration.post_intensity.source_configuration,
            ):
                raise ValueError("proposal post-lineage/model projection differs")
            if proposal.accepted:
                if any(
                    iteration.post_intensity is previous
                    for previous in seen_intensities
                ):
                    raise ValueError("accepted proposal reused an earlier intensity")
                if any(
                    iteration.post_envelope is previous for previous in seen_envelopes
                ):
                    raise ValueError("accepted proposal reused an earlier envelope")
                seen_intensities.append(iteration.post_intensity)
                seen_envelopes.append(iteration.post_envelope)
            current_intensity = iteration.post_intensity
            current_envelope = iteration.post_envelope
            current_lineage = transition.post_state
            current_cursor = iteration.proposal_time
            accepted_count += int(proposal.accepted)
            created_count += int(transition.created_occurrence is not None)
            destroyed_count += int(transition.destroyed_identifier is not None)
            raw_word_count += len(iteration.waiting_draw.raw_words)
            raw_word_count += len(iteration.decision.raw_words)
            address_sha256s.append(proposal.epoch_address_sha256)
        terminal = _validate_terminal_record(values["terminal"])
        if values["terminal_sha256"] != terminal.terminal_sha256:
            raise ValueError("operational epoch terminal digest differs")
        if terminal.certificate is not certificate:
            raise ValueError("operational epoch terminal has another certificate")
        if (
            terminal.run_id != run_id
            or terminal.step_index != step_index
            or terminal.completed_proposals != len(proposals)
        ):
            raise ValueError("operational epoch terminal address differs")
        terminal_waiting = terminal.waiting_draw
        if terminal_waiting.intensity_sha256 != _thinning._intensity_sha256(
            current_intensity
        ):
            raise ValueError("terminal waiting intensity differs")
        if terminal_waiting.envelope_sha256 != current_envelope.envelope_sha256:
            raise ValueError("terminal waiting envelope differs")
        if not _same_float(terminal_waiting.clock_start, current_cursor):
            raise ValueError("terminal waiting clock start differs")
        if not _same_float(terminal_waiting.right_endpoint, values["right_endpoint"]):
            raise ValueError("terminal waiting right endpoint differs")
        if terminal.active_terminal and len(proposals) >= budget:
            raise ValueError("active terminal was sampled at the proposal cap")
        if len(proposals) == budget and not terminal.deterministic_terminal:
            raise ValueError("a result at the cap requires deterministic terminal")
        if terminal.operational_epoch_stream is not None:
            address_sha256s.append(terminal.operational_epoch_stream.address_sha256)
        if len(set(address_sha256s)) != len(address_sha256s):
            raise ValueError("operational epoch result reused a tag-6 address")
        raw_word_count += len(terminal_waiting.raw_words)
        if raw_word_count > (COUNTER_KEYED_OPERATIONAL_EPOCH_MAX_RECORDED_RAW64_WORDS):
            raise ValueError("operational epoch raw-word transcript exceeds its bound")
        for name in (
            "proposal_count",
            "accepted_count",
            "rejected_count",
            "created_lineage_count",
            "destroyed_lineage_count",
            "operational_epoch_stream_count",
            "checkpoint23_terminal_wait_invocation_count",
            "checkpoint23_jump_proposal_stream_count",
            "recorded_raw64_word_count",
        ):
            _exact_nonnegative_integer(values[name], name="result.%s" % name)
        expected_counts = {
            "proposal_count": len(proposals),
            "accepted_count": accepted_count,
            "rejected_count": len(proposals) - accepted_count,
            "created_lineage_count": created_count,
            "destroyed_lineage_count": destroyed_count,
            "operational_epoch_stream_count": len(proposals)
            + int(terminal.active_terminal),
            "checkpoint23_terminal_wait_invocation_count": int(
                terminal.deterministic_terminal
            ),
            "checkpoint23_jump_proposal_stream_count": 0,
            "recorded_raw64_word_count": raw_word_count,
        }
        for name, expected in expected_counts.items():
            if values[name] != expected:
                raise ValueError("operational epoch result %s differs" % name)
        if not _same_float(values["final_clock_cursor"], current_cursor):
            raise ValueError("operational epoch final cursor differs")
        if values["final_intensity"] is not current_intensity:
            raise ValueError("operational epoch final intensity identity differs")
        if values["final_envelope"] is not current_envelope:
            raise ValueError("operational epoch final envelope identity differs")
        if values["final_lineage_state"] is not current_lineage:
            raise ValueError("operational epoch final lineage identity differs")
        if values["final_lineage_state"] is not (
            values["initial_lineage_state"]
            if not proposals
            else proposals[-1].lineage_transition.post_state
        ):
            raise ValueError("terminal did not reuse the exact final lineage state")
        if type(values["final_configuration"]) is not tuple:
            raise TypeError("result final configuration must be an exact tuple")
        expected_configuration = current_lineage.model_configuration
        if values["final_configuration"] is not expected_configuration:
            raise ValueError(
                "operational epoch final configuration is not the lineage projection"
            )
        if not _same_configuration_event_identities(
            current_intensity.source_configuration,
            expected_configuration,
        ):
            raise ValueError("final intensity and lineage projection differ")
        if values["final_model_state_sha256"] != (current_lineage.model_state_sha256):
            raise ValueError("operational epoch final model digest differs")
        if values["stop_reason"] != terminal.stop_reason:
            raise ValueError("operational epoch result stop reason differs")
        expected_flags = {
            "successful_local_interval_completion": True,
            "reference_intensity_zero": terminal.reference_intensity_zero,
            "right_endpoint_exhausted": terminal.right_endpoint_exhausted,
            "all_within_result_epoch_addresses_unique": True,
            "actual_operational_epoch_consumption": bool(
                len(proposals) or terminal.active_terminal
            ),
            "checkpoint23_jump_proposal_streams_consumed": False,
            "checkpoint22_execution_was_proposal_keyed": False,
            "terminal_reused_exact_lineage_state": True,
            "identifiers_absent_from_model_projection": True,
            "no_caller_rng": True,
        }
        for name, expected in expected_flags.items():
            if _exact_bool(values[name], name="result.%s" % name) is not expected:
                raise ValueError("operational epoch result %s differs" % name)
        for name in (
            "certificate_sha256",
            "initial_intensity_sha256",
            "initial_envelope_sha256",
            "initial_lineage_state_sha256",
            "base_context_sha256",
            "residual_context_sha256",
            "terminal_sha256",
            "final_intensity_sha256",
            "final_envelope_sha256",
            "final_lineage_state_sha256",
            "final_model_state_sha256",
            "result_sha256",
        ):
            _thinning._require_sha256(values[name], name="result.%s" % name)
        expected_digest = _thinning._semantic_digest(_result_payload(values))
        if values["result_sha256"] != expected_digest:
            raise ValueError("operational epoch loop result digest differs")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("operational epoch loop results are not pickle objects")


def _result_fields() -> Tuple[str, ...]:
    return tuple(CounterKeyedOperationalEpochLoopResult.__annotations__)


def _result_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    payload = dict(
        _without(
            values,
            "certificate",
            "initial_intensity",
            "initial_envelope",
            "initial_lineage_state",
            "proposals",
            "terminal",
            "final_intensity",
            "final_envelope",
            "final_lineage_state",
            "final_configuration",
            "result_sha256",
        )
    )
    payload["final_configuration"] = _configuration_payload(
        values["final_configuration"]  # type: ignore[arg-type]
    )
    return payload


def _validate_result_record(
    result: object,
) -> CounterKeyedOperationalEpochLoopResult:
    if type(result) is not CounterKeyedOperationalEpochLoopResult:
        raise TypeError(
            "result must be an exact CounterKeyedOperationalEpochLoopResult"
        )
    if type(result.proposals) is not tuple:
        raise TypeError("result proposals must be an exact tuple")
    if len(result.proposals) > COUNTER_KEYED_OPERATIONAL_EPOCH_MAX_PROPOSALS:
        raise ValueError("result proposals exceed their resource bound")
    if (
        type(result.base_context) is not tuple
        or type(result.residual_context) is not tuple
    ):
        raise TypeError("result contexts must be exact tuples")
    if len(result.base_context) > _loop._potential._MAX_CONTEXT_DIMENSION:
        raise ValueError("result base context exceeds its resource bound")
    if len(result.residual_context) > _loop._potential._MAX_CONTEXT_DIMENSION:
        raise ValueError("result residual context exceeds its resource bound")
    return CounterKeyedOperationalEpochLoopResult(
        **{name: getattr(result, name) for name in _result_fields()},
        _construction_token=_RESULT_TOKEN,
    )


def _make_result(
    certificate: CounterKeyedOperationalEpochLoopCertificate,
    *,
    run_id: int,
    step_index: int,
    initial_intensity: ReferenceCandidateIntensity,
    initial_envelope: _loop.TotalizedJumpRateEnvelope,
    initial_lineage_state: _lineage.OperationalLineageState,
    base_context: Tuple[float, ...],
    residual_context: Tuple[float, ...],
    clock_start: float,
    right_endpoint: float,
    proposal_budget: int,
    proposals: Tuple[CounterKeyedOperationalEpochProposal, ...],
    terminal: CounterKeyedOperationalEpochTerminal,
) -> CounterKeyedOperationalEpochLoopResult:
    final_intensity = (
        initial_intensity if not proposals else proposals[-1].iteration.post_intensity
    )
    final_envelope = (
        initial_envelope if not proposals else proposals[-1].iteration.post_envelope
    )
    final_lineage = (
        initial_lineage_state
        if not proposals
        else proposals[-1].lineage_transition.post_state
    )
    accepted_count = sum(int(proposal.accepted) for proposal in proposals)
    created_count = sum(
        int(proposal.lineage_transition.created_occurrence is not None)
        for proposal in proposals
    )
    destroyed_count = sum(
        int(proposal.lineage_transition.destroyed_identifier is not None)
        for proposal in proposals
    )
    raw_word_count = sum(
        len(proposal.iteration.waiting_draw.raw_words)
        + len(proposal.iteration.decision.raw_words)
        for proposal in proposals
    ) + len(terminal.waiting_draw.raw_words)
    final_cursor = (
        clock_start if not proposals else proposals[-1].iteration.proposal_time
    )
    values: Dict[str, object] = {
        "certificate": certificate,
        "certificate_sha256": certificate.certificate_sha256,
        "run_id": run_id,
        "step_index": step_index,
        "initial_intensity": initial_intensity,
        "initial_intensity_sha256": _thinning._intensity_sha256(initial_intensity),
        "initial_envelope": initial_envelope,
        "initial_envelope_sha256": initial_envelope.envelope_sha256,
        "initial_lineage_state": initial_lineage_state,
        "initial_lineage_state_sha256": initial_lineage_state.state_sha256,
        "base_context": base_context,
        "base_context_sha256": _loop._context_sha256(base_context, role="base"),
        "residual_context": residual_context,
        "residual_context_sha256": _loop._context_sha256(
            residual_context, role="residual"
        ),
        "frozen_reverse_time": initial_intensity.reverse_time,
        "frozen_direct_time": initial_intensity.direct_time,
        "clock_start": clock_start,
        "right_endpoint": right_endpoint,
        "proposal_budget": proposal_budget,
        "proposals": proposals,
        "proposal_sha256s": tuple(proposal.proposal_sha256 for proposal in proposals),
        "iteration_sha256s": tuple(proposal.iteration_sha256 for proposal in proposals),
        "route_evidence_sha256s": tuple(
            proposal.route_evidence_sha256 for proposal in proposals
        ),
        "lineage_transition_sha256s": tuple(
            proposal.lineage_transition_sha256 for proposal in proposals
        ),
        "terminal": terminal,
        "terminal_sha256": terminal.terminal_sha256,
        "stop_reason": terminal.stop_reason,
        "proposal_count": len(proposals),
        "accepted_count": accepted_count,
        "rejected_count": len(proposals) - accepted_count,
        "created_lineage_count": created_count,
        "destroyed_lineage_count": destroyed_count,
        "operational_epoch_stream_count": len(proposals)
        + int(terminal.active_terminal),
        "checkpoint23_terminal_wait_invocation_count": int(
            terminal.deterministic_terminal
        ),
        "checkpoint23_jump_proposal_stream_count": 0,
        "recorded_raw64_word_count": raw_word_count,
        "final_clock_cursor": final_cursor,
        "final_intensity": final_intensity,
        "final_intensity_sha256": _thinning._intensity_sha256(final_intensity),
        "final_envelope": final_envelope,
        "final_envelope_sha256": final_envelope.envelope_sha256,
        "final_lineage_state": final_lineage,
        "final_lineage_state_sha256": final_lineage.state_sha256,
        "final_configuration": final_lineage.model_configuration,
        "final_model_state_sha256": final_lineage.model_state_sha256,
        "successful_local_interval_completion": True,
        "reference_intensity_zero": terminal.reference_intensity_zero,
        "right_endpoint_exhausted": terminal.right_endpoint_exhausted,
        "all_within_result_epoch_addresses_unique": True,
        "actual_operational_epoch_consumption": bool(
            proposals or terminal.active_terminal
        ),
        "checkpoint23_jump_proposal_streams_consumed": False,
        "checkpoint22_execution_was_proposal_keyed": False,
        "terminal_reused_exact_lineage_state": True,
        "identifiers_absent_from_model_projection": True,
        "no_caller_rng": True,
        "result_sha256": _ZERO_SHA256,
    }
    values["result_sha256"] = _thinning._semantic_digest(_result_payload(values))
    return CounterKeyedOperationalEpochLoopResult(
        **values, _construction_token=_RESULT_TOKEN
    )


class CounterKeyedOperationalEpochLoop:
    """Immutable owner of bounded address-local operational epoch execution."""

    __slots__ = (
        "_contract_owner",
        "_certified_contract_owner",
        "_checkpoint22_owner",
        "_loop_owner",
        "_route_evidence_owner",
        "_thinning_owner",
        "_rate_owner",
        "_reference_composer",
        "_potential_composer",
        "_epoch_role_sha256",
        "_certificate",
        "_loop_make_iteration",
        "_lineage_make_transition",
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CounterKeyedOperationalEpochLoop cannot be subclassed")

    def __init__(
        self,
        contract_owner: _lineage.CounterKeyedLineageContractOwner,
        epoch_role_sha256: str,
        certificate: CounterKeyedOperationalEpochLoopCertificate,
        *,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _OWNER_TOKEN:
            raise TypeError("operational epoch loop owners require certification")
        if type(contract_owner) is not _lineage.CounterKeyedLineageContractOwner:
            raise TypeError("contract_owner has the wrong exact type")
        role = _thinning._require_sha256(epoch_role_sha256, name="epoch_role_sha256")
        checked_certificate = _validate_certificate(certificate)
        if checked_certificate.epoch_role_sha256 != role:
            raise ValueError("operational epoch role differs from certificate")
        checkpoint22 = contract_owner.parent_owner
        loop_owner = contract_owner.loop_owner
        route_owner = contract_owner.route_evidence_owner
        thinning_owner = contract_owner.thinning_owner
        object.__setattr__(self, "_contract_owner", contract_owner)
        object.__setattr__(self, "_certified_contract_owner", contract_owner)
        object.__setattr__(self, "_checkpoint22_owner", checkpoint22)
        object.__setattr__(self, "_loop_owner", loop_owner)
        object.__setattr__(self, "_route_evidence_owner", route_owner)
        object.__setattr__(self, "_thinning_owner", thinning_owner)
        object.__setattr__(self, "_rate_owner", loop_owner.rate_owner)
        object.__setattr__(self, "_reference_composer", loop_owner.reference_composer)
        object.__setattr__(self, "_potential_composer", loop_owner.potential_composer)
        object.__setattr__(self, "_epoch_role_sha256", role)
        object.__setattr__(self, "_certificate", checked_certificate)
        object.__setattr__(
            self,
            "_loop_make_iteration",
            type(loop_owner)._make_iteration,
        )
        object.__setattr__(
            self,
            "_lineage_make_transition",
            _lineage._make_transition,
        )

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("CounterKeyedOperationalEpochLoop is immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("CounterKeyedOperationalEpochLoop is immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("operational epoch loop owners are not pickle objects")

    @property
    def certificate(self) -> CounterKeyedOperationalEpochLoopCertificate:
        return self._certificate

    @property
    def contract_owner(self) -> _lineage.CounterKeyedLineageContractOwner:
        return self._contract_owner

    @property
    def checkpoint22_owner(
        self,
    ) -> _loop_route.BoundedOperationalThinningLoopRouteEvidence:
        return self._checkpoint22_owner

    @property
    def loop_owner(self) -> _loop.BoundedOperationalThinningLoop:
        return self._loop_owner

    @property
    def route_evidence_owner(
        self,
    ) -> _route_evidence.ContinuousRouteEvidenceOwner:
        return self._route_evidence_owner

    @property
    def thinning_owner(self) -> _thinning.OperationalJumpThinning:
        return self._thinning_owner

    @property
    def rate_owner(self):  # type: ignore[no-untyped-def]
        return self._rate_owner

    @property
    def reference_composer(self):  # type: ignore[no-untyped-def]
        return self._reference_composer

    @property
    def potential_composer(self):  # type: ignore[no-untyped-def]
        return self._potential_composer

    def _require_live_binding(
        self,
    ) -> CounterKeyedOperationalEpochLoopCertificate:
        _thinning._require_binary64_environment()
        if type(self._contract_owner) is not (
            _lineage.CounterKeyedLineageContractOwner
        ):
            raise TypeError("contract owner has the wrong exact type")
        if self._contract_owner is not self._certified_contract_owner:
            raise ValueError("operational epoch contract-owner binding changed")
        checkpoint23 = self._contract_owner._require_live_binding()
        if self._contract_owner.parent_owner is not self._checkpoint22_owner:
            raise ValueError("operational epoch checkpoint-22 binding changed")
        if self._contract_owner.loop_owner is not self._loop_owner:
            raise ValueError("operational epoch loop-owner binding changed")
        if self._contract_owner.route_evidence_owner is not (
            self._route_evidence_owner
        ):
            raise ValueError("operational epoch route-evidence binding changed")
        if self._contract_owner.thinning_owner is not self._thinning_owner:
            raise ValueError("operational epoch thinning-owner binding changed")
        if self._loop_owner.rate_owner is not self._rate_owner:
            raise ValueError("operational epoch rate-owner binding changed")
        if self._loop_owner.reference_composer is not self._reference_composer:
            raise ValueError("operational epoch reference binding changed")
        if self._loop_owner.potential_composer is not self._potential_composer:
            raise ValueError("operational epoch potential binding changed")
        if type(self._loop_owner)._make_iteration is not self._loop_make_iteration:
            raise ValueError("operational epoch iteration factory changed")
        if _lineage._make_transition is not self._lineage_make_transition:
            raise ValueError("operational epoch lineage factory changed")
        loop_certificate = self._loop_owner._require_live_binding()
        self._route_evidence_owner._require_live_binding()
        if self.certificate.epoch_runtime_sha256 != _runtime_sha256():
            raise ValueError("live operational epoch runtime differs")
        expected = _make_certificate(
            checkpoint23,
            loop_certificate,
            epoch_role_sha256=self._epoch_role_sha256,
        )
        for name in _certificate_fields():
            if not _thinning._field_matches(
                name,
                getattr(self.certificate, name),
                getattr(expected, name),
            ):
                raise ValueError(
                    "operational epoch certificate field %s differs" % name
                )
        _thinning._require_binary64_environment()
        return self.certificate

    def make_operational_epoch_stream(
        self,
        run_id: object,
        step_index: object,
        completed_proposals: object,
    ) -> CounterKeyedOperationalEpochStream:
        """Issue the direct tag-6 stream for one active boundary."""

        self._require_live_binding()
        checked_run = _lineage._exact_uint64(run_id, name="run_id")
        checked_step = _lineage._exact_uint64(step_index, name="step_index")
        checked_completed = _lineage._exact_uint64(
            completed_proposals, name="completed_proposals"
        )
        address = _make_address(
            self.certificate,
            run_id=checked_run,
            step_index=checked_step,
            completed_proposals=checked_completed,
        )
        stream = _make_stream(self.certificate, address)
        self.validate_operational_epoch_stream(stream)
        return stream

    def validate_operational_epoch_stream(
        self,
        stream: CounterKeyedOperationalEpochStream,
    ) -> CounterKeyedOperationalEpochStream:
        """Validate and same-runtime reconstruct an unused epoch receipt."""

        self._require_live_binding()
        checked = _validate_stream_record(stream)
        if checked.certificate is not self.certificate:
            raise ValueError("operational epoch stream belongs to another owner")
        generator = _route_evidence._generator_from_snapshot(checked.initial_state)
        reconstructed = _route_evidence._capture_philox_state(generator)
        if not _snapshot_matches(reconstructed, checked.initial_state):
            raise PluginBridgeCounterKeyedOperationalEpochLoopError(
                "operational epoch initial state did not reconstruct"
            )
        self._require_live_binding()
        return stream

    def reconstruct_operational_epoch_stream(
        self,
        stream: CounterKeyedOperationalEpochStream,
    ) -> np.random.Generator:
        """Return a fresh generator at one exact unused tag-6 state."""

        self.validate_operational_epoch_stream(stream)
        generator = _route_evidence._generator_from_snapshot(stream.initial_state)
        if not _snapshot_matches(
            _route_evidence._capture_philox_state(generator),
            stream.initial_state,
        ):
            raise PluginBridgeCounterKeyedOperationalEpochLoopError(
                "fresh operational epoch stream differs from its receipt"
            )
        return generator

    def _validate_initial_lineage(
        self,
        initial_lineage_state: _lineage.OperationalLineageState,
        initial_intensity: ReferenceCandidateIntensity,
        *,
        run_id: int,
        step_index: int,
    ) -> _lineage.OperationalLineageState:
        _preflight_lineage_state_resources(
            initial_lineage_state, name="initial_lineage_state"
        )
        checked = _lineage._validate_state(initial_lineage_state)
        if checked.certificate_sha256 != (
            self.contract_owner.certificate.certificate_sha256
        ):
            raise ValueError("initial lineage state belongs to another certificate")
        if checked.run_id != run_id:
            raise ValueError("initial lineage state belongs to another run")
        if not _same_configuration_event_identities(
            checked.model_configuration,
            initial_intensity.source_configuration,
        ):
            raise ValueError("initial lineage projection differs from initial state")
        identifiers = (
            tuple(occurrence.identifier for occurrence in checked.occurrences)
            + checked.retired_identifiers
        )
        for identifier in identifiers:
            if (
                identifier.origin_kind
                in (
                    _lineage._BIRTH_ORIGIN,
                    _lineage._REPLACEMENT_ORIGIN,
                )
                and identifier.origin_step_index >= step_index
            ):
                raise ValueError("pre-existing edit lineage does not precede this step")
        return initial_lineage_state

    def _canonical_run_inputs(
        self,
        initial_intensity: ReferenceCandidateIntensity,
        initial_envelope: _loop.TotalizedJumpRateEnvelope,
        initial_lineage_state: _lineage.OperationalLineageState,
        *,
        run_id: object,
        step_index: object,
        clock_start: object,
        right_endpoint: object,
        proposal_budget: object,
        base_context: object,
        residual_context: object,
    ) -> Tuple[
        ReferenceCandidateIntensity,
        _loop.TotalizedJumpRateEnvelope,
        _lineage.OperationalLineageState,
        int,
        int,
        float,
        float,
        int,
        Tuple[float, ...],
        Tuple[float, ...],
    ]:
        self._require_live_binding()
        checked_run = _lineage._exact_uint64(run_id, name="run_id")
        checked_step = _lineage._exact_uint64(step_index, name="step_index")
        budget = _proposal_budget(proposal_budget)
        start = _clock_float(clock_start, name="clock_start")
        end = _clock_float(right_endpoint, name="right_endpoint")
        if end < start:
            raise ValueError("right_endpoint must not precede clock_start")
        intensity, envelope = self.loop_owner._validate_parents(
            initial_intensity, initial_envelope
        )
        base, residual = self.loop_owner._canonical_contexts(
            base_context, residual_context
        )
        lineage_state = self._validate_initial_lineage(
            initial_lineage_state,
            intensity,
            run_id=checked_run,
            step_index=checked_step,
        )
        return (
            intensity,
            envelope,
            lineage_state,
            checked_run,
            checked_step,
            start,
            end,
            budget,
            base,
            residual,
        )

    def _make_iteration(
        self,
        *,
        proposal_index: int,
        pre_intensity: ReferenceCandidateIntensity,
        pre_envelope: _loop.TotalizedJumpRateEnvelope,
        waiting_draw: _thinning.OperationalWaitingTimeDraw,
        route_draw: _thinning.OperationalReferenceRouteDraw,
        potential_evaluation: object,
        rate_evaluation: object,
        decision: _thinning.OperationalAcceptanceDecision,
        post_intensity: ReferenceCandidateIntensity,
        post_envelope: _loop.TotalizedJumpRateEnvelope,
    ) -> _loop.OperationalProposalIteration:
        return self._loop_make_iteration(
            self.loop_owner,
            proposal_index=proposal_index,
            pre_intensity=pre_intensity,
            pre_envelope=pre_envelope,
            waiting_draw=waiting_draw,
            route_draw=route_draw,
            potential_evaluation=potential_evaluation,
            rate_evaluation=rate_evaluation,
            decision=decision,
            post_intensity=post_intensity,
            post_envelope=post_envelope,
        )

    def _make_lineage_transition(
        self,
        iteration: _loop.OperationalProposalIteration,
        evidence: _route_evidence.OperationalReferenceRouteEvidence,
        pre_state: _lineage.OperationalLineageState,
        *,
        step_index: int,
    ) -> _lineage.OperationalLineageTransition:
        return self._lineage_make_transition(
            self.contract_owner.certificate,
            iteration,
            evidence,
            pre_state,
            run_id=pre_state.run_id,
            step_index=step_index,
        )

    def _execute_proposal(
        self,
        stream: CounterKeyedOperationalEpochStream,
        current_intensity: ReferenceCandidateIntensity,
        current_envelope: _loop.TotalizedJumpRateEnvelope,
        current_lineage: _lineage.OperationalLineageState,
        *,
        cursor: float,
        right_endpoint: float,
        base_context: Tuple[float, ...],
        residual_context: Tuple[float, ...],
        run_id: int,
        step_index: int,
        proposal_index: int,
    ) -> Tuple[
        Optional[CounterKeyedOperationalEpochProposal],
        Optional[CounterKeyedOperationalEpochTerminal],
    ]:
        generator = self.reconstruct_operational_epoch_stream(stream)
        waiting = self.thinning_owner.draw_waiting_time(
            current_intensity,
            current_envelope,
            clock_start=cursor,
            right_endpoint=right_endpoint,
            rng=generator,
        )
        if waiting.rng_state_before_sha256 != stream.initial_state_sha256:
            raise ValueError("active waiting draw began at another epoch state")
        if not waiting.candidate_due:
            final_state = _route_evidence._capture_philox_state(generator)
            terminal = _make_terminal(
                self.certificate,
                run_id=run_id,
                step_index=step_index,
                completed_proposals=proposal_index,
                terminal_mode=_TERMINAL_ACTIVE_EPOCH,
                operational_epoch_stream=stream,
                checkpoint23_terminal_wait_stream=None,
                waiting_draw=waiting,
                final_state=final_state,
            )
            return None, terminal
        evidence = self.route_evidence_owner.draw_reference_route_with_evidence(
            waiting,
            current_intensity,
            current_envelope,
            rng=generator,
        )
        route = evidence.route_draw
        model_state = _route_evidence._capture_philox_state(generator)
        potential = self.potential_composer.evaluate(
            route.candidate,
            base_context=base_context,
            residual_context=residual_context,
        )
        if not _snapshot_matches(
            _route_evidence._capture_philox_state(generator), model_state
        ):
            raise ValueError("potential evaluation changed the epoch stream")
        rate_evaluation = self.rate_owner.evaluate_candidate(
            route.candidate,
            potential,
            envelope=current_envelope,
        )
        if not _snapshot_matches(
            _route_evidence._capture_philox_state(generator), model_state
        ):
            raise ValueError("rate evaluation changed the epoch stream")
        decision = self.thinning_owner.decide_acceptance(
            route,
            waiting,
            current_intensity,
            current_envelope,
            potential,
            rate_evaluation,
            rng=generator,
        )
        after_decision = _route_evidence._capture_philox_state(generator)
        if decision.accepted:
            next_intensity = self.reference_composer.preflight_candidate_intensity(
                decision.result_configuration,
                reverse_time=current_intensity.reverse_time,
            )
            if not _snapshot_matches(
                _route_evidence._capture_philox_state(generator), after_decision
            ):
                raise ValueError("accepted-state intensity refresh changed Philox")
            next_envelope = self.rate_owner.preflight_envelope(next_intensity)
            if not _snapshot_matches(
                _route_evidence._capture_philox_state(generator), after_decision
            ):
                raise ValueError("accepted-state envelope refresh changed Philox")
        else:
            next_intensity = current_intensity
            next_envelope = current_envelope
        iteration = self._make_iteration(
            proposal_index=proposal_index,
            pre_intensity=current_intensity,
            pre_envelope=current_envelope,
            waiting_draw=waiting,
            route_draw=route,
            potential_evaluation=potential,
            rate_evaluation=rate_evaluation,
            decision=decision,
            post_intensity=next_intensity,
            post_envelope=next_envelope,
        )
        self.loop_owner.validate_iteration(
            iteration,
            current_intensity,
            current_envelope,
            base_context=base_context,
            residual_context=residual_context,
        )
        transition = self._make_lineage_transition(
            iteration,
            evidence,
            current_lineage,
            step_index=step_index,
        )
        final_state = _route_evidence._capture_philox_state(generator)
        if not _snapshot_matches(final_state, after_decision):
            raise ValueError("proposal validation changed the epoch stream")
        proposal = _make_proposal(
            self.certificate,
            stream,
            iteration,
            evidence,
            transition,
            final_state,
            run_id=run_id,
            step_index=step_index,
        )
        return proposal, None

    def _execute_deterministic_terminal(
        self,
        current_intensity: ReferenceCandidateIntensity,
        current_envelope: _loop.TotalizedJumpRateEnvelope,
        *,
        cursor: float,
        right_endpoint: float,
        run_id: int,
        step_index: int,
        completed_proposals: int,
    ) -> CounterKeyedOperationalEpochTerminal:
        stream = self.contract_owner.make_terminal_wait_stream(
            run_id, step_index, completed_proposals
        )
        generator = self.contract_owner.reconstruct_stream(stream)
        waiting = self.thinning_owner.draw_waiting_time(
            current_intensity,
            current_envelope,
            clock_start=cursor,
            right_endpoint=right_endpoint,
            rng=generator,
        )
        final_state = _route_evidence._capture_philox_state(generator)
        return _make_terminal(
            self.certificate,
            run_id=run_id,
            step_index=step_index,
            completed_proposals=completed_proposals,
            terminal_mode=_TERMINAL_DETERMINISTIC_WAIT,
            operational_epoch_stream=None,
            checkpoint23_terminal_wait_stream=stream,
            waiting_draw=waiting,
            final_state=final_state,
        )

    def run(
        self,
        initial_intensity: ReferenceCandidateIntensity,
        initial_envelope: _loop.TotalizedJumpRateEnvelope,
        initial_lineage_state: _lineage.OperationalLineageState,
        *,
        run_id: object,
        step_index: object,
        clock_start: object,
        right_endpoint: object,
        proposal_budget: object,
        base_context: object,
        residual_context: object,
    ) -> CounterKeyedOperationalEpochLoopResult:
        """Run one bounded local interval with no caller-owned RNG."""

        (
            current_intensity,
            current_envelope,
            current_lineage,
            checked_run,
            checked_step,
            start,
            end,
            budget,
            base,
            residual,
        ) = self._canonical_run_inputs(
            initial_intensity,
            initial_envelope,
            initial_lineage_state,
            run_id=run_id,
            step_index=step_index,
            clock_start=clock_start,
            right_endpoint=right_endpoint,
            proposal_budget=proposal_budget,
            base_context=base_context,
            residual_context=residual_context,
        )
        initial_intensity_snapshot = _thinning._snapshot_fields(
            initial_intensity, _loop._intensity_fields()
        )
        initial_envelope_snapshot = _thinning._snapshot_fields(
            initial_envelope, _loop._envelope_fields()
        )
        initial_lineage_snapshot = {
            name: getattr(initial_lineage_state, name)
            for name in _lineage._state_fields()
        }
        proposals = []
        cursor = start
        terminal = None
        while terminal is None:
            completed = len(proposals)
            deterministic_terminal = current_intensity.is_zero or _same_float(
                cursor, end
            )
            if deterministic_terminal:
                terminal = self._execute_deterministic_terminal(
                    current_intensity,
                    current_envelope,
                    cursor=cursor,
                    right_endpoint=end,
                    run_id=checked_run,
                    step_index=checked_step,
                    completed_proposals=completed,
                )
                break
            if completed == budget:
                raise PluginBridgeCounterKeyedOperationalEpochLoopError(
                    "active operational epoch loop reached its proposal budget "
                    "before certified interval exhaustion"
                )
            stream = self.make_operational_epoch_stream(
                checked_run, checked_step, completed
            )
            proposal, active_terminal = self._execute_proposal(
                stream,
                current_intensity,
                current_envelope,
                current_lineage,
                cursor=cursor,
                right_endpoint=end,
                base_context=base,
                residual_context=residual,
                run_id=checked_run,
                step_index=checked_step,
                proposal_index=completed,
            )
            if active_terminal is not None:
                terminal = active_terminal
                break
            if proposal is None:
                raise RuntimeError(
                    "active epoch returned neither proposal nor terminal"
                )
            proposals.append(proposal)
            cursor = proposal.iteration.proposal_time
            current_intensity = proposal.iteration.post_intensity
            current_envelope = proposal.iteration.post_envelope
            current_lineage = proposal.lineage_transition.post_state
        if terminal is None:
            raise RuntimeError("successful epoch loop lacks terminal evidence")
        _thinning._record_unchanged(
            initial_intensity,
            initial_intensity_snapshot,
            context="initial reference intensity",
        )
        _thinning._record_unchanged(
            initial_envelope,
            initial_envelope_snapshot,
            context="initial rate envelope",
        )
        _thinning._record_unchanged(
            initial_lineage_state,
            initial_lineage_snapshot,
            context="initial lineage state",
        )
        result = _make_result(
            self.certificate,
            run_id=checked_run,
            step_index=checked_step,
            initial_intensity=initial_intensity,
            initial_envelope=initial_envelope,
            initial_lineage_state=initial_lineage_state,
            base_context=base,
            residual_context=residual,
            clock_start=start,
            right_endpoint=end,
            proposal_budget=budget,
            proposals=tuple(proposals),
            terminal=terminal,
        )
        self.validate_result(
            result,
            initial_intensity,
            initial_envelope,
            initial_lineage_state,
            run_id=checked_run,
            step_index=checked_step,
            clock_start=start,
            right_endpoint=end,
            proposal_budget=budget,
            base_context=base,
            residual_context=residual,
        )
        self._require_live_binding()
        return result

    def validate_proposal(
        self,
        proposal: CounterKeyedOperationalEpochProposal,
        pre_intensity: ReferenceCandidateIntensity,
        pre_envelope: _loop.TotalizedJumpRateEnvelope,
        pre_lineage_state: _lineage.OperationalLineageState,
        *,
        right_endpoint: object,
        base_context: object,
        residual_context: object,
    ) -> CounterKeyedOperationalEpochProposal:
        """Replay one tag-6 proposal using only a fresh local generator."""

        self._require_live_binding()
        checked = _validate_proposal_record(proposal)
        if checked.certificate is not self.certificate:
            raise ValueError("proposal belongs to another operational epoch owner")
        if checked.lineage_transition.certificate is not (
            self.contract_owner.certificate
        ):
            raise ValueError("proposal lineage transition has another exact owner")
        if checked.iteration.pre_intensity is not pre_intensity:
            raise ValueError("proposal belongs to another intensity object")
        if checked.iteration.pre_envelope is not pre_envelope:
            raise ValueError("proposal belongs to another envelope object")
        if checked.lineage_transition.pre_state is not pre_lineage_state:
            raise ValueError("proposal belongs to another lineage-state object")
        end = _clock_float(right_endpoint, name="right_endpoint")
        base, residual = self.loop_owner._canonical_contexts(
            base_context, residual_context
        )
        intensity, envelope = self.loop_owner._validate_parents(
            pre_intensity, pre_envelope
        )
        _preflight_lineage_state_resources(
            pre_lineage_state, name="proposal replay pre-lineage state"
        )
        _lineage._validate_state(pre_lineage_state)
        self.loop_owner.validate_iteration(
            checked.iteration,
            intensity,
            envelope,
            base_context=base,
            residual_context=residual,
        )
        self.route_evidence_owner.validate_reference_route_evidence(
            checked.route_evidence,
            checked.iteration.waiting_draw,
            intensity,
            envelope,
        )
        stream = self.validate_operational_epoch_stream(checked.epoch_stream)
        generator = self.reconstruct_operational_epoch_stream(stream)
        waiting = self.thinning_owner.draw_waiting_time(
            intensity,
            envelope,
            clock_start=checked.iteration.clock_start,
            right_endpoint=end,
            rng=generator,
        )
        if waiting.waiting_draw_sha256 != (checked.iteration.waiting_draw_sha256):
            raise ValueError("proposal waiting draw differs from address replay")
        if not waiting.candidate_due:
            raise ValueError("proposal address replay terminated before its route")
        evidence = self.route_evidence_owner.draw_reference_route_with_evidence(
            waiting,
            intensity,
            envelope,
            rng=generator,
        )
        if evidence.evidence_sha256 != checked.route_evidence_sha256:
            raise ValueError("proposal route evidence differs from address replay")
        route = evidence.route_draw
        model_state = _route_evidence._capture_philox_state(generator)
        potential = self.potential_composer.evaluate(
            route.candidate,
            base_context=base,
            residual_context=residual,
        )
        if not _snapshot_matches(
            _route_evidence._capture_philox_state(generator), model_state
        ):
            raise ValueError("proposal replay potential changed Philox")
        if potential.evaluation_sha256 != (
            checked.iteration.potential_evaluation_sha256
        ):
            raise ValueError("proposal potential differs from address replay")
        rate_evaluation = self.rate_owner.evaluate_candidate(
            route.candidate,
            potential,
            envelope=envelope,
        )
        if not _snapshot_matches(
            _route_evidence._capture_philox_state(generator), model_state
        ):
            raise ValueError("proposal replay rate evaluation changed Philox")
        if rate_evaluation.evaluation_sha256 != (
            checked.iteration.rate_evaluation_sha256
        ):
            raise ValueError("proposal rate differs from address replay")
        decision = self.thinning_owner.decide_acceptance(
            route,
            waiting,
            intensity,
            envelope,
            potential,
            rate_evaluation,
            rng=generator,
        )
        if decision.decision_sha256 != checked.iteration.decision_sha256:
            raise ValueError("proposal decision differs from address replay")
        replay_iteration = self._make_iteration(
            proposal_index=checked.proposal_index,
            pre_intensity=pre_intensity,
            pre_envelope=pre_envelope,
            waiting_draw=waiting,
            route_draw=route,
            potential_evaluation=potential,
            rate_evaluation=rate_evaluation,
            decision=decision,
            post_intensity=checked.iteration.post_intensity,
            post_envelope=checked.iteration.post_envelope,
        )
        self.loop_owner.validate_iteration(
            replay_iteration,
            pre_intensity,
            pre_envelope,
            base_context=base,
            residual_context=residual,
        )
        if replay_iteration.iteration_sha256 != checked.iteration_sha256:
            raise ValueError("proposal iteration differs from address replay")
        replay_transition = self._make_lineage_transition(
            replay_iteration,
            evidence,
            pre_lineage_state,
            step_index=checked.step_index,
        )
        if replay_transition.transition_sha256 != (checked.lineage_transition_sha256):
            raise ValueError("proposal lineage differs from deterministic replay")
        final_state = _route_evidence._capture_philox_state(generator)
        if not _snapshot_matches(final_state, checked.stream_final_state):
            raise ValueError("proposal final Philox state differs from replay")
        _require_no_recorded_counter_carry(stream.initial_state, final_state)
        self._require_live_binding()
        return proposal

    def validate_terminal(
        self,
        terminal: CounterKeyedOperationalEpochTerminal,
        current_intensity: ReferenceCandidateIntensity,
        current_envelope: _loop.TotalizedJumpRateEnvelope,
        *,
        clock_start: object,
        right_endpoint: object,
    ) -> CounterKeyedOperationalEpochTerminal:
        """Replay the unique active or deterministic terminal wait."""

        self._require_live_binding()
        checked = _validate_terminal_record(terminal)
        if checked.certificate is not self.certificate:
            raise ValueError("terminal belongs to another operational epoch owner")
        intensity, envelope = self.loop_owner._validate_parents(
            current_intensity, current_envelope
        )
        start = _clock_float(clock_start, name="clock_start")
        end = _clock_float(right_endpoint, name="right_endpoint")
        self.thinning_owner.validate_waiting_time(
            checked.waiting_draw,
            intensity,
            envelope,
        )
        if checked.terminal_mode == _TERMINAL_ACTIVE_EPOCH:
            stream = self.validate_operational_epoch_stream(
                checked.operational_epoch_stream  # type: ignore[arg-type]
            )
            generator = self.reconstruct_operational_epoch_stream(stream)
        else:
            stream = self.contract_owner.validate_stream(
                checked.checkpoint23_terminal_wait_stream  # type: ignore[arg-type]
            )
            generator = self.contract_owner.reconstruct_stream(stream)
        waiting = self.thinning_owner.draw_waiting_time(
            intensity,
            envelope,
            clock_start=start,
            right_endpoint=end,
            rng=generator,
        )
        if waiting.waiting_draw_sha256 != checked.waiting_draw_sha256:
            raise ValueError("terminal waiting draw differs from address replay")
        if waiting.candidate_due:
            raise ValueError("terminal address replay admitted a proposal")
        final_state = _route_evidence._capture_philox_state(generator)
        if not _snapshot_matches(final_state, checked.stream_final_state):
            raise ValueError("terminal final Philox state differs from replay")
        _require_no_recorded_counter_carry(stream.initial_state, final_state)
        self._require_live_binding()
        return terminal

    def validate_result(
        self,
        result: CounterKeyedOperationalEpochLoopResult,
        initial_intensity: ReferenceCandidateIntensity,
        initial_envelope: _loop.TotalizedJumpRateEnvelope,
        initial_lineage_state: _lineage.OperationalLineageState,
        *,
        run_id: object,
        step_index: object,
        clock_start: object,
        right_endpoint: object,
        proposal_budget: object,
        base_context: object,
        residual_context: object,
    ) -> CounterKeyedOperationalEpochLoopResult:
        """Fully replay a result without accepting or advancing caller RNG."""

        self._require_live_binding()
        if type(result) is not CounterKeyedOperationalEpochLoopResult:
            raise TypeError("result has the wrong exact type")
        if type(result.proposals) is not tuple:
            raise TypeError("result proposals must be an exact tuple")
        if len(result.proposals) > COUNTER_KEYED_OPERATIONAL_EPOCH_MAX_PROPOSALS:
            raise ValueError("result proposals exceed their resource bound")
        (
            checked_intensity,
            checked_envelope,
            checked_lineage,
            checked_run,
            checked_step,
            start,
            end,
            budget,
            base,
            residual,
        ) = self._canonical_run_inputs(
            initial_intensity,
            initial_envelope,
            initial_lineage_state,
            run_id=run_id,
            step_index=step_index,
            clock_start=clock_start,
            right_endpoint=right_endpoint,
            proposal_budget=proposal_budget,
            base_context=base_context,
            residual_context=residual_context,
        )
        checked_result = _validate_result_record(result)
        if checked_result.certificate is not self.certificate:
            raise ValueError("result belongs to another operational epoch owner")
        exact_inputs = {
            "initial_intensity": initial_intensity,
            "initial_envelope": initial_envelope,
            "initial_lineage_state": initial_lineage_state,
        }
        for name, expected in exact_inputs.items():
            if getattr(result, name) is not expected:
                raise ValueError("result requires the exact %s object" % name)
        expected_scalars = {
            "run_id": checked_run,
            "step_index": checked_step,
            "proposal_budget": budget,
        }
        for name, expected in expected_scalars.items():
            if getattr(result, name) != expected:
                raise ValueError("result %s differs from validation input" % name)
        expected_context_digests = {
            "base_context_sha256": _loop._context_sha256(base, role="base"),
            "residual_context_sha256": _loop._context_sha256(residual, role="residual"),
        }
        for name, expected in expected_context_digests.items():
            if getattr(result, name) != expected:
                raise ValueError("result %s differs from validation input" % name)
        for name, expected in (("clock_start", start), ("right_endpoint", end)):
            if not _same_float(getattr(result, name), expected):
                raise ValueError("result %s differs from validation input" % name)
        current_intensity = checked_intensity
        current_envelope = checked_envelope
        current_lineage = checked_lineage
        current_cursor = start
        for proposal in result.proposals:
            self.validate_proposal(
                proposal,
                current_intensity,
                current_envelope,
                current_lineage,
                right_endpoint=end,
                base_context=base,
                residual_context=residual,
            )
            current_intensity = proposal.iteration.post_intensity
            current_envelope = proposal.iteration.post_envelope
            current_lineage = proposal.lineage_transition.post_state
            current_cursor = proposal.iteration.proposal_time
        self.validate_terminal(
            result.terminal,
            current_intensity,
            current_envelope,
            clock_start=current_cursor,
            right_endpoint=end,
        )
        self._require_live_binding()
        return result


def certify_plugin_bridge_counter_keyed_operational_epoch_loop(
    contract_owner: _lineage.CounterKeyedLineageContractOwner,
    *,
    epoch_policy: object,
    epoch_role_sha256: object,
) -> CounterKeyedOperationalEpochLoop:
    """Certify the checkpoint-twenty-four address-local coordinator."""

    if type(epoch_policy) is not str:
        raise TypeError("epoch_policy must be exact text")
    if epoch_policy != PLUGIN_BRIDGE_COUNTER_KEYED_OPERATIONAL_EPOCH_LOOP_POLICY:
        raise ValueError("only the exported operational epoch policy is supported")
    role = _thinning._require_sha256(epoch_role_sha256, name="epoch_role_sha256")
    if type(contract_owner) is not _lineage.CounterKeyedLineageContractOwner:
        raise TypeError("contract_owner has the wrong exact type")
    checkpoint23 = contract_owner._require_live_binding()
    loop_certificate = contract_owner.loop_owner._require_live_binding()
    certificate = _make_certificate(
        checkpoint23,
        loop_certificate,
        epoch_role_sha256=role,
    )
    owner = CounterKeyedOperationalEpochLoop(
        contract_owner,
        role,
        certificate,
        _construction_token=_OWNER_TOKEN,
    )
    owner._require_live_binding()
    return owner


def require_matching_plugin_bridge_counter_keyed_operational_epoch_loop(
    contract_owner: _lineage.CounterKeyedLineageContractOwner,
    owner: CounterKeyedOperationalEpochLoop,
    *,
    epoch_policy: object,
    epoch_role_sha256: object,
) -> CounterKeyedOperationalEpochLoop:
    """Require exact owner identity, role, policy, and live parent custody."""

    if type(epoch_policy) is not str:
        raise TypeError("epoch_policy must be exact text")
    if epoch_policy != PLUGIN_BRIDGE_COUNTER_KEYED_OPERATIONAL_EPOCH_LOOP_POLICY:
        raise ValueError("only the exported operational epoch policy is supported")
    role = _thinning._require_sha256(epoch_role_sha256, name="epoch_role_sha256")
    if type(owner) is not CounterKeyedOperationalEpochLoop:
        raise TypeError("owner must be an exact CounterKeyedOperationalEpochLoop")
    if owner.contract_owner is not contract_owner:
        raise ValueError("operational epoch owner uses another contract owner")
    if owner.certificate.epoch_role_sha256 != role:
        raise ValueError("operational epoch owner uses another role")
    owner._require_live_binding()
    return owner


def validate_plugin_bridge_counter_keyed_operational_epoch_loop_certificate(
    contract_owner: _lineage.CounterKeyedLineageContractOwner,
    owner: CounterKeyedOperationalEpochLoop,
    *,
    epoch_policy: object,
    epoch_role_sha256: object,
) -> CounterKeyedOperationalEpochLoopCertificate:
    """Return the reconstructed live checkpoint-twenty-four certificate."""

    return require_matching_plugin_bridge_counter_keyed_operational_epoch_loop(
        contract_owner,
        owner,
        epoch_policy=epoch_policy,
        epoch_role_sha256=epoch_role_sha256,
    ).certificate


__all__ = [
    "PLUGIN_BRIDGE_COUNTER_KEYED_OPERATIONAL_EPOCH_LOOP_SCHEMA_VERSION",
    "PLUGIN_BRIDGE_COUNTER_KEYED_OPERATIONAL_EPOCH_LOOP_POLICY",
    "PLUGIN_BRIDGE_COUNTER_KEYED_OPERATIONAL_EPOCH_LOOP_SCOPE",
    "COUNTER_KEY_DOMAIN_OPERATIONAL_EPOCH",
    "COUNTER_KEY_DOMAIN_TAG_OPERATIONAL_EPOCH",
    "COUNTER_KEYED_OPERATIONAL_EPOCH_ADDRESS_LAYOUT",
    "COUNTER_KEYED_OPERATIONAL_EPOCH_MAX_PROPOSALS",
    "COUNTER_KEYED_OPERATIONAL_EPOCH_MAX_STREAM_RECORDS",
    "COUNTER_KEYED_OPERATIONAL_EPOCH_MAX_RECORDED_RAW64_WORDS",
    "CounterKeyedOperationalEpochLoopCertificate",
    "CounterKeyedOperationalEpochAddress",
    "CounterKeyedOperationalEpochStream",
    "CounterKeyedOperationalEpochProposal",
    "CounterKeyedOperationalEpochTerminal",
    "CounterKeyedOperationalEpochLoopResult",
    "CounterKeyedOperationalEpochLoop",
    "PluginBridgeCounterKeyedOperationalEpochLoopError",
    "certify_plugin_bridge_counter_keyed_operational_epoch_loop",
    "require_matching_plugin_bridge_counter_keyed_operational_epoch_loop",
    "validate_plugin_bridge_counter_keyed_operational_epoch_loop_certificate",
]
