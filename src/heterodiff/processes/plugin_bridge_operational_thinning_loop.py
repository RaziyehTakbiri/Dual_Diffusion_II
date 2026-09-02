"""Bounded repetition of the checkpoint-nineteen operational thinning step.

Checkpoint nineteen resolves one frozen local wait, normalized-reference
route, and exact represented-ratio Bernoulli.  This module composes that
primitive into a bounded successful-return proposal transcript.  Rejections
advance only the represented operational clock and reuse the exact state,
intensity, and envelope objects.  Acceptances advance the state and
immediately preflight a fresh process-owned intensity and rate envelope at the
same frozen generative time.

The transcript uses one continuing mutable Philox stream.  A result is
returned only after certified interval exhaustion: structural zero, a
zero-duration hold, or an active waiting draw beyond the right endpoint.  An
exact caller-supplied proposal budget no larger than sixty-four is a resource
cap, not a successful stop.  Reaching it while the subproblem remains active
refuses the whole call without rolling back consumed random bits.

This is not a counter-keyed stream, lineage manager, continuous-drift step,
analytic-target sampler, exact real-time Poisson/CTMC path, Strang integrator,
or full sampler.  In particular, repetition starts each new waiting clock at
checkpoint nineteen's rounded binary64 ``proposal_time`` and inherits the
finite-resolution normalized-reference route.
"""

from __future__ import annotations

from dataclasses import dataclass
import platform
import sys
from typing import Dict, Mapping, Tuple

import numpy as np

try:
    from heterodiff.models import (
        configuration_totalized_jump_rate_envelope_torch as _rate,
    )
    from heterodiff.processes import plugin_bridge_operational_thinning as _thin
except ModuleNotFoundError as error:  # pragma: no cover - subprocess tested
    if error.name == "torch" or "optional PyTorch" in str(error):
        raise ModuleNotFoundError(
            "bounded operational thinning loops require the optional PyTorch "
            "reference dependency; install the 'reference' extra"
        ) from error
    raise
from heterodiff.processes.plugin_bridge_sampler import ReferenceCandidateIntensity
from heterodiff.theory.configuration_reference import TransformedConfiguration


# Keep the unavoidable private cross-check helpers in one explicit adapter
# block.  Checkpoint nineteen already depends on these exact semantic digests.
_potential = _rate._potential
_configuration_semantic_payload = _thin._configuration_semantic_payload
_configuration_sha256 = _thin._configuration_sha256
_context_sha256 = _potential._context_sha256
_decision_fields = _thin._decision_fields
_envelope_fields = _rate._envelope_fields
_field_matches = _thin._field_matches
_intensity_sha256 = _thin._intensity_sha256
_record_unchanged = _thin._record_unchanged
_require_binary64_environment = _thin._require_binary64_environment
_require_philox_rng = _thin._require_philox_rng
_require_sha256 = _thin._require_sha256
_rng_state_sha256 = _thin._rng_state_sha256
_same_float = _thin._same_float
_semantic_digest = _thin._semantic_digest
_snapshot_fields = _thin._snapshot_fields
_validated_context = _potential._validated_context

OperationalAcceptanceDecision = _thin.OperationalAcceptanceDecision
OperationalJumpThinning = _thin.OperationalJumpThinning
OperationalReferenceRouteDraw = _thin.OperationalReferenceRouteDraw
OperationalWaitingTimeDraw = _thin.OperationalWaitingTimeDraw
TotalizedJumpPotentialCandidateEvaluation = (
    _rate.TotalizedJumpPotentialCandidateEvaluation
)
TotalizedJumpRateCandidateEvaluation = _rate.TotalizedJumpRateCandidateEvaluation
TotalizedJumpRateEnvelope = _rate.TotalizedJumpRateEnvelope


PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_SCHEMA_VERSION = (
    "plugin-bridge-operational-thinning-loop-v1"
)
PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_POLICY = (
    "checkpoint19-sequential-local-proposals;"
    "represented-proposal-time-clock-continuation;"
    "exact-rejection-parent-identity-reuse;"
    "accepted-state-immediate-intensity-envelope-refresh;"
    "single-continuing-philox-stream;"
    "terminal-hold-before-proposal-cap;"
    "bounded-proposal-cap-refusal;no-speculative-post-cap-wait-v1"
)
PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_SCOPE = (
    "checkpoint17-operational-surrogate-target;"
    "fixed-generative-time-bounded-successful-transcript;"
    "structural-zero-or-right-endpoint-success;proposal-budget-refusal;"
    "trusted-runtime;not-exact-real-time-poisson-or-ctmc-path;"
    "not-exact-categorical-or-gaussian-route;"
    "not-continuous-destination-operational-evidence;"
    "not-unconditional-local-completion;"
    "not-unconditional-exact-frozen-jump-law;"
    "not-active-total-exit;not-liveness;not-analytic-target;"
    "not-conditional-posterior-or-doob-target;"
    "not-rounded-detailed-balance;not-stationary-target;"
    "not-counter-key-stream;not-lineage;not-drift;not-initializer;"
    "not-path;not-strang-sampler;not-full-sampler"
)

OPERATIONAL_THINNING_LOOP_MAX_PROPOSALS = 64

_CERTIFICATE_TOKEN = object()
_ITERATION_TOKEN = object()
_RESULT_TOKEN = object()
_OWNER_TOKEN = object()

_STOP_REFERENCE_ZERO = "reference_intensity_zero"
_STOP_RIGHT_ENDPOINT = "right_endpoint_exhausted"
_STOP_REASONS = (
    _STOP_REFERENCE_ZERO,
    _STOP_RIGHT_ENDPOINT,
)


class PluginBridgeOperationalThinningLoopError(ArithmeticError):
    """Raised when a bounded local transcript cannot be certified safely."""


def _exact_nonnegative_integer(value: object, *, name: str) -> int:
    if type(value) is not int or isinstance(value, bool):
        raise TypeError("%s must be an exact integer" % name)
    if value < 0:
        raise ValueError("%s must be nonnegative" % name)
    return value


def _proposal_budget(value: object) -> int:
    result = _exact_nonnegative_integer(value, name="proposal_budget")
    if result > OPERATIONAL_THINNING_LOOP_MAX_PROPOSALS:
        raise ValueError("proposal_budget exceeds the certified loop maximum")
    return result


def _clock_float(value: object, *, name: str) -> float:
    return _thin._clock_float(value, name=name, nonnegative=True)


def _intensity_fields() -> Tuple[str, ...]:
    return tuple(ReferenceCandidateIntensity.__annotations__)


def _potential_evaluation_fields() -> Tuple[str, ...]:
    return tuple(TotalizedJumpPotentialCandidateEvaluation.__annotations__)


def _loop_runtime_sha256() -> str:
    return _semantic_digest(
        {
            "domain": "plugin-bridge-operational-thinning-loop-runtime-v1",
            "python_implementation": sys.implementation.name,
            "python_version": platform.python_version(),
            "platform_system": platform.system(),
            "platform_machine": platform.machine(),
            "numpy_version": np.__version__,
            "loop_policy": PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_POLICY,
            "maximum_proposals": OPERATIONAL_THINNING_LOOP_MAX_PROPOSALS,
            "stop_reference_zero": _STOP_REFERENCE_ZERO,
            "stop_right_endpoint": _STOP_RIGHT_ENDPOINT,
            "stop_reasons": _STOP_REASONS,
            "terminal_precedence": (
                "structural-zero-or-zero-duration-before-proposal-cap"
            ),
            "binary64_probe": _require_binary64_environment(),
        }
    )


def _certificate_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    return {
        name: value for name, value in values.items() if name != "certificate_sha256"
    }


@dataclass(frozen=True, eq=False, init=False)
class OperationalThinningLoopCertificate:
    """Transitive certificate for bounded checkpoint-nineteen repetition."""

    schema_version: str
    certificate_scope: str
    loop_policy: str
    loop_role_sha256: str
    process_parameter_sha256: str
    thinning_certificate_sha256: str
    thinning_role_sha256: str
    thinning_runtime_sha256: str
    rate_certificate_sha256: str
    rate_runtime_sha256: str
    target_policy: str
    rate_policy: str
    loop_runtime_sha256: str
    maximum_proposals: int
    base_context_dimension: int
    residual_context_dimension: int
    bounded_proposal_transcript_certified: bool
    represented_clock_continuation_certified: bool
    rejection_parent_identity_reuse_certified: bool
    accepted_state_refresh_certified: bool
    sequential_philox_custody_certified: bool
    deterministic_stop_precedence_certified: bool
    successful_local_interval_completion_certified: bool
    successful_local_interval_coordination_certified: bool
    exact_real_time_poisson_or_ctmc_path: bool
    exact_categorical_or_gaussian_route_sampling_certified: bool
    continuous_destination_operational_route_evidence_certified: bool
    unconditional_local_completion_certified: bool
    unconditional_exact_frozen_jump_law_certified: bool
    exact_active_controlled_total_exit_computed: bool
    analytic_target_preserved: bool
    conditional_posterior_or_doob_target: bool
    rounded_detailed_balance_or_stationarity_certified: bool
    all_route_rate_totality_certified: bool
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
        raise TypeError("OperationalThinningLoopCertificate cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _CERTIFICATE_TOKEN:
            raise TypeError("operational thinning-loop certificates are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError(
                "operational thinning-loop certificate fields are incomplete"
            )
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])
        _validate_certificate(self)

    def parameter_key(self) -> Tuple[object, ...]:
        return (
            "plugin-bridge-operational-thinning-loop-certificate-v1",
            self.certificate_sha256,
        )

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("operational thinning-loop certificates are not pickle objects")


def _certificate_fields() -> Tuple[str, ...]:
    return tuple(OperationalThinningLoopCertificate.__annotations__)


def _validate_certificate(
    certificate: object,
) -> OperationalThinningLoopCertificate:
    if type(certificate) is not OperationalThinningLoopCertificate:
        raise TypeError(
            "certificate must be an exact OperationalThinningLoopCertificate"
        )
    expected_text = {
        "schema_version": PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_SCHEMA_VERSION,
        "certificate_scope": PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_SCOPE,
        "loop_policy": PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_POLICY,
        "target_policy": _rate.CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_TARGET_POLICY,
        "rate_policy": _rate.CONFIGURATION_TOTALIZED_JUMP_RATE_POLICY,
    }
    for name, expected in expected_text.items():
        if getattr(certificate, name) != expected:
            raise ValueError("operational thinning-loop certificate %s differs" % name)
    for name in (
        "loop_role_sha256",
        "process_parameter_sha256",
        "thinning_certificate_sha256",
        "thinning_role_sha256",
        "thinning_runtime_sha256",
        "rate_certificate_sha256",
        "rate_runtime_sha256",
        "loop_runtime_sha256",
        "certificate_sha256",
    ):
        _require_sha256(getattr(certificate, name), name="certificate.%s" % name)
    if (
        type(certificate.maximum_proposals) is not int
        or isinstance(certificate.maximum_proposals, bool)
        or certificate.maximum_proposals != OPERATIONAL_THINNING_LOOP_MAX_PROPOSALS
    ):
        raise ValueError("operational thinning-loop maximum proposals differs")
    for name in ("base_context_dimension", "residual_context_dimension"):
        value = getattr(certificate, name)
        if type(value) is not int or isinstance(value, bool) or value < 0:
            raise ValueError("operational thinning-loop %s is invalid" % name)
        if value > _potential._MAX_CONTEXT_DIMENSION:
            raise ValueError("operational thinning-loop %s exceeds its limit" % name)
    true_flags = (
        "bounded_proposal_transcript_certified",
        "represented_clock_continuation_certified",
        "rejection_parent_identity_reuse_certified",
        "accepted_state_refresh_certified",
        "sequential_philox_custody_certified",
        "deterministic_stop_precedence_certified",
        "successful_local_interval_completion_certified",
        "successful_local_interval_coordination_certified",
        "passed",
    )
    false_flags = (
        "exact_real_time_poisson_or_ctmc_path",
        "exact_categorical_or_gaussian_route_sampling_certified",
        "continuous_destination_operational_route_evidence_certified",
        "unconditional_local_completion_certified",
        "unconditional_exact_frozen_jump_law_certified",
        "exact_active_controlled_total_exit_computed",
        "analytic_target_preserved",
        "conditional_posterior_or_doob_target",
        "rounded_detailed_balance_or_stationarity_certified",
        "all_route_rate_totality_certified",
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
        raise ValueError("operational thinning-loop positive flags are inconsistent")
    if any(getattr(certificate, name) for name in false_flags):
        raise ValueError("operational thinning-loop negative flags are inconsistent")
    values = {name: getattr(certificate, name) for name in _certificate_fields()}
    if certificate.certificate_sha256 != _semantic_digest(_certificate_payload(values)):
        raise ValueError("operational thinning-loop certificate digest differs")
    return certificate


def _make_certificate(
    thinning_certificate: _thin.OperationalThinningCertificate,
    potential_certificate: _potential.TotalizedJumpPotentialCompositionCertificate,
    *,
    loop_role_sha256: str,
) -> OperationalThinningLoopCertificate:
    values: Dict[str, object] = {
        "schema_version": PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_SCHEMA_VERSION,
        "certificate_scope": PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_SCOPE,
        "loop_policy": PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_POLICY,
        "loop_role_sha256": loop_role_sha256,
        "process_parameter_sha256": thinning_certificate.process_parameter_sha256,
        "thinning_certificate_sha256": thinning_certificate.certificate_sha256,
        "thinning_role_sha256": thinning_certificate.thinning_role_sha256,
        "thinning_runtime_sha256": thinning_certificate.thinning_runtime_sha256,
        "rate_certificate_sha256": thinning_certificate.rate_certificate_sha256,
        "rate_runtime_sha256": thinning_certificate.rate_runtime_sha256,
        "target_policy": _rate.CONFIGURATION_TOTALIZED_JUMP_POTENTIAL_TARGET_POLICY,
        "rate_policy": _rate.CONFIGURATION_TOTALIZED_JUMP_RATE_POLICY,
        "loop_runtime_sha256": _loop_runtime_sha256(),
        "maximum_proposals": OPERATIONAL_THINNING_LOOP_MAX_PROPOSALS,
        "base_context_dimension": potential_certificate.base_context_dimension,
        "residual_context_dimension": (
            potential_certificate.residual_context_dimension
        ),
        "bounded_proposal_transcript_certified": True,
        "represented_clock_continuation_certified": True,
        "rejection_parent_identity_reuse_certified": True,
        "accepted_state_refresh_certified": True,
        "sequential_philox_custody_certified": True,
        "deterministic_stop_precedence_certified": True,
        "successful_local_interval_completion_certified": True,
        "successful_local_interval_coordination_certified": True,
        "exact_real_time_poisson_or_ctmc_path": False,
        "exact_categorical_or_gaussian_route_sampling_certified": False,
        "continuous_destination_operational_route_evidence_certified": False,
        "unconditional_local_completion_certified": False,
        "unconditional_exact_frozen_jump_law_certified": False,
        "exact_active_controlled_total_exit_computed": False,
        "analytic_target_preserved": False,
        "conditional_posterior_or_doob_target": False,
        "rounded_detailed_balance_or_stationarity_certified": False,
        "all_route_rate_totality_certified": False,
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
    values["certificate_sha256"] = _semantic_digest(_certificate_payload(values))
    return OperationalThinningLoopCertificate(
        **values,
        _construction_token=_CERTIFICATE_TOKEN,
    )


def _iteration_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    omitted = {
        "certificate",
        "pre_intensity",
        "pre_envelope",
        "waiting_draw",
        "route_draw",
        "potential_evaluation",
        "rate_evaluation",
        "decision",
        "post_intensity",
        "post_envelope",
        "iteration_sha256",
    }
    return {name: value for name, value in values.items() if name not in omitted}


@dataclass(frozen=True, eq=False, init=False)
class OperationalProposalIteration:
    """One completed candidate proposal and its authenticated transition."""

    certificate: OperationalThinningLoopCertificate
    certificate_sha256: str
    proposal_index: int
    pre_intensity: ReferenceCandidateIntensity
    pre_intensity_sha256: str
    pre_envelope: TotalizedJumpRateEnvelope
    pre_envelope_sha256: str
    waiting_draw: OperationalWaitingTimeDraw
    waiting_draw_sha256: str
    route_draw: OperationalReferenceRouteDraw
    route_draw_sha256: str
    potential_evaluation: TotalizedJumpPotentialCandidateEvaluation
    potential_evaluation_sha256: str
    rate_evaluation: TotalizedJumpRateCandidateEvaluation
    rate_evaluation_sha256: str
    decision: OperationalAcceptanceDecision
    decision_sha256: str
    post_intensity: ReferenceCandidateIntensity
    post_intensity_sha256: str
    post_envelope: TotalizedJumpRateEnvelope
    post_envelope_sha256: str
    clock_start: float
    proposal_time: float
    frozen_reverse_time: float
    frozen_direct_time: float
    source_state_sha256: str
    result_state_sha256: str
    base_context_sha256: str
    residual_context_sha256: str
    accepted: bool
    rejection_parents_reused: bool
    accepted_parents_refreshed: bool
    rng_state_before_sha256: str
    rng_state_after_sha256: str
    iteration_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("OperationalProposalIteration cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _ITERATION_TOKEN:
            raise TypeError("operational proposal iterations are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("operational proposal iteration fields are incomplete")
        certificate = _validate_certificate(values["certificate"])
        if values["certificate_sha256"] != certificate.certificate_sha256:
            raise ValueError("proposal iteration certificate digest differs")
        _exact_nonnegative_integer(values["proposal_index"], name="proposal_index")
        if values["proposal_index"] >= OPERATIONAL_THINNING_LOOP_MAX_PROPOSALS:
            raise ValueError("proposal iteration index exceeds the loop maximum")
        exact_types = (
            ("pre_intensity", ReferenceCandidateIntensity),
            ("pre_envelope", TotalizedJumpRateEnvelope),
            ("waiting_draw", OperationalWaitingTimeDraw),
            ("route_draw", OperationalReferenceRouteDraw),
            (
                "potential_evaluation",
                TotalizedJumpPotentialCandidateEvaluation,
            ),
            ("rate_evaluation", TotalizedJumpRateCandidateEvaluation),
            ("decision", OperationalAcceptanceDecision),
            ("post_intensity", ReferenceCandidateIntensity),
            ("post_envelope", TotalizedJumpRateEnvelope),
        )
        for name, expected in exact_types:
            if type(values[name]) is not expected:
                raise TypeError("proposal iteration %s has the wrong exact type" % name)
        for name in (
            "certificate_sha256",
            "pre_intensity_sha256",
            "pre_envelope_sha256",
            "waiting_draw_sha256",
            "route_draw_sha256",
            "potential_evaluation_sha256",
            "rate_evaluation_sha256",
            "decision_sha256",
            "post_intensity_sha256",
            "post_envelope_sha256",
            "source_state_sha256",
            "result_state_sha256",
            "base_context_sha256",
            "residual_context_sha256",
            "rng_state_before_sha256",
            "rng_state_after_sha256",
            "iteration_sha256",
        ):
            _require_sha256(values[name], name="iteration.%s" % name)
        expected_digests = {
            "pre_intensity_sha256": _intensity_sha256(values["pre_intensity"]),
            "pre_envelope_sha256": values["pre_envelope"].envelope_sha256,
            "waiting_draw_sha256": values["waiting_draw"].waiting_draw_sha256,
            "route_draw_sha256": values["route_draw"].route_draw_sha256,
            "potential_evaluation_sha256": (
                values["potential_evaluation"].evaluation_sha256
            ),
            "rate_evaluation_sha256": values["rate_evaluation"].evaluation_sha256,
            "decision_sha256": values["decision"].decision_sha256,
            "post_intensity_sha256": _intensity_sha256(values["post_intensity"]),
            "post_envelope_sha256": values["post_envelope"].envelope_sha256,
        }
        for name, expected in expected_digests.items():
            if values[name] != expected:
                raise ValueError("proposal iteration %s differs" % name)
        waiting = values["waiting_draw"]
        route = values["route_draw"]
        potential = values["potential_evaluation"]
        rate_evaluation = values["rate_evaluation"]
        decision = values["decision"]
        if not waiting.candidate_due:
            raise ValueError("a completed proposal requires an admitted waiting draw")
        if route.waiting_draw_sha256 != waiting.waiting_draw_sha256:
            raise ValueError("proposal route and waiting draw differ")
        if decision.route_draw is not route:
            raise ValueError("proposal decision does not own the exact route record")
        if potential.candidate_sha256 != route.candidate_sha256:
            raise ValueError("proposal potential and route candidate differ")
        if rate_evaluation.candidate_sha256 != route.candidate_sha256:
            raise ValueError("proposal rate and route candidate differ")
        if decision.rate_evaluation_sha256 != rate_evaluation.evaluation_sha256:
            raise ValueError("proposal decision and rate evaluation differ")
        for name in (
            "clock_start",
            "proposal_time",
            "frozen_reverse_time",
            "frozen_direct_time",
        ):
            _clock_float(values[name], name="iteration.%s" % name)
        if not _same_float(values["clock_start"], waiting.clock_start):
            raise ValueError("proposal iteration clock start differs")
        if not _same_float(values["proposal_time"], waiting.proposal_time):
            raise ValueError("proposal iteration proposal time differs")
        if values["proposal_time"] <= values["clock_start"]:
            raise ValueError("proposal iteration did not advance its clock")
        pre_intensity = values["pre_intensity"]
        post_intensity = values["post_intensity"]
        for name, expected in (
            ("frozen_reverse_time", pre_intensity.reverse_time),
            ("frozen_direct_time", pre_intensity.direct_time),
        ):
            if not _same_float(values[name], expected):
                raise ValueError("proposal iteration %s differs" % name)
            if not _same_float(getattr(post_intensity, name[7:]), expected):
                raise ValueError("proposal post-intensity generative time differs")
        source_sha = _configuration_sha256(pre_intensity.source_configuration)
        result_sha = _configuration_sha256(decision.result_configuration)
        if values["source_state_sha256"] != source_sha:
            raise ValueError("proposal iteration source-state digest differs")
        if values["result_state_sha256"] != result_sha:
            raise ValueError("proposal iteration result-state digest differs")
        if _configuration_sha256(post_intensity.source_configuration) != result_sha:
            raise ValueError("proposal post-intensity source differs from the result")
        if values["base_context_sha256"] != potential.base_context_sha256:
            raise ValueError("proposal base-context digest differs")
        if values["residual_context_sha256"] != potential.residual_context_sha256:
            raise ValueError("proposal residual-context digest differs")
        for name in (
            "accepted",
            "rejection_parents_reused",
            "accepted_parents_refreshed",
        ):
            if type(values[name]) is not bool:
                raise TypeError("proposal iteration %s must be boolean" % name)
        if values["accepted"] is not decision.accepted:
            raise ValueError("proposal iteration acceptance flag differs")
        if values["accepted"]:
            if values["rejection_parents_reused"]:
                raise ValueError("accepted proposal cannot claim rejection reuse")
            if not values["accepted_parents_refreshed"]:
                raise ValueError("accepted proposal did not certify fresh parents")
            if post_intensity is pre_intensity:
                raise ValueError("accepted proposal reused its intensity object")
            if values["post_envelope"] is values["pre_envelope"]:
                raise ValueError("accepted proposal reused its envelope object")
        else:
            if not values["rejection_parents_reused"]:
                raise ValueError("rejected proposal did not certify parent reuse")
            if values["accepted_parents_refreshed"]:
                raise ValueError("rejected proposal cannot claim parent refresh")
            if post_intensity is not pre_intensity:
                raise ValueError("rejected proposal replaced its intensity object")
            if values["post_envelope"] is not values["pre_envelope"]:
                raise ValueError("rejected proposal replaced its envelope object")
        if values["rng_state_before_sha256"] != waiting.rng_state_before_sha256:
            raise ValueError("proposal iteration RNG start differs")
        if route.rng_state_before_sha256 != waiting.rng_state_after_sha256:
            raise ValueError("proposal route does not continue waiting RNG")
        if decision.rng_state_before_sha256 != route.rng_state_after_sha256:
            raise ValueError("proposal decision does not continue route RNG")
        if values["rng_state_after_sha256"] != decision.rng_state_after_sha256:
            raise ValueError("proposal iteration RNG end differs")
        expected_digest = _semantic_digest(_iteration_payload(values))
        if values["iteration_sha256"] != expected_digest:
            raise ValueError("proposal iteration digest differs")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("operational proposal iterations are not pickle objects")


def _iteration_fields() -> Tuple[str, ...]:
    return tuple(OperationalProposalIteration.__annotations__)


def _result_payload(values: Mapping[str, object]) -> Mapping[str, object]:
    omitted = {
        "certificate",
        "initial_intensity",
        "initial_envelope",
        "iterations",
        "terminal_waiting_draw",
        "final_configuration",
        "final_intensity",
        "final_envelope",
        "result_sha256",
    }
    payload = {name: value for name, value in values.items() if name not in omitted}
    payload["final_configuration"] = _configuration_semantic_payload(
        values["final_configuration"]  # type: ignore[arg-type]
    )
    return payload


@dataclass(frozen=True, eq=False, init=False)
class OperationalLocalThinningResult:
    """Sealed successful bounded local proposal transcript."""

    certificate: OperationalThinningLoopCertificate
    certificate_sha256: str
    initial_intensity: ReferenceCandidateIntensity
    initial_intensity_sha256: str
    initial_envelope: TotalizedJumpRateEnvelope
    initial_envelope_sha256: str
    base_context: Tuple[float, ...]
    base_context_sha256: str
    residual_context: Tuple[float, ...]
    residual_context_sha256: str
    frozen_reverse_time: float
    frozen_direct_time: float
    clock_start: float
    right_endpoint: float
    proposal_budget: int
    iterations: Tuple[OperationalProposalIteration, ...]
    iteration_sha256s: Tuple[str, ...]
    terminal_waiting_draw: OperationalWaitingTimeDraw
    terminal_waiting_draw_sha256: str
    stop_reason: str
    proposal_count: int
    accepted_count: int
    rejected_count: int
    final_clock_cursor: float
    final_configuration: TransformedConfiguration
    final_state_sha256: str
    final_intensity: ReferenceCandidateIntensity
    final_intensity_sha256: str
    final_envelope: TotalizedJumpRateEnvelope
    final_envelope_sha256: str
    successful_local_interval_completion: bool
    reference_intensity_zero: bool
    right_endpoint_exhausted: bool
    rng_bit_generator: str
    rng_state_before_sha256: str
    rng_state_after_sha256: str
    result_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("OperationalLocalThinningResult cannot be subclassed")

    def __init__(self, *, _construction_token: object, **values: object) -> None:
        if _construction_token is not _RESULT_TOKEN:
            raise TypeError("operational local thinning results are module-created")
        if set(values) != set(self.__annotations__):
            raise TypeError("operational local thinning result fields are incomplete")
        certificate = _validate_certificate(values["certificate"])
        if values["certificate_sha256"] != certificate.certificate_sha256:
            raise ValueError("local thinning result certificate digest differs")
        for name, expected in (
            ("initial_intensity", ReferenceCandidateIntensity),
            ("initial_envelope", TotalizedJumpRateEnvelope),
            ("final_intensity", ReferenceCandidateIntensity),
            ("final_envelope", TotalizedJumpRateEnvelope),
        ):
            if type(values[name]) is not expected:
                raise TypeError("local thinning result %s has wrong exact type" % name)
        if type(values["final_configuration"]) is not tuple:
            raise TypeError("local thinning final configuration must be an exact tuple")
        for name in (
            "certificate_sha256",
            "initial_intensity_sha256",
            "initial_envelope_sha256",
            "base_context_sha256",
            "residual_context_sha256",
            "final_state_sha256",
            "final_intensity_sha256",
            "final_envelope_sha256",
            "terminal_waiting_draw_sha256",
            "rng_state_before_sha256",
            "rng_state_after_sha256",
            "result_sha256",
        ):
            _require_sha256(values[name], name="result.%s" % name)
        if type(values["base_context"]) is not tuple:
            raise TypeError("local thinning base context must be an exact tuple")
        if type(values["residual_context"]) is not tuple:
            raise TypeError("local thinning residual context must be an exact tuple")
        if len(values["base_context"]) != certificate.base_context_dimension:
            raise ValueError("local thinning base-context dimension differs")
        if len(values["residual_context"]) != (certificate.residual_context_dimension):
            raise ValueError("local thinning residual-context dimension differs")
        if values["base_context_sha256"] != _context_sha256(
            values["base_context"], role="base"
        ):
            raise ValueError("local thinning base-context digest differs")
        if values["residual_context_sha256"] != _context_sha256(
            values["residual_context"], role="residual"
        ):
            raise ValueError("local thinning residual-context digest differs")
        for name in (
            "frozen_reverse_time",
            "frozen_direct_time",
            "clock_start",
            "right_endpoint",
            "final_clock_cursor",
        ):
            _clock_float(values[name], name="result.%s" % name)
        if values["right_endpoint"] < values["clock_start"]:
            raise ValueError("local thinning right endpoint precedes clock start")
        initial_intensity = values["initial_intensity"]
        if not _same_float(
            values["frozen_reverse_time"],
            initial_intensity.reverse_time,
        ):
            raise ValueError("local thinning frozen reverse time differs")
        if not _same_float(
            values["frozen_direct_time"],
            initial_intensity.direct_time,
        ):
            raise ValueError("local thinning frozen direct time differs")
        if not values["clock_start"] <= values["final_clock_cursor"] < (
            values["right_endpoint"]
        ) and not (
            _same_float(values["clock_start"], values["right_endpoint"])
            and _same_float(values["final_clock_cursor"], values["clock_start"])
        ):
            raise ValueError(
                "local thinning final clock cursor is outside its interval"
            )
        budget = _proposal_budget(values["proposal_budget"])
        for name in ("proposal_count", "accepted_count", "rejected_count"):
            _exact_nonnegative_integer(values[name], name="result.%s" % name)
        if type(values["iterations"]) is not tuple:
            raise TypeError("local thinning iterations must be an exact tuple")
        if type(values["iteration_sha256s"]) is not tuple:
            raise TypeError("local thinning iteration digests must be an exact tuple")
        iterations = values["iterations"]
        if len(iterations) != values["proposal_count"] or len(iterations) > budget:
            raise ValueError("local thinning proposal count differs")
        if values["iteration_sha256s"] != tuple(
            iteration.iteration_sha256 for iteration in iterations
        ):
            raise ValueError("local thinning iteration digest sequence differs")
        accepted_count = 0
        current_intensity = values["initial_intensity"]
        current_envelope = values["initial_envelope"]
        current_cursor = values["clock_start"]
        current_rng = values["rng_state_before_sha256"]
        seen_intensities = [current_intensity]
        seen_envelopes = [current_envelope]
        for index, iteration in enumerate(iterations):
            if type(iteration) is not OperationalProposalIteration:
                raise TypeError("local thinning iteration has the wrong exact type")
            OperationalProposalIteration(
                **_snapshot_fields(iteration, _iteration_fields()),
                _construction_token=_ITERATION_TOKEN,
            )
            if iteration.certificate is not certificate:
                raise ValueError("local thinning iteration has another certificate")
            if iteration.proposal_index != index:
                raise ValueError("local thinning proposal indices are not contiguous")
            if iteration.pre_intensity is not current_intensity:
                raise ValueError("local thinning intensity identity chain differs")
            if iteration.pre_envelope is not current_envelope:
                raise ValueError("local thinning envelope identity chain differs")
            if not _same_float(iteration.clock_start, current_cursor):
                raise ValueError("local thinning clock chain differs")
            if not _same_float(
                iteration.waiting_draw.right_endpoint,
                values["right_endpoint"],
            ):
                raise ValueError("local thinning iteration right endpoint differs")
            if iteration.rng_state_before_sha256 != current_rng:
                raise ValueError("local thinning RNG chain differs")
            if iteration.accepted:
                if any(
                    iteration.post_intensity is previous
                    for previous in seen_intensities
                ):
                    raise ValueError(
                        "accepted proposal reused an earlier intensity object"
                    )
                if any(
                    iteration.post_envelope is previous for previous in seen_envelopes
                ):
                    raise ValueError(
                        "accepted proposal reused an earlier envelope object"
                    )
                seen_intensities.append(iteration.post_intensity)
                seen_envelopes.append(iteration.post_envelope)
            current_intensity = iteration.post_intensity
            current_envelope = iteration.post_envelope
            current_cursor = iteration.proposal_time
            current_rng = iteration.rng_state_after_sha256
            accepted_count += int(iteration.accepted)
        if values["accepted_count"] != accepted_count:
            raise ValueError("local thinning accepted count differs")
        if values["rejected_count"] != len(iterations) - accepted_count:
            raise ValueError("local thinning rejected count differs")
        if not _same_float(values["final_clock_cursor"], current_cursor):
            raise ValueError("local thinning final clock cursor differs")
        if values["final_intensity"] is not current_intensity:
            raise ValueError("local thinning final intensity identity differs")
        if values["final_envelope"] is not current_envelope:
            raise ValueError("local thinning final envelope identity differs")
        expected_parent_digests = {
            "initial_intensity_sha256": _intensity_sha256(values["initial_intensity"]),
            "initial_envelope_sha256": values["initial_envelope"].envelope_sha256,
            "final_intensity_sha256": _intensity_sha256(values["final_intensity"]),
            "final_envelope_sha256": values["final_envelope"].envelope_sha256,
        }
        for name, expected in expected_parent_digests.items():
            if values[name] != expected:
                raise ValueError("local thinning %s differs" % name)
        final_state_sha = _configuration_sha256(values["final_configuration"])
        if values["final_state_sha256"] != final_state_sha:
            raise ValueError("local thinning final-state digest differs")
        if values["final_configuration"] != current_intensity.source_configuration:
            raise ValueError("local thinning final configuration differs")
        terminal = values["terminal_waiting_draw"]
        terminal_sha = values["terminal_waiting_draw_sha256"]
        if type(terminal) is not OperationalWaitingTimeDraw:
            raise TypeError("terminal waiting draw has the wrong exact type")
        if terminal_sha != terminal.waiting_draw_sha256:
            raise ValueError("terminal waiting-draw digest differs")
        if terminal.candidate_due:
            raise ValueError("terminal waiting draw admitted a proposal")
        if terminal.intensity_sha256 != _intensity_sha256(current_intensity):
            raise ValueError("terminal waiting intensity differs")
        if terminal.envelope_sha256 != current_envelope.envelope_sha256:
            raise ValueError("terminal waiting envelope differs")
        if not _same_float(terminal.clock_start, current_cursor):
            raise ValueError("terminal waiting clock start differs")
        if not _same_float(terminal.right_endpoint, values["right_endpoint"]):
            raise ValueError("terminal waiting right endpoint differs")
        if terminal.rng_state_before_sha256 != current_rng:
            raise ValueError("terminal waiting RNG start differs")
        current_rng = terminal.rng_state_after_sha256
        if values["rng_bit_generator"] != "numpy.random.Philox":
            raise ValueError("local thinning RNG type differs")
        if values["rng_state_after_sha256"] != current_rng:
            raise ValueError("local thinning RNG end differs")
        if values["stop_reason"] not in _STOP_REASONS:
            raise ValueError("local thinning stop reason is unknown")
        stop_flags = {
            _STOP_REFERENCE_ZERO: "reference_intensity_zero",
            _STOP_RIGHT_ENDPOINT: "right_endpoint_exhausted",
        }
        if type(values["successful_local_interval_completion"]) is not bool:
            raise TypeError("successful local interval completion must be boolean")
        if not values["successful_local_interval_completion"]:
            raise ValueError("returned local thinning result is not complete")
        for reason, flag_name in stop_flags.items():
            expected = values["stop_reason"] == reason
            if type(values[flag_name]) is not bool or values[flag_name] is not expected:
                raise ValueError("local thinning stop flag %s differs" % flag_name)
        if len(iterations) > budget:
            raise ValueError("terminal result exceeds its proposal budget")
        expected_reason = (
            _STOP_REFERENCE_ZERO
            if terminal.reference_intensity_zero
            else _STOP_RIGHT_ENDPOINT
        )
        if values["stop_reason"] != expected_reason:
            raise ValueError("terminal waiting stop precedence differs")
        if len(iterations) == budget and not (
            terminal.raw_words_consumed == 0
            and (terminal.reference_intensity_zero or terminal.zero_duration)
        ):
            raise ValueError(
                "a result at the proposal cap requires a deterministic terminal hold"
            )
        expected_digest = _semantic_digest(_result_payload(values))
        if values["result_sha256"] != expected_digest:
            raise ValueError("local thinning result digest differs")
        for name in self.__annotations__:
            object.__setattr__(self, name, values[name])

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("operational local thinning results are not pickle objects")


def _result_fields() -> Tuple[str, ...]:
    return tuple(OperationalLocalThinningResult.__annotations__)


class BoundedOperationalThinningLoop:
    """Immutable owner of one bounded frozen-time local proposal loop."""

    __slots__ = (
        "_thinning_owner",
        "_certified_thinning_owner",
        "_rate_owner",
        "_reference_composer",
        "_potential_composer",
        "_loop_role_sha256",
        "_certificate",
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("BoundedOperationalThinningLoop cannot be subclassed")

    def __init__(
        self,
        thinning_owner: OperationalJumpThinning,
        loop_role_sha256: str,
        certificate: OperationalThinningLoopCertificate,
        *,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _OWNER_TOKEN:
            raise TypeError("bounded thinning-loop owners require certification")
        if type(thinning_owner) is not OperationalJumpThinning:
            raise TypeError("thinning_owner has the wrong exact type")
        role = _require_sha256(loop_role_sha256, name="loop_role_sha256")
        checked_certificate = _validate_certificate(certificate)
        if checked_certificate.loop_role_sha256 != role:
            raise ValueError("bounded thinning-loop role differs from certificate")
        rate_owner = thinning_owner.rate_owner
        reference_composer = thinning_owner.reference_composer
        potential_composer = rate_owner.potential_composer
        object.__setattr__(self, "_thinning_owner", thinning_owner)
        object.__setattr__(self, "_certified_thinning_owner", thinning_owner)
        object.__setattr__(self, "_rate_owner", rate_owner)
        object.__setattr__(self, "_reference_composer", reference_composer)
        object.__setattr__(self, "_potential_composer", potential_composer)
        object.__setattr__(self, "_loop_role_sha256", role)
        object.__setattr__(self, "_certificate", checked_certificate)

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("BoundedOperationalThinningLoop is immutable")

    def __delattr__(self, name: str) -> None:
        del name
        raise AttributeError("BoundedOperationalThinningLoop is immutable")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("bounded thinning-loop owners are not pickle objects")

    @property
    def certificate(self) -> OperationalThinningLoopCertificate:
        return self._certificate

    @property
    def thinning_owner(self) -> OperationalJumpThinning:
        return self._thinning_owner

    @property
    def rate_owner(self) -> _rate.TotalizedConfigurationJumpRateEnvelope:
        return self._rate_owner

    @property
    def reference_composer(self):  # type: ignore[no-untyped-def]
        return self._reference_composer

    @property
    def potential_composer(self):  # type: ignore[no-untyped-def]
        return self._potential_composer

    def _require_live_binding(self) -> OperationalThinningLoopCertificate:
        _require_binary64_environment()
        if type(self._thinning_owner) is not OperationalJumpThinning:
            raise TypeError("thinning owner has the wrong exact type")
        if self._thinning_owner is not self._certified_thinning_owner:
            raise ValueError("bounded loop thinning-owner binding changed")
        thinning_certificate = self._thinning_owner._require_live_binding()
        if self.certificate.loop_runtime_sha256 != _loop_runtime_sha256():
            raise ValueError("live thinning-loop runtime differs from certificate")
        expected = _make_certificate(
            thinning_certificate,
            self.potential_composer.certificate,
            loop_role_sha256=self._loop_role_sha256,
        )
        for name in _certificate_fields():
            if not _field_matches(
                name,
                getattr(self.certificate, name),
                getattr(expected, name),
            ):
                raise ValueError(
                    "operational thinning-loop certificate field %s differs" % name
                )
        if self.rate_owner is not self._thinning_owner.rate_owner:
            raise ValueError("bounded loop rate-owner binding changed")
        if self.reference_composer is not self.rate_owner.reference_composer:
            raise ValueError("bounded loop reference-composer binding changed")
        if self.reference_composer is not self._thinning_owner.reference_composer:
            raise ValueError("bounded loop thinning/reference binding changed")
        if self.potential_composer is not self.rate_owner.potential_composer:
            raise ValueError("bounded loop potential-composer binding changed")
        if (
            self.certificate.base_context_dimension
            != self.potential_composer.certificate.base_context_dimension
            or self.certificate.residual_context_dimension
            != self.potential_composer.certificate.residual_context_dimension
        ):
            raise ValueError("bounded loop context dimensions changed")
        _require_binary64_environment()
        return self.certificate

    def _canonical_contexts(
        self,
        base_context: object,
        residual_context: object,
    ) -> Tuple[Tuple[float, ...], Tuple[float, ...]]:
        potential_certificate = self.potential_composer.certificate
        base = _validated_context(
            base_context,
            dimension=potential_certificate.base_context_dimension,
            name="base_context",
        )
        residual = _validated_context(
            residual_context,
            dimension=potential_certificate.residual_context_dimension,
            name="residual_context",
        )
        return base, residual

    def _validate_parents(
        self,
        intensity: ReferenceCandidateIntensity,
        envelope: TotalizedJumpRateEnvelope,
    ) -> Tuple[ReferenceCandidateIntensity, TotalizedJumpRateEnvelope]:
        checked_intensity = self.reference_composer.validate_candidate_intensity(
            intensity
        )
        checked_envelope = self.rate_owner.validate_envelope(
            envelope,
            checked_intensity,
        )
        return checked_intensity, checked_envelope

    def _make_iteration(
        self,
        *,
        proposal_index: int,
        pre_intensity: ReferenceCandidateIntensity,
        pre_envelope: TotalizedJumpRateEnvelope,
        waiting_draw: OperationalWaitingTimeDraw,
        route_draw: OperationalReferenceRouteDraw,
        potential_evaluation: TotalizedJumpPotentialCandidateEvaluation,
        rate_evaluation: TotalizedJumpRateCandidateEvaluation,
        decision: OperationalAcceptanceDecision,
        post_intensity: ReferenceCandidateIntensity,
        post_envelope: TotalizedJumpRateEnvelope,
    ) -> OperationalProposalIteration:
        accepted = decision.accepted
        values: Dict[str, object] = {
            "certificate": self.certificate,
            "certificate_sha256": self.certificate.certificate_sha256,
            "proposal_index": proposal_index,
            "pre_intensity": pre_intensity,
            "pre_intensity_sha256": _intensity_sha256(pre_intensity),
            "pre_envelope": pre_envelope,
            "pre_envelope_sha256": pre_envelope.envelope_sha256,
            "waiting_draw": waiting_draw,
            "waiting_draw_sha256": waiting_draw.waiting_draw_sha256,
            "route_draw": route_draw,
            "route_draw_sha256": route_draw.route_draw_sha256,
            "potential_evaluation": potential_evaluation,
            "potential_evaluation_sha256": potential_evaluation.evaluation_sha256,
            "rate_evaluation": rate_evaluation,
            "rate_evaluation_sha256": rate_evaluation.evaluation_sha256,
            "decision": decision,
            "decision_sha256": decision.decision_sha256,
            "post_intensity": post_intensity,
            "post_intensity_sha256": _intensity_sha256(post_intensity),
            "post_envelope": post_envelope,
            "post_envelope_sha256": post_envelope.envelope_sha256,
            "clock_start": waiting_draw.clock_start,
            "proposal_time": waiting_draw.proposal_time,
            "frozen_reverse_time": pre_intensity.reverse_time,
            "frozen_direct_time": pre_intensity.direct_time,
            "source_state_sha256": _configuration_sha256(
                pre_intensity.source_configuration
            ),
            "result_state_sha256": decision.result_state_sha256,
            "base_context_sha256": potential_evaluation.base_context_sha256,
            "residual_context_sha256": potential_evaluation.residual_context_sha256,
            "accepted": accepted,
            "rejection_parents_reused": not accepted,
            "accepted_parents_refreshed": accepted,
            "rng_state_before_sha256": waiting_draw.rng_state_before_sha256,
            "rng_state_after_sha256": decision.rng_state_after_sha256,
            "iteration_sha256": "0" * 64,
        }
        values["iteration_sha256"] = _semantic_digest(_iteration_payload(values))
        return OperationalProposalIteration(
            **values,
            _construction_token=_ITERATION_TOKEN,
        )

    def validate_iteration(
        self,
        iteration: OperationalProposalIteration,
        pre_intensity: ReferenceCandidateIntensity,
        pre_envelope: TotalizedJumpRateEnvelope,
        *,
        base_context: object,
        residual_context: object,
    ) -> OperationalProposalIteration:
        """Replay one completed iteration without consuming randomness."""

        if type(iteration) is not OperationalProposalIteration:
            raise TypeError("iteration has the wrong exact type")
        OperationalProposalIteration(
            **_snapshot_fields(iteration, _iteration_fields()),
            _construction_token=_ITERATION_TOKEN,
        )
        if iteration.certificate is not self.certificate:
            raise ValueError("iteration belongs to a different bounded loop")
        if iteration.pre_intensity is not pre_intensity:
            raise ValueError("iteration belongs to a different intensity object")
        if iteration.pre_envelope is not pre_envelope:
            raise ValueError("iteration belongs to a different envelope object")
        base, residual = self._canonical_contexts(base_context, residual_context)
        checked_intensity, checked_envelope = self._validate_parents(
            pre_intensity,
            pre_envelope,
        )
        waiting = self._thinning_owner.validate_waiting_time(
            iteration.waiting_draw,
            checked_intensity,
            checked_envelope,
        )
        route = self._thinning_owner.validate_reference_route(
            iteration.route_draw,
            waiting,
            checked_intensity,
            checked_envelope,
        )
        potential = self.potential_composer.validate_evaluation(
            iteration.potential_evaluation,
            route.candidate,
        )
        if potential.base_context != base or potential.residual_context != residual:
            raise ValueError("iteration contexts differ from the loop contexts")
        rate_evaluation = self.rate_owner.validate_candidate_evaluation(
            iteration.rate_evaluation,
            route.candidate,
            potential,
            envelope=checked_envelope,
        )
        decision = self._thinning_owner.validate_acceptance(
            iteration.decision,
            route,
            waiting,
            checked_intensity,
            checked_envelope,
            potential,
            rate_evaluation,
        )
        if decision.accepted:
            if iteration.post_intensity is checked_intensity:
                raise ValueError("accepted iteration reused its intensity")
            post_intensity = self.reference_composer.validate_candidate_intensity(
                iteration.post_intensity
            )
            if post_intensity.source_configuration != decision.result_configuration:
                raise ValueError("accepted iteration refresh has another source")
            if not _same_float(
                post_intensity.reverse_time,
                checked_intensity.reverse_time,
            ) or not _same_float(
                post_intensity.direct_time,
                checked_intensity.direct_time,
            ):
                raise ValueError("accepted iteration refresh changed generative time")
            self.rate_owner.validate_envelope(
                iteration.post_envelope,
                post_intensity,
            )
        else:
            if iteration.post_intensity is not checked_intensity:
                raise ValueError("rejected iteration replaced its intensity")
            if iteration.post_envelope is not checked_envelope:
                raise ValueError("rejected iteration replaced its envelope")
        self._require_live_binding()
        return iteration

    def run(
        self,
        initial_intensity: ReferenceCandidateIntensity,
        initial_envelope: TotalizedJumpRateEnvelope,
        *,
        clock_start: object,
        right_endpoint: object,
        proposal_budget: object,
        base_context: object,
        residual_context: object,
        rng: np.random.Generator,
    ) -> OperationalLocalThinningResult:
        """Run one bounded successful-return local proposal transcript."""

        self._require_live_binding()
        checked_rng = _require_philox_rng(rng)
        preflight_rng_sha = _rng_state_sha256(checked_rng.bit_generator.state)
        budget = _proposal_budget(proposal_budget)
        start = _clock_float(clock_start, name="clock_start")
        end = _clock_float(right_endpoint, name="right_endpoint")
        if end < start:
            raise ValueError("right_endpoint must not precede clock_start")
        current_intensity, current_envelope = self._validate_parents(
            initial_intensity,
            initial_envelope,
        )
        base, residual = self._canonical_contexts(base_context, residual_context)
        if _rng_state_sha256(checked_rng.bit_generator.state) != preflight_rng_sha:
            raise ValueError("Philox state changed during loop preflight")
        initial_intensity_snapshot = _snapshot_fields(
            current_intensity,
            _intensity_fields(),
        )
        initial_envelope_snapshot = _snapshot_fields(
            current_envelope,
            _envelope_fields(),
        )
        rng_before = preflight_rng_sha
        cursor = start
        iterations = []
        terminal_waiting = None
        stop_reason = None

        while True:
            expected_rng = _rng_state_sha256(checked_rng.bit_generator.state)
            deterministic_terminal = current_intensity.is_zero or _same_float(
                cursor,
                end,
            )
            if not deterministic_terminal and len(iterations) == budget:
                raise PluginBridgeOperationalThinningLoopError(
                    "active local thinning reached its proposal budget before "
                    "certified interval exhaustion"
                )
            waiting = self._thinning_owner.draw_waiting_time(
                current_intensity,
                current_envelope,
                clock_start=cursor,
                right_endpoint=end,
                rng=checked_rng,
            )
            if waiting.rng_state_before_sha256 != expected_rng:
                raise ValueError("waiting draw did not continue the loop stream")
            if not waiting.candidate_due:
                terminal_waiting = waiting
                stop_reason = (
                    _STOP_REFERENCE_ZERO
                    if waiting.reference_intensity_zero
                    else _STOP_RIGHT_ENDPOINT
                )
                break
            if deterministic_terminal:
                raise RuntimeError("deterministic terminal hold admitted a proposal")

            route = self._thinning_owner.draw_reference_route(
                waiting,
                current_intensity,
                current_envelope,
                rng=checked_rng,
            )
            if _rng_state_sha256(checked_rng.bit_generator.state) != (
                route.rng_state_after_sha256
            ):
                raise ValueError("Philox state changed after the route draw")
            model_rng_sha = route.rng_state_after_sha256
            potential = self.potential_composer.evaluate(
                route.candidate,
                base_context=base,
                residual_context=residual,
            )
            if _rng_state_sha256(checked_rng.bit_generator.state) != model_rng_sha:
                raise ValueError("potential evaluation changed the Philox state")
            rate_evaluation = self.rate_owner.evaluate_candidate(
                route.candidate,
                potential,
                envelope=current_envelope,
            )
            if _rng_state_sha256(checked_rng.bit_generator.state) != model_rng_sha:
                raise ValueError("rate evaluation changed the Philox state")
            decision = self._thinning_owner.decide_acceptance(
                route,
                waiting,
                current_intensity,
                current_envelope,
                potential,
                rate_evaluation,
                rng=checked_rng,
            )
            if _rng_state_sha256(checked_rng.bit_generator.state) != (
                decision.rng_state_after_sha256
            ):
                raise ValueError("Philox state changed after acceptance")

            if decision.accepted:
                refresh_rng_sha = decision.rng_state_after_sha256
                next_intensity = self.reference_composer.preflight_candidate_intensity(
                    decision.result_configuration,
                    reverse_time=current_intensity.reverse_time,
                )
                if (
                    _rng_state_sha256(checked_rng.bit_generator.state)
                    != refresh_rng_sha
                ):
                    raise ValueError("accepted-state intensity refresh changed Philox")
                next_envelope = self.rate_owner.preflight_envelope(next_intensity)
                if (
                    _rng_state_sha256(checked_rng.bit_generator.state)
                    != refresh_rng_sha
                ):
                    raise ValueError("accepted-state envelope refresh changed Philox")
            else:
                next_intensity = current_intensity
                next_envelope = current_envelope

            iteration = self._make_iteration(
                proposal_index=len(iterations),
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
            self.validate_iteration(
                iteration,
                current_intensity,
                current_envelope,
                base_context=base,
                residual_context=residual,
            )
            if _rng_state_sha256(checked_rng.bit_generator.state) != (
                decision.rng_state_after_sha256
            ):
                raise ValueError("iteration validation changed the Philox state")
            iterations.append(iteration)
            cursor = waiting.proposal_time
            current_intensity = next_intensity
            current_envelope = next_envelope

        if terminal_waiting is None or stop_reason is None:
            raise RuntimeError("successful loop return lacks terminal exhaustion")
        rng_after = _rng_state_sha256(checked_rng.bit_generator.state)
        if rng_after != terminal_waiting.rng_state_after_sha256:
            raise ValueError("terminal waiting draw and loop RNG state differ")

        _record_unchanged(
            initial_intensity,
            initial_intensity_snapshot,
            context="initial reference intensity",
        )
        _record_unchanged(
            initial_envelope,
            initial_envelope_snapshot,
            context="initial rate envelope",
        )
        self._require_live_binding()
        accepted_count = sum(int(iteration.accepted) for iteration in iterations)
        values: Dict[str, object] = {
            "certificate": self.certificate,
            "certificate_sha256": self.certificate.certificate_sha256,
            "initial_intensity": initial_intensity,
            "initial_intensity_sha256": _intensity_sha256(initial_intensity),
            "initial_envelope": initial_envelope,
            "initial_envelope_sha256": initial_envelope.envelope_sha256,
            "base_context": base,
            "base_context_sha256": _context_sha256(base, role="base"),
            "residual_context": residual,
            "residual_context_sha256": _context_sha256(residual, role="residual"),
            "frozen_reverse_time": initial_intensity.reverse_time,
            "frozen_direct_time": initial_intensity.direct_time,
            "clock_start": start,
            "right_endpoint": end,
            "proposal_budget": budget,
            "iterations": tuple(iterations),
            "iteration_sha256s": tuple(
                iteration.iteration_sha256 for iteration in iterations
            ),
            "terminal_waiting_draw": terminal_waiting,
            "terminal_waiting_draw_sha256": terminal_waiting.waiting_draw_sha256,
            "stop_reason": stop_reason,
            "proposal_count": len(iterations),
            "accepted_count": accepted_count,
            "rejected_count": len(iterations) - accepted_count,
            "final_clock_cursor": cursor,
            "final_configuration": current_intensity.source_configuration,
            "final_state_sha256": _configuration_sha256(
                current_intensity.source_configuration
            ),
            "final_intensity": current_intensity,
            "final_intensity_sha256": _intensity_sha256(current_intensity),
            "final_envelope": current_envelope,
            "final_envelope_sha256": current_envelope.envelope_sha256,
            "successful_local_interval_completion": True,
            "reference_intensity_zero": stop_reason == _STOP_REFERENCE_ZERO,
            "right_endpoint_exhausted": stop_reason == _STOP_RIGHT_ENDPOINT,
            "rng_bit_generator": "numpy.random.Philox",
            "rng_state_before_sha256": rng_before,
            "rng_state_after_sha256": rng_after,
            "result_sha256": "0" * 64,
        }
        values["result_sha256"] = _semantic_digest(_result_payload(values))
        result = OperationalLocalThinningResult(
            **values,
            _construction_token=_RESULT_TOKEN,
        )
        self.validate_result(
            result,
            initial_intensity,
            initial_envelope,
            clock_start=start,
            right_endpoint=end,
            proposal_budget=budget,
            base_context=base,
            residual_context=residual,
        )
        if _rng_state_sha256(checked_rng.bit_generator.state) != rng_after:
            raise ValueError("result validation changed the Philox state")
        return result

    def validate_result(
        self,
        result: OperationalLocalThinningResult,
        initial_intensity: ReferenceCandidateIntensity,
        initial_envelope: TotalizedJumpRateEnvelope,
        *,
        clock_start: object,
        right_endpoint: object,
        proposal_budget: object,
        base_context: object,
        residual_context: object,
    ) -> OperationalLocalThinningResult:
        """Fully replay a bounded result without consuming randomness."""

        if type(result) is not OperationalLocalThinningResult:
            raise TypeError("result has the wrong exact type")
        OperationalLocalThinningResult(
            **_snapshot_fields(result, _result_fields()),
            _construction_token=_RESULT_TOKEN,
        )
        if result.certificate is not self.certificate:
            raise ValueError("result belongs to a different bounded loop owner")
        if result.initial_intensity is not initial_intensity:
            raise ValueError("result belongs to a different initial intensity")
        if result.initial_envelope is not initial_envelope:
            raise ValueError("result belongs to a different initial envelope")
        start = _clock_float(clock_start, name="clock_start")
        end = _clock_float(right_endpoint, name="right_endpoint")
        if end < start:
            raise ValueError("right_endpoint must not precede clock_start")
        budget = _proposal_budget(proposal_budget)
        base, residual = self._canonical_contexts(base_context, residual_context)
        if not _same_float(result.clock_start, start):
            raise ValueError("result clock start differs from the request")
        if not _same_float(result.right_endpoint, end):
            raise ValueError("result right endpoint differs from the request")
        if result.proposal_budget != budget:
            raise ValueError("result proposal budget differs from the request")
        if result.base_context != base or result.residual_context != residual:
            raise ValueError("result contexts differ from the request")
        current_intensity, current_envelope = self._validate_parents(
            initial_intensity,
            initial_envelope,
        )
        if not _same_float(
            result.frozen_reverse_time,
            current_intensity.reverse_time,
        ) or not _same_float(
            result.frozen_direct_time,
            current_intensity.direct_time,
        ):
            raise ValueError("result frozen generative time differs from the request")
        cursor = start
        seen_intensities = [current_intensity]
        seen_envelopes = [current_envelope]
        for index, iteration in enumerate(result.iterations):
            if iteration.proposal_index != index:
                raise ValueError("result proposal indices are not contiguous")
            if not _same_float(iteration.clock_start, cursor):
                raise ValueError("result iteration clock start differs")
            if not _same_float(iteration.waiting_draw.right_endpoint, end):
                raise ValueError("result iteration right endpoint differs")
            self.validate_iteration(
                iteration,
                current_intensity,
                current_envelope,
                base_context=base,
                residual_context=residual,
            )
            if iteration.accepted:
                if any(
                    iteration.post_intensity is previous
                    for previous in seen_intensities
                ):
                    raise ValueError(
                        "accepted replay reused an earlier intensity object"
                    )
                if any(
                    iteration.post_envelope is previous for previous in seen_envelopes
                ):
                    raise ValueError(
                        "accepted replay reused an earlier envelope object"
                    )
                seen_intensities.append(iteration.post_intensity)
                seen_envelopes.append(iteration.post_envelope)
            current_intensity = iteration.post_intensity
            current_envelope = iteration.post_envelope
            cursor = iteration.proposal_time
        if result.terminal_waiting_draw is not None:
            self._thinning_owner.validate_waiting_time(
                result.terminal_waiting_draw,
                current_intensity,
                current_envelope,
            )
        if result.final_intensity is not current_intensity:
            raise ValueError("result final intensity differs from replay")
        if result.final_envelope is not current_envelope:
            raise ValueError("result final envelope differs from replay")
        if not _same_float(result.final_clock_cursor, cursor):
            raise ValueError("result final clock cursor differs from replay")
        if result.final_configuration != current_intensity.source_configuration:
            raise ValueError("result final configuration differs from replay")
        self._require_live_binding()
        return result


def certify_plugin_bridge_operational_thinning_loop(
    thinning_owner: OperationalJumpThinning,
    *,
    loop_policy: object,
    loop_role_sha256: object,
) -> BoundedOperationalThinningLoop:
    """Certify bounded repetition of one checkpoint-nineteen owner."""

    if type(loop_policy) is not str:
        raise TypeError("loop_policy must be exact text")
    if loop_policy != PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_POLICY:
        raise ValueError(
            "only the exported operational thinning-loop policy is supported"
        )
    role = _require_sha256(loop_role_sha256, name="loop_role_sha256")
    if type(thinning_owner) is not OperationalJumpThinning:
        raise TypeError("thinning_owner has the wrong exact type")
    thinning_certificate = thinning_owner._require_live_binding()
    certificate = _make_certificate(
        thinning_certificate,
        thinning_owner.rate_owner.potential_composer.certificate,
        loop_role_sha256=role,
    )
    owner = BoundedOperationalThinningLoop(
        thinning_owner,
        role,
        certificate,
        _construction_token=_OWNER_TOKEN,
    )
    owner._require_live_binding()
    return owner


def require_matching_plugin_bridge_operational_thinning_loop(
    thinning_owner: OperationalJumpThinning,
    owner: BoundedOperationalThinningLoop,
    *,
    loop_policy: object,
    loop_role_sha256: object,
) -> BoundedOperationalThinningLoop:
    """Require exact owner identity and reconstructed transitive custody."""

    if type(loop_policy) is not str:
        raise TypeError("loop_policy must be exact text")
    if loop_policy != PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_POLICY:
        raise ValueError(
            "only the exported operational thinning-loop policy is supported"
        )
    role = _require_sha256(loop_role_sha256, name="loop_role_sha256")
    if type(owner) is not BoundedOperationalThinningLoop:
        raise TypeError("owner must be an exact BoundedOperationalThinningLoop")
    if owner.thinning_owner is not thinning_owner:
        raise ValueError("bounded loop owner is bound to another thinning owner")
    if owner.certificate.loop_role_sha256 != role:
        raise ValueError("bounded loop owner is bound to another role")
    owner._require_live_binding()
    return owner


def validate_plugin_bridge_operational_thinning_loop_certificate(
    thinning_owner: OperationalJumpThinning,
    owner: BoundedOperationalThinningLoop,
    *,
    loop_policy: object,
    loop_role_sha256: object,
) -> OperationalThinningLoopCertificate:
    """Return the reconstructed live checkpoint-twenty certificate."""

    return require_matching_plugin_bridge_operational_thinning_loop(
        thinning_owner,
        owner,
        loop_policy=loop_policy,
        loop_role_sha256=loop_role_sha256,
    ).certificate


__all__ = [
    "OPERATIONAL_THINNING_LOOP_MAX_PROPOSALS",
    "PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_POLICY",
    "PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_SCHEMA_VERSION",
    "PLUGIN_BRIDGE_OPERATIONAL_THINNING_LOOP_SCOPE",
    "BoundedOperationalThinningLoop",
    "OperationalLocalThinningResult",
    "OperationalProposalIteration",
    "OperationalThinningLoopCertificate",
    "PluginBridgeOperationalThinningLoopError",
    "certify_plugin_bridge_operational_thinning_loop",
    "require_matching_plugin_bridge_operational_thinning_loop",
    "validate_plugin_bridge_operational_thinning_loop_certificate",
]
