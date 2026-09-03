"""Pure prospective Linux staging and lifecycle protocol.

This module freezes a portable protocol reducer.  It performs no syscall,
opens no descriptor or path, starts no process, reads no clock, and creates no
positive execution or confinement evidence.  Every timestamp and observation
event is supplied by a caller and can therefore be synthetic.

Bubblewrap 0.11.2 writes its ``child-pid`` JSON status before completing
sandbox setup and only later blocks in the read requested by ``--block-fd``.
Consequently that status is never admitted as proof that the first-stage
barrier has been reached.  The reducer can leave ``CREATED`` only after the
separate
``SETUP_EXACT_BARRIER_READ_BLOCK_KERNEL_OBSERVED`` event.  A future Linux
supervisor must establish that event from a reviewed, pidfd-bound kernel
observation; this pure module cannot establish it.

The exact 91-byte READY parser is incremental and independent of pipe
chunking.  It compares the public run nonce with ``hmac.compare_digest`` and
rejects every pre-release byte beyond the frame.  READY acceptance and a
pidfd-bound stop observation are still insufficient for stage 2: the reducer
also requires an explicit pre-release stdout-drained event.

The four cleanup branches order a deliberately incomplete set of supplied
milestones for pre-stage-1 failure, post-stage-1/pre-stage-2 failure,
post-stage-2-or-running cleanup, and emergency cleanup.  They do not define an
executed teardown protocol, its deadlines, or every resource-dependent
alternative.  A failure disposition is sticky through the modeled milestones,
and a terminal cleanup failure is absorbing.  A future reviewed Linux driver
must define and enforce the complete teardown protocol.

Every lifecycle event carries the same domain-separated run-binding digest.
The binding joins the policy digest, supervisor epoch, run sequence, and public
nonce as correlation syntax.  It rejects an unchanged foreign event whose
binding differs, but is not an authenticator: exact same-binding replay and a
history whose public binding is recomputed remain admissible.  Three typed
observation events and ``INNER_V1_COMPLETE`` also carry caller-supplied
evidence digests.  The latter is only a digest-shaped reference to a future
canonical native-supervisor inner-completion record.  This reducer validates
only digest shape and lifecycle position; it does not validate preimages or
custody.  Thus serializing or hashing a state records only a supplied protocol
transcript and is not a containment receipt.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import hmac
import json
import re
from types import MappingProxyType
from typing import Final, Optional, Tuple


LINUX_CONFINEMENT_STAGING_PROTOCOL_CONTRACT_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-staging-protocol-contract.v1"
)
LINUX_CONFINEMENT_STAGING_PROTOCOL_CONTRACT_DIGEST_DOMAIN: Final = (
    LINUX_CONFINEMENT_STAGING_PROTOCOL_CONTRACT_ARTIFACT_TYPE
)
LINUX_CONFINEMENT_STAGING_TRANSCRIPT_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-staging-transcript.v1"
)
LINUX_CONFINEMENT_STAGING_TRANSCRIPT_DIGEST_DOMAIN: Final = (
    LINUX_CONFINEMENT_STAGING_TRANSCRIPT_ARTIFACT_TYPE
)
LINUX_CONFINEMENT_STAGING_RUN_BINDING_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-staging-run-binding.v1"
)
LINUX_CONFINEMENT_STAGING_RUN_BINDING_DIGEST_DOMAIN: Final = (
    LINUX_CONFINEMENT_STAGING_RUN_BINDING_ARTIFACT_TYPE
)
LINUX_CONFINEMENT_STAGING_PROTOCOL_STATUS: Final = (
    "PROSPECTIVE_UNEXECUTED"
)
LINUX_CONFINEMENT_STAGING_PROTOCOL_TARGET_STATUS: Final = (
    "LINUX_CONFINED_DEVELOPMENT"
)

LINUX_CONFINEMENT_READY_FRAME_PREFIX: Final = (
    b"HETERODIFF-LINUX-READY-V1 "
)
LINUX_CONFINEMENT_READY_FRAME_SUFFIX: Final = b"\n"
LINUX_CONFINEMENT_READY_NONCE_HEX_BYTES: Final = 64
LINUX_CONFINEMENT_READY_FRAME_BYTES: Final = 91

MAXIMUM_LINUX_CONFINEMENT_STAGING_EVENTS: Final = 128
MAXIMUM_LINUX_CONFINEMENT_STAGING_PROTOCOL_CONTRACT_BYTES: Final = (
    64 * 1024
)
MAXIMUM_LINUX_CONFINEMENT_STAGING_TRANSCRIPT_BYTES: Final = 256 * 1024
MAXIMUM_LINUX_CONFINEMENT_STAGING_RUN_SEQUENCE_NUMBER: Final = 4095

_RUN_NONCE_RE = re.compile(r"^[0-9a-f]{64}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SUPERVISOR_EPOCH_RE = re.compile(r"^[0-9a-f]{64}$")


class LinuxConfinementStagingProtocolCode(str, Enum):
    """Closed, nonreflecting failures from the pure staging protocol."""

    INPUT_TYPE = "LINUX_CONFINEMENT_STAGING_INPUT_TYPE"
    INPUT_RESOURCE = "LINUX_CONFINEMENT_STAGING_INPUT_RESOURCE"
    NONCE_INVALID = "LINUX_CONFINEMENT_STAGING_NONCE_INVALID"
    RUN_BINDING_INVALID = (
        "LINUX_CONFINEMENT_STAGING_RUN_BINDING_INVALID"
    )
    EVIDENCE_DIGEST_INVALID = (
        "LINUX_CONFINEMENT_STAGING_EVIDENCE_DIGEST_INVALID"
    )
    READY_INVALID = "LINUX_CONFINEMENT_STAGING_READY_INVALID"
    EVENT_INVALID = "LINUX_CONFINEMENT_STAGING_EVENT_INVALID"
    TRANSITION_INVALID = "LINUX_CONFINEMENT_STAGING_TRANSITION_INVALID"
    CLOCK_INVALID = "LINUX_CONFINEMENT_STAGING_CLOCK_INVALID"
    STATE_INVALID = "LINUX_CONFINEMENT_STAGING_STATE_INVALID"
    TRANSCRIPT_INVALID = "LINUX_CONFINEMENT_STAGING_TRANSCRIPT_INVALID"


_ERROR_MESSAGES = MappingProxyType(
    {
        LinuxConfinementStagingProtocolCode.INPUT_TYPE: (
            "Linux confinement staging input has an invalid exact type"
        ),
        LinuxConfinementStagingProtocolCode.INPUT_RESOURCE: (
            "Linux confinement staging input exceeds a resource ceiling"
        ),
        LinuxConfinementStagingProtocolCode.NONCE_INVALID: (
            "Linux confinement staging nonce is invalid"
        ),
        LinuxConfinementStagingProtocolCode.RUN_BINDING_INVALID: (
            "Linux confinement staging run binding is invalid"
        ),
        LinuxConfinementStagingProtocolCode.EVIDENCE_DIGEST_INVALID: (
            "Linux confinement staging evidence digest is invalid"
        ),
        LinuxConfinementStagingProtocolCode.READY_INVALID: (
            "Linux confinement staging READY frame is invalid"
        ),
        LinuxConfinementStagingProtocolCode.EVENT_INVALID: (
            "Linux confinement staging event is invalid"
        ),
        LinuxConfinementStagingProtocolCode.TRANSITION_INVALID: (
            "Linux confinement staging transition is invalid"
        ),
        LinuxConfinementStagingProtocolCode.CLOCK_INVALID: (
            "Linux confinement staging timestamp is invalid"
        ),
        LinuxConfinementStagingProtocolCode.STATE_INVALID: (
            "Linux confinement staging state is invalid"
        ),
        LinuxConfinementStagingProtocolCode.TRANSCRIPT_INVALID: (
            "Linux confinement staging transcript is invalid"
        ),
    }
)


class LinuxConfinementStagingProtocolError(ValueError):
    """One fixed-message failure with a closed machine-readable code."""

    def __init__(
        self,
        code: LinuxConfinementStagingProtocolCode,
    ) -> None:
        if type(code) is not LinuxConfinementStagingProtocolCode:
            raise TypeError("staging protocol code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


def _fail(code: LinuxConfinementStagingProtocolCode) -> None:
    raise LinuxConfinementStagingProtocolError(code) from None


class LinuxConfinementStagingPhase(str, Enum):
    """Closed prospective lifecycle phases."""

    CREATED = "CREATED"
    SETUP_BLOCKED = "SETUP_BLOCKED"
    STAGE1_RELEASED = "STAGE1_RELEASED"
    READY_AND_STOPPED = "READY_AND_STOPPED"
    STAGE2_RELEASED = "STAGE2_RELEASED"
    INNER_COMPLETE = "INNER_COMPLETE"
    TEARDOWN = "TEARDOWN"
    QUIESCENT = "QUIESCENT"
    TERMINAL_FAILURE = "TERMINAL_FAILURE"


class LinuxConfinementCleanupBranch(str, Enum):
    """Four incomplete supplied-milestone cleanup orderings."""

    PRE_STAGE1_FAILURE = "PRE_STAGE1_FAILURE"
    POST_STAGE1_PRE_STAGE2_FAILURE = (
        "POST_STAGE1_PRE_STAGE2_FAILURE"
    )
    POST_STAGE2_OR_RUNNING = "POST_STAGE2_OR_RUNNING"
    EMERGENCY = "EMERGENCY"


class LinuxConfinementStagingEvent(str, Enum):
    """Closed events accepted by the lifecycle reducer."""

    SUPERVISOR_CREATED = "SUPERVISOR_CREATED"
    ABORT_BEFORE_CHILDREN_CREATED = "ABORT_BEFORE_CHILDREN_CREATED"
    SETUP_EXACT_BARRIER_READ_BLOCK_KERNEL_OBSERVED = (
        "SETUP_EXACT_BARRIER_READ_BLOCK_KERNEL_OBSERVED"
    )
    STAGE1_REQUIRED_OBSERVATION_GATE_RECORDED = (
        "STAGE1_REQUIRED_OBSERVATION_GATE_RECORDED"
    )
    STAGE1_RELEASED = "STAGE1_RELEASED"
    READY_FRAME_ACCEPTED = "READY_FRAME_ACCEPTED"
    PIDFD_BOUND_APPLICATION_SIGSTOP_OBSERVED = (
        "PIDFD_BOUND_APPLICATION_SIGSTOP_OBSERVED"
    )
    PRE_RELEASE_STDOUT_DRAINED = "PRE_RELEASE_STDOUT_DRAINED"
    STAGE2_REQUIRED_OBSERVATION_GATE_RECORDED = (
        "STAGE2_REQUIRED_OBSERVATION_GATE_RECORDED"
    )
    STAGE2_RELEASED = "STAGE2_RELEASED"
    INNER_V1_COMPLETE = "INNER_V1_COMPLETE"
    TEARDOWN_STARTED = "TEARDOWN_STARTED"
    FAIL_CLOSED = "FAIL_CLOSED"
    EMERGENCY_CGROUP_KILL_ENTERED = "EMERGENCY_CGROUP_KILL_ENTERED"
    USERNS_OBSERVER_REAPED = "USERNS_OBSERVER_REAPED"
    SETUP_CHILD_PIDFD_EXIT_OBSERVED = (
        "SETUP_CHILD_PIDFD_EXIT_OBSERVED"
    )
    APPLICATION_REAPED_BY_SANDBOX_PID1 = (
        "APPLICATION_REAPED_BY_SANDBOX_PID1"
    )
    ALL_BOUND_SANDBOX_EXITS_OBSERVED = (
        "ALL_BOUND_SANDBOX_EXITS_OBSERVED"
    )
    REQUEST_WRITER_CLOSED = "REQUEST_WRITER_CLOSED"
    APPLICATION_PIDFD_SIGKILL_WITHOUT_TERM_GRACE_SENT = (
        "APPLICATION_PIDFD_SIGKILL_WITHOUT_TERM_GRACE_SENT"
    )
    APPLICATION_PIDFD_SIGTERM_SENT = (
        "APPLICATION_PIDFD_SIGTERM_SENT"
    )
    TERM_GRACE_AND_CONDITIONAL_PIDFD_SIGKILL_RESOLVED = (
        "TERM_GRACE_AND_CONDITIONAL_PIDFD_SIGKILL_RESOLVED"
    )
    BUBBLEWRAP_MONITOR_REAPED = "BUBBLEWRAP_MONITOR_REAPED"
    ADOPTED_DESCENDANTS_REAPED = "ADOPTED_DESCENDANTS_REAPED"
    BARRIER_WRITER_CLOSED_AFTER_SETUP_EXIT = (
        "BARRIER_WRITER_CLOSED_AFTER_SETUP_EXIT"
    )
    CGROUP_POPULATED_ZERO_OBSERVED = (
        "CGROUP_POPULATED_ZERO_OBSERVED"
    )
    STREAM_EOF_DRAINED = "STREAM_EOF_DRAINED"
    TERMINAL_CLEANUP_FAILURE = "TERMINAL_CLEANUP_FAILURE"


_EVIDENCE_DIGEST_EVENT_IDS: Final = frozenset(
    {
        (
            LinuxConfinementStagingEvent
            .SETUP_EXACT_BARRIER_READ_BLOCK_KERNEL_OBSERVED
        ),
        (
            LinuxConfinementStagingEvent
            .STAGE1_REQUIRED_OBSERVATION_GATE_RECORDED
        ),
        (
            LinuxConfinementStagingEvent
            .STAGE2_REQUIRED_OBSERVATION_GATE_RECORDED
        ),
        LinuxConfinementStagingEvent.INNER_V1_COMPLETE,
    }
)


_PRE_STAGE1_CLEANUP = (
    LinuxConfinementStagingEvent.USERNS_OBSERVER_REAPED,
    LinuxConfinementStagingEvent.SETUP_CHILD_PIDFD_EXIT_OBSERVED,
    LinuxConfinementStagingEvent.BUBBLEWRAP_MONITOR_REAPED,
    LinuxConfinementStagingEvent.ADOPTED_DESCENDANTS_REAPED,
    (
        LinuxConfinementStagingEvent
        .BARRIER_WRITER_CLOSED_AFTER_SETUP_EXIT
    ),
    LinuxConfinementStagingEvent.CGROUP_POPULATED_ZERO_OBSERVED,
    LinuxConfinementStagingEvent.STREAM_EOF_DRAINED,
)
_POST_STAGE1_CLEANUP = (
    LinuxConfinementStagingEvent.REQUEST_WRITER_CLOSED,
    (
        LinuxConfinementStagingEvent
        .APPLICATION_PIDFD_SIGKILL_WITHOUT_TERM_GRACE_SENT
    ),
    LinuxConfinementStagingEvent.APPLICATION_REAPED_BY_SANDBOX_PID1,
    LinuxConfinementStagingEvent.BUBBLEWRAP_MONITOR_REAPED,
    LinuxConfinementStagingEvent.ADOPTED_DESCENDANTS_REAPED,
    LinuxConfinementStagingEvent.CGROUP_POPULATED_ZERO_OBSERVED,
    LinuxConfinementStagingEvent.STREAM_EOF_DRAINED,
)
_POST_STAGE2_CLEANUP = (
    LinuxConfinementStagingEvent.REQUEST_WRITER_CLOSED,
    LinuxConfinementStagingEvent.APPLICATION_PIDFD_SIGTERM_SENT,
    (
        LinuxConfinementStagingEvent
        .TERM_GRACE_AND_CONDITIONAL_PIDFD_SIGKILL_RESOLVED
    ),
    LinuxConfinementStagingEvent.APPLICATION_REAPED_BY_SANDBOX_PID1,
    LinuxConfinementStagingEvent.BUBBLEWRAP_MONITOR_REAPED,
    LinuxConfinementStagingEvent.ADOPTED_DESCENDANTS_REAPED,
    LinuxConfinementStagingEvent.CGROUP_POPULATED_ZERO_OBSERVED,
    LinuxConfinementStagingEvent.STREAM_EOF_DRAINED,
)
_EMERGENCY_CLEANUP = (
    LinuxConfinementStagingEvent.ALL_BOUND_SANDBOX_EXITS_OBSERVED,
    LinuxConfinementStagingEvent.BUBBLEWRAP_MONITOR_REAPED,
    LinuxConfinementStagingEvent.ADOPTED_DESCENDANTS_REAPED,
    LinuxConfinementStagingEvent.CGROUP_POPULATED_ZERO_OBSERVED,
    LinuxConfinementStagingEvent.STREAM_EOF_DRAINED,
)
_CLEANUP_EVENTS_BY_BRANCH = MappingProxyType(
    {
        LinuxConfinementCleanupBranch.PRE_STAGE1_FAILURE: (
            _PRE_STAGE1_CLEANUP
        ),
        (
            LinuxConfinementCleanupBranch
            .POST_STAGE1_PRE_STAGE2_FAILURE
        ): _POST_STAGE1_CLEANUP,
        LinuxConfinementCleanupBranch.POST_STAGE2_OR_RUNNING: (
            _POST_STAGE2_CLEANUP
        ),
        LinuxConfinementCleanupBranch.EMERGENCY: _EMERGENCY_CLEANUP,
    }
)


def _validated_nonce(value: object) -> str:
    if (
        type(value) is not str
        or _RUN_NONCE_RE.fullmatch(value) is None
        or value == "0" * LINUX_CONFINEMENT_READY_NONCE_HEX_BYTES
    ):
        _fail(LinuxConfinementStagingProtocolCode.NONCE_INVALID)
    return value


def _validated_nonzero_sha256(
    value: object,
    *,
    code: LinuxConfinementStagingProtocolCode,
) -> str:
    if (
        type(value) is not str
        or _SHA256_RE.fullmatch(value) is None
        or value == "0" * 64
    ):
        _fail(code)
    return value


def _validated_supervisor_epoch(value: object) -> str:
    if (
        type(value) is not str
        or _SUPERVISOR_EPOCH_RE.fullmatch(value) is None
        or value == "0" * 64
    ):
        _fail(LinuxConfinementStagingProtocolCode.RUN_BINDING_INVALID)
    return value


def _validated_run_sequence_number(value: object) -> int:
    if (
        type(value) is not int
        or value < 0
        or value
        > MAXIMUM_LINUX_CONFINEMENT_STAGING_RUN_SEQUENCE_NUMBER
    ):
        _fail(LinuxConfinementStagingProtocolCode.RUN_BINDING_INVALID)
    return value


def _domain_sha256(domain: str, payload: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(domain.encode("ascii"))
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def _staging_run_binding_bytes(
    *,
    policy_sha256: str,
    supervisor_epoch_id_hex: str,
    run_sequence_number: int,
    run_nonce_hex: str,
) -> bytes:
    policy_digest = _validated_nonzero_sha256(
        policy_sha256,
        code=LinuxConfinementStagingProtocolCode.RUN_BINDING_INVALID,
    )
    epoch = _validated_supervisor_epoch(supervisor_epoch_id_hex)
    sequence = _validated_run_sequence_number(run_sequence_number)
    nonce = _validated_nonce(run_nonce_hex)
    if epoch == nonce:
        _fail(LinuxConfinementStagingProtocolCode.RUN_BINDING_INVALID)
    try:
        return json.dumps(
            {
                "artifact_type": (
                    LINUX_CONFINEMENT_STAGING_RUN_BINDING_ARTIFACT_TYPE
                ),
                "format_version": "1",
                "policy_sha256": policy_digest,
                "run_nonce_hex": nonce,
                "run_sequence_number": sequence,
                "supervisor_epoch_id_hex": epoch,
            },
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError):
        _fail(LinuxConfinementStagingProtocolCode.RUN_BINDING_INVALID)


def linux_confinement_staging_run_binding_sha256(
    *,
    policy_sha256: str,
    supervisor_epoch_id_hex: str,
    run_sequence_number: int,
    run_nonce_hex: str,
) -> str:
    """Return correlation syntax for four caller-supplied run IDs."""

    return _domain_sha256(
        LINUX_CONFINEMENT_STAGING_RUN_BINDING_DIGEST_DOMAIN,
        _staging_run_binding_bytes(
            policy_sha256=policy_sha256,
            supervisor_epoch_id_hex=supervisor_epoch_id_hex,
            run_sequence_number=run_sequence_number,
            run_nonce_hex=run_nonce_hex,
        ),
    )


def _validate_event_evidence_digest(
    event_id: LinuxConfinementStagingEvent,
    evidence_digest_sha256: object,
) -> None:
    if event_id in _EVIDENCE_DIGEST_EVENT_IDS:
        _validated_nonzero_sha256(
            evidence_digest_sha256,
            code=(
                LinuxConfinementStagingProtocolCode
                .EVIDENCE_DIGEST_INVALID
            ),
        )
    elif type(evidence_digest_sha256) is not str or (
        evidence_digest_sha256 != ""
    ):
        _fail(
            LinuxConfinementStagingProtocolCode.EVIDENCE_DIGEST_INVALID
        )


@dataclass(frozen=True)
class LinuxConfinementReadyParserV1:
    """Immutable state for the bounded incremental READY parser."""

    expected_run_nonce_hex: str
    buffered_bytes: bytes = b""
    complete: bool = False

    def __post_init__(self) -> None:
        if type(self) is not LinuxConfinementReadyParserV1:
            _fail(LinuxConfinementStagingProtocolCode.INPUT_TYPE)
        _validated_nonce(self.expected_run_nonce_hex)
        if (
            type(self.buffered_bytes) is not bytes
            or len(self.buffered_bytes)
            > LINUX_CONFINEMENT_READY_FRAME_BYTES
            or type(self.complete) is not bool
        ):
            _fail(LinuxConfinementStagingProtocolCode.STATE_INVALID)
        if self.complete != (
            len(self.buffered_bytes)
            == LINUX_CONFINEMENT_READY_FRAME_BYTES
        ):
            _fail(LinuxConfinementStagingProtocolCode.STATE_INVALID)
        if self.complete:
            _validate_complete_ready_frame(
                self.buffered_bytes,
                self.expected_run_nonce_hex,
            )


def new_linux_confinement_ready_parser(
    run_nonce_hex: str,
) -> LinuxConfinementReadyParserV1:
    """Create one empty parser for an exact nonzero public run nonce."""

    return LinuxConfinementReadyParserV1(
        expected_run_nonce_hex=_validated_nonce(run_nonce_hex),
    )


def _validate_complete_ready_frame(
    frame: bytes,
    expected_run_nonce_hex: str,
) -> None:
    if (
        len(frame) != LINUX_CONFINEMENT_READY_FRAME_BYTES
        or not frame.startswith(LINUX_CONFINEMENT_READY_FRAME_PREFIX)
        or not frame.endswith(LINUX_CONFINEMENT_READY_FRAME_SUFFIX)
    ):
        _fail(LinuxConfinementStagingProtocolCode.READY_INVALID)
    start = len(LINUX_CONFINEMENT_READY_FRAME_PREFIX)
    end = start + LINUX_CONFINEMENT_READY_NONCE_HEX_BYTES
    observed_nonce = frame[start:end]
    expected_nonce = expected_run_nonce_hex.encode("ascii")
    if not hmac.compare_digest(observed_nonce, expected_nonce):
        _fail(LinuxConfinementStagingProtocolCode.READY_INVALID)


def feed_linux_confinement_ready_parser(
    parser: LinuxConfinementReadyParserV1,
    chunk: bytes,
) -> LinuxConfinementReadyParserV1:
    """Consume one exact chunk, rejecting every byte after byte 91."""

    if (
        type(parser) is not LinuxConfinementReadyParserV1
        or type(chunk) is not bytes
    ):
        _fail(LinuxConfinementStagingProtocolCode.INPUT_TYPE)
    LinuxConfinementReadyParserV1.__post_init__(parser)
    if not chunk:
        return parser
    if parser.complete:
        _fail(LinuxConfinementStagingProtocolCode.READY_INVALID)
    if (
        len(parser.buffered_bytes) + len(chunk)
        > LINUX_CONFINEMENT_READY_FRAME_BYTES
    ):
        _fail(LinuxConfinementStagingProtocolCode.READY_INVALID)
    combined = parser.buffered_bytes + chunk
    complete = len(combined) == LINUX_CONFINEMENT_READY_FRAME_BYTES
    if complete:
        _validate_complete_ready_frame(
            combined,
            parser.expected_run_nonce_hex,
        )
    return LinuxConfinementReadyParserV1(
        expected_run_nonce_hex=parser.expected_run_nonce_hex,
        buffered_bytes=combined,
        complete=complete,
    )


def finalize_linux_confinement_ready_parser(
    parser: LinuxConfinementReadyParserV1,
) -> bytes:
    """Return the exact accepted frame or reject truncation."""

    if type(parser) is not LinuxConfinementReadyParserV1:
        _fail(LinuxConfinementStagingProtocolCode.INPUT_TYPE)
    LinuxConfinementReadyParserV1.__post_init__(parser)
    if not parser.complete:
        _fail(LinuxConfinementStagingProtocolCode.READY_INVALID)
    return parser.buffered_bytes


@dataclass(frozen=True)
class LinuxConfinementStagingEventV1:
    """One supplied event carrying run-correlation and sequence syntax."""

    sequence_number: int
    monotonic_timestamp_ns: int
    event_id: LinuxConfinementStagingEvent
    staging_run_binding_sha256: str
    evidence_digest_sha256: str = ""

    def __post_init__(self) -> None:
        if type(self) is not LinuxConfinementStagingEventV1:
            _fail(LinuxConfinementStagingProtocolCode.INPUT_TYPE)
        if (
            type(self.sequence_number) is not int
            or self.sequence_number < 0
            or self.sequence_number
            >= MAXIMUM_LINUX_CONFINEMENT_STAGING_EVENTS
            or type(self.monotonic_timestamp_ns) is not int
            or self.monotonic_timestamp_ns < 0
            or self.monotonic_timestamp_ns > ((1 << 64) - 1)
            or type(self.event_id) is not LinuxConfinementStagingEvent
        ):
            _fail(LinuxConfinementStagingProtocolCode.EVENT_INVALID)
        _validated_nonzero_sha256(
            self.staging_run_binding_sha256,
            code=LinuxConfinementStagingProtocolCode.EVENT_INVALID,
        )
        _validate_event_evidence_digest(
            self.event_id,
            self.evidence_digest_sha256,
        )


@dataclass(frozen=True)
class LinuxConfinementStagingStateV1:
    """Immutable prospective reducer state; never execution evidence."""

    policy_sha256: str
    supervisor_epoch_id_hex: str
    run_sequence_number: int
    run_nonce_hex: str
    phase: LinuxConfinementStagingPhase
    events: Tuple[LinuxConfinementStagingEventV1, ...]
    staging_run_binding_sha256: str = field(init=False)
    cleanup_branch: Optional[LinuxConfinementCleanupBranch] = None
    cleanup_step_index: int = 0
    stage1_required_observation_gate_recorded: bool = False
    ready_frame_accepted: bool = False
    application_sigstop_observed: bool = False
    pre_release_stdout_drained: bool = False
    stage2_required_observation_gate_recorded: bool = False
    failure_sticky: bool = False

    def __post_init__(self) -> None:
        if type(self) is not LinuxConfinementStagingStateV1:
            _fail(LinuxConfinementStagingProtocolCode.INPUT_TYPE)
        expected_run_binding_sha256 = (
            linux_confinement_staging_run_binding_sha256(
                policy_sha256=self.policy_sha256,
                supervisor_epoch_id_hex=self.supervisor_epoch_id_hex,
                run_sequence_number=self.run_sequence_number,
                run_nonce_hex=self.run_nonce_hex,
            )
        )
        object.__setattr__(
            self,
            "staging_run_binding_sha256",
            expected_run_binding_sha256,
        )
        if (
            type(self.phase) is not LinuxConfinementStagingPhase
            or type(self.events) is not tuple
            or not self.events
            or len(self.events)
            > MAXIMUM_LINUX_CONFINEMENT_STAGING_EVENTS
            or any(
                type(event) is not LinuxConfinementStagingEventV1
                for event in self.events
            )
            or (
                self.cleanup_branch is not None
                and type(self.cleanup_branch)
                is not LinuxConfinementCleanupBranch
            )
            or type(self.cleanup_step_index) is not int
            or self.cleanup_step_index < 0
            or type(
                self.stage1_required_observation_gate_recorded
            )
            is not bool
            or type(self.ready_frame_accepted) is not bool
            or type(self.application_sigstop_observed) is not bool
            or type(self.pre_release_stdout_drained) is not bool
            or type(
                self.stage2_required_observation_gate_recorded
            )
            is not bool
            or type(self.failure_sticky) is not bool
        ):
            _fail(LinuxConfinementStagingProtocolCode.STATE_INVALID)
        previous_timestamp = -1
        for index, event in enumerate(self.events):
            LinuxConfinementStagingEventV1.__post_init__(event)
            if (
                event.sequence_number != index
                or event.monotonic_timestamp_ns < previous_timestamp
                or event.staging_run_binding_sha256
                != expected_run_binding_sha256
            ):
                _fail(
                    LinuxConfinementStagingProtocolCode.STATE_INVALID
                )
            previous_timestamp = event.monotonic_timestamp_ns
        if (
            self.events[0].event_id
            is not LinuxConfinementStagingEvent.SUPERVISOR_CREATED
        ):
            _fail(LinuxConfinementStagingProtocolCode.STATE_INVALID)
        if self.cleanup_branch is None:
            if self.cleanup_step_index != 0:
                _fail(LinuxConfinementStagingProtocolCode.STATE_INVALID)
        else:
            maximum = len(
                _CLEANUP_EVENTS_BY_BRANCH[self.cleanup_branch]
            )
            if self.cleanup_step_index > maximum:
                _fail(LinuxConfinementStagingProtocolCode.STATE_INVALID)
        if (
            self.phase
            in (
                LinuxConfinementStagingPhase.TEARDOWN,
                LinuxConfinementStagingPhase.QUIESCENT,
            )
            and self.cleanup_branch is None
        ):
            _fail(LinuxConfinementStagingProtocolCode.STATE_INVALID)
        if (
            self.phase is LinuxConfinementStagingPhase.QUIESCENT
            and self.cleanup_step_index
            != len(_CLEANUP_EVENTS_BY_BRANCH[self.cleanup_branch])
        ):
            _fail(LinuxConfinementStagingProtocolCode.STATE_INVALID)
        if (
            self.phase
            is LinuxConfinementStagingPhase.TERMINAL_FAILURE
            and not self.failure_sticky
        ):
            _fail(LinuxConfinementStagingProtocolCode.STATE_INVALID)
        reconstructed = _reconstruct_state_from_events(self.events)
        observed = (
            self.phase,
            self.cleanup_branch,
            self.cleanup_step_index,
            self.stage1_required_observation_gate_recorded,
            self.ready_frame_accepted,
            self.application_sigstop_observed,
            self.pre_release_stdout_drained,
            self.stage2_required_observation_gate_recorded,
            self.failure_sticky,
        )
        if reconstructed != observed:
            _fail(LinuxConfinementStagingProtocolCode.STATE_INVALID)


def new_linux_confinement_staging_state(
    *,
    policy_sha256: str,
    supervisor_epoch_id_hex: str,
    run_sequence_number: int,
    run_nonce_hex: str,
    created_monotonic_timestamp_ns: int,
) -> LinuxConfinementStagingStateV1:
    """Create the one prospective ``CREATED`` state."""

    run_binding_sha256 = linux_confinement_staging_run_binding_sha256(
        policy_sha256=policy_sha256,
        supervisor_epoch_id_hex=supervisor_epoch_id_hex,
        run_sequence_number=run_sequence_number,
        run_nonce_hex=run_nonce_hex,
    )
    event = LinuxConfinementStagingEventV1(
        sequence_number=0,
        monotonic_timestamp_ns=created_monotonic_timestamp_ns,
        event_id=LinuxConfinementStagingEvent.SUPERVISOR_CREATED,
        staging_run_binding_sha256=run_binding_sha256,
    )
    return LinuxConfinementStagingStateV1(
        policy_sha256=policy_sha256,
        supervisor_epoch_id_hex=supervisor_epoch_id_hex,
        run_sequence_number=run_sequence_number,
        run_nonce_hex=run_nonce_hex,
        phase=LinuxConfinementStagingPhase.CREATED,
        events=(event,),
    )


def _append_event(
    state: LinuxConfinementStagingStateV1,
    event_id: LinuxConfinementStagingEvent,
    timestamp_ns: int,
    evidence_digest_sha256: str = "",
    **changes: object,
) -> LinuxConfinementStagingStateV1:
    if len(state.events) >= MAXIMUM_LINUX_CONFINEMENT_STAGING_EVENTS:
        _fail(LinuxConfinementStagingProtocolCode.INPUT_RESOURCE)
    event = LinuxConfinementStagingEventV1(
        sequence_number=len(state.events),
        monotonic_timestamp_ns=timestamp_ns,
        event_id=event_id,
        staging_run_binding_sha256=(
            state.staging_run_binding_sha256
        ),
        evidence_digest_sha256=evidence_digest_sha256,
    )
    values = {
        "policy_sha256": state.policy_sha256,
        "supervisor_epoch_id_hex": state.supervisor_epoch_id_hex,
        "run_sequence_number": state.run_sequence_number,
        "run_nonce_hex": state.run_nonce_hex,
        "phase": state.phase,
        "events": state.events + (event,),
        "cleanup_branch": state.cleanup_branch,
        "cleanup_step_index": state.cleanup_step_index,
        "stage1_required_observation_gate_recorded": (
            state.stage1_required_observation_gate_recorded
        ),
        "ready_frame_accepted": state.ready_frame_accepted,
        "application_sigstop_observed": (
            state.application_sigstop_observed
        ),
        "pre_release_stdout_drained": (
            state.pre_release_stdout_drained
        ),
        "stage2_required_observation_gate_recorded": (
            state.stage2_required_observation_gate_recorded
        ),
        "failure_sticky": state.failure_sticky,
    }
    values.update(changes)
    try:
        return LinuxConfinementStagingStateV1(**values)
    except TypeError:
        _fail(LinuxConfinementStagingProtocolCode.STATE_INVALID)


def _failure_branch_for_phase(
    phase: LinuxConfinementStagingPhase,
) -> LinuxConfinementCleanupBranch:
    if phase is LinuxConfinementStagingPhase.SETUP_BLOCKED:
        return LinuxConfinementCleanupBranch.PRE_STAGE1_FAILURE
    if phase in (
        LinuxConfinementStagingPhase.STAGE1_RELEASED,
        LinuxConfinementStagingPhase.READY_AND_STOPPED,
    ):
        return (
            LinuxConfinementCleanupBranch
            .POST_STAGE1_PRE_STAGE2_FAILURE
        )
    if phase in (
        LinuxConfinementStagingPhase.STAGE2_RELEASED,
        LinuxConfinementStagingPhase.INNER_COMPLETE,
    ):
        return LinuxConfinementCleanupBranch.POST_STAGE2_OR_RUNNING
    _fail(LinuxConfinementStagingProtocolCode.TRANSITION_INVALID)


def _reconstruct_state_from_events(
    events: Tuple[LinuxConfinementStagingEventV1, ...],
) -> tuple:
    """Reconstruct from event IDs without trusting supplied state fields."""

    phase = LinuxConfinementStagingPhase.CREATED
    cleanup_branch = None
    cleanup_step_index = 0
    stage1_required_observation_gate_recorded = False
    ready_frame_accepted = False
    application_sigstop_observed = False
    pre_release_stdout_drained = False
    stage2_required_observation_gate_recorded = False
    failure_sticky = False

    for record in events[1:]:
        event_id = record.event_id
        if phase in (
            LinuxConfinementStagingPhase.QUIESCENT,
            LinuxConfinementStagingPhase.TERMINAL_FAILURE,
        ):
            _fail(LinuxConfinementStagingProtocolCode.STATE_INVALID)
        if event_id is LinuxConfinementStagingEvent.SUPERVISOR_CREATED:
            _fail(LinuxConfinementStagingProtocolCode.STATE_INVALID)
        if (
            event_id
            is LinuxConfinementStagingEvent
            .ABORT_BEFORE_CHILDREN_CREATED
        ):
            if phase is not LinuxConfinementStagingPhase.CREATED:
                _fail(LinuxConfinementStagingProtocolCode.STATE_INVALID)
            failure_sticky = True
            phase = LinuxConfinementStagingPhase.TERMINAL_FAILURE
            continue
        if event_id is LinuxConfinementStagingEvent.FAIL_CLOSED:
            if phase in (
                LinuxConfinementStagingPhase.CREATED,
                LinuxConfinementStagingPhase.TEARDOWN,
            ):
                _fail(LinuxConfinementStagingProtocolCode.STATE_INVALID)
            try:
                cleanup_branch = _failure_branch_for_phase(phase)
            except LinuxConfinementStagingProtocolError:
                _fail(LinuxConfinementStagingProtocolCode.STATE_INVALID)
            cleanup_step_index = 0
            failure_sticky = True
            phase = LinuxConfinementStagingPhase.TEARDOWN
            continue
        if (
            event_id
            is LinuxConfinementStagingEvent
            .EMERGENCY_CGROUP_KILL_ENTERED
        ):
            if (
                phase is LinuxConfinementStagingPhase.CREATED
                or (
                phase is LinuxConfinementStagingPhase.TEARDOWN
                and cleanup_branch
                is LinuxConfinementCleanupBranch.EMERGENCY
                )
            ):
                _fail(LinuxConfinementStagingProtocolCode.STATE_INVALID)
            cleanup_branch = LinuxConfinementCleanupBranch.EMERGENCY
            cleanup_step_index = 0
            failure_sticky = True
            phase = LinuxConfinementStagingPhase.TEARDOWN
            continue
        if (
            event_id
            is LinuxConfinementStagingEvent.TERMINAL_CLEANUP_FAILURE
        ):
            if phase is not LinuxConfinementStagingPhase.TEARDOWN:
                _fail(LinuxConfinementStagingProtocolCode.STATE_INVALID)
            failure_sticky = True
            phase = LinuxConfinementStagingPhase.TERMINAL_FAILURE
            continue
        if phase is LinuxConfinementStagingPhase.TEARDOWN:
            if cleanup_branch is None:
                _fail(LinuxConfinementStagingProtocolCode.STATE_INVALID)
            sequence = _CLEANUP_EVENTS_BY_BRANCH[cleanup_branch]
            if (
                cleanup_step_index >= len(sequence)
                or event_id is not sequence[cleanup_step_index]
            ):
                _fail(LinuxConfinementStagingProtocolCode.STATE_INVALID)
            cleanup_step_index += 1
            if cleanup_step_index == len(sequence):
                phase = LinuxConfinementStagingPhase.QUIESCENT
            continue
        if (
            phase is LinuxConfinementStagingPhase.CREATED
            and event_id
            is LinuxConfinementStagingEvent
            .SETUP_EXACT_BARRIER_READ_BLOCK_KERNEL_OBSERVED
        ):
            phase = LinuxConfinementStagingPhase.SETUP_BLOCKED
            continue
        if (
            phase is LinuxConfinementStagingPhase.SETUP_BLOCKED
            and event_id
            is LinuxConfinementStagingEvent
            .STAGE1_REQUIRED_OBSERVATION_GATE_RECORDED
            and not stage1_required_observation_gate_recorded
        ):
            stage1_required_observation_gate_recorded = True
            continue
        if (
            phase is LinuxConfinementStagingPhase.SETUP_BLOCKED
            and event_id is LinuxConfinementStagingEvent.STAGE1_RELEASED
            and stage1_required_observation_gate_recorded
        ):
            phase = LinuxConfinementStagingPhase.STAGE1_RELEASED
            continue
        if phase is LinuxConfinementStagingPhase.STAGE1_RELEASED:
            if (
                event_id
                is LinuxConfinementStagingEvent.READY_FRAME_ACCEPTED
                and not ready_frame_accepted
            ):
                ready_frame_accepted = True
                continue
            if (
                event_id
                is LinuxConfinementStagingEvent
                .PIDFD_BOUND_APPLICATION_SIGSTOP_OBSERVED
                and not application_sigstop_observed
            ):
                application_sigstop_observed = True
                continue
            if (
                event_id
                is LinuxConfinementStagingEvent
                .PRE_RELEASE_STDOUT_DRAINED
                and ready_frame_accepted
                and application_sigstop_observed
                and not pre_release_stdout_drained
            ):
                pre_release_stdout_drained = True
                phase = LinuxConfinementStagingPhase.READY_AND_STOPPED
                continue
        if (
            phase is LinuxConfinementStagingPhase.READY_AND_STOPPED
            and event_id
            is LinuxConfinementStagingEvent
            .STAGE2_REQUIRED_OBSERVATION_GATE_RECORDED
            and not stage2_required_observation_gate_recorded
        ):
            stage2_required_observation_gate_recorded = True
            continue
        if (
            phase is LinuxConfinementStagingPhase.READY_AND_STOPPED
            and event_id is LinuxConfinementStagingEvent.STAGE2_RELEASED
            and stage2_required_observation_gate_recorded
        ):
            phase = LinuxConfinementStagingPhase.STAGE2_RELEASED
            continue
        if (
            phase is LinuxConfinementStagingPhase.STAGE2_RELEASED
            and event_id is LinuxConfinementStagingEvent.INNER_V1_COMPLETE
        ):
            phase = LinuxConfinementStagingPhase.INNER_COMPLETE
            continue
        if (
            phase is LinuxConfinementStagingPhase.INNER_COMPLETE
            and event_id is LinuxConfinementStagingEvent.TEARDOWN_STARTED
        ):
            cleanup_branch = (
                LinuxConfinementCleanupBranch.POST_STAGE2_OR_RUNNING
            )
            phase = LinuxConfinementStagingPhase.TEARDOWN
            continue
        _fail(LinuxConfinementStagingProtocolCode.STATE_INVALID)
    return (
        phase,
        cleanup_branch,
        cleanup_step_index,
        stage1_required_observation_gate_recorded,
        ready_frame_accepted,
        application_sigstop_observed,
        pre_release_stdout_drained,
        stage2_required_observation_gate_recorded,
        failure_sticky,
    )


def _apply_cleanup_event(
    state: LinuxConfinementStagingStateV1,
    event_id: LinuxConfinementStagingEvent,
    timestamp_ns: int,
) -> LinuxConfinementStagingStateV1:
    if state.cleanup_branch is None:
        _fail(LinuxConfinementStagingProtocolCode.STATE_INVALID)
    sequence = _CLEANUP_EVENTS_BY_BRANCH[state.cleanup_branch]
    if (
        state.cleanup_step_index >= len(sequence)
        or event_id is not sequence[state.cleanup_step_index]
    ):
        _fail(LinuxConfinementStagingProtocolCode.TRANSITION_INVALID)
    next_index = state.cleanup_step_index + 1
    next_phase = (
        LinuxConfinementStagingPhase.QUIESCENT
        if next_index == len(sequence)
        else LinuxConfinementStagingPhase.TEARDOWN
    )
    return _append_event(
        state,
        event_id,
        timestamp_ns,
        cleanup_step_index=next_index,
        phase=next_phase,
    )


def apply_linux_confinement_staging_event(
    state: LinuxConfinementStagingStateV1,
    *,
    event_id: LinuxConfinementStagingEvent,
    monotonic_timestamp_ns: int,
    evidence_digest_sha256: str = "",
) -> LinuxConfinementStagingStateV1:
    """Apply one exact event through the closed fail-closed reducer."""

    if (
        type(state) is not LinuxConfinementStagingStateV1
        or type(event_id) is not LinuxConfinementStagingEvent
        or type(monotonic_timestamp_ns) is not int
        or type(evidence_digest_sha256) is not str
    ):
        _fail(LinuxConfinementStagingProtocolCode.INPUT_TYPE)
    LinuxConfinementStagingStateV1.__post_init__(state)
    _validate_event_evidence_digest(
        event_id,
        evidence_digest_sha256,
    )
    if (
        monotonic_timestamp_ns < state.events[-1].monotonic_timestamp_ns
        or monotonic_timestamp_ns > ((1 << 64) - 1)
    ):
        _fail(LinuxConfinementStagingProtocolCode.CLOCK_INVALID)
    if state.phase is LinuxConfinementStagingPhase.TERMINAL_FAILURE:
        return state
    if state.phase is LinuxConfinementStagingPhase.QUIESCENT:
        _fail(LinuxConfinementStagingProtocolCode.TRANSITION_INVALID)
    if (
        event_id
        is LinuxConfinementStagingEvent.ABORT_BEFORE_CHILDREN_CREATED
    ):
        if state.phase is not LinuxConfinementStagingPhase.CREATED:
            _fail(
                LinuxConfinementStagingProtocolCode.TRANSITION_INVALID
            )
        return _append_event(
            state,
            event_id,
            monotonic_timestamp_ns,
            phase=LinuxConfinementStagingPhase.TERMINAL_FAILURE,
            failure_sticky=True,
        )
    if event_id is LinuxConfinementStagingEvent.FAIL_CLOSED:
        if state.phase in (
            LinuxConfinementStagingPhase.CREATED,
            LinuxConfinementStagingPhase.TEARDOWN,
        ):
            _fail(
                LinuxConfinementStagingProtocolCode.TRANSITION_INVALID
            )
        return _append_event(
            state,
            event_id,
            monotonic_timestamp_ns,
            phase=LinuxConfinementStagingPhase.TEARDOWN,
            cleanup_branch=_failure_branch_for_phase(state.phase),
            cleanup_step_index=0,
            failure_sticky=True,
        )
    if (
        event_id
        is LinuxConfinementStagingEvent.EMERGENCY_CGROUP_KILL_ENTERED
    ):
        if (
            state.phase is LinuxConfinementStagingPhase.CREATED
            or (
                state.phase is LinuxConfinementStagingPhase.TEARDOWN
                and state.cleanup_branch
                is LinuxConfinementCleanupBranch.EMERGENCY
            )
        ):
            _fail(
                LinuxConfinementStagingProtocolCode.TRANSITION_INVALID
            )
        return _append_event(
            state,
            event_id,
            monotonic_timestamp_ns,
            phase=LinuxConfinementStagingPhase.TEARDOWN,
            cleanup_branch=LinuxConfinementCleanupBranch.EMERGENCY,
            cleanup_step_index=0,
            failure_sticky=True,
        )
    if (
        event_id
        is LinuxConfinementStagingEvent.TERMINAL_CLEANUP_FAILURE
    ):
        if state.phase is not LinuxConfinementStagingPhase.TEARDOWN:
            _fail(
                LinuxConfinementStagingProtocolCode.TRANSITION_INVALID
            )
        return _append_event(
            state,
            event_id,
            monotonic_timestamp_ns,
            phase=LinuxConfinementStagingPhase.TERMINAL_FAILURE,
            failure_sticky=True,
        )
    if state.phase is LinuxConfinementStagingPhase.TEARDOWN:
        return _apply_cleanup_event(
            state,
            event_id,
            monotonic_timestamp_ns,
        )

    if (
        state.phase is LinuxConfinementStagingPhase.CREATED
        and event_id
        is LinuxConfinementStagingEvent
        .SETUP_EXACT_BARRIER_READ_BLOCK_KERNEL_OBSERVED
    ):
        return _append_event(
            state,
            event_id,
            monotonic_timestamp_ns,
            evidence_digest_sha256=evidence_digest_sha256,
            phase=LinuxConfinementStagingPhase.SETUP_BLOCKED,
        )
    if (
        state.phase is LinuxConfinementStagingPhase.SETUP_BLOCKED
        and event_id
        is LinuxConfinementStagingEvent
        .STAGE1_REQUIRED_OBSERVATION_GATE_RECORDED
        and not state.stage1_required_observation_gate_recorded
    ):
        return _append_event(
            state,
            event_id,
            monotonic_timestamp_ns,
            evidence_digest_sha256=evidence_digest_sha256,
            stage1_required_observation_gate_recorded=True,
        )
    if (
        state.phase is LinuxConfinementStagingPhase.SETUP_BLOCKED
        and event_id is LinuxConfinementStagingEvent.STAGE1_RELEASED
        and state.stage1_required_observation_gate_recorded
    ):
        return _append_event(
            state,
            event_id,
            monotonic_timestamp_ns,
            phase=LinuxConfinementStagingPhase.STAGE1_RELEASED,
        )
    if state.phase is LinuxConfinementStagingPhase.STAGE1_RELEASED:
        if (
            event_id
            is LinuxConfinementStagingEvent.READY_FRAME_ACCEPTED
            and not state.ready_frame_accepted
        ):
            return _append_event(
                state,
                event_id,
                monotonic_timestamp_ns,
                ready_frame_accepted=True,
            )
        if (
            event_id
            is LinuxConfinementStagingEvent
            .PIDFD_BOUND_APPLICATION_SIGSTOP_OBSERVED
            and not state.application_sigstop_observed
        ):
            return _append_event(
                state,
                event_id,
                monotonic_timestamp_ns,
                application_sigstop_observed=True,
            )
        if (
            event_id
            is LinuxConfinementStagingEvent
            .PRE_RELEASE_STDOUT_DRAINED
            and state.ready_frame_accepted
            and state.application_sigstop_observed
            and not state.pre_release_stdout_drained
        ):
            return _append_event(
                state,
                event_id,
                monotonic_timestamp_ns,
                pre_release_stdout_drained=True,
                phase=(
                    LinuxConfinementStagingPhase.READY_AND_STOPPED
                ),
            )
    if (
        state.phase is LinuxConfinementStagingPhase.READY_AND_STOPPED
        and event_id
        is LinuxConfinementStagingEvent
        .STAGE2_REQUIRED_OBSERVATION_GATE_RECORDED
        and not state.stage2_required_observation_gate_recorded
    ):
        return _append_event(
            state,
            event_id,
            monotonic_timestamp_ns,
            evidence_digest_sha256=evidence_digest_sha256,
            stage2_required_observation_gate_recorded=True,
        )
    if (
        state.phase is LinuxConfinementStagingPhase.READY_AND_STOPPED
        and event_id is LinuxConfinementStagingEvent.STAGE2_RELEASED
        and state.stage2_required_observation_gate_recorded
    ):
        return _append_event(
            state,
            event_id,
            monotonic_timestamp_ns,
            phase=LinuxConfinementStagingPhase.STAGE2_RELEASED,
        )
    if (
        state.phase is LinuxConfinementStagingPhase.STAGE2_RELEASED
        and event_id is LinuxConfinementStagingEvent.INNER_V1_COMPLETE
    ):
        return _append_event(
            state,
            event_id,
            monotonic_timestamp_ns,
            evidence_digest_sha256=evidence_digest_sha256,
            phase=LinuxConfinementStagingPhase.INNER_COMPLETE,
        )
    if (
        state.phase is LinuxConfinementStagingPhase.INNER_COMPLETE
        and event_id is LinuxConfinementStagingEvent.TEARDOWN_STARTED
    ):
        return _append_event(
            state,
            event_id,
            monotonic_timestamp_ns,
            phase=LinuxConfinementStagingPhase.TEARDOWN,
            cleanup_branch=(
                LinuxConfinementCleanupBranch.POST_STAGE2_OR_RUNNING
            ),
            cleanup_step_index=0,
        )
    _fail(LinuxConfinementStagingProtocolCode.TRANSITION_INVALID)


def _contract_tree() -> dict:
    return {
        "artifact_type": (
            LINUX_CONFINEMENT_STAGING_PROTOCOL_CONTRACT_ARTIFACT_TYPE
        ),
        "cleanup_event_ids_by_branch": {
            branch.value: [event.value for event in events]
            for branch, events in _CLEANUP_EVENTS_BY_BRANCH.items()
        },
        "cleanup_model_scope_id": (
            "caller-supplied-milestone-order-only-v1"
        ),
        "evidence_digest_event_ids": [
            event.value
            for event in LinuxConfinementStagingEvent
            if event in _EVIDENCE_DIGEST_EVENT_IDS
        ],
        "event_ids": [event.value for event in LinuxConfinementStagingEvent],
        "event_payload_schema": {
            "evidence_digest_encoding_id": (
                "lowercase-hex-fixed-64-nonzero-v1"
            ),
            "evidence_digest_preimages_validated_by_reducer": False,
            (
                "inner_v1_complete_evidence_digest_semantics_id"
            ): (
                "caller-supplied-digest-shaped-reference-to-future-"
                "canonical-native-supervisor-inner-completion-record-v1"
            ),
            "non_evidence_event_evidence_digest_sha256": "",
            "staging_run_binding_sha256_required_every_event": True,
        },
        "fixed_requirements": {
            "abort_before_children_created_is_absorbing": True,
            "all_events_are_caller_supplied_and_not_evidence": True,
            "bubblewrap_child_pid_status_is_barrier_proof": False,
            "cleanup_action_events_are_supplied_and_not_evidence": True,
            "cleanup_deadline_enforcement_modeled": False,
            (
                "cleanup_milestones_are_complete_executed_teardown_"
                "protocol"
            ): False,
            "constant_time_public_nonce_comparison_required": True,
            "emergency_from_created_admitted": False,
            "exact_ready_frame_length_bytes": (
                LINUX_CONFINEMENT_READY_FRAME_BYTES
            ),
            "executed_teardown_protocol_defined": False,
            (
                "future_linux_driver_ready_event_must_derive_from_"
                "complete_exact_parser"
            ): True,
            (
                "reducer_enforces_ready_event_parser_derivation"
            ): False,
            (
                "ready_event_parser_preimage_validated_by_reducer"
            ): False,
            "fail_closed_from_created_admitted": False,
            "failure_disposition_sticky_through_cleanup": True,
            "gate_evidence_digest_preimages_validated_by_reducer": False,
            (
                "inner_v1_complete_digest_is_execution_evidence"
            ): False,
            (
                "inner_v1_complete_digest_preimage_validated_by_reducer"
            ): False,
            (
                "inner_v1_complete_event_requires_nonzero_digest"
            ): True,
            "kernel_observed_exact_barrier_read_block_required": True,
            "non_evidence_event_payload_empty_required": True,
            "pre_release_stdout_drain_event_required": True,
            "post_stage_cleanup_signal_sequences_distinct": True,
            (
                "recomputed_cross_run_rebinding_rejected_by_reducer"
            ): False,
            "resource_dependent_cleanup_alternatives_modeled": False,
            "run_binding_is_authenticator": False,
            "run_binding_required_on_every_event": True,
            "same_binding_replay_rejected_by_reducer": False,
            (
                "signal_grace_and_monitor_deadline_enforcement_is_"
                "linux_driver_responsibility"
            ): True,
            "stage1_required_observation_gate_before_release": True,
            (
                "stage2_required_observation_gate_after_ready_stop_"
                "drain_before_release"
            ): True,
            "supplied_evidence_digest_is_execution_evidence": False,
            "supplied_ready_event_is_not_parser_proof": True,
            "terminal_cleanup_failure_absorbing": True,
            "timestamps_monotonic_nondecreasing_required": True,
            (
                "future_executed_preimage_and_custody_validator_"
                "required_for_replay_or_splice_rejection"
            ): True,
            (
                "future_native_supervisor_canonical_inner_completion_"
                "record_required"
            ): True,
        },
        "format_version": "1",
        "implementation_status_id": (
            LINUX_CONFINEMENT_STAGING_PROTOCOL_STATUS
        ),
        "phase_ids": [
            phase.value for phase in LinuxConfinementStagingPhase
        ],
        "ready_frame_prefix_ascii": (
            LINUX_CONFINEMENT_READY_FRAME_PREFIX.decode("ascii")
        ),
        "ready_frame_suffix_ascii": (
            LINUX_CONFINEMENT_READY_FRAME_SUFFIX.decode("ascii")
        ),
        "run_nonce_encoding_id": "lowercase-hex-fixed-64-nonzero-v1",
        "staging_run_binding_schema": {
            "artifact_type": (
                LINUX_CONFINEMENT_STAGING_RUN_BINDING_ARTIFACT_TYPE
            ),
            "binding_field_ids": [
                "policy-sha256",
                "run-nonce-hex",
                "run-sequence-number",
                "supervisor-epoch-id-hex",
            ],
            "digest_domain": (
                LINUX_CONFINEMENT_STAGING_RUN_BINDING_DIGEST_DOMAIN
            ),
            "maximum_run_sequence_number": (
                MAXIMUM_LINUX_CONFINEMENT_STAGING_RUN_SEQUENCE_NUMBER
            ),
            "scope_id": (
                "caller-supplied-correlation-syntax-only-v1"
            ),
        },
        "target_status_id": (
            LINUX_CONFINEMENT_STAGING_PROTOCOL_TARGET_STATUS
        ),
    }


def linux_confinement_staging_protocol_contract_tree() -> dict:
    """Return a fresh exact projection of the prospective contract."""

    return _contract_tree()


def linux_confinement_staging_protocol_contract_bytes() -> bytes:
    """Return bounded canonical ASCII JSON for the fixed contract."""

    try:
        result = json.dumps(
            _contract_tree(),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError):
        _fail(LinuxConfinementStagingProtocolCode.TRANSCRIPT_INVALID)
    if (
        not result
        or len(result)
        > MAXIMUM_LINUX_CONFINEMENT_STAGING_PROTOCOL_CONTRACT_BYTES
    ):
        _fail(LinuxConfinementStagingProtocolCode.INPUT_RESOURCE)
    return result


def linux_confinement_staging_protocol_contract_sha256() -> str:
    """Return the length-framed domain digest of the fixed contract."""

    return _domain_sha256(
        LINUX_CONFINEMENT_STAGING_PROTOCOL_CONTRACT_DIGEST_DOMAIN,
        linux_confinement_staging_protocol_contract_bytes(),
    )


def linux_confinement_staging_transcript_tree(
    state: LinuxConfinementStagingStateV1,
) -> dict:
    """Project one supplied state without upgrading any execution claim."""

    if type(state) is not LinuxConfinementStagingStateV1:
        _fail(LinuxConfinementStagingProtocolCode.INPUT_TYPE)
    LinuxConfinementStagingStateV1.__post_init__(state)
    return {
        "artifact_type": (
            LINUX_CONFINEMENT_STAGING_TRANSCRIPT_ARTIFACT_TYPE
        ),
        "application_sigstop_observed_as_supplied_event": (
            state.application_sigstop_observed
        ),
        "claim_state": {
            "confinement_attested": False,
            "linux_execution_observed": False,
            "named_controls_observed": False,
            "receipt_eligible": False,
        },
        "cleanup_branch_id": (
            None
            if state.cleanup_branch is None
            else state.cleanup_branch.value
        ),
        "cleanup_step_index": state.cleanup_step_index,
        "cleanup_transcript_is_complete_executed_protocol": False,
        "evidence_digest_preimages_validated_by_reducer": False,
        "event_count": len(state.events),
        "events": [
            {
                "evidence_digest_sha256": (
                    event.evidence_digest_sha256
                ),
                "event_id": event.event_id.value,
                "monotonic_timestamp_ns": event.monotonic_timestamp_ns,
                "sequence_number": event.sequence_number,
                "staging_run_binding_sha256": (
                    event.staging_run_binding_sha256
                ),
            }
            for event in state.events
        ],
        "executed_teardown_protocol_defined": False,
        "failure_sticky": state.failure_sticky,
        "format_version": "1",
        "implementation_status_id": (
            LINUX_CONFINEMENT_STAGING_PROTOCOL_STATUS
        ),
        "is_execution_evidence": False,
        "phase_id": state.phase.value,
        "policy_sha256": state.policy_sha256,
        "pre_release_stdout_drained_as_supplied_event": (
            state.pre_release_stdout_drained
        ),
        "protocol_contract_sha256": (
            linux_confinement_staging_protocol_contract_sha256()
        ),
        "ready_frame_accepted_as_supplied_event": (
            state.ready_frame_accepted
        ),
        "run_nonce_hex": state.run_nonce_hex,
        "run_sequence_number": state.run_sequence_number,
        "stage1_required_observation_gate_recorded_as_supplied_event": (
            state.stage1_required_observation_gate_recorded
        ),
        "stage2_required_observation_gate_recorded_as_supplied_event": (
            state.stage2_required_observation_gate_recorded
        ),
        "staging_run_binding_sha256": (
            state.staging_run_binding_sha256
        ),
        "supervisor_epoch_id_hex": state.supervisor_epoch_id_hex,
        "synthetic_inputs_possible": True,
        "target_status_id": (
            LINUX_CONFINEMENT_STAGING_PROTOCOL_TARGET_STATUS
        ),
    }


def linux_confinement_staging_transcript_bytes(
    state: LinuxConfinementStagingStateV1,
) -> bytes:
    """Serialize one bounded canonical non-evidentiary transcript."""

    try:
        result = json.dumps(
            linux_confinement_staging_transcript_tree(state),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    except LinuxConfinementStagingProtocolError:
        raise
    except (TypeError, ValueError, UnicodeError):
        _fail(LinuxConfinementStagingProtocolCode.TRANSCRIPT_INVALID)
    if (
        not result
        or len(result)
        > MAXIMUM_LINUX_CONFINEMENT_STAGING_TRANSCRIPT_BYTES
    ):
        _fail(LinuxConfinementStagingProtocolCode.INPUT_RESOURCE)
    return result


def linux_confinement_staging_transcript_sha256(
    state: LinuxConfinementStagingStateV1,
) -> str:
    """Hash canonical supplied events; never promote them to evidence."""

    return _domain_sha256(
        LINUX_CONFINEMENT_STAGING_TRANSCRIPT_DIGEST_DOMAIN,
        linux_confinement_staging_transcript_bytes(state),
    )


__all__ = [
    "LINUX_CONFINEMENT_READY_FRAME_BYTES",
    "LINUX_CONFINEMENT_READY_FRAME_PREFIX",
    "LINUX_CONFINEMENT_READY_FRAME_SUFFIX",
    "LINUX_CONFINEMENT_READY_NONCE_HEX_BYTES",
    "LINUX_CONFINEMENT_STAGING_PROTOCOL_CONTRACT_ARTIFACT_TYPE",
    "LINUX_CONFINEMENT_STAGING_PROTOCOL_CONTRACT_DIGEST_DOMAIN",
    "LINUX_CONFINEMENT_STAGING_PROTOCOL_STATUS",
    "LINUX_CONFINEMENT_STAGING_PROTOCOL_TARGET_STATUS",
    "LINUX_CONFINEMENT_STAGING_RUN_BINDING_ARTIFACT_TYPE",
    "LINUX_CONFINEMENT_STAGING_RUN_BINDING_DIGEST_DOMAIN",
    "LINUX_CONFINEMENT_STAGING_TRANSCRIPT_ARTIFACT_TYPE",
    "LINUX_CONFINEMENT_STAGING_TRANSCRIPT_DIGEST_DOMAIN",
    "MAXIMUM_LINUX_CONFINEMENT_STAGING_EVENTS",
    "MAXIMUM_LINUX_CONFINEMENT_STAGING_PROTOCOL_CONTRACT_BYTES",
    "MAXIMUM_LINUX_CONFINEMENT_STAGING_RUN_SEQUENCE_NUMBER",
    "MAXIMUM_LINUX_CONFINEMENT_STAGING_TRANSCRIPT_BYTES",
    "LinuxConfinementCleanupBranch",
    "LinuxConfinementReadyParserV1",
    "LinuxConfinementStagingEvent",
    "LinuxConfinementStagingEventV1",
    "LinuxConfinementStagingPhase",
    "LinuxConfinementStagingProtocolCode",
    "LinuxConfinementStagingProtocolError",
    "LinuxConfinementStagingStateV1",
    "apply_linux_confinement_staging_event",
    "feed_linux_confinement_ready_parser",
    "finalize_linux_confinement_ready_parser",
    "linux_confinement_staging_protocol_contract_bytes",
    "linux_confinement_staging_protocol_contract_sha256",
    "linux_confinement_staging_protocol_contract_tree",
    "linux_confinement_staging_run_binding_sha256",
    "linux_confinement_staging_transcript_bytes",
    "linux_confinement_staging_transcript_sha256",
    "linux_confinement_staging_transcript_tree",
    "new_linux_confinement_ready_parser",
    "new_linux_confinement_staging_state",
]
