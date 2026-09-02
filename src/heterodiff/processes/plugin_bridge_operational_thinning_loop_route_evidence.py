"""Route-replay evidence over one frozen bounded operational thinning loop.

Checkpoint twenty returns a bounded successful local proposal transcript, but
its frozen schema retains only Philox state hashes at route boundaries.
Checkpoint twenty-one can certify one route when given reconstructable Philox
states.  This additive successor composes the two without changing either
parent: it snapshots the caller stream around the black-box checkpoint-twenty
run, reconstructs a fresh local stream, replays every recorded waiting and
acceptance raw-word prefix, and inserts one checkpoint-twenty-one route
evidence record at every reconstructed route boundary.

The route object in the evidence is a same-runtime replay object, not the
identical Python object stored by checkpoint twenty.  The records are bound by
their semantic and candidate digests, parents, order, and exact Philox states.
This is finite-resolution procedural custody.  It is not an ideal categorical,
integer, or Gaussian law, a bounded raw-normal-word trace, a counter-keyed or
lineage-aware path, a liveness result, or a complete sampler.
"""

from __future__ import annotations

from dataclasses import dataclass
import platform
import sys
from typing import Dict, Mapping, Optional, Tuple

import numpy as np

try:
    from heterodiff.processes import (
        plugin_bridge_continuous_route_evidence as _route_evidence,
    )
    from heterodiff.processes import (
        plugin_bridge_operational_thinning as _thinning,
    )
    from heterodiff.processes import (
        plugin_bridge_operational_thinning_loop as _loop,
    )
except ModuleNotFoundError as error:  # pragma: no cover - subprocess tested
    if error.name == "torch" or "optional PyTorch" in str(error):
        raise ModuleNotFoundError(
            "route-evidenced operational thinning loops require the optional "
            "PyTorch reference dependency; install the 'reference' extra"
        ) from error
    raise
from heterodiff.processes.plugin_bridge_sampler import ReferenceCandidateIntensity


PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_ROUTE_EVIDENCE_SCHEMA_VERSION = (
    "plugin-bridge-operational-thinning-loop-route-evidence-v1"
)
PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_ROUTE_EVIDENCE_POLICY = (
    "checkpoint20-black-box-live-loop;exact-philox-loop-entry-exit-snapshots;"
    "checkpoint19-waiting-acceptance-raw64-prefix-replay;"
    "checkpoint21-route-evidence-at-every-reconstructed-route-boundary;"
    "ordered-semantic-route-binding;exact-reconstructed-loop-exit-v1"
)
PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_ROUTE_EVIDENCE_SCOPE = (
    "successful-return-bounded-checkpoint20-transcripts;"
    "one-checkpoint21-evidence-record-per-completed-proposal;"
    "same-runtime-finite-resolution-wait-route-accept-stream-custody;"
    "continuous-birth-and-unequal-positive-dimension-route-support;"
    "not-original-route-python-object-identity;"
    "not-live-snapshot-capture-at-original-route-call;"
    "not-bounded-raw-normal-word-trace;not-exact-categorical-law;"
    "not-exact-integer-law;not-exact-gaussian-law;"
    "not-analytic-lebesgue-output-law;not-distribution-recovery;"
    "not-unconditional-continuous-route-occurrence;"
    "not-unconditional-completion;not-exact-real-time-poisson-or-ctmc;"
    "not-exact-frozen-jump-law;not-active-total-exit;"
    "not-all-route-totality;not-analytic-or-conditional-target;"
    "not-stationarity;not-liveness;not-counter-key-stream;not-lineage;"
    "not-drift;not-initializer;not-path;not-strang;not-full-sampler;"
    "not-runtime-portable;not-cryptographic-authentication"
)

_CERTIFICATE_TOKEN = object()
_RESULT_TOKEN = object()
_OWNER_TOKEN = object()


class PluginBridgeOperationalThinningLoopRouteEvidenceError(ArithmeticError):
    """Raised when a returned loop cannot be reconstructed exactly."""


def _runtime_sha256() -> str:
    return _thinning._semantic_digest(
        {
            "domain": "plugin-bridge-loop-route-evidence-runtime-v1",
            "python_implementation": sys.implementation.name,
            "python_version": platform.python_version(),
            "platform_system": platform.system(),
            "platform_machine": platform.machine(),
            "numpy_version": np.__version__,
            "policy": (PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_ROUTE_EVIDENCE_POLICY),
            "snapshot_schema": (
                _route_evidence.PLUGIN_BRIDGE_PHILOX_ROUTE_STATE_SCHEMA_VERSION
            ),
            "maximum_proposals": _loop.OPERATIONAL_THINNING_LOOP_MAX_PROPOSALS,
            "binary64_probe": _thinning._require_binary64_environment(),
        }
    )


def _certificate_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return {
        name: value for name, value in values.items() if name != "certificate_sha256"
    }


@dataclass(frozen=True, eq=False, init=False)
class OperationalThinningLoopRouteEvidenceCertificate:
    """Transitive certificate for the checkpoint-twenty-two overlay."""

    schema_version: str
    certificate_scope: str
    integration_policy: str
    integration_role_sha256: str
    process_parameter_sha256: str
    loop_certificate_sha256: str
    loop_role_sha256: str
    loop_runtime_sha256: str
    route_evidence_certificate_sha256: str
    route_evidence_role_sha256: str
    route_evidence_runtime_sha256: str
    thinning_certificate_sha256: str
    rate_certificate_sha256: str
    integration_runtime_sha256: str
    philox_snapshot_schema_version: str
    rng_bit_generator: str
    maximum_proposals: int
    base_context_dimension: int
    residual_context_dimension: int
    parent_loop_black_box_delegation_certified: bool
    exact_loop_entry_exit_philox_snapshots_certified: bool
    waiting_acceptance_raw64_prefix_replay_certified: bool
    one_route_evidence_per_returned_proposal_certified: bool
    ordered_proposal_evidence_binding_certified: bool
    same_runtime_route_boundary_reconstruction_certified: bool
    candidate_semantic_and_post_state_replay_certified: bool
    sequential_wait_route_accept_state_custody_certified: bool
    accepted_refresh_rejected_reuse_inherited: bool
    terminal_stop_semantics_inherited: bool
    offline_validation_no_caller_rng_certified: bool
    returned_route_kind_and_continuous_classification_certified: bool
    active_cap_no_partial_return_inherited: bool
    original_route_python_object_identity_certified: bool
    live_snapshot_capture_at_original_route_call_certified: bool
    bounded_raw_normal_word_trace_certified: bool
    exact_categorical_law_certified: bool
    exact_integer_law_certified: bool
    exact_gaussian_law_certified: bool
    analytic_lebesgue_output_law_certified: bool
    ideal_distribution_recovery_certified: bool
    unconditional_continuous_route_occurrence_certified: bool
    unconditional_local_completion_certified: bool
    exact_real_time_poisson_or_ctmc_path_certified: bool
    unconditional_exact_frozen_jump_law_certified: bool
    exact_active_controlled_total_exit_computed: bool
    all_route_rate_totality_certified: bool
    analytic_target_preserved: bool
    conditional_posterior_or_doob_target: bool
    rounded_detailed_balance_or_stationarity_certified: bool
    sampler_liveness_certified: bool
    counter_key_stream_contract_certified: bool
    lineage_contract_certified: bool
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
            "OperationalThinningLoopRouteEvidenceCertificate cannot be subclassed"
        )

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError("loop route-evidence certificates are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("loop route-evidence certificate fields are incomplete")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])
        _validate_certificate(self)

    def parameter_key(self) -> Tuple[object, ...]:
        return (
            "plugin-bridge-operational-thinning-loop-route-evidence-v1",
            self.certificate_sha256,
        )

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("loop route-evidence certificates are not pickle objects")


def _certificate_fields() -> Tuple[str, ...]:
    return tuple(OperationalThinningLoopRouteEvidenceCertificate.__annotations__)


def _validate_certificate(
    certificate: object,
) -> OperationalThinningLoopRouteEvidenceCertificate:
    if type(certificate) is not OperationalThinningLoopRouteEvidenceCertificate:
        raise TypeError(
            "certificate must be an exact "
            "OperationalThinningLoopRouteEvidenceCertificate"
        )
    expected_text = {
        "schema_version": (
            PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_ROUTE_EVIDENCE_SCHEMA_VERSION
        ),
        "certificate_scope": (
            PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_ROUTE_EVIDENCE_SCOPE
        ),
        "integration_policy": (
            PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_ROUTE_EVIDENCE_POLICY
        ),
        "philox_snapshot_schema_version": (
            _route_evidence.PLUGIN_BRIDGE_PHILOX_ROUTE_STATE_SCHEMA_VERSION
        ),
        "rng_bit_generator": "numpy.random.Philox",
    }
    for name, expected in expected_text.items():
        if getattr(certificate, name) != expected:
            raise ValueError("loop route-evidence certificate %s differs" % name)
    for name in (
        "integration_role_sha256",
        "process_parameter_sha256",
        "loop_certificate_sha256",
        "loop_role_sha256",
        "loop_runtime_sha256",
        "route_evidence_certificate_sha256",
        "route_evidence_role_sha256",
        "route_evidence_runtime_sha256",
        "thinning_certificate_sha256",
        "rate_certificate_sha256",
        "integration_runtime_sha256",
        "certificate_sha256",
    ):
        _thinning._require_sha256(
            getattr(certificate, name),
            name="certificate.%s" % name,
        )
    for name in (
        "maximum_proposals",
        "base_context_dimension",
        "residual_context_dimension",
    ):
        _loop._exact_nonnegative_integer(
            getattr(certificate, name),
            name="certificate.%s" % name,
        )
    for name in ("base_context_dimension", "residual_context_dimension"):
        if getattr(certificate, name) > _loop._potential._MAX_CONTEXT_DIMENSION:
            raise ValueError("loop route-evidence %s exceeds its limit" % name)
    if certificate.maximum_proposals != _loop.OPERATIONAL_THINNING_LOOP_MAX_PROPOSALS:
        raise ValueError("loop route-evidence proposal maximum differs")
    true_flags = (
        "parent_loop_black_box_delegation_certified",
        "exact_loop_entry_exit_philox_snapshots_certified",
        "waiting_acceptance_raw64_prefix_replay_certified",
        "one_route_evidence_per_returned_proposal_certified",
        "ordered_proposal_evidence_binding_certified",
        "same_runtime_route_boundary_reconstruction_certified",
        "candidate_semantic_and_post_state_replay_certified",
        "sequential_wait_route_accept_state_custody_certified",
        "accepted_refresh_rejected_reuse_inherited",
        "terminal_stop_semantics_inherited",
        "offline_validation_no_caller_rng_certified",
        "returned_route_kind_and_continuous_classification_certified",
        "active_cap_no_partial_return_inherited",
        "passed",
    )
    false_flags = (
        "original_route_python_object_identity_certified",
        "live_snapshot_capture_at_original_route_call_certified",
        "bounded_raw_normal_word_trace_certified",
        "exact_categorical_law_certified",
        "exact_integer_law_certified",
        "exact_gaussian_law_certified",
        "analytic_lebesgue_output_law_certified",
        "ideal_distribution_recovery_certified",
        "unconditional_continuous_route_occurrence_certified",
        "unconditional_local_completion_certified",
        "exact_real_time_poisson_or_ctmc_path_certified",
        "unconditional_exact_frozen_jump_law_certified",
        "exact_active_controlled_total_exit_computed",
        "all_route_rate_totality_certified",
        "analytic_target_preserved",
        "conditional_posterior_or_doob_target",
        "rounded_detailed_balance_or_stationarity_certified",
        "sampler_liveness_certified",
        "counter_key_stream_contract_certified",
        "lineage_contract_certified",
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
        raise ValueError("loop route-evidence positive flags are inconsistent")
    if any(getattr(certificate, name) for name in false_flags):
        raise ValueError("loop route-evidence negative flags are inconsistent")
    values = {name: getattr(certificate, name) for name in _certificate_fields()}
    expected_digest = _thinning._semantic_digest(_certificate_payload(values))
    if certificate.certificate_sha256 != expected_digest:
        raise ValueError("loop route-evidence certificate digest differs")
    return certificate


def _make_certificate(
    loop_certificate: _loop.OperationalThinningLoopCertificate,
    route_certificate: _route_evidence.ContinuousRouteEvidenceCertificate,
    *,
    integration_role_sha256: str,
) -> OperationalThinningLoopRouteEvidenceCertificate:
    checked_loop = _loop._validate_certificate(loop_certificate)
    checked_route = _route_evidence._validate_certificate(route_certificate)
    if (
        checked_loop.thinning_certificate_sha256
        != checked_route.thinning_certificate_sha256
    ):
        raise ValueError("loop and route evidence use different thinning owners")
    if checked_loop.process_parameter_sha256 != checked_route.process_parameter_sha256:
        raise ValueError("loop and route evidence use different processes")
    if checked_loop.rate_certificate_sha256 != checked_route.rate_certificate_sha256:
        raise ValueError("loop and route evidence use different rate owners")
    values: Dict[str, object] = {
        "schema_version": (
            PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_ROUTE_EVIDENCE_SCHEMA_VERSION
        ),
        "certificate_scope": (
            PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_ROUTE_EVIDENCE_SCOPE
        ),
        "integration_policy": (
            PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_ROUTE_EVIDENCE_POLICY
        ),
        "integration_role_sha256": integration_role_sha256,
        "process_parameter_sha256": checked_loop.process_parameter_sha256,
        "loop_certificate_sha256": checked_loop.certificate_sha256,
        "loop_role_sha256": checked_loop.loop_role_sha256,
        "loop_runtime_sha256": checked_loop.loop_runtime_sha256,
        "route_evidence_certificate_sha256": checked_route.certificate_sha256,
        "route_evidence_role_sha256": checked_route.evidence_role_sha256,
        "route_evidence_runtime_sha256": checked_route.evidence_runtime_sha256,
        "thinning_certificate_sha256": checked_loop.thinning_certificate_sha256,
        "rate_certificate_sha256": checked_loop.rate_certificate_sha256,
        "integration_runtime_sha256": _runtime_sha256(),
        "philox_snapshot_schema_version": (
            _route_evidence.PLUGIN_BRIDGE_PHILOX_ROUTE_STATE_SCHEMA_VERSION
        ),
        "rng_bit_generator": "numpy.random.Philox",
        "maximum_proposals": checked_loop.maximum_proposals,
        "base_context_dimension": checked_loop.base_context_dimension,
        "residual_context_dimension": checked_loop.residual_context_dimension,
        "parent_loop_black_box_delegation_certified": True,
        "exact_loop_entry_exit_philox_snapshots_certified": True,
        "waiting_acceptance_raw64_prefix_replay_certified": True,
        "one_route_evidence_per_returned_proposal_certified": True,
        "ordered_proposal_evidence_binding_certified": True,
        "same_runtime_route_boundary_reconstruction_certified": True,
        "candidate_semantic_and_post_state_replay_certified": True,
        "sequential_wait_route_accept_state_custody_certified": True,
        "accepted_refresh_rejected_reuse_inherited": True,
        "terminal_stop_semantics_inherited": True,
        "offline_validation_no_caller_rng_certified": True,
        "returned_route_kind_and_continuous_classification_certified": True,
        "active_cap_no_partial_return_inherited": True,
        "original_route_python_object_identity_certified": False,
        "live_snapshot_capture_at_original_route_call_certified": False,
        "bounded_raw_normal_word_trace_certified": False,
        "exact_categorical_law_certified": False,
        "exact_integer_law_certified": False,
        "exact_gaussian_law_certified": False,
        "analytic_lebesgue_output_law_certified": False,
        "ideal_distribution_recovery_certified": False,
        "unconditional_continuous_route_occurrence_certified": False,
        "unconditional_local_completion_certified": False,
        "exact_real_time_poisson_or_ctmc_path_certified": False,
        "unconditional_exact_frozen_jump_law_certified": False,
        "exact_active_controlled_total_exit_computed": False,
        "all_route_rate_totality_certified": False,
        "analytic_target_preserved": False,
        "conditional_posterior_or_doob_target": False,
        "rounded_detailed_balance_or_stationarity_certified": False,
        "sampler_liveness_certified": False,
        "counter_key_stream_contract_certified": False,
        "lineage_contract_certified": False,
        "continuous_drift_admissible": False,
        "initializer_admissible": False,
        "path_admissible": False,
        "strang_sampler_admissible": False,
        "full_sampler_admissible": False,
        "runtime_portable": False,
        "cryptographic_authentication": False,
        "passed": True,
        "certificate_sha256": "0" * 64,
    }
    values["certificate_sha256"] = _thinning._semantic_digest(
        _certificate_payload(values)
    )
    return OperationalThinningLoopRouteEvidenceCertificate(
        **values,
        _construction_token=_CERTIFICATE_TOKEN,
    )


def _result_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    omitted = {
        "certificate",
        "loop_result",
        "loop_entry_state",
        "loop_exit_state",
        "route_evidences",
        "result_sha256",
    }
    return {name: value for name, value in values.items() if name not in omitted}


def _validate_loop_result_record(
    result: object,
) -> _loop.OperationalLocalThinningResult:
    if type(result) is not _loop.OperationalLocalThinningResult:
        raise TypeError("loop_result has the wrong exact type")
    return _loop.OperationalLocalThinningResult(
        **_thinning._snapshot_fields(result, _loop._result_fields()),
        _construction_token=_loop._RESULT_TOKEN,
    )


def _validate_route_evidence_record(
    evidence: object,
) -> _route_evidence.OperationalReferenceRouteEvidence:
    if type(evidence) is not _route_evidence.OperationalReferenceRouteEvidence:
        raise TypeError("route evidence has the wrong exact type")
    return _route_evidence.OperationalReferenceRouteEvidence(
        **{
            name: getattr(evidence, name) for name in _route_evidence._evidence_fields()
        },
        _construction_token=_route_evidence._EVIDENCE_TOKEN,
    )


def _snapshot_matches(
    first: _route_evidence.PhiloxRouteStateSnapshot,
    second: _route_evidence.PhiloxRouteStateSnapshot,
) -> bool:
    return all(
        getattr(first, name) == getattr(second, name)
        for name in _route_evidence._snapshot_fields()
    )


def _require_iteration_evidence_binding(
    iteration: _loop.OperationalProposalIteration,
    evidence: _route_evidence.OperationalReferenceRouteEvidence,
) -> None:
    expected = {
        "waiting_draw_sha256": iteration.waiting_draw_sha256,
        "intensity_sha256": iteration.pre_intensity_sha256,
        "envelope_sha256": iteration.pre_envelope_sha256,
        "route_draw_sha256": iteration.route_draw_sha256,
        "process_parameter_sha256": (iteration.route_draw.process_parameter_sha256),
        "source_state_sha256": iteration.route_draw.source_state_sha256,
        "destination_state_sha256": iteration.route_draw.destination_state_sha256,
        "rng_state_before_sha256": iteration.route_draw.rng_state_before_sha256,
        "rng_state_after_sha256": iteration.route_draw.rng_state_after_sha256,
    }
    for name, value in expected.items():
        if getattr(evidence, name) != value:
            raise ValueError("route evidence %s differs from loop iteration" % name)
    if evidence.route_draw.candidate_sha256 != iteration.route_draw.candidate_sha256:
        raise ValueError("route evidence candidate differs from loop iteration")
    if evidence.edit_kind != iteration.route_draw.edit_kind:
        raise ValueError("route evidence edit kind differs from loop iteration")
    if evidence.pre_route_state.state_sha256 != (
        iteration.waiting_draw.rng_state_after_sha256
    ):
        raise ValueError("route evidence pre-state differs from waiting transition")
    if evidence.post_route_state.state_sha256 != (
        iteration.decision.rng_state_before_sha256
    ):
        raise ValueError("route evidence post-state differs from acceptance transition")


@dataclass(frozen=True, eq=False, init=False)
class OperationalLocalThinningRouteEvidence:
    """Sealed route-evidence overlay for one successful checkpoint-20 result."""

    certificate: OperationalThinningLoopRouteEvidenceCertificate
    certificate_sha256: str
    loop_result: _loop.OperationalLocalThinningResult
    loop_result_sha256: str
    loop_entry_state: _route_evidence.PhiloxRouteStateSnapshot
    loop_entry_snapshot_sha256: str
    loop_exit_state: _route_evidence.PhiloxRouteStateSnapshot
    loop_exit_snapshot_sha256: str
    route_evidences: Tuple[_route_evidence.OperationalReferenceRouteEvidence, ...]
    route_evidence_sha256s: Tuple[str, ...]
    proposal_count: int
    accepted_count: int
    rejected_count: int
    continuous_destination_proposal_count: int
    continuous_destination_accepted_count: int
    positive_dimensional_birth_proposal_count: int
    positive_dimensional_replacement_proposal_count: int
    unequal_positive_dimensional_replacement_proposal_count: int
    unequal_positive_dimensional_replacement_accepted_count: int
    every_completed_proposal_has_route_evidence: bool
    same_runtime_full_loop_rng_replay_completed: bool
    terminal_waiting_prefix_replayed: bool
    original_route_python_object_identity_certified: bool
    live_snapshot_capture_at_original_route_call_certified: bool
    rng_state_before_sha256: str
    rng_state_after_sha256: str
    result_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("OperationalLocalThinningRouteEvidence cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _RESULT_TOKEN:
            raise TypeError("loop route-evidence results are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("loop route-evidence result fields are incomplete")
        certificate = _validate_certificate(values["certificate"])
        if values["certificate_sha256"] != certificate.certificate_sha256:
            raise ValueError("loop route-evidence result certificate differs")
        loop_result = _validate_loop_result_record(values["loop_result"])
        if values["loop_result_sha256"] != loop_result.result_sha256:
            raise ValueError("loop route-evidence parent-result digest differs")
        if loop_result.certificate_sha256 != certificate.loop_certificate_sha256:
            raise ValueError("loop route-evidence result uses another parent loop")
        entry = _route_evidence._validate_snapshot(values["loop_entry_state"])
        exit_state = _route_evidence._validate_snapshot(values["loop_exit_state"])
        for name in (
            "certificate_sha256",
            "loop_result_sha256",
            "loop_entry_snapshot_sha256",
            "loop_exit_snapshot_sha256",
            "rng_state_before_sha256",
            "rng_state_after_sha256",
            "result_sha256",
        ):
            _thinning._require_sha256(
                values[name],
                name="loop_route_evidence.%s" % name,
            )
        if values["loop_entry_snapshot_sha256"] != entry.snapshot_sha256:
            raise ValueError("loop-entry snapshot digest differs")
        if values["loop_exit_snapshot_sha256"] != exit_state.snapshot_sha256:
            raise ValueError("loop-exit snapshot digest differs")
        if values["rng_state_before_sha256"] != entry.state_sha256:
            raise ValueError("loop-entry state digest differs")
        if values["rng_state_after_sha256"] != exit_state.state_sha256:
            raise ValueError("loop-exit state digest differs")
        if values["rng_state_before_sha256"] != loop_result.rng_state_before_sha256:
            raise ValueError("loop-entry snapshot differs from checkpoint twenty")
        if values["rng_state_after_sha256"] != loop_result.rng_state_after_sha256:
            raise ValueError("loop-exit snapshot differs from checkpoint twenty")
        if type(values["route_evidences"]) is not tuple:
            raise TypeError("route_evidences must be an exact tuple")
        if type(values["route_evidence_sha256s"]) is not tuple:
            raise TypeError("route evidence digests must be an exact tuple")
        evidences = values["route_evidences"]
        if len(evidences) != loop_result.proposal_count:
            raise ValueError("route evidence count differs from proposal count")
        checked_evidences = tuple(
            _validate_route_evidence_record(evidence) for evidence in evidences
        )
        expected_evidence_digests = tuple(
            evidence.evidence_sha256 for evidence in checked_evidences
        )
        if values["route_evidence_sha256s"] != expected_evidence_digests:
            raise ValueError("ordered route evidence digests differ")
        for iteration, evidence in zip(loop_result.iterations, checked_evidences):
            if (
                evidence.certificate_sha256
                != certificate.route_evidence_certificate_sha256
            ):
                raise ValueError("route evidence belongs to another evidence owner")
            _require_iteration_evidence_binding(iteration, evidence)
        integer_counts = (
            "proposal_count",
            "accepted_count",
            "rejected_count",
            "continuous_destination_proposal_count",
            "continuous_destination_accepted_count",
            "positive_dimensional_birth_proposal_count",
            "positive_dimensional_replacement_proposal_count",
            "unequal_positive_dimensional_replacement_proposal_count",
            "unequal_positive_dimensional_replacement_accepted_count",
        )
        for name in integer_counts:
            _loop._exact_nonnegative_integer(
                values[name],
                name="loop_route_evidence.%s" % name,
            )
        expected_counts = {
            "proposal_count": loop_result.proposal_count,
            "accepted_count": loop_result.accepted_count,
            "rejected_count": loop_result.rejected_count,
            "continuous_destination_proposal_count": sum(
                int(evidence.continuous_destination) for evidence in checked_evidences
            ),
            "continuous_destination_accepted_count": sum(
                int(evidence.continuous_destination and iteration.accepted)
                for iteration, evidence in zip(
                    loop_result.iterations,
                    checked_evidences,
                )
            ),
            "positive_dimensional_birth_proposal_count": sum(
                int(evidence.positive_dimensional_birth)
                for evidence in checked_evidences
            ),
            "positive_dimensional_replacement_proposal_count": sum(
                int(evidence.positive_dimensional_replacement)
                for evidence in checked_evidences
            ),
            "unequal_positive_dimensional_replacement_proposal_count": sum(
                int(evidence.unequal_positive_dimensional_replacement)
                for evidence in checked_evidences
            ),
            "unequal_positive_dimensional_replacement_accepted_count": sum(
                int(
                    evidence.unequal_positive_dimensional_replacement
                    and iteration.accepted
                )
                for iteration, evidence in zip(
                    loop_result.iterations,
                    checked_evidences,
                )
            ),
        }
        for name, expected in expected_counts.items():
            if values[name] != expected:
                raise ValueError("loop route-evidence %s differs" % name)
        expected_booleans = {
            "every_completed_proposal_has_route_evidence": True,
            "same_runtime_full_loop_rng_replay_completed": True,
            "terminal_waiting_prefix_replayed": True,
            "original_route_python_object_identity_certified": False,
            "live_snapshot_capture_at_original_route_call_certified": False,
        }
        for name, expected in expected_booleans.items():
            if type(values[name]) is not bool or values[name] is not expected:
                raise ValueError("loop route-evidence %s differs" % name)
        expected_digest = _thinning._semantic_digest(_result_payload(values))
        if values["result_sha256"] != expected_digest:
            raise ValueError("loop route-evidence result digest differs")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("loop route-evidence results are not pickle objects")


def _result_fields() -> Tuple[str, ...]:
    return tuple(OperationalLocalThinningRouteEvidence.__annotations__)


def _replay_raw64_prefix(
    rng: np.random.Generator,
    record: object,
    *,
    context: str,
) -> None:
    session = _thinning._PhiloxRaw64Session(rng)
    if session.state_before_sha256 != record.rng_state_before_sha256:
        raise PluginBridgeOperationalThinningLoopRouteEvidenceError(
            "%s did not begin at the recorded Philox state" % context
        )
    for index, expected in enumerate(record.raw_words):
        actual = session.draw_word()
        if actual != expected:
            raise PluginBridgeOperationalThinningLoopRouteEvidenceError(
                "%s raw word %d differs" % (context, index)
            )
    after = session.finish()
    if after != record.rng_state_after_sha256:
        raise PluginBridgeOperationalThinningLoopRouteEvidenceError(
            "%s did not end at the recorded Philox state" % context
        )


class BoundedOperationalThinningLoopRouteEvidence:
    """Immutable black-box checkpoint-20 route-evidence overlay."""

    __slots__ = (
        "_loop_owner",
        "_certified_loop_owner",
        "_route_evidence_owner",
        "_certified_route_evidence_owner",
        "_thinning_owner",
        "_reference_composer",
        "_integration_role_sha256",
        "_certificate",
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError(
            "BoundedOperationalThinningLoopRouteEvidence cannot be subclassed"
        )

    def __init__(
        self,
        loop_owner: _loop.BoundedOperationalThinningLoop,
        route_evidence_owner: _route_evidence.ContinuousRouteEvidenceOwner,
        integration_role_sha256: str,
        certificate: OperationalThinningLoopRouteEvidenceCertificate,
        *,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _OWNER_TOKEN:
            raise TypeError("loop route-evidence owners require certification")
        if type(loop_owner) is not _loop.BoundedOperationalThinningLoop:
            raise TypeError("loop_owner has the wrong exact type")
        if (
            type(route_evidence_owner)
            is not _route_evidence.ContinuousRouteEvidenceOwner
        ):
            raise TypeError("route_evidence_owner has the wrong exact type")
        role = _thinning._require_sha256(
            integration_role_sha256,
            name="integration_role_sha256",
        )
        checked_certificate = _validate_certificate(certificate)
        if checked_certificate.integration_role_sha256 != role:
            raise ValueError("loop route-evidence role differs from certificate")
        object.__setattr__(self, "_loop_owner", loop_owner)
        object.__setattr__(self, "_certified_loop_owner", loop_owner)
        object.__setattr__(self, "_route_evidence_owner", route_evidence_owner)
        object.__setattr__(
            self,
            "_certified_route_evidence_owner",
            route_evidence_owner,
        )
        object.__setattr__(self, "_thinning_owner", loop_owner.thinning_owner)
        object.__setattr__(
            self,
            "_reference_composer",
            loop_owner.reference_composer,
        )
        object.__setattr__(self, "_integration_role_sha256", role)
        object.__setattr__(self, "_certificate", checked_certificate)

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("BoundedOperationalThinningLoopRouteEvidence is immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("BoundedOperationalThinningLoopRouteEvidence is immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("loop route-evidence owners are not pickle objects")

    @property
    def certificate(self) -> OperationalThinningLoopRouteEvidenceCertificate:
        return self._certificate

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
    def reference_composer(self):  # type: ignore[no-untyped-def]
        return self._reference_composer

    def _require_live_binding(
        self,
    ) -> OperationalThinningLoopRouteEvidenceCertificate:
        _thinning._require_binary64_environment()
        if type(self._loop_owner) is not _loop.BoundedOperationalThinningLoop:
            raise TypeError("loop owner has the wrong exact type")
        if self._loop_owner is not self._certified_loop_owner:
            raise ValueError("loop-owner binding changed")
        if (
            type(self._route_evidence_owner)
            is not _route_evidence.ContinuousRouteEvidenceOwner
        ):
            raise TypeError("route-evidence owner has the wrong exact type")
        if self._route_evidence_owner is not self._certified_route_evidence_owner:
            raise ValueError("route-evidence-owner binding changed")
        loop_certificate = self._loop_owner._require_live_binding()
        route_certificate = self._route_evidence_owner._require_live_binding()
        if self._loop_owner.thinning_owner is not self._thinning_owner:
            raise ValueError("loop/thinning-owner binding changed")
        if self._route_evidence_owner.thinning_owner is not self._thinning_owner:
            raise ValueError("route-evidence/thinning-owner binding changed")
        if self._loop_owner.reference_composer is not self._reference_composer:
            raise ValueError("loop reference-composer binding changed")
        if self._route_evidence_owner.reference_composer is not (
            self._reference_composer
        ):
            raise ValueError("route-evidence reference-composer binding changed")
        if self.certificate.integration_runtime_sha256 != _runtime_sha256():
            raise ValueError("live loop route-evidence runtime differs")
        expected = _make_certificate(
            loop_certificate,
            route_certificate,
            integration_role_sha256=self._integration_role_sha256,
        )
        for name in _certificate_fields():
            if not _thinning._field_matches(
                name,
                getattr(self.certificate, name),
                getattr(expected, name),
            ):
                raise ValueError(
                    "loop route-evidence certificate field %s differs" % name
                )
        _thinning._require_binary64_environment()
        return self.certificate

    def _replay_stream(
        self,
        loop_result: _loop.OperationalLocalThinningResult,
        entry_state: _route_evidence.PhiloxRouteStateSnapshot,
        *,
        expected_evidences: Optional[
            Tuple[_route_evidence.OperationalReferenceRouteEvidence, ...]
        ],
    ) -> Tuple[
        Tuple[_route_evidence.OperationalReferenceRouteEvidence, ...],
        _route_evidence.PhiloxRouteStateSnapshot,
    ]:
        replay_rng = _route_evidence._generator_from_snapshot(entry_state)
        collected = []
        for index, iteration in enumerate(loop_result.iterations):
            _replay_raw64_prefix(
                replay_rng,
                iteration.waiting_draw,
                context="proposal %d waiting prefix" % index,
            )
            if expected_evidences is None:
                evidence = self.route_evidence_owner.draw_reference_route_with_evidence(
                    iteration.waiting_draw,
                    iteration.pre_intensity,
                    iteration.pre_envelope,
                    rng=replay_rng,
                )
            else:
                evidence = expected_evidences[index]
                current = _route_evidence._capture_philox_state(replay_rng)
                if not _snapshot_matches(current, evidence.pre_route_state):
                    raise PluginBridgeOperationalThinningLoopRouteEvidenceError(
                        "proposal %d route pre-state differs" % index
                    )
                self.route_evidence_owner.validate_reference_route_evidence(
                    evidence,
                    iteration.waiting_draw,
                    iteration.pre_intensity,
                    iteration.pre_envelope,
                )
                replay_rng = _route_evidence._generator_from_snapshot(
                    evidence.post_route_state
                )
            _require_iteration_evidence_binding(iteration, evidence)
            route_post = _route_evidence._capture_philox_state(replay_rng)
            if not _snapshot_matches(route_post, evidence.post_route_state):
                raise PluginBridgeOperationalThinningLoopRouteEvidenceError(
                    "proposal %d route post-state differs" % index
                )
            _replay_raw64_prefix(
                replay_rng,
                iteration.decision,
                context="proposal %d acceptance prefix" % index,
            )
            collected.append(evidence)
        _replay_raw64_prefix(
            replay_rng,
            loop_result.terminal_waiting_draw,
            context="terminal waiting prefix",
        )
        return tuple(collected), _route_evidence._capture_philox_state(replay_rng)

    def _make_result(
        self,
        loop_result: _loop.OperationalLocalThinningResult,
        entry_state: _route_evidence.PhiloxRouteStateSnapshot,
        exit_state: _route_evidence.PhiloxRouteStateSnapshot,
        evidences: Tuple[_route_evidence.OperationalReferenceRouteEvidence, ...],
    ) -> OperationalLocalThinningRouteEvidence:
        pairs = tuple(zip(loop_result.iterations, evidences))
        values: Dict[str, object] = {
            "certificate": self.certificate,
            "certificate_sha256": self.certificate.certificate_sha256,
            "loop_result": loop_result,
            "loop_result_sha256": loop_result.result_sha256,
            "loop_entry_state": entry_state,
            "loop_entry_snapshot_sha256": entry_state.snapshot_sha256,
            "loop_exit_state": exit_state,
            "loop_exit_snapshot_sha256": exit_state.snapshot_sha256,
            "route_evidences": evidences,
            "route_evidence_sha256s": tuple(
                evidence.evidence_sha256 for evidence in evidences
            ),
            "proposal_count": loop_result.proposal_count,
            "accepted_count": loop_result.accepted_count,
            "rejected_count": loop_result.rejected_count,
            "continuous_destination_proposal_count": sum(
                int(evidence.continuous_destination) for evidence in evidences
            ),
            "continuous_destination_accepted_count": sum(
                int(evidence.continuous_destination and iteration.accepted)
                for iteration, evidence in pairs
            ),
            "positive_dimensional_birth_proposal_count": sum(
                int(evidence.positive_dimensional_birth) for evidence in evidences
            ),
            "positive_dimensional_replacement_proposal_count": sum(
                int(evidence.positive_dimensional_replacement) for evidence in evidences
            ),
            "unequal_positive_dimensional_replacement_proposal_count": sum(
                int(evidence.unequal_positive_dimensional_replacement)
                for evidence in evidences
            ),
            "unequal_positive_dimensional_replacement_accepted_count": sum(
                int(
                    evidence.unequal_positive_dimensional_replacement
                    and iteration.accepted
                )
                for iteration, evidence in pairs
            ),
            "every_completed_proposal_has_route_evidence": True,
            "same_runtime_full_loop_rng_replay_completed": True,
            "terminal_waiting_prefix_replayed": True,
            "original_route_python_object_identity_certified": False,
            "live_snapshot_capture_at_original_route_call_certified": False,
            "rng_state_before_sha256": entry_state.state_sha256,
            "rng_state_after_sha256": exit_state.state_sha256,
            "result_sha256": "0" * 64,
        }
        values["result_sha256"] = _thinning._semantic_digest(_result_payload(values))
        return OperationalLocalThinningRouteEvidence(
            **values,
            _construction_token=_RESULT_TOKEN,
        )

    def run(
        self,
        initial_intensity: ReferenceCandidateIntensity,
        initial_envelope: _loop.TotalizedJumpRateEnvelope,
        *,
        clock_start: object,
        right_endpoint: object,
        proposal_budget: object,
        base_context: object,
        residual_context: object,
        rng: np.random.Generator,
    ) -> OperationalLocalThinningRouteEvidence:
        """Run checkpoint twenty and add one replay witness per proposal."""

        self._require_live_binding()
        checked_rng = _thinning._require_philox_rng(rng)
        entry_state = _route_evidence._capture_philox_state(checked_rng)
        loop_result = self.loop_owner.run(
            initial_intensity,
            initial_envelope,
            clock_start=clock_start,
            right_endpoint=right_endpoint,
            proposal_budget=proposal_budget,
            base_context=base_context,
            residual_context=residual_context,
            rng=checked_rng,
        )
        exit_state = _route_evidence._capture_philox_state(checked_rng)
        if entry_state.state_sha256 != loop_result.rng_state_before_sha256:
            raise PluginBridgeOperationalThinningLoopRouteEvidenceError(
                "checkpoint twenty began from another Philox state"
            )
        if exit_state.state_sha256 != loop_result.rng_state_after_sha256:
            raise PluginBridgeOperationalThinningLoopRouteEvidenceError(
                "checkpoint twenty ended at another Philox state"
            )
        evidences, replay_exit = self._replay_stream(
            loop_result,
            entry_state,
            expected_evidences=None,
        )
        if not _snapshot_matches(replay_exit, exit_state):
            raise PluginBridgeOperationalThinningLoopRouteEvidenceError(
                "reconstructed loop exit differs from the caller stream"
            )
        result = self._make_result(
            loop_result,
            entry_state,
            exit_state,
            evidences,
        )
        self.validate_result(
            result,
            initial_intensity,
            initial_envelope,
            clock_start=clock_start,
            right_endpoint=right_endpoint,
            proposal_budget=proposal_budget,
            base_context=base_context,
            residual_context=residual_context,
        )
        unchanged = _route_evidence._capture_philox_state(checked_rng)
        if not _snapshot_matches(unchanged, exit_state):
            raise PluginBridgeOperationalThinningLoopRouteEvidenceError(
                "offline loop replay consumed caller randomness"
            )
        self._require_live_binding()
        return result

    def validate_result(
        self,
        result: OperationalLocalThinningRouteEvidence,
        initial_intensity: ReferenceCandidateIntensity,
        initial_envelope: _loop.TotalizedJumpRateEnvelope,
        *,
        clock_start: object,
        right_endpoint: object,
        proposal_budget: object,
        base_context: object,
        residual_context: object,
    ) -> OperationalLocalThinningRouteEvidence:
        """Replay the composite result without accepting a caller RNG."""

        self._require_live_binding()
        if type(result) is not OperationalLocalThinningRouteEvidence:
            raise TypeError("result has the wrong exact type")
        OperationalLocalThinningRouteEvidence(
            **{name: getattr(result, name) for name in _result_fields()},
            _construction_token=_RESULT_TOKEN,
        )
        if result.certificate is not self.certificate:
            raise ValueError("result belongs to another loop route-evidence owner")
        loop_result = self.loop_owner.validate_result(
            result.loop_result,
            initial_intensity,
            initial_envelope,
            clock_start=clock_start,
            right_endpoint=right_endpoint,
            proposal_budget=proposal_budget,
            base_context=base_context,
            residual_context=residual_context,
        )
        replayed, replay_exit = self._replay_stream(
            loop_result,
            result.loop_entry_state,
            expected_evidences=result.route_evidences,
        )
        if tuple(evidence.evidence_sha256 for evidence in replayed) != (
            result.route_evidence_sha256s
        ):
            raise ValueError("route evidence sequence differs from replay")
        if not _snapshot_matches(replay_exit, result.loop_exit_state):
            raise PluginBridgeOperationalThinningLoopRouteEvidenceError(
                "offline loop replay ended at another Philox state"
            )
        self._require_live_binding()
        return result


def certify_plugin_bridge_operational_thinning_loop_route_evidence(
    loop_owner: _loop.BoundedOperationalThinningLoop,
    route_evidence_owner: _route_evidence.ContinuousRouteEvidenceOwner,
    *,
    integration_policy: object,
    integration_role_sha256: object,
) -> BoundedOperationalThinningLoopRouteEvidence:
    """Certify the additive checkpoint-twenty-two route-evidence overlay."""

    if type(integration_policy) is not str:
        raise TypeError("integration_policy must be exact text")
    if integration_policy != (
        PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_ROUTE_EVIDENCE_POLICY
    ):
        raise ValueError("only the exported loop route-evidence policy is supported")
    role = _thinning._require_sha256(
        integration_role_sha256,
        name="integration_role_sha256",
    )
    if type(loop_owner) is not _loop.BoundedOperationalThinningLoop:
        raise TypeError("loop_owner has the wrong exact type")
    if type(route_evidence_owner) is not _route_evidence.ContinuousRouteEvidenceOwner:
        raise TypeError("route_evidence_owner has the wrong exact type")
    if loop_owner.thinning_owner is not route_evidence_owner.thinning_owner:
        raise ValueError("loop and route-evidence owners use different thinning owners")
    if loop_owner.reference_composer is not route_evidence_owner.reference_composer:
        raise ValueError(
            "loop and route-evidence owners use different reference composers"
        )
    loop_certificate = loop_owner._require_live_binding()
    route_certificate = route_evidence_owner._require_live_binding()
    certificate = _make_certificate(
        loop_certificate,
        route_certificate,
        integration_role_sha256=role,
    )
    owner = BoundedOperationalThinningLoopRouteEvidence(
        loop_owner,
        route_evidence_owner,
        role,
        certificate,
        _construction_token=_OWNER_TOKEN,
    )
    owner._require_live_binding()
    return owner


def require_matching_plugin_bridge_operational_thinning_loop_route_evidence(
    loop_owner: _loop.BoundedOperationalThinningLoop,
    route_evidence_owner: _route_evidence.ContinuousRouteEvidenceOwner,
    owner: BoundedOperationalThinningLoopRouteEvidence,
    *,
    integration_policy: object,
    integration_role_sha256: object,
) -> BoundedOperationalThinningLoopRouteEvidence:
    """Require exact parent identities and reconstructed transitive custody."""

    if type(integration_policy) is not str:
        raise TypeError("integration_policy must be exact text")
    if integration_policy != (
        PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_ROUTE_EVIDENCE_POLICY
    ):
        raise ValueError("only the exported loop route-evidence policy is supported")
    role = _thinning._require_sha256(
        integration_role_sha256,
        name="integration_role_sha256",
    )
    if type(owner) is not BoundedOperationalThinningLoopRouteEvidence:
        raise TypeError(
            "owner must be an exact BoundedOperationalThinningLoopRouteEvidence"
        )
    if owner.loop_owner is not loop_owner:
        raise ValueError("loop route-evidence owner uses another loop owner")
    if owner.route_evidence_owner is not route_evidence_owner:
        raise ValueError("loop route-evidence owner uses another evidence owner")
    if owner.certificate.integration_role_sha256 != role:
        raise ValueError("loop route-evidence owner uses another role")
    owner._require_live_binding()
    return owner


def validate_plugin_bridge_operational_thinning_loop_route_evidence_certificate(
    loop_owner: _loop.BoundedOperationalThinningLoop,
    route_evidence_owner: _route_evidence.ContinuousRouteEvidenceOwner,
    owner: BoundedOperationalThinningLoopRouteEvidence,
    *,
    integration_policy: object,
    integration_role_sha256: object,
) -> OperationalThinningLoopRouteEvidenceCertificate:
    """Return the reconstructed live checkpoint-twenty-two certificate."""

    return require_matching_plugin_bridge_operational_thinning_loop_route_evidence(
        loop_owner,
        route_evidence_owner,
        owner,
        integration_policy=integration_policy,
        integration_role_sha256=integration_role_sha256,
    ).certificate


__all__ = [
    "PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_ROUTE_EVIDENCE_POLICY",
    "PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_ROUTE_EVIDENCE_SCHEMA_VERSION",
    "PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_ROUTE_EVIDENCE_SCOPE",
    "BoundedOperationalThinningLoopRouteEvidence",
    "OperationalLocalThinningRouteEvidence",
    "OperationalThinningLoopRouteEvidenceCertificate",
    "PluginBridgeOperationalThinningLoopRouteEvidenceError",
    "certify_plugin_bridge_operational_thinning_loop_route_evidence",
    "require_matching_plugin_bridge_operational_thinning_loop_route_evidence",
    "validate_plugin_bridge_operational_thinning_loop_route_evidence_certificate",
]
