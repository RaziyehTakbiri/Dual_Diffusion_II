"""Fresh-process, exactly-once execution boundary for frozen A1 learners.

Importing this module uses only the Python standard library and never trains a
learner.  The public launcher starts a new interpreter with native thread
limits in its environment.  Only the hidden worker imports NumPy, SciPy, and
PyTorch, verifies every discovered native pool, atomically reserves a ledger
key, persists PREPARED, and then issues the single-use permit required by the
sampled learner executor.

The CLI requires the literal ``--execute-learner`` flag.  Tests exercise only
request, digest, environment, and ledger primitives; they never invoke the
worker or an optimizer.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import asdict, dataclass
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import resource
import stat
import subprocess
import sys
import tempfile
import time
from typing import Dict, Iterator, Mapping, Optional, Sequence, Tuple


_CANONICAL_MODULE_NAME = "heterodiff.experiments.finite_association_isolated_runner"
if __name__ == "__main__":
    _direct_script_module = sys.modules.get(__name__)
    if _direct_script_module is None:
        raise RuntimeError("direct-script module identity is unavailable")
    _registered_module = sys.modules.get(_CANONICAL_MODULE_NAME)
    if _registered_module is None:
        sys.modules[_CANONICAL_MODULE_NAME] = _direct_script_module
    elif _registered_module is not _direct_script_module:
        raise RuntimeError("canonical isolated-runner module identity conflicts")


_METHODS = ("direct", "guided", "strong_direct", "guide_input", "mismatch")
_SEEDS = (1_729, 3_253, 5_003, 7_411, 10_007, 13_007, 16_001, 20_011)
_BUDGETS = (512, 4_096, 32_768)
_THREAD_ENVIRONMENT = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "BLIS_NUM_THREADS",
)
_LEDGER_SCHEMA = "heterodiff-a1-exactly-once-ledger-v5"
_RUN_KEY_SCHEMA = "heterodiff-a1-sampled-run-key-v4"
_RUNTIME_SCHEMA = "heterodiff-a1-isolated-runtime-v3"
_CAMPAIGN_SCHEMA = "heterodiff-a1-sampled-campaign-v4"
_WORKER_SESSION_SCHEMA = "heterodiff-a1-worker-session-v3"
_LAUNCH_AUTHORIZATION_SCHEMA = (
    "heterodiff-a1-sampled-launch-authorization-v3"
)
_OPTIMIZER_COMPLETION_SCHEMA = (
    "heterodiff-a1-sampled-optimizer-completion-v2"
)
_AGGREGATE_SCHEMA = "heterodiff-a1-sampled-aggregate-v3"
_MAXIMUM_LEDGER_BYTES = 16 * 1024 * 1024
_MAXIMUM_STALE_LEDGER_TEMPORARIES = 64
_LEDGER_TEMPORARY_PREFIX = ".ledger-"
_METHOD_UPDATES = {
    "direct": 3_000,
    "guided": 3_000,
    "strong_direct": 4_500,
    "guide_input": 3_000,
    "mismatch": 3_000,
}
_EXPECTED_TOTAL_OPTIMIZER_STEPS = 396_000
_LAUNCH_STATES = frozenset(
    ("ISSUED", "BOUND", "CONSUMED", "FAILURE", "HOLD")
)
_PARENT_LAUNCH_FAILURE_STAGES = frozenset(
    (
        "ISSUE_COMMIT",
        "POPEN",
        "BIND",
        "TOKEN_DELIVERY",
        "CHILD_WAIT",
        "CHILD_EXIT_BEFORE_CONSUMPTION",
    )
)
_TERMINAL_STATES = frozenset(("SUCCESS", "FAILURE", "HOLD"))
_ALL_STATES = frozenset(
    ("RESERVED", "PREPARED", "RUNNING", *_TERMINAL_STATES)
)
_SUCCESS_ADDITION_FIELDS = frozenset(
    (
        "classifier_sha256",
        "certificate_sha256",
        "certified_maximum_absolute_correction",
        "parameter_sha256",
        "final_empirical_risk",
        "maximum_unclipped_gradient_norm",
        "optimizer_steps_taken",
        "optimizer_transcript_sha256",
        "optimizer_completion_receipt",
        "optimizer_completion_receipt_sha256",
        "checkpoint_file",
        "checkpoint_sha256",
        "optimizer_wall_seconds",
        "total_wall_seconds",
        "total_cpu_seconds",
        "process_peak_rss_bytes",
        "completed_unix_ns",
    )
)
_SUCCESS_EXIT_OBSERVATION_FIELDS = frozenset(
    (
        "exit_observation_previous_receipt_sha256",
        "exit_observed_unix_ns",
        "exit_child_returncode",
        "exit_child_signal",
        "exit_observation_receipt_sha256",
    )
)

_OPTIMIZER_COMPLETION_FIELDS = frozenset(
    (
        "schema",
        "seed",
        "budget",
        "method",
        "run_key_sha256",
        "campaign_sha256",
        "preflight_sha256",
        "prepared_ledger_sha256",
        "running_ledger_sha256",
        "execution_runtime_sha256",
        "worker_session_sha256",
        "expected_optimizer_steps",
        "observed_optimizer_steps",
        "optimizer_transcript_sha256",
        "initial_parameter_sha256",
        "last_post_update_parameter_sha256",
        "final_parameter_sha256",
        "certificate_sha256",
        "classifier_sha256",
        "resource_sha256",
        "checkpoint_identity_sha256",
        "completion_receipt_sha256",
    )
)
_AGGREGATE_MEMBER_FIELDS = frozenset(
    (
        "ordinal",
        "seed",
        "budget",
        "method",
        "run_key_sha256",
        "preflight_sha256",
        "prepared_ledger_sha256",
        "running_ledger_sha256",
        "success_ledger_sha256",
        "exit_observation_receipt_sha256",
        "worker_process_id",
        "worker_parent_process_id",
        "worker_process_identity_sha256",
        "worker_session_sha256",
        "launch_authorization_sha256",
        "launch_receipt_sha256",
        "execution_runtime_sha256",
        "campaign_sha256",
        "optimizer_completion_receipt_sha256",
        "checkpoint_sha256",
        "classifier_sha256",
        "parameter_sha256",
        "certificate_sha256",
        "optimizer_steps_taken",
        "optimizer_transcript_sha256",
        "resources",
        "resource_receipt_sha256",
        "completed_unix_ns",
    )
)
_AGGREGATE_FIELDS = frozenset(
    (
        "schema",
        "campaign_sha256",
        "coordinate_manifest_sha256",
        "ordered_success_receipts",
        "ordered_success_receipts_sha256",
        "ordered_checkpoint_sha256",
        "total_optimizer_steps_taken",
        "resource_totals",
        "fresh_metric_recomputation_required",
        "execution_order_attested",
        "scientific_decision_eligible",
        "aggregate_sha256",
    )
)


def _canonical_json(value: object) -> bytes:
    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise TypeError("value is not canonical-JSON serializable") from error
    return encoded.encode("ascii")


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _peak_rss_bytes() -> int:
    native = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return native if sys.platform == "darwin" else native * 1024


def _lower_sha256(value: object, *, name: str) -> str:
    if type(value) is not str or len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError("%s must be a lowercase SHA-256 digest" % name)
    return value


def _validated_launch_authorization_record(value: object) -> dict:
    """Validate one hash-chained parent-issued launch authorization."""

    if type(value) is not dict or value.get("state") not in _LAUNCH_STATES:
        raise RuntimeError("launch authorization state is invalid")
    state = value["state"]
    issued_fields = {
        "schema",
        "state",
        "request",
        "ledger_directory",
        "parent_process_id",
        "worker_token_sha256",
        "issued_unix_ns",
        "launch_authorization_sha256",
        "issued_receipt_sha256",
    }
    bound_additions = {
        "child_process_id",
        "bound_unix_ns",
        "bound_receipt_sha256",
    }
    consumed_additions = {
        "consumed_unix_ns",
        "consumed_receipt_sha256",
    }
    terminal_additions = {
        "terminal_owner",
        "terminal_process_id",
        "previous_state",
        "previous_receipt_sha256",
        "failed_stage",
        "error_type",
        "error_message",
        "failed_unix_ns",
        "terminal_receipt_sha256",
    }
    parent_terminal_additions = {
        "observed_child_process_id",
        "child_returncode",
        "child_signal",
    }
    parent_exit_observation_additions = {
        "exit_observation_previous_receipt_sha256",
        "exit_observed_unix_ns",
        "exit_child_returncode",
        "exit_child_signal",
        "exit_observation_receipt_sha256",
    }
    terminal_state = state in ("FAILURE", "HOLD")
    owner = value.get("terminal_owner") if terminal_state else None
    previous_state = value.get("previous_state") if terminal_state else None
    if terminal_state and (
        (owner == "PARENT" and previous_state in ("ISSUED", "BOUND"))
        or (owner == "PARENT_REAPER" and previous_state == "CONSUMED")
        or (owner == "CHILD" and previous_state == "CONSUMED")
    ):
        has_bound = previous_state in ("BOUND", "CONSUMED")
        has_consumed = previous_state == "CONSUMED"
    elif terminal_state:
        raise RuntimeError("terminal launch ownership/stage is invalid")
    else:
        has_bound = state in ("BOUND", "CONSUMED")
        has_consumed = state == "CONSUMED"
    expected = set(issued_fields)
    if has_bound:
        expected.update(bound_additions)
    if has_consumed:
        expected.update(consumed_additions)
    if terminal_state:
        expected.update(terminal_additions)
        if owner in ("PARENT", "PARENT_REAPER"):
            expected.update(parent_terminal_additions)
        has_exit_observation = (
            owner in ("PARENT", "CHILD")
            and "exit_observation_receipt_sha256" in value
        )
        if has_exit_observation:
            expected.update(parent_exit_observation_additions)
    else:
        has_exit_observation = False
    if set(value) != expected:
        raise RuntimeError("launch authorization has an invalid exact schema")
    if value.get("schema") != _LAUNCH_AUTHORIZATION_SCHEMA:
        raise RuntimeError("launch authorization schema is invalid")
    request = value.get("request")
    if type(request) is not dict or set(request) != {"seed", "budget", "method"}:
        raise RuntimeError("launch authorization request is invalid")
    FrozenAssociationSampledRunRequest(**request)
    directory = value.get("ledger_directory")
    if (
        type(directory) is not str
        or str(Path(directory).resolve()) != directory
    ):
        raise RuntimeError("launch authorization path is not canonical")
    parent = value.get("parent_process_id")
    issued_ns = value.get("issued_unix_ns")
    if (
        isinstance(parent, bool)
        or type(parent) is not int
        or parent <= 0
        or isinstance(issued_ns, bool)
        or type(issued_ns) is not int
        or issued_ns <= 0
    ):
        raise RuntimeError("launch authorization parent/timestamp is invalid")
    token_sha256 = _lower_sha256(
        value.get("worker_token_sha256"), name="worker_token_sha256"
    )
    identity = {
        "schema": _LAUNCH_AUTHORIZATION_SCHEMA,
        "request": request,
        "ledger_directory": directory,
        "parent_process_id": parent,
        "worker_token_sha256": token_sha256,
        "issued_unix_ns": issued_ns,
    }
    authorization_sha256 = _lower_sha256(
        value.get("launch_authorization_sha256"),
        name="launch_authorization_sha256",
    )
    if _sha256_json(identity) != authorization_sha256:
        raise RuntimeError("launch authorization identity digest is inconsistent")
    issued = {**identity, "state": "ISSUED"}
    issued["launch_authorization_sha256"] = authorization_sha256
    issued_receipt = _lower_sha256(
        value.get("issued_receipt_sha256"), name="issued_receipt_sha256"
    )
    if _sha256_json(issued) != issued_receipt:
        raise RuntimeError("launch ISSUED receipt digest is inconsistent")
    issued["issued_receipt_sha256"] = issued_receipt
    bound = None
    if has_bound:
        child = value.get("child_process_id")
        bound_ns = value.get("bound_unix_ns")
        if (
            isinstance(child, bool)
            or type(child) is not int
            or child <= 0
            or isinstance(bound_ns, bool)
            or type(bound_ns) is not int
            or bound_ns < issued_ns
        ):
            raise RuntimeError("launch BOUND process/timestamp is invalid")
        bound = dict(issued)
        bound.update(
            {
                "state": "BOUND",
                "child_process_id": child,
                "bound_unix_ns": bound_ns,
            }
        )
        bound_receipt = _lower_sha256(
            value.get("bound_receipt_sha256"), name="bound_receipt_sha256"
        )
        if _sha256_json(bound) != bound_receipt:
            raise RuntimeError("launch BOUND receipt digest is inconsistent")
        bound["bound_receipt_sha256"] = bound_receipt
    consumed = None
    if has_consumed:
        consumed_ns = value.get("consumed_unix_ns")
        if (
            isinstance(consumed_ns, bool)
            or type(consumed_ns) is not int
            or consumed_ns < value["bound_unix_ns"]
        ):
            raise RuntimeError("launch CONSUMED timestamp is invalid")
        consumed = dict(bound)
        consumed.update(
            {"state": "CONSUMED", "consumed_unix_ns": consumed_ns}
        )
        consumed_receipt = _lower_sha256(
            value.get("consumed_receipt_sha256"),
            name="consumed_receipt_sha256",
        )
        if _sha256_json(consumed) != consumed_receipt:
            raise RuntimeError("launch CONSUMED receipt digest is inconsistent")
        consumed["consumed_receipt_sha256"] = consumed_receipt
    if terminal_state:
        terminal_process_id = value.get("terminal_process_id")
        if (
            isinstance(terminal_process_id, bool)
            or type(terminal_process_id) is not int
            or terminal_process_id <= 0
        ):
            raise RuntimeError("terminal launch process identity is invalid")
        if owner in ("PARENT", "PARENT_REAPER"):
            if terminal_process_id != parent:
                raise RuntimeError("terminal launch is not owned by its parent")
        if owner == "PARENT":
            failed_stage = value.get("failed_stage")
            if failed_stage not in _PARENT_LAUNCH_FAILURE_STAGES:
                raise RuntimeError("parent launch failure stage is invalid")
            allowed_previous = {
                "ISSUE_COMMIT": frozenset(("ISSUED",)),
                "POPEN": frozenset(("ISSUED",)),
                "BIND": frozenset(("ISSUED", "BOUND")),
                "TOKEN_DELIVERY": frozenset(("BOUND",)),
                "CHILD_WAIT": frozenset(("BOUND",)),
                "CHILD_EXIT_BEFORE_CONSUMPTION": frozenset(("BOUND",)),
            }[failed_stage]
            if previous_state not in allowed_previous:
                raise RuntimeError(
                    "parent launch failure stage disagrees with prior state"
                )
            observed_child = value.get("observed_child_process_id")
            child_returncode = value.get("child_returncode")
            child_signal = value.get("child_signal")
            if failed_stage in ("ISSUE_COMMIT", "POPEN"):
                if (
                    observed_child is not None
                    or child_returncode is not None
                    or child_signal is not None
                ):
                    raise RuntimeError(
                        "pre-child failure cannot claim a child process outcome"
                    )
            else:
                if (
                    isinstance(observed_child, bool)
                    or type(observed_child) is not int
                    or observed_child <= 0
                ):
                    raise RuntimeError(
                        "parent terminal child process identity is invalid"
                    )
                if has_bound and observed_child != value["child_process_id"]:
                    raise RuntimeError(
                        "parent terminal child process identity changed"
                    )
                if failed_stage == "CHILD_EXIT_BEFORE_CONSUMPTION":
                    if isinstance(child_returncode, bool) or type(
                        child_returncode
                    ) is not int:
                        raise RuntimeError("parent terminal return code is invalid")
                    expected_signal = (
                        -child_returncode if child_returncode < 0 else None
                    )
                    if (
                        (expected_signal is None and child_signal is not None)
                        or (
                            expected_signal is not None
                            and (
                                isinstance(child_signal, bool)
                                or type(child_signal) is not int
                                or child_signal != expected_signal
                            )
                        )
                    ):
                        raise RuntimeError(
                            "parent terminal child signal is inconsistent"
                        )
                elif child_returncode is not None or child_signal is not None:
                    raise RuntimeError(
                        "non-exit parent terminal cannot claim a return code"
                    )
        elif owner == "PARENT_REAPER":
            if (
                value.get("state") != "FAILURE"
                or value.get("failed_stage")
                != "CHILD_EXIT_AFTER_CONSUMPTION_NO_RUN"
            ):
                raise RuntimeError("parent-reaper launch stage is invalid")
            observed_child = value.get("observed_child_process_id")
            child_returncode = value.get("child_returncode")
            child_signal = value.get("child_signal")
            expected_signal = (
                -child_returncode
                if type(child_returncode) is int
                and not isinstance(child_returncode, bool)
                and child_returncode < 0
                else None
            )
            if (
                isinstance(observed_child, bool)
                or type(observed_child) is not int
                or observed_child != value["child_process_id"]
                or isinstance(child_returncode, bool)
                or type(child_returncode) is not int
                or (expected_signal is None and child_signal is not None)
                or (
                    expected_signal is not None
                    and (
                        isinstance(child_signal, bool)
                        or type(child_signal) is not int
                        or child_signal != expected_signal
                    )
                )
            ):
                raise RuntimeError(
                    "parent-reaper child exit observation is invalid"
                )
        else:
            if terminal_process_id != value["child_process_id"]:
                raise RuntimeError("terminal launch is not owned by its child")
            if value.get("failed_stage") != "PRE_RUN_RESERVATION":
                raise RuntimeError("child launch failure stage is invalid")
        if type(value.get("error_type")) is not str or not value["error_type"]:
            raise RuntimeError("terminal launch error type is invalid")
        if type(value.get("error_message")) is not str:
            raise RuntimeError("terminal launch error message is invalid")
        failed_unix_ns = value.get("failed_unix_ns")
        previous = (
            issued
            if previous_state == "ISSUED"
            else bound
            if previous_state == "BOUND"
            else consumed
        )
        previous_receipt_name = {
            "ISSUED": "issued_receipt_sha256",
            "BOUND": "bound_receipt_sha256",
            "CONSUMED": "consumed_receipt_sha256",
        }[previous_state]
        previous_receipt = _lower_sha256(
            value.get("previous_receipt_sha256"),
            name="previous_receipt_sha256",
        )
        if previous_receipt != previous[previous_receipt_name]:
            raise RuntimeError("terminal launch previous receipt changed")
        previous_timestamp = {
            "ISSUED": issued_ns,
            "BOUND": value.get("bound_unix_ns"),
            "CONSUMED": value.get("consumed_unix_ns"),
        }[previous_state]
        if (
            isinstance(failed_unix_ns, bool)
            or type(failed_unix_ns) is not int
            or failed_unix_ns < previous_timestamp
        ):
            raise RuntimeError("terminal launch timestamp is invalid")
        terminal = dict(previous)
        terminal.update(
            {
                "state": state,
                "terminal_owner": owner,
                "terminal_process_id": terminal_process_id,
                "previous_state": previous_state,
                "previous_receipt_sha256": previous_receipt,
                "failed_stage": value["failed_stage"],
                "error_type": value["error_type"],
                "error_message": value["error_message"],
                "failed_unix_ns": failed_unix_ns,
            }
        )
        if owner in ("PARENT", "PARENT_REAPER"):
            terminal.update(
                {
                    "observed_child_process_id": value[
                        "observed_child_process_id"
                    ],
                    "child_returncode": value["child_returncode"],
                    "child_signal": value["child_signal"],
                }
            )
        terminal_receipt = _lower_sha256(
            value.get("terminal_receipt_sha256"),
            name="terminal_receipt_sha256",
        )
        if _sha256_json(terminal) != terminal_receipt:
            raise RuntimeError("terminal launch receipt digest is inconsistent")
        if has_exit_observation:
            if not (
                (
                    owner == "PARENT"
                    and value["failed_stage"]
                    in ("BIND", "TOKEN_DELIVERY", "CHILD_WAIT")
                )
                or (
                    owner == "CHILD"
                    and value["failed_stage"] == "PRE_RUN_RESERVATION"
                )
            ):
                raise RuntimeError(
                    "parent exit observation follows an invalid failure stage"
                )
            observation_previous = _lower_sha256(
                value.get("exit_observation_previous_receipt_sha256"),
                name="exit_observation_previous_receipt_sha256",
            )
            if observation_previous != terminal_receipt:
                raise RuntimeError(
                    "parent exit observation changed its terminal receipt"
                )
            exit_observed_unix_ns = value.get("exit_observed_unix_ns")
            exit_returncode = value.get("exit_child_returncode")
            exit_signal = value.get("exit_child_signal")
            expected_exit_signal = (
                -exit_returncode
                if type(exit_returncode) is int
                and not isinstance(exit_returncode, bool)
                and exit_returncode < 0
                else None
            )
            if (
                isinstance(exit_observed_unix_ns, bool)
                or type(exit_observed_unix_ns) is not int
                or exit_observed_unix_ns < failed_unix_ns
                or isinstance(exit_returncode, bool)
                or type(exit_returncode) is not int
                or (expected_exit_signal is None and exit_signal is not None)
                or (
                    expected_exit_signal is not None
                    and (
                        isinstance(exit_signal, bool)
                        or type(exit_signal) is not int
                        or exit_signal != expected_exit_signal
                    )
                )
            ):
                raise RuntimeError("parent exit observation is invalid")
            observation = dict(terminal)
            observation["terminal_receipt_sha256"] = terminal_receipt
            observation.update(
                {
                    "exit_observation_previous_receipt_sha256": (
                        observation_previous
                    ),
                    "exit_observed_unix_ns": exit_observed_unix_ns,
                    "exit_child_returncode": exit_returncode,
                    "exit_child_signal": exit_signal,
                }
            )
            observation_receipt = _lower_sha256(
                value.get("exit_observation_receipt_sha256"),
                name="exit_observation_receipt_sha256",
            )
            if _sha256_json(observation) != observation_receipt:
                raise RuntimeError(
                    "parent exit observation receipt is inconsistent"
                )
    return value


def _issue_launch_authorization(
    ledger_directory: Path,
    request: "FrozenAssociationSampledRunRequest",
    worker_token_sha256: object,
) -> str:
    """Durably authorize one coordinate before the child process exists."""

    if type(request) is not FrozenAssociationSampledRunRequest:
        raise TypeError("launch authorization requires an exact request")
    directory = _absolute_without_symlink_resolution(ledger_directory)
    token = _lower_sha256(worker_token_sha256, name="worker_token_sha256")
    identity = {
        "schema": _LAUNCH_AUTHORIZATION_SCHEMA,
        "request": asdict(request),
        "ledger_directory": str(directory),
        "parent_process_id": os.getpid(),
        "worker_token_sha256": token,
        "issued_unix_ns": time.time_ns(),
    }
    authorization_sha256 = _sha256_json(identity)
    issued = {
        **identity,
        "state": "ISSUED",
        "launch_authorization_sha256": authorization_sha256,
    }
    issued["issued_receipt_sha256"] = _sha256_json(issued)
    _validated_launch_authorization_record(issued)
    write_attempted = False
    try:
        with _locked_ledger(directory) as (path, ledger):
            authorizations = ledger["launch_authorizations"]
            if any(
                value.get("request") == asdict(request)
                for value in authorizations.values()
                if isinstance(value, dict)
            ):
                raise RuntimeError(
                    "sampled coordinate already has a launch authorization"
                )
            if authorization_sha256 in authorizations:
                raise RuntimeError("launch authorization identity already exists")
            authorizations[authorization_sha256] = issued
            write_attempted = True
            _atomic_write_json(path, ledger)
    except BaseException as issue_error:
        if write_attempted:
            try:
                with _locked_ledger(directory) as (_, ledger):
                    durable = ledger["launch_authorizations"].get(
                        authorization_sha256
                    )
                if durable is not None:
                    if _validated_launch_authorization_record(durable) != issued:
                        raise RuntimeError(
                            "ambiguous launch issuance differs from its preimage"
                        )
                    _terminalize_parent_launch_preserving_primary(
                        issue_error,
                        "issue-commit recovery",
                        directory,
                        authorization_sha256,
                        request,
                        failed_stage="ISSUE_COMMIT",
                        state=(
                            "HOLD"
                            if isinstance(
                                issue_error, (KeyboardInterrupt, SystemExit)
                            )
                            else "FAILURE"
                        ),
                    )
            except BaseException as recovery_error:
                issue_error.add_note(
                    "ambiguous launch issuance recovery also failed: %r"
                    % recovery_error
                )
        raise
    return authorization_sha256


def _bind_launch_authorization_child(
    ledger_directory: Path,
    launch_authorization_sha256: object,
    child_process_id: object,
) -> str:
    """Bind the already-issued authorization to the actual ``Popen`` PID."""

    authorization = _lower_sha256(
        launch_authorization_sha256, name="launch_authorization_sha256"
    )
    if (
        isinstance(child_process_id, bool)
        or type(child_process_id) is not int
        or child_process_id <= 0
    ):
        raise ValueError("child_process_id must be a positive integer")
    directory = _absolute_without_symlink_resolution(ledger_directory)
    with _locked_ledger(directory) as (path, ledger):
        issued = _validated_launch_authorization_record(
            ledger["launch_authorizations"].get(authorization)
        )
        if issued["state"] != "ISSUED" or issued["parent_process_id"] != os.getpid():
            raise RuntimeError("launch authorization is not parent-bindable")
        bound = dict(issued)
        bound.update(
            {
                "state": "BOUND",
                "child_process_id": child_process_id,
                "bound_unix_ns": time.time_ns(),
            }
        )
        bound["bound_receipt_sha256"] = _sha256_json(bound)
        _validated_launch_authorization_record(bound)
        ledger["launch_authorizations"][authorization] = bound
        _atomic_write_json(path, ledger)
    return bound["bound_receipt_sha256"]


def _terminalize_parent_launch_authorization(
    ledger_directory: Path,
    launch_authorization_sha256: object,
    request: "FrozenAssociationSampledRunRequest",
    *,
    failed_stage: object,
    error: BaseException,
    state: str = "FAILURE",
    observed_child_process_id: Optional[int] = None,
    child_returncode: Optional[int] = None,
) -> dict:
    """Terminalize only an unconsumed launch owned by this parent process.

    A CONSUMED launch, a child-owned terminal receipt, or any associated run is
    observed but never overwritten.  Re-observing a parent terminal receipt is
    idempotent and returns the already durable record.
    """

    authorization = _lower_sha256(
        launch_authorization_sha256, name="launch_authorization_sha256"
    )
    if type(request) is not FrozenAssociationSampledRunRequest:
        raise TypeError("parent launch terminalization requires an exact request")
    if type(failed_stage) is not str or failed_stage not in (
        _PARENT_LAUNCH_FAILURE_STAGES
    ):
        raise ValueError("parent launch failure stage is invalid")
    if not isinstance(error, BaseException):
        raise TypeError("parent launch terminalization requires an exception")
    if type(state) is not str or state not in ("FAILURE", "HOLD"):
        raise ValueError("parent launch terminal state must be FAILURE or HOLD")
    if observed_child_process_id is not None and (
        isinstance(observed_child_process_id, bool)
        or type(observed_child_process_id) is not int
        or observed_child_process_id <= 0
    ):
        raise ValueError("observed_child_process_id must be positive or None")
    if child_returncode is not None and (
        isinstance(child_returncode, bool) or type(child_returncode) is not int
    ):
        raise TypeError("child_returncode must be an integer or None")
    directory = _absolute_without_symlink_resolution(ledger_directory)
    with _locked_ledger(directory) as (path, ledger):
        current = _validated_launch_authorization_record(
            ledger["launch_authorizations"].get(authorization)
        )
        if (
            current["launch_authorization_sha256"] != authorization
            or current["request"] != asdict(request)
            or current["ledger_directory"] != str(directory)
            or current["parent_process_id"] != os.getpid()
        ):
            raise RuntimeError(
                "parent launch terminalization does not own this authorization"
            )
        associated_run = any(
            type(run) is dict
            and type(run.get("worker_session")) is dict
            and run["worker_session"].get(
                "launch_authorization_sha256"
            )
            == authorization
            for run in ledger["runs"].values()
        )
        if current["state"] == "CONSUMED" or (
            current["state"] in ("FAILURE", "HOLD")
            and current.get("terminal_owner") == "CHILD"
        ):
            return current
        if current["state"] in ("FAILURE", "HOLD"):
            if current.get("terminal_owner") not in (
                "PARENT",
                "PARENT_REAPER",
            ):
                raise RuntimeError("launch terminal ownership is invalid")
            return current
        if associated_run:
            raise RuntimeError(
                "parent cannot terminalize launch after run custody exists"
            )
        if current["state"] not in ("ISSUED", "BOUND"):
            raise RuntimeError("parent launch is not terminalizable")
        previous_state = current["state"]
        previous_receipt_name = {
            "ISSUED": "issued_receipt_sha256",
            "BOUND": "bound_receipt_sha256",
        }[previous_state]
        terminal = dict(current)
        terminal.update(
            {
                "state": state,
                "terminal_owner": "PARENT",
                "terminal_process_id": os.getpid(),
                "previous_state": previous_state,
                "previous_receipt_sha256": current[previous_receipt_name],
                "failed_stage": failed_stage,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "failed_unix_ns": time.time_ns(),
                "observed_child_process_id": observed_child_process_id,
                "child_returncode": child_returncode,
                "child_signal": (
                    -child_returncode
                    if child_returncode is not None and child_returncode < 0
                    else None
                ),
            }
        )
        terminal["terminal_receipt_sha256"] = _sha256_json(terminal)
        _validated_launch_authorization_record(terminal)
        ledger["launch_authorizations"][authorization] = terminal
        _atomic_write_json(path, ledger)
        return terminal


def _terminalize_parent_launch_preserving_primary(
    primary_error: BaseException,
    label: str,
    ledger_directory: Path,
    launch_authorization_sha256: str,
    request: "FrozenAssociationSampledRunRequest",
    *,
    failed_stage: str,
    state: str,
    observed_child_process_id: Optional[int] = None,
    child_returncode: Optional[int] = None,
) -> Optional[dict]:
    """Retry parent terminalization without replacing its primary error."""

    for attempt in (1, 2):
        try:
            return _terminalize_parent_launch_authorization(
                ledger_directory,
                launch_authorization_sha256,
                request,
                failed_stage=failed_stage,
                error=primary_error,
                state=state,
                observed_child_process_id=observed_child_process_id,
                child_returncode=child_returncode,
            )
        except BaseException as terminalization_error:
            primary_error.add_note(
                "%s launch-terminalization attempt %d failed: %r"
                % (label, attempt, terminalization_error)
            )
    try:
        directory = _absolute_without_symlink_resolution(ledger_directory)
        with _locked_ledger(directory) as (_, ledger):
            current = _validated_launch_authorization_record(
                ledger["launch_authorizations"].get(
                    launch_authorization_sha256
                )
            )
        if (
            current["launch_authorization_sha256"]
            != launch_authorization_sha256
            or current["request"] != asdict(request)
            or current["ledger_directory"] != str(directory)
            or current["parent_process_id"] != os.getpid()
            or current["state"]
            not in ("CONSUMED", "FAILURE", "HOLD")
        ):
            raise RuntimeError(
                "launch remains outside consumed or terminal custody"
            )
        return current
    except BaseException as verification_error:
        primary_error.add_note(
            "%s durable launch-terminal verification failed: %r"
            % (label, verification_error)
        )
        return None


def _record_parent_launch_exit_observation(
    ledger_directory: Path,
    launch_authorization_sha256: object,
    request: "FrozenAssociationSampledRunRequest",
    *,
    child_process_id: object,
    child_returncode: object,
) -> dict:
    """Append a second receipt after cleanup observes a parent's child exit.

    The first terminal receipt remains the digest of the original launch
    failure.  This observation chains from that immutable digest and records
    only the later return-code/signal evidence.
    """

    authorization = _lower_sha256(
        launch_authorization_sha256, name="launch_authorization_sha256"
    )
    if type(request) is not FrozenAssociationSampledRunRequest:
        raise TypeError("parent exit observation requires an exact request")
    if (
        isinstance(child_process_id, bool)
        or type(child_process_id) is not int
        or child_process_id <= 0
    ):
        raise ValueError("child_process_id must be a positive integer")
    if isinstance(child_returncode, bool) or type(child_returncode) is not int:
        raise TypeError("child_returncode must be an integer")
    directory = _absolute_without_symlink_resolution(ledger_directory)
    with _locked_ledger(directory) as (path, ledger):
        current = _validated_launch_authorization_record(
            ledger["launch_authorizations"].get(authorization)
        )
        if (
            current["launch_authorization_sha256"] != authorization
            or current["request"] != asdict(request)
            or current["ledger_directory"] != str(directory)
            or current["parent_process_id"] != os.getpid()
        ):
            raise RuntimeError("parent exit observation lacks launch ownership")
        owner = current.get("terminal_owner")
        eligible_parent_terminal = (
            owner == "PARENT"
            and current.get("failed_stage")
            in ("BIND", "TOKEN_DELIVERY", "CHILD_WAIT")
            and current.get("observed_child_process_id") == child_process_id
        )
        eligible_child_terminal = (
            owner == "CHILD"
            and current.get("failed_stage") == "PRE_RUN_RESERVATION"
            and current.get("child_process_id") == child_process_id
            and current.get("terminal_process_id") == child_process_id
        )
        if not (eligible_parent_terminal or eligible_child_terminal):
            raise RuntimeError(
                "parent exit observation does not follow an eligible terminal"
            )
        associated_run = any(
            type(run) is dict
            and type(run.get("worker_session")) is dict
            and run["worker_session"].get(
                "launch_authorization_sha256"
            )
            == authorization
            for run in ledger["runs"].values()
        )
        if associated_run:
            raise RuntimeError(
                "parent exit observation cannot replace durable run custody"
            )
        if "exit_observation_receipt_sha256" in current:
            if (
                current["exit_child_returncode"] != child_returncode
                or current["exit_child_signal"]
                != (-child_returncode if child_returncode < 0 else None)
            ):
                raise RuntimeError("parent exit observation changed on retry")
            return current
        observed = dict(current)
        observed.update(
            {
                "exit_observation_previous_receipt_sha256": current[
                    "terminal_receipt_sha256"
                ],
                "exit_observed_unix_ns": time.time_ns(),
                "exit_child_returncode": child_returncode,
                "exit_child_signal": (
                    -child_returncode if child_returncode < 0 else None
                ),
            }
        )
        observed["exit_observation_receipt_sha256"] = _sha256_json(observed)
        _validated_launch_authorization_record(observed)
        ledger["launch_authorizations"][authorization] = observed
        _atomic_write_json(path, ledger)
        return observed


def _consume_launch_authorization(
    ledger_directory: Path,
    launch_authorization_sha256: object,
    request: "FrozenAssociationSampledRunRequest",
    worker_token_sha256: object,
) -> dict:
    """Atomically consume the parent/PID/token/request authorization in child."""

    authorization = _lower_sha256(
        launch_authorization_sha256, name="launch_authorization_sha256"
    )
    token = _lower_sha256(worker_token_sha256, name="worker_token_sha256")
    if type(request) is not FrozenAssociationSampledRunRequest:
        raise TypeError("launch consumption requires an exact request")
    directory = _absolute_without_symlink_resolution(ledger_directory)
    with _locked_ledger(directory) as (path, ledger):
        bound = _validated_launch_authorization_record(
            ledger["launch_authorizations"].get(authorization)
        )
        if (
            bound["state"] != "BOUND"
            or bound["request"] != asdict(request)
            or bound["ledger_directory"] != str(directory)
            or bound["worker_token_sha256"] != token
            or bound["parent_process_id"] != os.getppid()
            or bound["child_process_id"] != os.getpid()
        ):
            raise RuntimeError("launch authorization does not admit this child")
        consumed = dict(bound)
        consumed.update(
            {"state": "CONSUMED", "consumed_unix_ns": time.time_ns()}
        )
        consumed["consumed_receipt_sha256"] = _sha256_json(consumed)
        _validated_launch_authorization_record(consumed)
        ledger["launch_authorizations"][authorization] = consumed
        _atomic_write_json(path, ledger)
    return consumed


def _terminalize_sampled_worker_failure(
    directory: Path,
    worker_session: object,
    error: BaseException,
    *,
    run_key: Optional[str] = None,
    total_wall_start: Optional[float] = None,
    total_cpu_start: Optional[float] = None,
) -> dict:
    """Close either the owned run or its consumed pre-reservation launch."""

    if type(worker_session) is not _FrozenAssociationWorkerSession:
        raise TypeError("worker failure custody requires its exact session")
    if not isinstance(error, BaseException):
        raise TypeError("worker failure custody requires an exception")
    worker_session.validate_current_process()
    checked_run_key = (
        None
        if run_key is None
        else _lower_sha256(run_key, name="run_key_sha256")
    )
    state = (
        "HOLD"
        if type(error).__name__ == "ContinuousCorrectionCertificateError"
        else "FAILURE"
    )
    wall_start = (
        time.perf_counter()
        if total_wall_start is None
        else float(total_wall_start)
    )
    cpu_start = (
        time.process_time()
        if total_cpu_start is None
        else float(total_cpu_start)
    )
    with _locked_ledger(directory) as (path, ledger):
        owned = [
            (key, record)
            for key, record in ledger["runs"].items()
            if type(record) is dict
            and record.get("worker_session") == worker_session.record
        ]
        if len(owned) > 1:
            raise RuntimeError("one sampled worker session owns multiple runs")
        owned_key = None if not owned else owned[0][0]
        existing = None if not owned else owned[0][1]
        if (
            checked_run_key is not None
            and owned_key is not None
            and checked_run_key != owned_key
        ):
            raise RuntimeError("sampled worker failure run key changed")
        if existing is not None:
            if (
                existing.get("worker_session") != worker_session.record
                or existing.get("worker_pid") != worker_session.record["worker_pid"]
                or existing.get("worker_session_run_sha256")
                != _worker_session_run_sha256(
                    worker_session.session_sha256, owned_key
                )
            ):
                raise RuntimeError(
                    "sampled worker cannot terminalize another session's run"
                )
            if existing.get("state") in _TERMINAL_STATES:
                return existing
            if existing.get("state") not in ("RESERVED", "PREPARED", "RUNNING"):
                raise RuntimeError("sampled worker failure stage is invalid")
            previous_state = existing["state"]
            previous_receipt = _active_run_receipt_sha256(existing)
            terminal = dict(existing)
            terminal.update(
                {
                    "state": state,
                    "terminal_owner": "CHILD",
                    "terminal_process_id": os.getpid(),
                    "previous_state": previous_state,
                    "previous_ledger_sha256": previous_receipt,
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                    "failed_stage": previous_state,
                    "failure_total_wall_seconds": max(
                        0.0, time.perf_counter() - wall_start
                    ),
                    "failure_total_cpu_seconds": max(
                        0.0, time.process_time() - cpu_start
                    ),
                    "failure_process_peak_rss_bytes": _peak_rss_bytes(),
                    "failed_unix_ns": time.time_ns(),
                }
            )
            terminal["terminal_ledger_sha256"] = _sha256_json(terminal)
            launch = ledger["launch_authorizations"].get(
                worker_session.record["launch_authorization_sha256"]
            )
            _validated_terminal_run_record(owned_key, terminal, launch)
            ledger["runs"][owned_key] = terminal
            _atomic_write_json(path, ledger)
            return terminal

        launch_key = worker_session.record["launch_authorization_sha256"]
        consumed = _validated_launch_authorization_record(
            ledger["launch_authorizations"].get(launch_key)
        )
        if (
            consumed["state"] != "CONSUMED"
            or consumed["consumed_receipt_sha256"]
            != worker_session.record["launch_receipt_sha256"]
            or consumed["child_process_id"]
            != worker_session.record["worker_pid"]
            or consumed["parent_process_id"]
            != worker_session.record["worker_parent_pid"]
            or consumed["worker_token_sha256"]
            != worker_session.record["worker_token_sha256"]
            or consumed["ledger_directory"] != str(directory.resolve())
        ):
            raise RuntimeError(
                "sampled worker session differs from consumed launch custody"
            )
        terminal = dict(consumed)
        terminal.update(
            {
                "state": state,
                "terminal_owner": "CHILD",
                "terminal_process_id": os.getpid(),
                "previous_state": "CONSUMED",
                "previous_receipt_sha256": consumed[
                    "consumed_receipt_sha256"
                ],
                "failed_stage": "PRE_RUN_RESERVATION",
                "error_type": type(error).__name__,
                "error_message": str(error),
                "failed_unix_ns": time.time_ns(),
            }
        )
        terminal["terminal_receipt_sha256"] = _sha256_json(terminal)
        _validated_launch_authorization_record(terminal)
        ledger["launch_authorizations"][launch_key] = terminal
        _atomic_write_json(path, ledger)
        return terminal


def _validated_worker_session_record(value: object) -> dict:
    """Validate the durable marker emitted by the launcher handshake.

    This is an API/process-custody control under a non-hostile-host threat
    model.  It is deliberately not represented as authentication against a
    user who owns the Python process or campaign filesystem.
    """

    expected = {
        "schema",
        "worker_pid",
        "worker_parent_pid",
        "worker_token_sha256",
        "launch_authorization_sha256",
        "launch_receipt_sha256",
        "isolated_worker_execution_eligible",
        "session_sha256",
    }
    if type(value) is not dict or set(value) != expected:
        raise RuntimeError("worker session record has an invalid exact schema")
    if value.get("schema") != _WORKER_SESSION_SCHEMA:
        raise RuntimeError("worker session record has an invalid schema")
    for name in ("worker_pid", "worker_parent_pid"):
        raw = value.get(name)
        if isinstance(raw, bool) or type(raw) is not int or raw <= 0:
            raise RuntimeError("worker session process identifiers are invalid")
    _lower_sha256(value.get("worker_token_sha256"), name="worker_token_sha256")
    _lower_sha256(
        value.get("launch_authorization_sha256"),
        name="launch_authorization_sha256",
    )
    _lower_sha256(
        value.get("launch_receipt_sha256"), name="launch_receipt_sha256"
    )
    if value.get("isolated_worker_execution_eligible") is not True:
        raise RuntimeError(
            "worker session is not isolated-worker execution eligible"
        )
    claimed = _lower_sha256(value.get("session_sha256"), name="session_sha256")
    body = dict(value)
    body.pop("session_sha256")
    if _sha256_json(body) != claimed:
        raise RuntimeError("worker session digest is inconsistent")
    return value


def _validated_optimizer_completion_receipt_record(value: object) -> dict:
    """Validate the executor-emitted completion receipt's exact preimage.

    The receipt is a custody/API control, not authentication against a user
    who owns the process.  Production SUCCESS additionally requires the
    live, single-use completion capability returned by the optimizer executor.
    """

    if type(value) is not dict or set(value) != _OPTIMIZER_COMPLETION_FIELDS:
        raise RuntimeError(
            "optimizer completion receipt has an invalid exact schema"
        )
    if value.get("schema") != _OPTIMIZER_COMPLETION_SCHEMA:
        raise RuntimeError("optimizer completion receipt schema is invalid")
    request = FrozenAssociationSampledRunRequest(
        value.get("seed"), value.get("budget"), value.get("method")
    )
    expected_steps = value.get("expected_optimizer_steps")
    observed_steps = value.get("observed_optimizer_steps")
    if (
        isinstance(expected_steps, bool)
        or type(expected_steps) is not int
        or isinstance(observed_steps, bool)
        or type(observed_steps) is not int
        or expected_steps != _METHOD_UPDATES[request.method]
        or observed_steps != expected_steps
    ):
        raise RuntimeError(
            "optimizer completion receipt has an invalid step count"
        )
    for name in (
        "run_key_sha256",
        "campaign_sha256",
        "preflight_sha256",
        "prepared_ledger_sha256",
        "running_ledger_sha256",
        "execution_runtime_sha256",
        "worker_session_sha256",
        "optimizer_transcript_sha256",
        "initial_parameter_sha256",
        "last_post_update_parameter_sha256",
        "final_parameter_sha256",
        "certificate_sha256",
        "classifier_sha256",
        "resource_sha256",
        "checkpoint_identity_sha256",
    ):
        _lower_sha256(value.get(name), name=name)
    if (
        value["last_post_update_parameter_sha256"]
        != value["final_parameter_sha256"]
    ):
        raise RuntimeError(
            "optimizer completion final parameters differ from its last update"
        )
    claimed = _lower_sha256(
        value.get("completion_receipt_sha256"),
        name="completion_receipt_sha256",
    )
    body = dict(value)
    body.pop("completion_receipt_sha256")
    if _sha256_json(body) != claimed:
        raise RuntimeError("optimizer completion receipt digest is inconsistent")
    return value


def _canonical_sampled_coordinates() -> Tuple[Tuple[int, int, str], ...]:
    return tuple(
        (seed, budget, method)
        for seed in _SEEDS
        for budget in _BUDGETS
        for method in _METHODS
    )


def _coordinate_manifest_sha256() -> str:
    return _sha256_json(
        {
            "schema": "heterodiff-a1-sampled-coordinate-manifest-v1",
            "coordinates": [
                {"seed": seed, "budget": budget, "method": method}
                for seed, budget, method in _canonical_sampled_coordinates()
            ],
        }
    )


def _aggregate_resource_receipt_sha256(resources: dict) -> str:
    return _sha256_json(
        {
            "schema": "heterodiff-a1-sampled-member-resources-v1",
            "resources": resources,
        }
    )


def _worker_process_identity_sha256(session: dict) -> str:
    """Bind one child process identity to its unique launch/session custody."""

    return _sha256_json(
        {
            "schema": "heterodiff-a1-sampled-worker-process-identity-v1",
            "worker_process_id": session["worker_pid"],
            "worker_parent_process_id": session["worker_parent_pid"],
            "worker_session_sha256": session["session_sha256"],
            "launch_authorization_sha256": session[
                "launch_authorization_sha256"
            ],
            "launch_receipt_sha256": session["launch_receipt_sha256"],
        }
    )


def _validated_aggregate_record(value: object) -> dict:
    """Validate the durable custody-only sampled aggregate receipt."""

    if type(value) is not dict or set(value) != _AGGREGATE_FIELDS:
        raise RuntimeError("sampled aggregate has an invalid exact schema")
    if value.get("schema") != _AGGREGATE_SCHEMA:
        raise RuntimeError("sampled aggregate schema is invalid")
    _lower_sha256(value.get("campaign_sha256"), name="campaign_sha256")
    if value.get("coordinate_manifest_sha256") != _coordinate_manifest_sha256():
        raise RuntimeError("sampled aggregate coordinate manifest changed")
    members = value.get("ordered_success_receipts")
    coordinates = _canonical_sampled_coordinates()
    if type(members) is not list or len(members) != len(coordinates):
        raise RuntimeError("sampled aggregate does not contain 120 members")
    uniqueness = {
        name: set()
        for name in (
            "run_key_sha256",
            "success_ledger_sha256",
            "exit_observation_receipt_sha256",
            "worker_process_identity_sha256",
            "worker_session_sha256",
            "launch_authorization_sha256",
            "launch_receipt_sha256",
            "optimizer_completion_receipt_sha256",
        )
    }
    step_total = 0
    resource_rows = []
    for ordinal, (member, coordinate) in enumerate(zip(members, coordinates)):
        if type(member) is not dict or set(member) != _AGGREGATE_MEMBER_FIELDS:
            raise RuntimeError("sampled aggregate member schema is invalid")
        if (
            member.get("ordinal") != ordinal
            or (
                member.get("seed"),
                member.get("budget"),
                member.get("method"),
            )
            != coordinate
        ):
            raise RuntimeError("sampled aggregate member order is not canonical")
        FrozenAssociationSampledRunRequest(*coordinate)
        for name in (
            "run_key_sha256",
            "preflight_sha256",
            "prepared_ledger_sha256",
            "running_ledger_sha256",
            "success_ledger_sha256",
            "exit_observation_receipt_sha256",
            "worker_process_identity_sha256",
            "worker_session_sha256",
            "launch_authorization_sha256",
            "launch_receipt_sha256",
            "execution_runtime_sha256",
            "campaign_sha256",
            "optimizer_completion_receipt_sha256",
            "checkpoint_sha256",
            "classifier_sha256",
            "parameter_sha256",
            "certificate_sha256",
            "optimizer_transcript_sha256",
            "resource_receipt_sha256",
        ):
            _lower_sha256(member.get(name), name=name)
        worker_process_id = member.get("worker_process_id")
        worker_parent_process_id = member.get("worker_parent_process_id")
        if (
            isinstance(worker_process_id, bool)
            or type(worker_process_id) is not int
            or worker_process_id <= 0
            or isinstance(worker_parent_process_id, bool)
            or type(worker_parent_process_id) is not int
            or worker_parent_process_id <= 0
        ):
            raise RuntimeError("sampled aggregate worker process identity is invalid")
        process_identity = {
            "worker_pid": worker_process_id,
            "worker_parent_pid": worker_parent_process_id,
            "session_sha256": member["worker_session_sha256"],
            "launch_authorization_sha256": member[
                "launch_authorization_sha256"
            ],
            "launch_receipt_sha256": member["launch_receipt_sha256"],
        }
        if member["worker_process_identity_sha256"] != (
            _worker_process_identity_sha256(process_identity)
        ):
            raise RuntimeError("sampled aggregate worker process binding changed")
        if member["campaign_sha256"] != value["campaign_sha256"]:
            raise RuntimeError("sampled aggregate member changed campaign")
        for name, observed in uniqueness.items():
            item = member[name]
            if item in observed:
                raise RuntimeError(
                    "sampled aggregate reuses %s" % name
                )
            observed.add(item)
        steps = member.get("optimizer_steps_taken")
        if (
            isinstance(steps, bool)
            or type(steps) is not int
            or steps != _METHOD_UPDATES[coordinate[2]]
        ):
            raise RuntimeError("sampled aggregate optimizer steps are invalid")
        step_total += steps
        resources = member.get("resources")
        expected_resource_fields = {
            "preparation_cpu_seconds",
            "preparation_wall_seconds",
            "optimizer_wall_seconds",
            "total_cpu_seconds",
            "total_wall_seconds",
            "process_peak_rss_bytes",
        }
        if type(resources) is not dict or set(resources) != expected_resource_fields:
            raise RuntimeError("sampled aggregate member resources are invalid")
        for name in expected_resource_fields - {"process_peak_rss_bytes"}:
            raw = resources[name]
            if (
                isinstance(raw, bool)
                or not isinstance(raw, (int, float))
                or not math.isfinite(float(raw))
                or float(raw) < 0.0
            ):
                raise RuntimeError("sampled aggregate resource is invalid")
        peak = resources["process_peak_rss_bytes"]
        if isinstance(peak, bool) or type(peak) is not int or peak <= 0:
            raise RuntimeError("sampled aggregate peak RSS is invalid")
        if (
            float(resources["preparation_cpu_seconds"])
            > float(resources["total_cpu_seconds"]) + 1.0e-9
            or float(resources["preparation_wall_seconds"])
            + float(resources["optimizer_wall_seconds"])
            > float(resources["total_wall_seconds"]) + 1.0e-9
            or member["resource_receipt_sha256"]
            != _aggregate_resource_receipt_sha256(resources)
        ):
            raise RuntimeError("sampled aggregate resource nesting is invalid")
        completed = member.get("completed_unix_ns")
        if isinstance(completed, bool) or type(completed) is not int or completed <= 0:
            raise RuntimeError("sampled aggregate completion timestamp is invalid")
        resource_rows.append(resources)
    if step_total != _EXPECTED_TOTAL_OPTIMIZER_STEPS:
        raise RuntimeError("sampled aggregate optimizer total is not 396000")
    receipts_digest = _sha256_json(
        {
            "schema": "heterodiff-a1-sampled-ordered-success-receipts-v1",
            "receipts": members,
        }
    )
    if value.get("ordered_success_receipts_sha256") != receipts_digest:
        raise RuntimeError("sampled aggregate ordered receipt digest changed")
    checkpoint_digest = _sha256_json(
        {
            "schema": "heterodiff-a1-sampled-ordered-checkpoints-v1",
            "checkpoints": [
                {
                    "run_key_sha256": member["run_key_sha256"],
                    "checkpoint_sha256": member["checkpoint_sha256"],
                    "optimizer_completion_receipt_sha256": member[
                        "optimizer_completion_receipt_sha256"
                    ],
                }
                for member in members
            ],
        }
    )
    if value.get("ordered_checkpoint_sha256") != checkpoint_digest:
        raise RuntimeError("sampled aggregate ordered checkpoint digest changed")
    totals = value.get("resource_totals")
    expected_totals = {
        "coordinate_count": len(coordinates),
        "preparation_cpu_seconds": math.fsum(
            float(row["preparation_cpu_seconds"]) for row in resource_rows
        ),
        "preparation_wall_seconds": math.fsum(
            float(row["preparation_wall_seconds"]) for row in resource_rows
        ),
        "optimizer_wall_seconds": math.fsum(
            float(row["optimizer_wall_seconds"]) for row in resource_rows
        ),
        "total_cpu_seconds": math.fsum(
            float(row["total_cpu_seconds"]) for row in resource_rows
        ),
        "total_wall_seconds": math.fsum(
            float(row["total_wall_seconds"]) for row in resource_rows
        ),
        "maximum_process_peak_rss_bytes": max(
            row["process_peak_rss_bytes"] for row in resource_rows
        ),
    }
    if totals != expected_totals:
        raise RuntimeError("sampled aggregate resource totals are inconsistent")
    if (
        value.get("total_optimizer_steps_taken")
        != _EXPECTED_TOTAL_OPTIMIZER_STEPS
        or value.get("fresh_metric_recomputation_required") is not True
        or value.get("execution_order_attested") is not False
        or value.get("scientific_decision_eligible") is not False
    ):
        raise RuntimeError("sampled aggregate overstates its decision authority")
    body = dict(value)
    claimed = _lower_sha256(
        body.pop("aggregate_sha256"), name="aggregate_sha256"
    )
    if _sha256_json(body) != claimed:
        raise RuntimeError("sampled aggregate digest is inconsistent")
    return value


_WORKER_SESSION_CONSTRUCTION_KEY = object()


class _FrozenAssociationWorkerSession:
    """Opaque, process-bound result of the parent-to-worker pipe handshake."""

    __slots__ = ("_record", "_bound_run_key", "_locked")

    def __init__(self, record: object, *, _construction_key: object) -> None:
        if _construction_key is not _WORKER_SESSION_CONSTRUCTION_KEY:
            raise TypeError("worker sessions are created only by the pipe handshake")
        checked = dict(_validated_worker_session_record(record))
        if (
            checked["worker_pid"] != os.getpid()
            or checked["worker_parent_pid"] != os.getppid()
        ):
            raise RuntimeError("worker session belongs to another process")
        object.__setattr__(self, "_record", checked)
        object.__setattr__(self, "_bound_run_key", None)
        object.__setattr__(self, "_locked", True)

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_locked", False):
            raise AttributeError("worker session is immutable")
        object.__setattr__(self, name, value)

    @property
    def record(self) -> dict:
        return dict(self._record)

    @property
    def session_sha256(self) -> str:
        return self._record["session_sha256"]

    def validate_current_process(self) -> None:
        _validated_worker_session_record(self._record)
        if (
            self._record["worker_pid"] != os.getpid()
            or self._record["worker_parent_pid"] != os.getppid()
        ):
            raise RuntimeError("worker session is no longer in its issuing process")

    def bind_run(self, run_key_sha256: object) -> None:
        self.validate_current_process()
        run_key = _lower_sha256(run_key_sha256, name="run_key_sha256")
        if self._bound_run_key is not None:
            raise RuntimeError("worker session is already bound to one run key")
        object.__setattr__(self, "_bound_run_key", run_key)

    def validate_run(self, run_key_sha256: object) -> None:
        self.validate_current_process()
        run_key = _lower_sha256(run_key_sha256, name="run_key_sha256")
        if self._bound_run_key != run_key:
            raise RuntimeError("worker session is not bound to this run key")


def _worker_session_run_sha256(session_sha256: object, run_key_sha256: object) -> str:
    return _sha256_json(
        {
            "schema": "heterodiff-a1-worker-session-run-binding-v1",
            "session_sha256": _lower_sha256(
                session_sha256, name="session_sha256"
            ),
            "run_key_sha256": _lower_sha256(
                run_key_sha256, name="run_key_sha256"
            ),
        }
    )


@dataclass(frozen=True)
class FrozenAssociationSampledRunRequest:
    seed: int
    budget: int
    method: str

    def __post_init__(self) -> None:
        if isinstance(self.seed, bool) or type(self.seed) is not int:
            raise TypeError("seed must be an integer non-boolean value")
        if self.seed not in _SEEDS:
            raise ValueError("seed is not frozen")
        if isinstance(self.budget, bool) or type(self.budget) is not int:
            raise TypeError("budget must be an integer non-boolean value")
        if self.budget not in _BUDGETS:
            raise ValueError("budget is not frozen")
        if type(self.method) is not str or self.method not in _METHODS:
            raise ValueError("method is not frozen")


def frozen_association_worker_environment(
    base: Optional[Mapping[str, str]] = None,
) -> Dict[str, str]:
    """Return a child environment with limits set before numerical imports."""

    source = os.environ if base is None else base
    result = {str(key): str(value) for key, value in source.items()}
    for name in _THREAD_ENVIRONMENT:
        result[name] = "1"
    result["PYTHONHASHSEED"] = "0"
    result["CUDA_VISIBLE_DEVICES"] = ""
    return result


def _consume_parent_handshake(
    control_fd: object,
    token_sha256: object,
    *,
    request: FrozenAssociationSampledRunRequest,
    ledger_directory: Path,
    launch_authorization_sha256: object,
) -> _FrozenAssociationWorkerSession:
    if isinstance(control_fd, bool) or type(control_fd) is not int or control_fd < 3:
        raise RuntimeError("isolated worker control descriptor is invalid")
    expected = _lower_sha256(token_sha256, name="worker_token_sha256")
    payload = b""
    try:
        while len(payload) < 33:
            block = os.read(control_fd, 33 - len(payload))
            if not block:
                break
            payload += block
    except OSError as error:
        raise RuntimeError("isolated worker handshake could not be read") from error
    finally:
        try:
            os.close(control_fd)
        except OSError:
            pass
    if len(payload) != 32 or hashlib.sha256(payload).hexdigest() != expected:
        raise RuntimeError("isolated worker handshake is invalid")
    launch = _consume_launch_authorization(
        ledger_directory,
        launch_authorization_sha256,
        request,
        expected,
    )
    record = {
        "schema": _WORKER_SESSION_SCHEMA,
        "worker_pid": os.getpid(),
        "worker_parent_pid": os.getppid(),
        "worker_token_sha256": expected,
        "launch_authorization_sha256": launch[
            "launch_authorization_sha256"
        ],
        "launch_receipt_sha256": launch["consumed_receipt_sha256"],
        "isolated_worker_execution_eligible": True,
    }
    record["session_sha256"] = _sha256_json(record)
    return _FrozenAssociationWorkerSession(
        record, _construction_key=_WORKER_SESSION_CONSTRUCTION_KEY
    )


def frozen_association_campaign_directory() -> Path:
    """Return the one repository-local ledger location for this campaign."""

    return Path(__file__).resolve().parents[3] / "artifacts" / "a1_campaign_v4"


def _require_preimport_worker_environment() -> Dict[str, str]:
    observed = {name: os.environ.get(name) for name in _THREAD_ENVIRONMENT}
    if any(value != "1" for value in observed.values()):
        raise RuntimeError(
            "every BLAS/OpenMP thread variable must equal one before import"
        )
    if os.environ.get("PYTHONHASHSEED") != "0":
        raise RuntimeError("PYTHONHASHSEED must equal zero in the worker")
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "":
        raise RuntimeError("CUDA_VISIBLE_DEVICES must be empty in the CPU worker")
    result = {name: str(value) for name, value in observed.items()}
    result["PYTHONHASHSEED"] = "0"
    result["CUDA_VISIBLE_DEVICES"] = ""
    return result


def _validated_runtime_record(value: object) -> dict:
    expected_keys = {
        "schema",
        "python",
        "python_implementation",
        "numpy",
        "scipy",
        "torch",
        "threadpoolctl",
        "platform",
        "system",
        "release",
        "machine",
        "processor",
        "cpu_identity",
        "thread_environment",
        "native_pools",
        "numpy_configuration",
        "torch_environment",
        "sha256",
    }
    if type(value) is not dict or set(value) != expected_keys:
        raise RuntimeError("execution runtime has an invalid exact schema")
    if value.get("schema") != _RUNTIME_SCHEMA:
        raise RuntimeError("execution runtime schema is invalid")
    exact_versions = {
        "python": "3.11.5",
        "numpy": "2.4.6",
        "scipy": "1.17.1",
        "torch": "2.12.1",
        "threadpoolctl": "3.6.0",
    }
    if any(value.get(name) != wanted for name, wanted in exact_versions.items()):
        raise RuntimeError("execution runtime versions are not frozen")
    for name in (
        "python_implementation",
        "platform",
        "system",
        "release",
        "machine",
    ):
        if type(value.get(name)) is not str or not value[name]:
            raise RuntimeError("execution runtime platform metadata is incomplete")
    if type(value.get("processor")) is not str:
        raise RuntimeError("execution runtime processor metadata must be a string")
    if type(value.get("cpu_identity")) is not str or not value["cpu_identity"]:
        raise RuntimeError("execution runtime CPU identity is absent")
    expected_thread_environment = {
        **{name: "1" for name in _THREAD_ENVIRONMENT},
        "PYTHONHASHSEED": "0",
        "CUDA_VISIBLE_DEVICES": "",
    }
    if value.get("thread_environment") != expected_thread_environment:
        raise RuntimeError("execution runtime pre-import environment is not frozen")
    pools = value.get("native_pools")
    pool_keys = {"user_api", "internal_api", "prefix", "version", "num_threads"}
    if type(pools) is not list or not pools:
        raise RuntimeError("execution runtime has no native pool records")
    for pool in pools:
        if type(pool) is not dict or set(pool) != pool_keys:
            raise RuntimeError("native pool record has an invalid exact schema")
        for name in ("user_api", "internal_api", "prefix"):
            if type(pool.get(name)) is not str or not pool[name]:
                raise RuntimeError("native pool identity is incomplete")
        version = pool.get("version")
        if version is not None and (type(version) is not str or not version):
            raise RuntimeError("native pool version has an invalid type")
        if isinstance(pool.get("num_threads"), bool) or type(
            pool.get("num_threads")
        ) is not int or pool["num_threads"] != 1:
            raise RuntimeError("native pool is not exactly single-threaded")
    numpy_configuration = value.get("numpy_configuration")
    if type(numpy_configuration) is not dict or not numpy_configuration:
        raise RuntimeError("NumPy build configuration is absent")
    _canonical_json(numpy_configuration)
    torch_environment = value.get("torch_environment")
    expected_torch_keys = {
        "python_version",
        "numpy_version",
        "scipy_version",
        "torch_version",
        "torch_cpu_only",
        "torch_threads",
        "torch_interop_threads",
        "deterministic_algorithms",
    }
    if type(torch_environment) is not dict or set(torch_environment) != expected_torch_keys:
        raise RuntimeError("Torch runtime record has an invalid exact schema")
    if (
        torch_environment["python_version"] != exact_versions["python"]
        or torch_environment["numpy_version"] != exact_versions["numpy"]
        or torch_environment["scipy_version"] != exact_versions["scipy"]
        or torch_environment["torch_version"] != exact_versions["torch"]
        or torch_environment["torch_cpu_only"] is not True
        or type(torch_environment["torch_threads"]) is not int
        or torch_environment["torch_threads"] != 1
        or type(torch_environment["torch_interop_threads"]) is not int
        or torch_environment["torch_interop_threads"] != 1
        or torch_environment["deterministic_algorithms"] is not True
    ):
        raise RuntimeError("Torch runtime execution mode is not frozen")
    body = dict(value)
    claimed = _lower_sha256(body.pop("sha256"), name="execution runtime SHA-256")
    if _sha256_json(body) != claimed:
        raise RuntimeError("execution runtime digest is inconsistent")
    return value


def _runtime_record_after_import(thread_environment: Dict[str, str]) -> dict:
    """Import the frozen stack and return verified native/runtime custody."""

    import numpy as np
    import scipy
    import torch
    import threadpoolctl

    from heterodiff.experiments.finite_association_residual_training_torch import (
        configure_frozen_association_training_environment,
    )

    if threadpoolctl.__version__ != "3.6.0":
        raise RuntimeError("threadpoolctl must equal the frozen version 3.6.0")
    environment = configure_frozen_association_training_environment()
    pools = threadpoolctl.threadpool_info()
    if not pools:
        raise RuntimeError("threadpoolctl discovered no native thread pools")
    normalized_pools = []
    for pool in pools:
        count = pool.get("num_threads")
        if isinstance(count, bool) or not isinstance(count, int) or count != 1:
            raise RuntimeError("a discovered BLAS/OpenMP pool is not single-threaded")
        normalized_pools.append(
            {
                "user_api": pool.get("user_api"),
                "internal_api": pool.get("internal_api"),
                "prefix": pool.get("prefix"),
                "version": pool.get("version"),
                "num_threads": count,
            }
        )
    normalized_pools.sort(
        key=lambda value: (
            str(value["user_api"]),
            str(value["internal_api"]),
            str(value["prefix"]),
        )
    )
    numpy_configuration = getattr(np.__config__, "CONFIG", None)
    if not isinstance(numpy_configuration, dict):
        raise RuntimeError("NumPy build configuration is unavailable")
    processor = platform.processor()
    cpu_identity = (
        processor.strip()
        or platform.uname().processor.strip()
        or platform.machine().strip()
    )
    if not cpu_identity:
        raise RuntimeError("no nonempty CPU identity fallback is available")
    record = {
        "schema": _RUNTIME_SCHEMA,
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "torch": torch.__version__,
        "threadpoolctl": threadpoolctl.__version__,
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": processor,
        "cpu_identity": cpu_identity,
        "thread_environment": thread_environment,
        "native_pools": normalized_pools,
        "numpy_configuration": numpy_configuration,
        "torch_environment": asdict(environment),
    }
    record["sha256"] = _sha256_json(record)
    return _validated_runtime_record(record)


def frozen_association_sampled_run_key(
    request: FrozenAssociationSampledRunRequest,
    *,
    fixture_sha256: object,
    source_sha256: object,
    configuration_sha256: object,
    execution_runtime_sha256: object,
) -> str:
    if type(request) is not FrozenAssociationSampledRunRequest:
        raise TypeError("request must be an exact sampled-run request")
    record = {
        "schema": _RUN_KEY_SCHEMA,
        "seed": request.seed,
        "budget": request.budget,
        "method": request.method,
        "fixture_sha256": _lower_sha256(
            fixture_sha256, name="fixture_sha256"
        ),
        "source_sha256": _lower_sha256(source_sha256, name="source_sha256"),
        "configuration_sha256": _lower_sha256(
            configuration_sha256, name="configuration_sha256"
        ),
        "execution_runtime_sha256": _lower_sha256(
            execution_runtime_sha256, name="execution_runtime_sha256"
        ),
    }
    return _sha256_json(record)


def _empty_ledger() -> dict:
    return _seal_ledger(
        {"schema": _LEDGER_SCHEMA, "launch_authorizations": {}, "runs": {}}
    )


def _seal_ledger(value: dict) -> dict:
    sealed = dict(value)
    sealed.pop("ledger_sha256", None)
    sealed["ledger_sha256"] = _sha256_json(sealed)
    return sealed


def _validated_ledger(value: object) -> dict:
    if not isinstance(value, dict) or value.get("schema") != _LEDGER_SCHEMA:
        raise ValueError("ledger schema is invalid")
    expected_fields = {
        "schema",
        "launch_authorizations",
        "runs",
        "ledger_sha256",
    }
    if "campaign" in value:
        expected_fields.add("campaign")
    if "aggregate" in value:
        expected_fields.add("aggregate")
    if set(value) != expected_fields:
        raise ValueError("ledger has an invalid exact top-level schema")
    runs = value.get("runs")
    if not isinstance(runs, dict):
        raise ValueError("ledger runs must be a mapping")
    authorizations = value.get("launch_authorizations")
    if not isinstance(authorizations, dict):
        raise ValueError("ledger launch authorizations must be a mapping")
    for key, record in authorizations.items():
        _lower_sha256(key, name="launch authorization key")
        try:
            _validated_launch_authorization_record(record)
        except RuntimeError as error:
            raise ValueError("ledger launch authorization is invalid") from error
        if record.get("launch_authorization_sha256") != key:
            raise ValueError("launch authorization key differs from its receipt")
    for key, record in runs.items():
        _lower_sha256(key, name="ledger run key")
        if not isinstance(record, dict) or record.get("state") not in _ALL_STATES:
            raise ValueError("ledger contains an invalid run record")
        if record["state"] in ("FAILURE", "HOLD"):
            if record.get("terminal_owner") not in (
                "CHILD",
                "PARENT_REAPER",
            ):
                raise ValueError(
                    "ledger terminal run lacks exact custody ownership"
                )
            session = record.get("worker_session")
            launch_key = (
                session.get("launch_authorization_sha256")
                if type(session) is dict
                else None
            )
            try:
                _validated_terminal_run_record(
                    key, record, authorizations.get(launch_key)
                )
            except RuntimeError as error:
                raise ValueError("ledger terminal run is invalid") from error
        elif (
            "terminal_owner" in record
            or "terminal_ledger_sha256" in record
        ):
            raise ValueError("nonterminal ledger run claims terminal custody")
    campaign = value.get("campaign")
    if "campaign" in value and campaign is None:
        raise ValueError("ledger campaign cannot be null")
    if campaign is not None:
        if not isinstance(campaign, dict) or campaign.get("schema") != _CAMPAIGN_SCHEMA:
            raise ValueError("ledger campaign schema is invalid")
        claimed_campaign = _lower_sha256(
            campaign.get("campaign_sha256"), name="campaign_sha256"
        )
        campaign_body = dict(campaign)
        campaign_body.pop("campaign_sha256")
        if _sha256_json(campaign_body) != claimed_campaign:
            raise ValueError("campaign content digest is inconsistent")
    aggregate = value.get("aggregate")
    if "aggregate" in value and aggregate is None:
        raise ValueError("ledger sampled aggregate cannot be null")
    if aggregate is not None:
        try:
            _validated_aggregate_record(aggregate)
        except RuntimeError as error:
            raise ValueError("ledger sampled aggregate is invalid") from error
        if campaign is None or aggregate["campaign_sha256"] != campaign[
            "campaign_sha256"
        ]:
            raise ValueError("sampled aggregate belongs to another campaign")
    claimed = _lower_sha256(value.get("ledger_sha256"), name="ledger_sha256")
    unsealed = dict(value)
    unsealed.pop("ledger_sha256")
    if _sha256_json(unsealed) != claimed:
        raise ValueError("ledger content digest is inconsistent")
    return value


def _reject_duplicate_ledger_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise RuntimeError("sampled ledger contains duplicate JSON keys")
        result[key] = value
    return result


def _filesystem_identity(metadata: os.stat_result) -> tuple:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _read_ledger(path: Path, *, allow_missing: bool = True) -> dict:
    """Read one bounded, canonical ledger without following its pathname.

    ``allow_missing`` exists only for mutation paths that are permitted to
    initialize a new ledger.  Custody/admission loaders pass ``False`` so a
    read can never manufacture an empty campaign as a side effect.
    """

    if type(allow_missing) is not bool:
        raise TypeError("allow_missing must be boolean")
    try:
        before = os.lstat(path)
    except FileNotFoundError:
        if allow_missing:
            return _empty_ledger()
        raise RuntimeError("sampled ledger is absent")
    if not stat.S_ISREG(before.st_mode):
        raise RuntimeError("sampled ledger is not a regular file")
    if before.st_size <= 0 or before.st_size > _MAXIMUM_LEDGER_BYTES:
        raise RuntimeError("sampled ledger has an invalid byte length")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(os.fspath(path), flags)
    except OSError as error:
        raise RuntimeError("sampled ledger could not be opened safely") from error
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or _filesystem_identity(opened) != _filesystem_identity(before)
        ):
            raise RuntimeError("sampled ledger identity changed while opening")
        payload = b""
        while len(payload) <= _MAXIMUM_LEDGER_BYTES:
            block = os.read(
                descriptor,
                min(
                    1024 * 1024,
                    _MAXIMUM_LEDGER_BYTES + 1 - len(payload),
                ),
            )
            if not block:
                break
            payload += block
    finally:
        os.close(descriptor)
    if not payload:
        raise RuntimeError("sampled ledger is empty")
    if len(payload) > _MAXIMUM_LEDGER_BYTES:
        raise RuntimeError("sampled ledger exceeds its byte limit")
    try:
        value = json.loads(
            payload.decode("ascii"),
            object_pairs_hook=_reject_duplicate_ledger_keys,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError("non-finite JSON constant %s" % token)
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise RuntimeError("sampled ledger is invalid JSON") from error
    checked = _validated_ledger(value)
    if payload != _canonical_json(checked) + b"\n":
        raise RuntimeError("sampled ledger bytes are not canonical")
    try:
        after = os.lstat(path)
    except FileNotFoundError as error:
        raise RuntimeError("sampled ledger disappeared while reading") from error
    if _filesystem_identity(after) != _filesystem_identity(opened):
        raise RuntimeError("sampled ledger changed while reading")
    return checked


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(
        str(path), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    )
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _absolute_without_symlink_resolution(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _ensure_ledger_directory(path: Path, *, create: bool) -> Path:
    """Validate every custody ancestor and durably create only when allowed."""

    if type(create) is not bool:
        raise TypeError("create must be boolean")
    directory = _absolute_without_symlink_resolution(path)
    missing = []
    current = directory
    while True:
        try:
            metadata = os.lstat(current)
        except FileNotFoundError:
            missing.append(current)
            if current.parent == current:
                raise RuntimeError("sampled ledger has no durable parent")
            current = current.parent
            continue
        if stat.S_ISLNK(metadata.st_mode):
            raise RuntimeError("sampled ledger custody ancestors must not be symlinks")
        if not stat.S_ISDIR(metadata.st_mode):
            raise RuntimeError("sampled ledger custody path is not a directory")
        break
    if missing and not create:
        raise RuntimeError("sampled ledger directory is absent")
    for component in reversed(missing):
        try:
            os.mkdir(component, 0o700)
        except FileExistsError:
            metadata = os.lstat(component)
            if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(
                metadata.st_mode
            ):
                raise RuntimeError(
                    "sampled ledger custody path changed during creation"
                )
        else:
            _fsync_directory(component.parent)
    if directory.resolve(strict=True) != directory:
        raise RuntimeError("sampled ledger custody escaped its canonical path")
    return directory


def _open_regular_ledger_lock(
    directory: Path, *, create: bool
) -> Tuple[int, bool]:
    lock_path = directory / "ledger.lock"
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    created = False
    if create:
        try:
            descriptor = os.open(
                os.fspath(lock_path),
                os.O_RDWR | os.O_CREAT | os.O_EXCL | nofollow,
                0o600,
            )
            created = True
            before = os.fstat(descriptor)
        except FileExistsError:
            before = os.lstat(lock_path)
            if not stat.S_ISREG(before.st_mode):
                raise RuntimeError("sampled ledger lock is not a regular file")
            try:
                descriptor = os.open(
                    os.fspath(lock_path), os.O_RDWR | nofollow
                )
            except OSError as error:
                raise RuntimeError(
                    "sampled ledger lock could not be opened safely"
                ) from error
    else:
        try:
            before = os.lstat(lock_path)
        except FileNotFoundError as error:
            raise RuntimeError("sampled ledger lock is absent") from error
        if not stat.S_ISREG(before.st_mode):
            raise RuntimeError("sampled ledger lock is not a regular file")
        try:
            descriptor = os.open(os.fspath(lock_path), os.O_RDONLY | nofollow)
        except OSError as error:
            raise RuntimeError(
                "sampled ledger lock could not be opened safely"
            ) from error
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or _filesystem_identity(opened) != _filesystem_identity(before)
        ):
            raise RuntimeError("sampled ledger lock identity changed while opening")
        if created:
            os.fsync(descriptor)
            _fsync_directory(directory)
        return descriptor, created
    except BaseException:
        os.close(descriptor)
        raise


def _reconcile_stale_ledger_temporaries(directory: Path) -> int:
    """Remove bounded crash residue while rejecting ambiguous path types."""

    stale = []
    with os.scandir(directory) as entries:
        for entry in entries:
            if not entry.name.startswith(_LEDGER_TEMPORARY_PREFIX):
                continue
            suffix = entry.name[len(_LEDGER_TEMPORARY_PREFIX) :]
            if (
                not suffix
                or len(suffix) > 64
                or any(
                    character
                    not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
                    for character in suffix
                )
            ):
                raise RuntimeError("sampled ledger temporary name is invalid")
            stale.append(entry.name)
            if len(stale) > _MAXIMUM_STALE_LEDGER_TEMPORARIES:
                raise RuntimeError("too many stale sampled ledger temporaries")
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    opened_temporaries = []
    try:
        for name in sorted(stale):
            path = directory / name
            before = os.lstat(path)
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                raise RuntimeError(
                    "sampled ledger temporary is not an isolated regular file"
                )
            try:
                descriptor = os.open(os.fspath(path), os.O_RDONLY | nofollow)
            except OSError as error:
                raise RuntimeError(
                    "sampled ledger temporary could not be opened safely"
                ) from error
            opened_temporaries.append((path, descriptor))
            opened = os.fstat(descriptor)
            if (
                not stat.S_ISREG(opened.st_mode)
                or opened.st_nlink != 1
                or _filesystem_identity(opened) != _filesystem_identity(before)
            ):
                raise RuntimeError(
                    "sampled ledger temporary identity changed while opening"
                )
            after = os.lstat(path)
            if (
                after.st_nlink != 1
                or _filesystem_identity(after) != _filesystem_identity(opened)
            ):
                raise RuntimeError(
                    "sampled ledger temporary changed during reconciliation"
                )
        for path, descriptor in opened_temporaries:
            current = os.lstat(path)
            opened = os.fstat(descriptor)
            if (
                current.st_nlink != 1
                or _filesystem_identity(current)
                != _filesystem_identity(opened)
            ):
                raise RuntimeError(
                    "sampled ledger temporary changed before removal"
                )
            os.unlink(path)
    finally:
        for _, descriptor in opened_temporaries:
            os.close(descriptor)
    if stale:
        _fsync_directory(directory)
    return len(stale)


def _atomic_write_json(path: Path, value: object) -> None:
    if not isinstance(value, dict) or value.get("schema") != _LEDGER_SCHEMA:
        raise TypeError("only a frozen exactly-once ledger may be written")
    sealed = _seal_ledger(value)
    payload = _canonical_json(sealed) + b"\n"
    if len(payload) > _MAXIMUM_LEDGER_BYTES:
        raise RuntimeError("sampled ledger exceeds its byte limit")
    try:
        destination = os.lstat(path)
    except FileNotFoundError:
        destination = None
    if destination is not None and not stat.S_ISREG(destination.st_mode):
        raise RuntimeError("sampled ledger destination is not a regular file")
    temporary_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=str(path.parent), prefix=".ledger-", delete=False
        ) as handle:
            temporary_name = handle.name
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
        temporary_name = None
        _fsync_directory(path.parent)
    finally:
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass
            else:
                _fsync_directory(path.parent)


@contextmanager
def _locked_ledger(
    ledger_directory: Path, *, create: bool = True
) -> Iterator[Tuple[Path, dict]]:
    """Lock sampled custody, with noncreating semantics for public reads."""

    directory = _ensure_ledger_directory(ledger_directory, create=create)
    ledger_path = directory / "ledger.json"
    descriptor, _ = _open_regular_ledger_lock(directory, create=create)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        try:
            lock_path = directory / "ledger.lock"
            after_lock = os.lstat(lock_path)
            opened_lock = os.fstat(descriptor)
            if (
                not stat.S_ISREG(after_lock.st_mode)
                or _filesystem_identity(after_lock)
                != _filesystem_identity(opened_lock)
            ):
                raise RuntimeError("sampled ledger lock changed while acquiring")
            if create:
                _reconcile_stale_ledger_temporaries(directory)
            yield ledger_path, _read_ledger(
                ledger_path, allow_missing=create
            )
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
    finally:
        os.close(descriptor)


def _reserve_run(
    ledger_directory: Path,
    run_key: str,
    request: FrozenAssociationSampledRunRequest,
    runtime_record: dict,
    worker_session: _FrozenAssociationWorkerSession,
) -> None:
    if type(worker_session) is not _FrozenAssociationWorkerSession:
        raise TypeError("run reservation requires a parent-handshaken worker session")
    runtime = dict(_validated_runtime_record(runtime_record))
    with _locked_ledger(ledger_directory) as (path, ledger):
        if run_key in ledger["runs"]:
            state = ledger["runs"][run_key]["state"]
            raise RuntimeError(
                "exactly-once run key already exists in state %s" % state
            )
        launch = _validated_launch_authorization_record(
            ledger["launch_authorizations"].get(
                worker_session.record["launch_authorization_sha256"]
            )
        )
        if (
            launch["state"] != "CONSUMED"
            or launch["consumed_receipt_sha256"]
            != worker_session.record["launch_receipt_sha256"]
            or launch["request"] != asdict(request)
            or launch["ledger_directory"]
            != str(_absolute_without_symlink_resolution(ledger_directory))
            or launch["child_process_id"] != os.getpid()
            or launch["parent_process_id"] != os.getppid()
            or launch["worker_token_sha256"]
            != worker_session.record["worker_token_sha256"]
        ):
            raise RuntimeError(
                "run reservation lacks consumed parent launch authorization"
            )
        worker_session.bind_run(run_key)
        ledger["runs"][run_key] = {
            "state": "RESERVED",
            "request": asdict(request),
            "runtime": runtime,
            "worker_session": worker_session.record,
            "worker_session_run_sha256": _worker_session_run_sha256(
                worker_session.session_sha256, run_key
            ),
            "worker_pid": os.getpid(),
            "reserved_unix_ns": time.time_ns(),
        }
        _atomic_write_json(path, ledger)


def _campaign_record(
    *,
    fixture_sha256: str,
    source_sha256: str,
    configuration_sha256: str,
    execution_runtime_sha256: str,
) -> dict:
    record = {
        "schema": _CAMPAIGN_SCHEMA,
        "fixture_sha256": fixture_sha256,
        "source_sha256": source_sha256,
        "configuration_sha256": configuration_sha256,
        "execution_runtime_sha256": execution_runtime_sha256,
        "expected_sampled_coordinates": [
            {"seed": seed, "budget": budget, "method": method}
            for seed in _SEEDS
            for budget in _BUDGETS
            for method in _METHODS
        ],
    }
    record["campaign_sha256"] = _sha256_json(record)
    return record


def _ensure_frozen_campaign(
    ledger_directory: Path,
    *,
    fixture_sha256: str,
    source_sha256: str,
    configuration_sha256: str,
    execution_runtime_sha256: str,
) -> dict:
    expected = _campaign_record(
        fixture_sha256=fixture_sha256,
        source_sha256=source_sha256,
        configuration_sha256=configuration_sha256,
        execution_runtime_sha256=execution_runtime_sha256,
    )
    with _locked_ledger(ledger_directory) as (path, ledger):
        existing = ledger.get("campaign")
        if existing is None:
            ledger["campaign"] = expected
            _atomic_write_json(path, ledger)
        elif existing != expected:
            raise RuntimeError(
                "campaign source/configuration/runtime is already frozen"
            )
    return expected


def _transition_run(
    ledger_directory: Path,
    run_key: str,
    *,
    expected_state: str,
    record: dict,
) -> dict:
    if record.get("state") not in _ALL_STATES:
        raise ValueError("transition record has an invalid state")
    if record.get("state") in ("FAILURE", "HOLD"):
        raise RuntimeError(
            "terminal run transitions require the exact custody helper"
        )
    allowed = {
        "RESERVED": frozenset(("PREPARED",)),
        "PREPARED": frozenset(),
        "RUNNING": frozenset(),
        "SUCCESS": frozenset(),
        "FAILURE": frozenset(),
        "HOLD": frozenset(),
    }
    if expected_state not in allowed or record.get("state") not in allowed[
        expected_state
    ]:
        raise RuntimeError("ledger transition is outside the frozen state graph")
    with _locked_ledger(ledger_directory) as (path, ledger):
        existing = ledger["runs"].get(run_key)
        if not isinstance(existing, dict) or existing.get("state") != expected_state:
            raise RuntimeError("ledger state changed before atomic transition")
        ledger["runs"][run_key] = record
        _atomic_write_json(path, ledger)
    return record


def _validated_running_record(record: object) -> dict:
    """Validate the durable PREPARED -> RUNNING hash chain."""

    if not isinstance(record, dict) or record.get("state") != "RUNNING":
        raise RuntimeError("ledger run is not durably RUNNING")
    _validated_runtime_record(record.get("runtime"))
    session = _validated_worker_session_record(record.get("worker_session"))
    if record.get("worker_pid") != session["worker_pid"]:
        raise RuntimeError("RUNNING worker PID differs from its session")
    run_key = _lower_sha256(record.get("run_key_sha256"), name="run_key_sha256")
    if record.get("worker_session_run_sha256") != _worker_session_run_sha256(
        session["session_sha256"], run_key
    ):
        raise RuntimeError("RUNNING worker session/run binding is inconsistent")
    running_base = dict(record)
    running_claimed = _lower_sha256(
        running_base.pop("running_ledger_sha256", None),
        name="running_ledger_sha256",
    )
    if _sha256_json(running_base) != running_claimed:
        raise RuntimeError("RUNNING ledger receipt digest is inconsistent")
    prepared_base = dict(running_base)
    prepared_base["state"] = "PREPARED"
    prepared_base.pop("update_started_unix_ns", None)
    prepared_claimed = _lower_sha256(
        prepared_base.pop("prepared_ledger_sha256", None),
        name="prepared_ledger_sha256",
    )
    if _sha256_json(prepared_base) != prepared_claimed:
        raise RuntimeError("RUNNING record breaks the PREPARED receipt chain")
    prepared_unix_ns = prepared_base.get("prepared_unix_ns")
    update_started_unix_ns = running_base.get("update_started_unix_ns")
    if (
        isinstance(prepared_unix_ns, bool)
        or not isinstance(prepared_unix_ns, int)
        or prepared_unix_ns <= 0
        or isinstance(update_started_unix_ns, bool)
        or not isinstance(update_started_unix_ns, int)
        or update_started_unix_ns < prepared_unix_ns
    ):
        raise RuntimeError("RUNNING ledger timestamps are invalid")
    return record


def _validated_active_run_for_parent_reaper(
    run_key: object,
    record: object,
    launch: object,
) -> dict:
    """Validate exact child-owned custody before a parent reaper transition."""

    key = _lower_sha256(run_key, name="run_key_sha256")
    authorization = _validated_launch_authorization_record(launch)
    if authorization["state"] != "CONSUMED":
        raise RuntimeError("parent reaper requires a consumed launch")
    if type(record) is not dict or record.get("state") not in (
        "RESERVED",
        "PREPARED",
        "RUNNING",
    ):
        raise RuntimeError("parent reaper requires an active run")
    state = record["state"]
    reserved_fields = {
        "state",
        "request",
        "runtime",
        "worker_session",
        "worker_session_run_sha256",
        "worker_pid",
        "reserved_unix_ns",
    }
    prepared_fields = {
        "state",
        "request",
        "runtime",
        "worker_session",
        "worker_session_run_sha256",
        "worker_pid",
        "run_key_sha256",
        "preflight",
        "preparation_wall_seconds",
        "preparation_cpu_seconds",
        "prepared_unix_ns",
        "prepared_ledger_sha256",
    }
    running_fields = prepared_fields | {
        "update_started_unix_ns",
        "running_ledger_sha256",
    }
    expected_fields = {
        "RESERVED": reserved_fields,
        "PREPARED": prepared_fields,
        "RUNNING": running_fields,
    }[state]
    if set(record) != expected_fields:
        raise RuntimeError("active reaper source has an invalid exact schema")
    _validated_runtime_record(record.get("runtime"))
    session = _validated_worker_session_record(record.get("worker_session"))
    if (
        record.get("request") != authorization["request"]
        or session["launch_authorization_sha256"]
        != authorization["launch_authorization_sha256"]
        or session["launch_receipt_sha256"]
        != authorization["consumed_receipt_sha256"]
        or session["worker_pid"] != authorization["child_process_id"]
        or session["worker_parent_pid"] != authorization["parent_process_id"]
        or record.get("worker_pid") != session["worker_pid"]
        or record.get("worker_session_run_sha256")
        != _worker_session_run_sha256(session["session_sha256"], key)
        or (state != "RESERVED" and record.get("run_key_sha256") != key)
    ):
        raise RuntimeError("active run differs from consumed launch custody")
    if state == "RESERVED":
        reserved_ns = record.get("reserved_unix_ns")
        if (
            isinstance(reserved_ns, bool)
            or type(reserved_ns) is not int
            or reserved_ns < authorization["consumed_unix_ns"]
        ):
            raise RuntimeError("RESERVED reaper timestamp is invalid")
    elif state == "PREPARED":
        claimed = _lower_sha256(
            record.get("prepared_ledger_sha256"),
            name="prepared_ledger_sha256",
        )
        body = dict(record)
        body.pop("prepared_ledger_sha256")
        if _sha256_json(body) != claimed:
            raise RuntimeError("PREPARED reaper source digest is inconsistent")
    else:
        _validated_running_record(record)
    return record


def _active_run_receipt_sha256(record: dict) -> str:
    state = record["state"]
    if state == "RESERVED":
        return _sha256_json(record)
    if state == "PREPARED":
        return _lower_sha256(
            record.get("prepared_ledger_sha256"),
            name="prepared_ledger_sha256",
        )
    if state == "RUNNING":
        return _lower_sha256(
            record.get("running_ledger_sha256"),
            name="running_ledger_sha256",
        )
    raise RuntimeError("run has no active-stage receipt")


def _validated_terminal_run_record(
    run_key: object,
    record: object,
    launch: object,
) -> dict:
    """Validate a child or parent-reaper active-run terminal receipt."""

    key = _lower_sha256(run_key, name="run_key_sha256")
    authorization = _validated_launch_authorization_record(launch)
    if (
        type(record) is not dict
        or record.get("state") not in ("FAILURE", "HOLD")
        or record.get("terminal_owner") not in ("CHILD", "PARENT_REAPER")
    ):
        raise RuntimeError("run is not a recognized terminal receipt")
    owner = record["terminal_owner"]
    common_additions = {
        "terminal_owner",
        "terminal_process_id",
        "previous_state",
        "previous_ledger_sha256",
        "error_type",
        "error_message",
        "failed_stage",
        "failed_unix_ns",
        "terminal_ledger_sha256",
    }
    owner_additions = (
        {
            "failure_total_wall_seconds",
            "failure_total_cpu_seconds",
            "failure_process_peak_rss_bytes",
        }
        if owner == "CHILD"
        else {
            "observed_child_process_id",
            "child_returncode",
            "child_signal",
        }
    )
    required_terminal_fields = common_additions | owner_additions
    if any(name not in record for name in required_terminal_fields):
        raise RuntimeError("terminal run has an incomplete exact schema")
    exit_observation_fields = {
        "exit_observation_previous_receipt_sha256",
        "exit_observed_unix_ns",
        "exit_child_returncode",
        "exit_child_signal",
        "exit_observation_receipt_sha256",
    }
    has_exit_observation = (
        owner == "CHILD" and "exit_observation_receipt_sha256" in record
    )
    if has_exit_observation and any(
        name not in record for name in exit_observation_fields
    ):
        raise RuntimeError("terminal run exit observation is incomplete")
    base_record = dict(record)
    if has_exit_observation:
        for name in exit_observation_fields:
            base_record.pop(name)
    body = dict(base_record)
    claimed = _lower_sha256(
        body.pop("terminal_ledger_sha256"), name="terminal_ledger_sha256"
    )
    if _sha256_json(body) != claimed:
        raise RuntimeError("terminal run digest is inconsistent")
    previous = dict(base_record)
    for name in required_terminal_fields:
        previous.pop(name)
    previous_state = record.get("previous_state")
    if previous_state not in ("RESERVED", "PREPARED", "RUNNING"):
        raise RuntimeError("terminal run previous state is invalid")
    previous["state"] = previous_state
    _validated_active_run_for_parent_reaper(key, previous, authorization)
    previous_receipt = _active_run_receipt_sha256(previous)
    if record.get("previous_ledger_sha256") != previous_receipt:
        raise RuntimeError("terminal run previous receipt changed")
    if type(record.get("error_type")) is not str or not record["error_type"]:
        raise RuntimeError("terminal run error type is invalid")
    if type(record.get("error_message")) is not str:
        raise RuntimeError("terminal run error message is invalid")
    terminal_process_id = record.get("terminal_process_id")
    if (
        isinstance(terminal_process_id, bool)
        or type(terminal_process_id) is not int
        or terminal_process_id <= 0
    ):
        raise RuntimeError("terminal run process identity is invalid")
    failed_ns = record.get("failed_unix_ns")
    previous_ns = {
        "RESERVED": previous.get("reserved_unix_ns"),
        "PREPARED": previous.get("prepared_unix_ns"),
        "RUNNING": previous.get("update_started_unix_ns"),
    }[previous_state]
    if (
        isinstance(previous_ns, bool)
        or type(previous_ns) is not int
        or previous_ns <= 0
        or isinstance(failed_ns, bool)
        or type(failed_ns) is not int
        or failed_ns < previous_ns
    ):
        raise RuntimeError("terminal run timestamp is invalid")
    if owner == "CHILD":
        if (
            record["terminal_process_id"]
            != authorization["child_process_id"]
            or record.get("failed_stage") != previous_state
        ):
            raise RuntimeError("child terminal run ownership/stage is invalid")
        for name in (
            "failure_total_wall_seconds",
            "failure_total_cpu_seconds",
        ):
            raw = record.get(name)
            if (
                isinstance(raw, bool)
                or not isinstance(raw, (int, float))
                or not math.isfinite(float(raw))
                or float(raw) < 0.0
            ):
                raise RuntimeError("child terminal run resources are invalid")
        peak = record.get("failure_process_peak_rss_bytes")
        if isinstance(peak, bool) or type(peak) is not int or peak <= 0:
            raise RuntimeError("child terminal run peak RSS is invalid")
    else:
        child_returncode = record.get("child_returncode")
        child_signal = record.get("child_signal")
        expected_signal = (
            -child_returncode
            if type(child_returncode) is int
            and not isinstance(child_returncode, bool)
            and child_returncode < 0
            else None
        )
        if (
            record.get("state") != "FAILURE"
            or record.get("terminal_process_id")
            != authorization["parent_process_id"]
            or record.get("observed_child_process_id")
            != authorization["child_process_id"]
            or isinstance(child_returncode, bool)
            or type(child_returncode) is not int
            or (expected_signal is None and child_signal is not None)
            or (
                expected_signal is not None
                and (
                    isinstance(child_signal, bool)
                    or type(child_signal) is not int
                    or child_signal != expected_signal
                )
            )
            or record.get("failed_stage")
            != "CHILD_EXIT_AFTER_CONSUMPTION"
        ):
            raise RuntimeError("parent-reaper run observation is invalid")
    if has_exit_observation:
        observation_previous = _lower_sha256(
            record.get("exit_observation_previous_receipt_sha256"),
            name="exit_observation_previous_receipt_sha256",
        )
        exit_observed_unix_ns = record.get("exit_observed_unix_ns")
        exit_returncode = record.get("exit_child_returncode")
        exit_signal = record.get("exit_child_signal")
        expected_exit_signal = (
            -exit_returncode
            if type(exit_returncode) is int
            and not isinstance(exit_returncode, bool)
            and exit_returncode < 0
            else None
        )
        if (
            observation_previous != claimed
            or isinstance(exit_observed_unix_ns, bool)
            or type(exit_observed_unix_ns) is not int
            or exit_observed_unix_ns < failed_ns
            or isinstance(exit_returncode, bool)
            or type(exit_returncode) is not int
            or (expected_exit_signal is None and exit_signal is not None)
            or (
                expected_exit_signal is not None
                and (
                    isinstance(exit_signal, bool)
                    or type(exit_signal) is not int
                    or exit_signal != expected_exit_signal
                )
            )
        ):
            raise RuntimeError("terminal run exit observation is invalid")
        observation = dict(base_record)
        observation.update(
            {
                "exit_observation_previous_receipt_sha256": (
                    observation_previous
                ),
                "exit_observed_unix_ns": exit_observed_unix_ns,
                "exit_child_returncode": exit_returncode,
                "exit_child_signal": exit_signal,
            }
        )
        observation_receipt = _lower_sha256(
            record.get("exit_observation_receipt_sha256"),
            name="exit_observation_receipt_sha256",
        )
        if _sha256_json(observation) != observation_receipt:
            raise RuntimeError(
                "terminal run exit observation receipt is inconsistent"
            )
    return record


def _record_parent_run_exit_observation(
    ledger_directory: Path,
    launch_authorization_sha256: object,
    request: "FrozenAssociationSampledRunRequest",
    *,
    child_process_id: object,
    child_returncode: object,
) -> dict:
    """Chain a parent exit observation from a child-owned run terminal."""

    authorization = _lower_sha256(
        launch_authorization_sha256, name="launch_authorization_sha256"
    )
    if type(request) is not FrozenAssociationSampledRunRequest:
        raise TypeError("parent run exit observation requires an exact request")
    if (
        isinstance(child_process_id, bool)
        or type(child_process_id) is not int
        or child_process_id <= 0
    ):
        raise ValueError("child_process_id must be a positive integer")
    if isinstance(child_returncode, bool) or type(child_returncode) is not int:
        raise TypeError("child_returncode must be an integer")
    directory = _absolute_without_symlink_resolution(ledger_directory)
    with _locked_ledger(directory) as (path, ledger):
        launch = _validated_launch_authorization_record(
            ledger["launch_authorizations"].get(authorization)
        )
        if (
            launch["state"] != "CONSUMED"
            or launch["launch_authorization_sha256"] != authorization
            or launch["request"] != asdict(request)
            or launch["ledger_directory"] != str(directory)
            or launch["parent_process_id"] != os.getpid()
            or launch["child_process_id"] != child_process_id
        ):
            raise RuntimeError("parent run exit observation lacks custody")
        matching = []
        for run_key, run in ledger["runs"].items():
            session = run.get("worker_session") if type(run) is dict else None
            if (
                type(session) is dict
                and session.get("launch_authorization_sha256")
                == authorization
            ):
                matching.append((run_key, run))
        if len(matching) != 1:
            raise RuntimeError(
                "parent run exit observation requires exactly one owned run"
            )
        run_key, current = matching[0]
        checked = _validated_terminal_run_record(run_key, current, launch)
        if (
            checked.get("terminal_owner") != "CHILD"
            or checked.get("terminal_process_id") != child_process_id
        ):
            raise RuntimeError(
                "parent run exit observation requires a child terminal"
            )
        if "exit_observation_receipt_sha256" in checked:
            if (
                checked["exit_child_returncode"] != child_returncode
                or checked["exit_child_signal"]
                != (-child_returncode if child_returncode < 0 else None)
            ):
                raise RuntimeError("parent run exit observation changed on retry")
            return checked
        observed = dict(checked)
        observed.update(
            {
                "exit_observation_previous_receipt_sha256": checked[
                    "terminal_ledger_sha256"
                ],
                "exit_observed_unix_ns": time.time_ns(),
                "exit_child_returncode": child_returncode,
                "exit_child_signal": (
                    -child_returncode if child_returncode < 0 else None
                ),
            }
        )
        observed["exit_observation_receipt_sha256"] = _sha256_json(observed)
        _validated_terminal_run_record(run_key, observed, launch)
        ledger["runs"][run_key] = observed
        _atomic_write_json(path, ledger)
        return observed


def _validated_success_record(record: object) -> dict:
    """Validate SUCCESS and every prior durable stage receipt."""

    if not isinstance(record, dict) or record.get("state") != "SUCCESS":
        raise RuntimeError("ledger run is not durably SUCCESS")
    has_exit_observation = "exit_observation_receipt_sha256" in record
    if has_exit_observation and any(
        name not in record for name in _SUCCESS_EXIT_OBSERVATION_FIELDS
    ):
        raise RuntimeError("SUCCESS exit observation is incomplete")
    base_record = dict(record)
    if has_exit_observation:
        for name in _SUCCESS_EXIT_OBSERVATION_FIELDS:
            base_record.pop(name)
    success_base = dict(base_record)
    success_claimed = _lower_sha256(
        success_base.pop("success_ledger_sha256", None),
        name="success_ledger_sha256",
    )
    if _sha256_json(success_base) != success_claimed:
        raise RuntimeError("SUCCESS ledger receipt digest is inconsistent")
    if any(name not in success_base for name in _SUCCESS_ADDITION_FIELDS):
        raise RuntimeError("SUCCESS ledger receipt is incomplete")
    running = dict(success_base)
    running["state"] = "RUNNING"
    for name in _SUCCESS_ADDITION_FIELDS:
        running.pop(name)
    _validated_running_record(running)
    steps = success_base.get("optimizer_steps_taken")
    expected_steps = success_base.get("preflight", {}).get("updates")
    if (
        isinstance(steps, bool)
        or type(steps) is not int
        or steps <= 0
        or steps != expected_steps
    ):
        raise RuntimeError("SUCCESS optimizer step count is inconsistent")
    _lower_sha256(
        success_base.get("optimizer_transcript_sha256"),
        name="optimizer_transcript_sha256",
    )
    completion = _validated_optimizer_completion_receipt_record(
        success_base.get("optimizer_completion_receipt")
    )
    if (
        success_base.get("optimizer_completion_receipt_sha256")
        != completion["completion_receipt_sha256"]
        or completion["run_key_sha256"]
        != success_base.get("run_key_sha256")
        or completion["preflight_sha256"]
        != success_base.get("preflight", {}).get("preflight_sha256")
        or completion["prepared_ledger_sha256"]
        != success_base.get("prepared_ledger_sha256")
        or completion["running_ledger_sha256"]
        != success_base.get("running_ledger_sha256")
        or completion["execution_runtime_sha256"]
        != success_base.get("runtime", {}).get("sha256")
        or completion["worker_session_sha256"]
        != success_base.get("worker_session", {}).get("session_sha256")
        or completion["optimizer_transcript_sha256"]
        != success_base.get("optimizer_transcript_sha256")
        or completion["observed_optimizer_steps"] != steps
        or completion["final_parameter_sha256"]
        != success_base.get("parameter_sha256")
        or completion["last_post_update_parameter_sha256"]
        != success_base.get("parameter_sha256")
        or completion["certificate_sha256"]
        != success_base.get("certificate_sha256")
        or completion["classifier_sha256"]
        != success_base.get("classifier_sha256")
    ):
        raise RuntimeError(
            "SUCCESS optimizer completion receipt is inconsistent"
        )
    completed_unix_ns = success_base.get("completed_unix_ns")
    update_started_unix_ns = running.get("update_started_unix_ns")
    if (
        isinstance(completed_unix_ns, bool)
        or not isinstance(completed_unix_ns, int)
        or completed_unix_ns < update_started_unix_ns
    ):
        raise RuntimeError("SUCCESS ledger timestamp is invalid")
    if has_exit_observation:
        observation_previous = _lower_sha256(
            record.get("exit_observation_previous_receipt_sha256"),
            name="exit_observation_previous_receipt_sha256",
        )
        exit_observed_unix_ns = record.get("exit_observed_unix_ns")
        if (
            observation_previous != success_claimed
            or isinstance(exit_observed_unix_ns, bool)
            or type(exit_observed_unix_ns) is not int
            or exit_observed_unix_ns < completed_unix_ns
            or type(record.get("exit_child_returncode")) is not int
            or record.get("exit_child_returncode") != 0
            or record.get("exit_child_signal") is not None
        ):
            raise RuntimeError("SUCCESS exit observation is invalid")
        observation = dict(base_record)
        observation.update(
            {
                "exit_observation_previous_receipt_sha256": (
                    observation_previous
                ),
                "exit_observed_unix_ns": exit_observed_unix_ns,
                "exit_child_returncode": 0,
                "exit_child_signal": None,
            }
        )
        observation_receipt = _lower_sha256(
            record.get("exit_observation_receipt_sha256"),
            name="exit_observation_receipt_sha256",
        )
        if _sha256_json(observation) != observation_receipt:
            raise RuntimeError("SUCCESS exit observation receipt is inconsistent")
    return record


def _validated_parent_observed_success_record(record: object) -> dict:
    """Require validator-exact SUCCESS plus a chained parent zero exit."""

    checked = _validated_success_record(record)
    if "exit_observation_receipt_sha256" not in checked:
        raise RuntimeError("SUCCESS lacks a durable parent zero-exit observation")
    return checked


def _record_parent_success_exit_observation(
    ledger_directory: Path,
    launch_authorization_sha256: object,
    request: "FrozenAssociationSampledRunRequest",
    *,
    child_process_id: object,
    child_returncode: object,
) -> dict:
    """Chain a confirmed parent zero exit from immutable SUCCESS custody."""

    authorization = _lower_sha256(
        launch_authorization_sha256, name="launch_authorization_sha256"
    )
    if type(request) is not FrozenAssociationSampledRunRequest:
        raise TypeError("SUCCESS exit observation requires an exact request")
    if (
        isinstance(child_process_id, bool)
        or type(child_process_id) is not int
        or child_process_id <= 0
    ):
        raise ValueError("child_process_id must be a positive integer")
    if type(child_returncode) is not int or child_returncode != 0:
        raise RuntimeError("SUCCESS can record only an exact zero child exit")
    directory = _absolute_without_symlink_resolution(ledger_directory)
    with _locked_ledger(directory) as (path, ledger):
        launch = _validated_launch_authorization_record(
            ledger["launch_authorizations"].get(authorization)
        )
        if (
            launch["state"] != "CONSUMED"
            or launch["launch_authorization_sha256"] != authorization
            or launch["request"] != asdict(request)
            or launch["ledger_directory"] != str(directory)
            or launch["parent_process_id"] != os.getpid()
            or launch["child_process_id"] != child_process_id
        ):
            raise RuntimeError("SUCCESS exit observation lacks launch custody")
        matching = []
        for run_key, run in ledger["runs"].items():
            session = run.get("worker_session") if type(run) is dict else None
            if (
                type(session) is dict
                and session.get("launch_authorization_sha256")
                == authorization
            ):
                matching.append((run_key, run))
        if len(matching) != 1:
            raise RuntimeError(
                "SUCCESS exit observation requires exactly one owned run"
            )
        run_key, current = matching[0]
        checked = _validated_success_record(current)
        session = _validated_worker_session_record(
            checked.get("worker_session")
        )
        if (
            checked.get("run_key_sha256") != run_key
            or checked.get("request") != asdict(request)
            or checked.get("worker_pid") != child_process_id
            or session["worker_pid"] != child_process_id
            or session["worker_parent_pid"] != os.getpid()
            or session["launch_authorization_sha256"] != authorization
            or session["launch_receipt_sha256"]
            != launch["consumed_receipt_sha256"]
        ):
            raise RuntimeError("SUCCESS exit observation differs from custody")
        if "exit_observation_receipt_sha256" in checked:
            return _validated_parent_observed_success_record(checked)
        observed = dict(checked)
        observed.update(
            {
                "exit_observation_previous_receipt_sha256": checked[
                    "success_ledger_sha256"
                ],
                "exit_observed_unix_ns": time.time_ns(),
                "exit_child_returncode": 0,
                "exit_child_signal": None,
            }
        )
        observed["exit_observation_receipt_sha256"] = _sha256_json(observed)
        _validated_parent_observed_success_record(observed)
        ledger["runs"][run_key] = observed
        _atomic_write_json(path, ledger)
        return observed


def _complete_run_success(
    ledger_directory: Path,
    run_key: str,
    *,
    completed_training: object,
    checkpoint_path: Path,
    checkpoint_sha256: object,
    worker_session: _FrozenAssociationWorkerSession,
) -> dict:
    """Consume the executor capability and derive the only SUCCESS receipt."""

    from heterodiff.experiments.finite_association_residual_training_torch import (
        OptimizerCompletedAssociationResidualTraining,
        _require_fitted_checkpoint_integrity,
        load_fitted_association_checkpoint,
    )

    if type(completed_training) is not OptimizerCompletedAssociationResidualTraining:
        raise TypeError(
            "SUCCESS requires executor-completed sampled training"
        )
    if type(worker_session) is not _FrozenAssociationWorkerSession:
        raise TypeError("SUCCESS requires the parent-handshaken worker session")
    worker_session.validate_run(run_key)
    checkpoint = completed_training.checkpoint
    if checkpoint.run_key_sha256 != run_key:
        raise RuntimeError("completed checkpoint belongs to another run key")
    directory = _absolute_without_symlink_resolution(ledger_directory)
    checkpoint_candidate = _absolute_without_symlink_resolution(
        checkpoint_path
    )
    if (
        checkpoint_candidate.parent != directory
        or checkpoint_candidate.name != "%s.pt" % run_key
    ):
        raise RuntimeError("SUCCESS checkpoint path is not canonical")
    checked_file_sha256 = _lower_sha256(
        checkpoint_sha256, name="checkpoint_sha256"
    )
    with _locked_ledger(ledger_directory) as (path, ledger):
        running = ledger["runs"].get(run_key)
        _validated_running_record(running)
        if running.get("worker_session") != worker_session.record:
            raise RuntimeError("SUCCESS worker session differs from RUNNING custody")
        persisted = load_fitted_association_checkpoint(
            checkpoint_candidate, expected_sha256=checked_file_sha256
        )
        _require_fitted_checkpoint_integrity(persisted)
        if (
            persisted.optimizer_completion_receipt
            != checkpoint.optimizer_completion_receipt
            or persisted.classifier_sha256 != checkpoint.classifier_sha256
            or persisted.final_snapshot.parameter_sha256
            != checkpoint.final_snapshot.parameter_sha256
            or persisted.certificate.certificate_sha256
            != checkpoint.certificate.certificate_sha256
        ):
            raise RuntimeError(
                "serialized checkpoint differs from executor completion"
            )
        completion = asdict(persisted.optimizer_completion_receipt)
        _validated_optimizer_completion_receipt_record(completion)
        if (
            completion["campaign_sha256"]
            != ledger.get("campaign", {}).get("campaign_sha256")
            or completion["running_ledger_sha256"]
            != running.get("running_ledger_sha256")
        ):
            raise RuntimeError(
                "optimizer completion receipt differs from campaign RUNNING custody"
            )
        completed_training._consume_for_success(running, worker_session)
        additions = {
            "classifier_sha256": persisted.classifier_sha256,
            "certificate_sha256": (
                persisted.certificate.certificate_sha256
            ),
            "certified_maximum_absolute_correction": (
                persisted.certificate.certified_maximum_absolute_correction
            ),
            "parameter_sha256": persisted.final_snapshot.parameter_sha256,
            "final_empirical_risk": persisted.final_empirical_risk,
            "maximum_unclipped_gradient_norm": (
                persisted.maximum_unclipped_gradient_norm
            ),
            "optimizer_steps_taken": persisted.optimizer_steps_taken,
            "optimizer_transcript_sha256": (
                persisted.optimizer_transcript_sha256
            ),
            "optimizer_completion_receipt": completion,
            "optimizer_completion_receipt_sha256": completion[
                "completion_receipt_sha256"
            ],
            "checkpoint_file": checkpoint_path.name,
            "checkpoint_sha256": checked_file_sha256,
            "optimizer_wall_seconds": persisted.elapsed_training_seconds,
            "total_wall_seconds": persisted.total_wall_seconds,
            "total_cpu_seconds": persisted.total_cpu_seconds,
            "process_peak_rss_bytes": persisted.process_peak_rss_bytes,
            "completed_unix_ns": time.time_ns(),
        }
        if set(additions) != _SUCCESS_ADDITION_FIELDS:
            raise AssertionError("derived SUCCESS additions lost schema closure")
        success = dict(running)
        success["state"] = "SUCCESS"
        success.update(additions)
        success["success_ledger_sha256"] = _sha256_json(success)
        _validated_success_record(success)
        ledger["runs"][run_key] = success
        _atomic_write_json(path, ledger)
    return success


def _validated_prepared_record(
    record: object,
    *,
    permit: object,
    preflight: object,
) -> dict:
    if not isinstance(record, dict) or record.get("state") != "PREPARED":
        raise RuntimeError("ledger run is not durably PREPARED")
    runtime = _validated_runtime_record(record.get("runtime"))
    session = _validated_worker_session_record(record.get("worker_session"))
    expected_session_run = _worker_session_run_sha256(
        session["session_sha256"], permit.run_key_sha256
    )
    if (
        record.get("run_key_sha256") != permit.run_key_sha256
        or record.get("prepared_ledger_sha256")
        != permit.prepared_ledger_sha256
        or _canonical_json(record.get("preflight"))
        != _canonical_json(asdict(preflight))
        or runtime.get("sha256") != permit.execution_runtime_sha256
        or session.get("session_sha256") != permit.worker_session_sha256
        or session.get("worker_parent_pid") != permit.worker_parent_process_id
        or record.get("worker_session_run_sha256") != expected_session_run
        or record.get("worker_pid") != permit.worker_process_id
        or record.get("worker_pid") != session.get("worker_pid")
        or record.get("request")
        != {
            "seed": preflight.seed,
            "budget": preflight.budget,
            "method": preflight.method,
        }
    ):
        raise RuntimeError("PREPARED ledger receipt does not match the permit")
    base = dict(record)
    claimed = base.pop("prepared_ledger_sha256")
    if _sha256_json(base) != claimed:
        raise RuntimeError("PREPARED ledger receipt digest is inconsistent")
    return record


def _validated_permit_campaign(
    ledger: dict,
    *,
    permit: object,
    preflight: object,
) -> None:
    if type(getattr(permit, "_worker_session", None)) is not _FrozenAssociationWorkerSession:
        raise RuntimeError("execution permit has no parent-handshaken worker session")
    permit._worker_session.validate_current_process()
    permit._worker_session.validate_run(permit.run_key_sha256)
    if (
        permit._worker_session.session_sha256 != permit.worker_session_sha256
        or permit.worker_process_id != os.getpid()
        or permit.worker_parent_process_id != os.getppid()
    ):
        raise RuntimeError("execution permit worker session is inconsistent")
    directory = _absolute_without_symlink_resolution(
        Path(permit.ledger_directory)
    )
    if directory != _absolute_without_symlink_resolution(
        frozen_association_campaign_directory()
    ):
        raise RuntimeError("execution permit is outside the frozen campaign")
    request = FrozenAssociationSampledRunRequest(
        preflight.seed, preflight.budget, preflight.method
    )
    derived_key = frozen_association_sampled_run_key(
        request,
        fixture_sha256=preflight.fixture_sha256,
        source_sha256=preflight.source_sha256,
        configuration_sha256=preflight.configuration_sha256,
        execution_runtime_sha256=permit.execution_runtime_sha256,
    )
    if derived_key != permit.run_key_sha256:
        raise RuntimeError("execution permit run key is not derivable")
    expected_campaign = _campaign_record(
        fixture_sha256=preflight.fixture_sha256,
        source_sha256=preflight.source_sha256,
        configuration_sha256=preflight.configuration_sha256,
        execution_runtime_sha256=permit.execution_runtime_sha256,
    )
    if (
        permit.campaign_sha256 != expected_campaign["campaign_sha256"]
        or ledger.get("campaign") != expected_campaign
    ):
        raise RuntimeError("execution permit campaign manifest does not match")


def _verify_prepared_execution_permit(permit: object, preflight: object) -> None:
    ledger_directory = _absolute_without_symlink_resolution(
        Path(permit.ledger_directory)
    )
    with _locked_ledger(ledger_directory) as (_, ledger):
        _validated_permit_campaign(
            ledger, permit=permit, preflight=preflight
        )
        record = ledger["runs"].get(permit.run_key_sha256)
        _validated_prepared_record(
            record, permit=permit, preflight=preflight
        )


def _consume_prepared_execution_permit(permit: object, preflight: object) -> str:
    ledger_directory = _absolute_without_symlink_resolution(
        Path(permit.ledger_directory)
    )
    with _locked_ledger(ledger_directory) as (path, ledger):
        _validated_permit_campaign(
            ledger, permit=permit, preflight=preflight
        )
        record = ledger["runs"].get(permit.run_key_sha256)
        prepared = _validated_prepared_record(
            record, permit=permit, preflight=preflight
        )
        running = dict(prepared)
        running["state"] = "RUNNING"
        running["update_started_unix_ns"] = time.time_ns()
        running["running_ledger_sha256"] = _sha256_json(running)
        _validated_running_record(running)
        ledger["runs"][permit.run_key_sha256] = running
        _atomic_write_json(path, ledger)
        return running["running_ledger_sha256"]


def _atomic_torch_save(checkpoint: object, destination: Path) -> str:
    import torch
    from heterodiff.experiments.finite_association_residual_training_torch import (
        fitted_association_checkpoint_payload,
    )

    payload = fitted_association_checkpoint_payload(checkpoint)
    temporary_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w+b", dir=str(destination.parent), prefix=".checkpoint-", delete=False
        ) as handle:
            temporary_name = handle.name
        with open(temporary_name, "wb") as handle:
            torch.save(payload, handle)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, destination)
        temporary_name = None
        _fsync_directory(destination.parent)
        return _sha256_file(destination)
    finally:
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass


def load_successful_frozen_association_checkpoint(run_key_sha256: object):
    """Load one checkpoint only through its canonical campaign SUCCESS receipt."""

    run_key = _lower_sha256(run_key_sha256, name="run_key_sha256")
    directory = _absolute_without_symlink_resolution(
        frozen_association_campaign_directory()
    )
    from heterodiff.experiments.finite_association_residual_training_torch import (
        _ledger_verified_fitted_association_checkpoint,
        load_fitted_association_checkpoint,
    )

    with _locked_ledger(directory, create=False) as (_, ledger):
        campaign = ledger.get("campaign")
        if not isinstance(campaign, dict):
            raise RuntimeError("canonical campaign manifest is absent")
        record = ledger["runs"].get(run_key)
        if not isinstance(record, dict) or record.get("state") != "SUCCESS":
            raise RuntimeError("run key has no canonical SUCCESS receipt")
        _validated_parent_observed_success_record(record)
        request = FrozenAssociationSampledRunRequest(**record.get("request", {}))
        runtime = record.get("runtime")
        runtime = _validated_runtime_record(runtime)
        runtime_sha = runtime["sha256"]
        session = _validated_worker_session_record(record.get("worker_session"))
        if session["worker_pid"] != record.get("worker_pid"):
            raise RuntimeError("SUCCESS worker session differs from its worker PID")
        launch = _validated_launch_authorization_record(
            ledger["launch_authorizations"].get(
                session["launch_authorization_sha256"]
            )
        )
        if (
            launch["state"] != "CONSUMED"
            or launch["consumed_receipt_sha256"]
            != session["launch_receipt_sha256"]
            or launch["request"] != record.get("request")
            or launch["child_process_id"] != session["worker_pid"]
            or launch["parent_process_id"] != session["worker_parent_pid"]
            or launch["worker_token_sha256"]
            != session["worker_token_sha256"]
        ):
            raise RuntimeError(
                "SUCCESS worker session lacks canonical launch authorization"
            )
        if record.get("worker_session_run_sha256") != _worker_session_run_sha256(
            session["session_sha256"], run_key
        ):
            raise RuntimeError("SUCCESS worker session/run binding is inconsistent")
        reused_session_keys = tuple(
            key
            for key, other in ledger["runs"].items()
            if isinstance(other, dict)
            and isinstance(other.get("worker_session"), dict)
            and other["worker_session"].get("session_sha256")
            == session["session_sha256"]
        )
        if reused_session_keys != (run_key,):
            raise RuntimeError("worker session was reused across sampled run keys")
        preflight_record = record.get("preflight")
        if not isinstance(preflight_record, dict):
            raise RuntimeError("SUCCESS receipt has no preflight")
        derived_key = frozen_association_sampled_run_key(
            request,
            fixture_sha256=preflight_record.get("fixture_sha256"),
            source_sha256=preflight_record.get("source_sha256"),
            configuration_sha256=preflight_record.get("configuration_sha256"),
            execution_runtime_sha256=runtime_sha,
        )
        if derived_key != run_key or record.get("run_key_sha256") != run_key:
            raise RuntimeError("SUCCESS receipt run key is inconsistent")
        expected_campaign = _campaign_record(
            fixture_sha256=preflight_record["fixture_sha256"],
            source_sha256=preflight_record["source_sha256"],
            configuration_sha256=preflight_record["configuration_sha256"],
            execution_runtime_sha256=runtime_sha,
        )
        if campaign != expected_campaign:
            raise RuntimeError("SUCCESS receipt is outside the frozen campaign")
        checkpoint_name = "%s.pt" % run_key
        if record.get("checkpoint_file") != checkpoint_name:
            raise RuntimeError("SUCCESS checkpoint filename is inconsistent")
        checkpoint_path = directory / checkpoint_name
        checkpoint_sha = _lower_sha256(
            record.get("checkpoint_sha256"), name="checkpoint_sha256"
        )
        checkpoint = load_fitted_association_checkpoint(
            checkpoint_path, expected_sha256=checkpoint_sha
        )
        expected_runtime_environment = {
            "python_version": runtime.get("python"),
            "numpy_version": runtime.get("numpy"),
            "scipy_version": runtime.get("scipy"),
            "torch_version": runtime.get("torch"),
            "torch_cpu_only": runtime.get("torch_environment", {}).get(
                "torch_cpu_only"
            ),
            "torch_threads": runtime.get("torch_environment", {}).get(
                "torch_threads"
            ),
            "torch_interop_threads": runtime.get("torch_environment", {}).get(
                "torch_interop_threads"
            ),
            "deterministic_algorithms": runtime.get(
                "torch_environment", {}
            ).get("deterministic_algorithms"),
        }
        if (
            runtime.get("schema") != _RUNTIME_SCHEMA
            or runtime.get("threadpoolctl") != "3.6.0"
            or runtime.get("torch_environment")
            != asdict(checkpoint.environment)
            or expected_runtime_environment != asdict(checkpoint.environment)
            or runtime.get("thread_environment")
            != {
                **{name: "1" for name in _THREAD_ENVIRONMENT},
                "PYTHONHASHSEED": "0",
                "CUDA_VISIBLE_DEVICES": "",
            }
            or not isinstance(runtime.get("native_pools"), list)
            or not runtime["native_pools"]
            or any(
                not isinstance(pool, dict) or pool.get("num_threads") != 1
                for pool in runtime["native_pools"]
            )
        ):
            raise RuntimeError("SUCCESS runtime differs from checkpoint custody")
        if checkpoint.execution_runtime_sha256 != runtime_sha:
            raise RuntimeError("checkpoint is bound to a different execution runtime")
        comparisons = {
            "run_key_sha256": checkpoint.run_key_sha256,
            "prepared_ledger_sha256": checkpoint.prepared_ledger_sha256,
            "classifier_sha256": checkpoint.classifier_sha256,
            "certificate_sha256": checkpoint.certificate.certificate_sha256,
            "certified_maximum_absolute_correction": (
                checkpoint.certificate.certified_maximum_absolute_correction
            ),
            "parameter_sha256": checkpoint.final_snapshot.parameter_sha256,
            "final_empirical_risk": checkpoint.final_empirical_risk,
            "maximum_unclipped_gradient_norm": (
                checkpoint.maximum_unclipped_gradient_norm
            ),
            "optimizer_steps_taken": checkpoint.optimizer_steps_taken,
            "optimizer_transcript_sha256": (
                checkpoint.optimizer_transcript_sha256
            ),
            "optimizer_completion_receipt_sha256": (
                checkpoint.optimizer_completion_receipt.completion_receipt_sha256
            ),
            "optimizer_wall_seconds": checkpoint.elapsed_training_seconds,
            "total_wall_seconds": checkpoint.total_wall_seconds,
            "total_cpu_seconds": checkpoint.total_cpu_seconds,
            "process_peak_rss_bytes": checkpoint.process_peak_rss_bytes,
        }
        for name, actual in comparisons.items():
            if record.get(name) != actual:
                raise RuntimeError(
                    "SUCCESS receipt field %s is inconsistent" % name
                )
        if _canonical_json(preflight_record) != _canonical_json(
            asdict(checkpoint.preflight)
        ):
            raise RuntimeError("SUCCESS preflight differs from checkpoint")
        completion = asdict(checkpoint.optimizer_completion_receipt)
        _validated_optimizer_completion_receipt_record(completion)
        if (
            record.get("optimizer_completion_receipt") != completion
            or completion["campaign_sha256"] != campaign["campaign_sha256"]
        ):
            raise RuntimeError(
                "SUCCESS completion receipt differs from checkpoint/campaign"
            )
        success_receipt_sha256 = record["success_ledger_sha256"]
        return _ledger_verified_fitted_association_checkpoint(
            checkpoint,
            success_receipt_sha256=success_receipt_sha256,
            campaign_sha256=campaign["campaign_sha256"],
            running_ledger_sha256=record["running_ledger_sha256"],
            optimizer_completion_receipt_sha256=completion[
                "completion_receipt_sha256"
            ],
            worker_session_sha256=session["session_sha256"],
            launch_authorization_sha256=session[
                "launch_authorization_sha256"
            ],
            launch_receipt_sha256=session["launch_receipt_sha256"],
            worker_process_id=session["worker_pid"],
            worker_parent_process_id=session["worker_parent_pid"],
            worker_process_identity_sha256=(
                _worker_process_identity_sha256(session)
            ),
            preparation_cpu_seconds=record.get("preparation_cpu_seconds"),
            preparation_wall_seconds=record.get("preparation_wall_seconds"),
        )


def revalidate_successful_frozen_association_checkpoint(verified: object) -> None:
    """Re-open canonical custody before admitting an already loaded wrapper.

    The wrapper's private construction token is API hygiene, not an
    authentication claim.  This check makes production admission depend on
    the current canonical SUCCESS ledger and checkpoint bytes rather than on
    possession of an in-memory Python object alone.
    """

    from heterodiff.experiments.finite_association_residual_training_torch import (
        LedgerVerifiedFittedAssociationCheckpoint,
        _require_fitted_checkpoint_integrity,
    )

    if type(verified) is not LedgerVerifiedFittedAssociationCheckpoint:
        raise TypeError("checkpoint must be a canonical SUCCESS-ledger wrapper")
    checkpoint = verified.checkpoint
    _require_fitted_checkpoint_integrity(checkpoint)
    canonical = load_successful_frozen_association_checkpoint(
        checkpoint.run_key_sha256
    )
    canonical_checkpoint = canonical.checkpoint
    if (
        verified.success_receipt_sha256 != canonical.success_receipt_sha256
        or verified.campaign_sha256 != canonical.campaign_sha256
        or verified.running_ledger_sha256 != canonical.running_ledger_sha256
        or verified.optimizer_completion_receipt_sha256
        != canonical.optimizer_completion_receipt_sha256
        or verified.worker_session_sha256 != canonical.worker_session_sha256
        or verified.launch_authorization_sha256
        != canonical.launch_authorization_sha256
        or verified.launch_receipt_sha256 != canonical.launch_receipt_sha256
        or verified.worker_process_id != canonical.worker_process_id
        or verified.worker_parent_process_id
        != canonical.worker_parent_process_id
        or verified.worker_process_identity_sha256
        != canonical.worker_process_identity_sha256
        or verified.preparation_cpu_seconds
        != canonical.preparation_cpu_seconds
        or verified.preparation_wall_seconds
        != canonical.preparation_wall_seconds
        or checkpoint.preflight != canonical_checkpoint.preflight
        or checkpoint.environment != canonical_checkpoint.environment
        or checkpoint.run_key_sha256 != canonical_checkpoint.run_key_sha256
        or checkpoint.prepared_ledger_sha256
        != canonical_checkpoint.prepared_ledger_sha256
        or checkpoint.execution_runtime_sha256
        != canonical_checkpoint.execution_runtime_sha256
        or checkpoint.classifier_sha256
        != canonical_checkpoint.classifier_sha256
        or checkpoint.final_snapshot.parameter_sha256
        != canonical_checkpoint.final_snapshot.parameter_sha256
        or checkpoint.certificate.certificate_sha256
        != canonical_checkpoint.certificate.certificate_sha256
        or checkpoint.final_empirical_risk
        != canonical_checkpoint.final_empirical_risk
        or checkpoint.maximum_unclipped_gradient_norm
        != canonical_checkpoint.maximum_unclipped_gradient_norm
        or checkpoint.optimizer_steps_taken
        != canonical_checkpoint.optimizer_steps_taken
        or checkpoint.optimizer_transcript_sha256
        != canonical_checkpoint.optimizer_transcript_sha256
        or checkpoint.optimizer_completion_receipt
        != canonical_checkpoint.optimizer_completion_receipt
        or checkpoint.elapsed_training_seconds
        != canonical_checkpoint.elapsed_training_seconds
        or checkpoint.total_cpu_seconds != canonical_checkpoint.total_cpu_seconds
        or checkpoint.total_wall_seconds
        != canonical_checkpoint.total_wall_seconds
        or checkpoint.process_peak_rss_bytes
        != canonical_checkpoint.process_peak_rss_bytes
    ):
        raise RuntimeError(
            "in-memory checkpoint differs from canonical SUCCESS custody"
        )


def _sampled_aggregate_custody_sha256(ledger: dict) -> str:
    return _sha256_json(
        {
            "schema": "heterodiff-a1-sampled-aggregate-custody-snapshot-v1",
            "campaign": ledger.get("campaign"),
            "launch_authorizations": ledger.get("launch_authorizations"),
            "runs": ledger.get("runs"),
        }
    )


def _canonical_sampled_primary_coordinates(
) -> Tuple[Tuple[int, int, str], ...]:
    """Return the frozen direct/guided barrier in interleaved order."""

    return tuple(
        (seed, budget, method)
        for seed in _SEEDS
        for budget in _BUDGETS
        for method in ("direct", "guided")
    )


def _primary_coordinate_manifest_sha256() -> str:
    return _sha256_json(
        {
            "schema": "heterodiff-a1-sampled-primary-coordinate-manifest-v1",
            "coordinates": [
                {"seed": seed, "budget": budget, "method": method}
                for seed, budget, method in (
                    _canonical_sampled_primary_coordinates()
                )
            ],
        }
    )


def _primary_success_set_custody_sha256(ledger: dict) -> str:
    """Digest every mutable ledger field relevant to primary admission."""

    return _sha256_json(
        {
            "schema": "heterodiff-a1-sampled-primary-custody-snapshot-v1",
            "campaign": ledger.get("campaign"),
            "launch_authorizations": ledger.get("launch_authorizations"),
            "runs": ledger.get("runs"),
            "aggregate": ledger.get("aggregate"),
        }
    )


def _assemble_frozen_association_primary_success_set(
    directory: Path,
    ledger: dict,
    *,
    checkpoint_loader=None,
    require_production_wrappers: bool = True,
    allow_post_primary_state: bool = False,
):
    """Reopen exactly the 48 primary SUCCESS payloads, without aggregating.

    This stage-scoped admission deliberately rejects every sampled control
    coordinate and any full-campaign aggregate.  It therefore proves that the
    primary metric barrier was reached before controls could start.  The
    synthetic-loader option is private and exists only for no-update tests;
    public admission always requires canonical checkpoint wrapper types.
    """

    if type(require_production_wrappers) is not bool:
        raise TypeError("require_production_wrappers must be boolean")
    if type(allow_post_primary_state) is not bool:
        raise TypeError("allow_post_primary_state must be boolean")
    from heterodiff.experiments.finite_association_guided_residual_pilot import (
        frozen_association_fixture_sha256,
    )
    from heterodiff.experiments.finite_association_residual_training_torch import (
        LedgerVerifiedFittedAssociationCheckpoint,
        _require_fitted_checkpoint_integrity,
        frozen_association_training_configuration_sha256,
        frozen_association_training_source_sha256,
    )

    if ledger.get("aggregate") is not None and not allow_post_primary_state:
        raise RuntimeError(
            "primary success-set admission rejects a sampled aggregate"
        )
    campaign = ledger.get("campaign")
    if not isinstance(campaign, dict):
        raise RuntimeError("sampled primary campaign manifest is absent")
    runtime_sha256 = _lower_sha256(
        campaign.get("execution_runtime_sha256"),
        name="execution_runtime_sha256",
    )
    source_sha256 = frozen_association_training_source_sha256()
    configuration_sha256 = frozen_association_training_configuration_sha256(
        source_sha256=source_sha256
    )
    fixture_sha256 = frozen_association_fixture_sha256()
    expected_campaign = _campaign_record(
        fixture_sha256=fixture_sha256,
        source_sha256=source_sha256,
        configuration_sha256=configuration_sha256,
        execution_runtime_sha256=runtime_sha256,
    )
    if campaign != expected_campaign:
        raise RuntimeError("sampled primary campaign has stale custody")

    coordinates = _canonical_sampled_primary_coordinates()
    expected_run_keys = []
    for seed, budget, method in coordinates:
        request = FrozenAssociationSampledRunRequest(seed, budget, method)
        expected_run_keys.append(
            frozen_association_sampled_run_key(
                request,
                fixture_sha256=fixture_sha256,
                source_sha256=source_sha256,
                configuration_sha256=configuration_sha256,
                execution_runtime_sha256=runtime_sha256,
            )
        )
    runs = ledger.get("runs")
    authorizations = ledger.get("launch_authorizations")
    expected_run_key_set = set(expected_run_keys)
    allowed_post_primary_run_keys = {
        frozen_association_sampled_run_key(
            FrozenAssociationSampledRunRequest(seed, budget, method),
            fixture_sha256=fixture_sha256,
            source_sha256=source_sha256,
            configuration_sha256=configuration_sha256,
            execution_runtime_sha256=runtime_sha256,
        )
        for seed, budget, method in _canonical_sampled_coordinates()
    }
    if not isinstance(runs, dict) or (
        (
            not allow_post_primary_state
            and set(runs) != expected_run_key_set
        )
        or (
            allow_post_primary_state
            and (
                not expected_run_key_set.issubset(set(runs))
                or not set(runs).issubset(allowed_post_primary_run_keys)
            )
        )
    ):
        raise RuntimeError(
            "primary success-set requires exactly 48 canonical run keys"
        )
    if not isinstance(authorizations, dict) or (
        (
            not allow_post_primary_state
            and len(authorizations) != len(coordinates)
        )
        or (
            allow_post_primary_state
            and len(authorizations) < len(coordinates)
        )
    ):
        raise RuntimeError(
            "primary success-set requires exactly 48 launch authorizations"
        )

    loader = (
        load_successful_frozen_association_checkpoint
        if checkpoint_loader is None
        else checkpoint_loader
    )
    wrappers = []
    identities = []
    preflights = {}
    used = {
        name: set()
        for name in (
            "run_key_sha256",
            "success_ledger_sha256",
            "exit_observation_receipt_sha256",
            "worker_process_identity_sha256",
            "worker_session_sha256",
            "launch_authorization_sha256",
            "launch_receipt_sha256",
            "optimizer_completion_receipt_sha256",
            "checkpoint_sha256",
        )
    }
    for ordinal, (coordinate, run_key) in enumerate(
        zip(coordinates, expected_run_keys)
    ):
        seed, budget, method = coordinate
        record = _validated_parent_observed_success_record(runs.get(run_key))
        request = FrozenAssociationSampledRunRequest(**record.get("request", {}))
        if (request.seed, request.budget, request.method) != coordinate:
            raise RuntimeError("sampled primary SUCCESS request order changed")
        runtime = _validated_runtime_record(record.get("runtime"))
        if runtime["sha256"] != runtime_sha256:
            raise RuntimeError(
                "sampled primary SUCCESS runtime changed within campaign"
            )
        session = _validated_worker_session_record(record.get("worker_session"))
        launch = _validated_launch_authorization_record(
            authorizations.get(session["launch_authorization_sha256"])
        )
        if (
            launch["state"] != "CONSUMED"
            or launch["consumed_receipt_sha256"]
            != session["launch_receipt_sha256"]
            or launch["request"] != asdict(request)
            or launch["child_process_id"] != session["worker_pid"]
            or launch["parent_process_id"] != session["worker_parent_pid"]
            or launch["ledger_directory"] != str(directory.resolve())
        ):
            raise RuntimeError(
                "sampled primary SUCCESS launch/session custody is inconsistent"
            )
        preflight_record = record.get("preflight")
        if not isinstance(preflight_record, dict):
            raise RuntimeError("sampled primary SUCCESS preflight is absent")
        derived_key = frozen_association_sampled_run_key(
            request,
            fixture_sha256=preflight_record.get("fixture_sha256"),
            source_sha256=preflight_record.get("source_sha256"),
            configuration_sha256=preflight_record.get("configuration_sha256"),
            execution_runtime_sha256=runtime_sha256,
        )
        if (
            derived_key != run_key
            or record.get("run_key_sha256") != run_key
            or preflight_record.get("source_sha256") != source_sha256
            or preflight_record.get("configuration_sha256")
            != configuration_sha256
            or preflight_record.get("fixture_sha256") != fixture_sha256
        ):
            raise RuntimeError(
                "sampled primary SUCCESS run/preflight custody changed"
            )
        completion = _validated_optimizer_completion_receipt_record(
            record.get("optimizer_completion_receipt")
        )
        if (
            completion["completion_receipt_sha256"]
            != record.get("optimizer_completion_receipt_sha256")
            or completion["campaign_sha256"] != campaign["campaign_sha256"]
        ):
            raise RuntimeError(
                "sampled primary optimizer completion custody changed"
            )
        wrapper = loader(run_key)
        if require_production_wrappers and type(
            wrapper
        ) is not LedgerVerifiedFittedAssociationCheckpoint:
            raise TypeError(
                "primary success-set loader returned a noncanonical checkpoint"
            )
        checkpoint = wrapper.checkpoint
        if require_production_wrappers:
            _require_fitted_checkpoint_integrity(checkpoint)
        if (
            wrapper.success_receipt_sha256 != record["success_ledger_sha256"]
            or wrapper.campaign_sha256 != campaign["campaign_sha256"]
            or _canonical_json(asdict(checkpoint.preflight))
            != _canonical_json(preflight_record)
            or checkpoint.run_key_sha256 != run_key
            or checkpoint.optimizer_completion_receipt.completion_receipt_sha256
            != completion["completion_receipt_sha256"]
        ):
            raise RuntimeError(
                "sampled primary checkpoint differs from SUCCESS custody"
            )
        process_identity = _worker_process_identity_sha256(session)
        identity = {
            "ordinal": ordinal,
            "seed": seed,
            "budget": budget,
            "method": method,
            "run_key_sha256": run_key,
            "preflight_sha256": checkpoint.preflight.preflight_sha256,
            "prepared_ledger_sha256": record["prepared_ledger_sha256"],
            "running_ledger_sha256": record["running_ledger_sha256"],
            "success_ledger_sha256": record["success_ledger_sha256"],
            "exit_observation_receipt_sha256": record[
                "exit_observation_receipt_sha256"
            ],
            "worker_process_identity_sha256": process_identity,
            "worker_session_sha256": session["session_sha256"],
            "launch_authorization_sha256": session[
                "launch_authorization_sha256"
            ],
            "launch_receipt_sha256": session["launch_receipt_sha256"],
            "execution_runtime_sha256": runtime_sha256,
            "campaign_sha256": campaign["campaign_sha256"],
            "optimizer_completion_receipt_sha256": completion[
                "completion_receipt_sha256"
            ],
            "checkpoint_sha256": record["checkpoint_sha256"],
            "classifier_sha256": checkpoint.classifier_sha256,
            "parameter_sha256": checkpoint.final_snapshot.parameter_sha256,
            "certificate_sha256": checkpoint.certificate.certificate_sha256,
            "feature_sha256": checkpoint.certificate.feature_sha256,
            "optimizer_steps_taken": checkpoint.optimizer_steps_taken,
            "optimizer_transcript_sha256": (
                checkpoint.optimizer_transcript_sha256
            ),
        }
        for name, observed in used.items():
            item = identity[name]
            if item in observed:
                raise RuntimeError("sampled primary reuses %s" % name)
            observed.add(item)
        preflights[coordinate] = checkpoint.preflight
        wrappers.append(wrapper)
        identities.append(identity)

    if (
        not allow_post_primary_state
        and used["launch_authorization_sha256"] != set(authorizations)
    ):
        raise RuntimeError(
            "primary success-set has unused launch authorizations"
        )

    # The primary comparison is paired within seed/budget and nested in budget.
    for seed in _SEEDS:
        seed_preflights = [
            preflights[(seed, budget, method)]
            for budget in _BUDGETS
            for method in ("direct", "guided")
        ]
        for name in (
            "custody_sha256",
            "all_dataset_sha256",
            "all_batch_schedule_sha256",
        ):
            if len({getattr(value, name) for value in seed_preflights}) != 1:
                raise RuntimeError("sampled primary seed does not share one %s" % name)
        for method in ("direct", "guided"):
            if len(
                {
                    preflights[(seed, budget, method)].initial_parameter_sha256
                    for budget in _BUDGETS
                }
            ) != 1:
                raise RuntimeError(
                    "sampled primary initialization changes across budgets"
                )
        for budget in _BUDGETS:
            pair = [
                preflights[(seed, budget, method)]
                for method in ("direct", "guided")
            ]
            if len({value.dataset_sha256 for value in pair}) != 1:
                raise RuntimeError(
                    "sampled primary paired methods use different datasets"
                )
            if len({value.batch_schedule_sha256 for value in pair}) != 1:
                raise RuntimeError(
                    "sampled primary paired methods use different schedules"
                )
            if len({value.initial_parameter_sha256 for value in pair}) != 1:
                raise RuntimeError(
                    "sampled primary paired methods use different initializations"
                )

    ordered_success_sha256 = _sha256_json(
        {
            "schema": "heterodiff-a1-sampled-primary-ordered-success-v1",
            "identities": identities,
        }
    )
    ordered_checkpoint_sha256 = _sha256_json(
        {
            "schema": "heterodiff-a1-sampled-primary-ordered-checkpoints-v1",
            "checkpoints": [
                {
                    "run_key_sha256": item["run_key_sha256"],
                    "checkpoint_sha256": item["checkpoint_sha256"],
                    "optimizer_completion_receipt_sha256": item[
                        "optimizer_completion_receipt_sha256"
                    ],
                    "parameter_sha256": item["parameter_sha256"],
                    "classifier_sha256": item["classifier_sha256"],
                    "certificate_sha256": item["certificate_sha256"],
                    "feature_sha256": item["feature_sha256"],
                }
                for item in identities
            ],
        }
    )
    success_set_body = {
        "schema": "heterodiff-a1-sampled-primary-success-set-v1",
        "campaign_sha256": campaign["campaign_sha256"],
        "source_sha256": source_sha256,
        "configuration_sha256": configuration_sha256,
        "fixture_sha256": fixture_sha256,
        "execution_runtime_sha256": runtime_sha256,
        "coordinate_manifest_sha256": _primary_coordinate_manifest_sha256(),
        "ordered_success_receipts_sha256": ordered_success_sha256,
        "ordered_checkpoint_sha256": ordered_checkpoint_sha256,
        "coordinate_count": len(coordinates),
        "total_optimizer_steps_taken": sum(
            item["optimizer_steps_taken"] for item in identities
        ),
        "fresh_metric_recomputation_required": True,
        "execution_order_attested": False,
        "scientific_decision_eligible": False,
    }
    if success_set_body["total_optimizer_steps_taken"] != 144_000:
        raise RuntimeError("sampled primary optimizer total is not 144000")
    success_set = dict(success_set_body)
    success_set["primary_success_set_sha256"] = _sha256_json(success_set_body)
    return tuple(wrappers), tuple(identities), success_set


_VERIFIED_PRIMARY_SUCCESS_SET_KEY = object()


class LedgerVerifiedFrozenAssociationPrimarySuccessSet:
    """Loader-only, immutable admission of the exact 48 primary learners."""

    __slots__ = (
        "_checkpoints",
        "_checkpoint_identities",
        "_campaign_sha256",
        "_source_sha256",
        "_configuration_sha256",
        "_fixture_sha256",
        "_execution_runtime_sha256",
        "_coordinate_manifest_sha256",
        "_ordered_success_receipts_sha256",
        "_ordered_checkpoint_sha256",
        "_primary_success_set_sha256",
        "_locked",
    )

    def __init__(
        self,
        checkpoints: tuple,
        identities: tuple,
        success_set: dict,
        *,
        _construction_key: object,
    ) -> None:
        if _construction_key is not _VERIFIED_PRIMARY_SUCCESS_SET_KEY:
            raise TypeError(
                "primary success-set wrappers come only from the canonical loader"
            )
        from heterodiff.experiments.finite_association_residual_training_torch import (
            LedgerVerifiedFittedAssociationCheckpoint,
            _require_fitted_checkpoint_integrity,
        )

        coordinates = _canonical_sampled_primary_coordinates()
        if type(checkpoints) is not tuple or len(checkpoints) != len(coordinates):
            raise TypeError("primary success-set requires 48 checkpoint wrappers")
        if any(
            type(value) is not LedgerVerifiedFittedAssociationCheckpoint
            for value in checkpoints
        ):
            raise TypeError("primary success-set requires canonical wrappers")
        if type(identities) is not tuple or len(identities) != len(coordinates):
            raise TypeError("primary success-set identities are incomplete")
        checked_identities = []
        for coordinate, wrapper, member in zip(
            coordinates, checkpoints, identities
        ):
            checkpoint = wrapper.checkpoint
            _require_fitted_checkpoint_integrity(checkpoint)
            observed = (
                checkpoint.preflight.seed,
                checkpoint.preflight.budget,
                checkpoint.preflight.method,
                checkpoint.run_key_sha256,
                wrapper.success_receipt_sha256,
                checkpoint.optimizer_completion_receipt.completion_receipt_sha256,
                checkpoint.final_snapshot.parameter_sha256,
                checkpoint.classifier_sha256,
                checkpoint.certificate.certificate_sha256,
                checkpoint.certificate.feature_sha256,
            )
            expected = (
                *coordinate,
                member["run_key_sha256"],
                member["success_ledger_sha256"],
                member["optimizer_completion_receipt_sha256"],
                member["parameter_sha256"],
                member["classifier_sha256"],
                member["certificate_sha256"],
                member["feature_sha256"],
            )
            if observed != expected:
                raise RuntimeError(
                    "primary success-set wrapper identity is inconsistent"
                )
            checked_identities.append(observed)
        expected_fields = {
            "schema",
            "campaign_sha256",
            "source_sha256",
            "configuration_sha256",
            "fixture_sha256",
            "execution_runtime_sha256",
            "coordinate_manifest_sha256",
            "ordered_success_receipts_sha256",
            "ordered_checkpoint_sha256",
            "coordinate_count",
            "total_optimizer_steps_taken",
            "fresh_metric_recomputation_required",
            "execution_order_attested",
            "scientific_decision_eligible",
            "primary_success_set_sha256",
        }
        if type(success_set) is not dict or set(success_set) != expected_fields:
            raise RuntimeError("primary success-set record has an invalid schema")
        body = dict(success_set)
        claimed = _lower_sha256(
            body.pop("primary_success_set_sha256"),
            name="primary_success_set_sha256",
        )
        if (
            success_set["schema"]
            != "heterodiff-a1-sampled-primary-success-set-v1"
            or success_set["coordinate_manifest_sha256"]
            != _primary_coordinate_manifest_sha256()
            or success_set["coordinate_count"] != 48
            or success_set["total_optimizer_steps_taken"] != 144_000
            or success_set["fresh_metric_recomputation_required"] is not True
            or success_set["execution_order_attested"] is not False
            or success_set["scientific_decision_eligible"] is not False
            or _sha256_json(body) != claimed
        ):
            raise RuntimeError("primary success-set record is inconsistent")
        object.__setattr__(self, "_checkpoints", checkpoints)
        object.__setattr__(
            self, "_checkpoint_identities", tuple(checked_identities)
        )
        for name in (
            "campaign_sha256",
            "source_sha256",
            "configuration_sha256",
            "fixture_sha256",
            "execution_runtime_sha256",
            "coordinate_manifest_sha256",
            "ordered_success_receipts_sha256",
            "ordered_checkpoint_sha256",
            "primary_success_set_sha256",
        ):
            object.__setattr__(self, "_" + name, success_set[name])
        object.__setattr__(self, "_locked", True)

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_locked", False):
            raise AttributeError("primary success-set wrapper is immutable")
        object.__setattr__(self, name, value)

    def assert_integrity(self) -> None:
        from heterodiff.experiments.finite_association_residual_training_torch import (
            _require_fitted_checkpoint_integrity,
        )

        identities = []
        for wrapper in self._checkpoints:
            checkpoint = wrapper.checkpoint
            _require_fitted_checkpoint_integrity(checkpoint)
            identities.append(
                (
                    checkpoint.preflight.seed,
                    checkpoint.preflight.budget,
                    checkpoint.preflight.method,
                    checkpoint.run_key_sha256,
                    wrapper.success_receipt_sha256,
                    checkpoint.optimizer_completion_receipt.completion_receipt_sha256,
                    checkpoint.final_snapshot.parameter_sha256,
                    checkpoint.classifier_sha256,
                    checkpoint.certificate.certificate_sha256,
                    checkpoint.certificate.feature_sha256,
                )
            )
        if tuple(identities) != self._checkpoint_identities:
            raise RuntimeError(
                "primary success-set checkpoint changed after admission"
            )

    @property
    def checkpoints(self) -> tuple:
        self.assert_integrity()
        return self._checkpoints

    @property
    def coordinates(self) -> Tuple[Tuple[int, int, str], ...]:
        return _canonical_sampled_primary_coordinates()

    @property
    def campaign_sha256(self) -> str:
        return self._campaign_sha256

    @property
    def source_sha256(self) -> str:
        return self._source_sha256

    @property
    def configuration_sha256(self) -> str:
        return self._configuration_sha256

    @property
    def fixture_sha256(self) -> str:
        return self._fixture_sha256

    @property
    def execution_runtime_sha256(self) -> str:
        return self._execution_runtime_sha256

    @property
    def coordinate_manifest_sha256(self) -> str:
        return self._coordinate_manifest_sha256

    @property
    def ordered_success_receipts_sha256(self) -> str:
        return self._ordered_success_receipts_sha256

    @property
    def ordered_checkpoint_sha256(self) -> str:
        return self._ordered_checkpoint_sha256

    @property
    def primary_success_set_sha256(self) -> str:
        return self._primary_success_set_sha256

    @property
    def fresh_metric_recomputation_required(self) -> bool:
        return True

    @property
    def execution_order_attested(self) -> bool:
        return False

    @property
    def scientific_decision_eligible(self) -> bool:
        return False


def _admit_primary_success_set(
    checkpoints: tuple, identities: tuple, success_set: dict
) -> LedgerVerifiedFrozenAssociationPrimarySuccessSet:
    return LedgerVerifiedFrozenAssociationPrimarySuccessSet(
        checkpoints,
        identities,
        success_set,
        _construction_key=_VERIFIED_PRIMARY_SUCCESS_SET_KEY,
    )


def load_completed_frozen_association_primary_success_set(
) -> LedgerVerifiedFrozenAssociationPrimarySuccessSet:
    """Load the exact pre-control 48-primary barrier from canonical custody."""

    directory = _absolute_without_symlink_resolution(
        frozen_association_campaign_directory()
    )
    with _locked_ledger(directory, create=False) as (_, ledger):
        snapshot = ledger
        custody_sha256 = _primary_success_set_custody_sha256(snapshot)
    checkpoints, identities, success_set = (
        _assemble_frozen_association_primary_success_set(directory, snapshot)
    )
    with _locked_ledger(directory, create=False) as (_, current):
        if _primary_success_set_custody_sha256(current) != custody_sha256:
            raise RuntimeError(
                "sampled primary custody changed while it was loading"
            )
    return _admit_primary_success_set(checkpoints, identities, success_set)


def revalidate_completed_frozen_association_primary_success_set(
    admitted: object,
) -> LedgerVerifiedFrozenAssociationPrimarySuccessSet:
    """Reopen the pre-control barrier and match an earlier loader admission."""

    if type(admitted) is not LedgerVerifiedFrozenAssociationPrimarySuccessSet:
        raise TypeError("primary success-set revalidation requires loader admission")
    admitted.assert_integrity()
    fresh = load_completed_frozen_association_primary_success_set()
    for name in (
        "campaign_sha256",
        "source_sha256",
        "configuration_sha256",
        "fixture_sha256",
        "execution_runtime_sha256",
        "coordinate_manifest_sha256",
        "ordered_success_receipts_sha256",
        "ordered_checkpoint_sha256",
        "primary_success_set_sha256",
    ):
        if getattr(fresh, name) != getattr(admitted, name):
            raise RuntimeError(
                "canonical primary success-set changed on revalidation"
            )
    return fresh


def _assemble_complete_frozen_association_sampled_campaign(
    directory: Path,
    ledger: dict,
    *,
    checkpoint_loader=None,
    require_production_wrappers: bool = True,
):
    """Reopen all 120 members and construct the deterministic aggregate body.

    ``require_production_wrappers=False`` is reserved for synthetic no-update
    unit tests.  Public finalization/loading always uses the fail-closed
    default and can mint the loader-only campaign wrapper only from exact
    canonical checkpoint wrappers.
    """

    if type(require_production_wrappers) is not bool:
        raise TypeError("require_production_wrappers must be boolean")
    from heterodiff.experiments.finite_association_guided_residual_pilot import (
        frozen_association_fixture_sha256,
    )
    from heterodiff.experiments.finite_association_residual_training_torch import (
        LedgerVerifiedFittedAssociationCheckpoint,
        _require_fitted_checkpoint_integrity,
        frozen_association_training_configuration_sha256,
        frozen_association_training_source_sha256,
    )

    loader = (
        load_successful_frozen_association_checkpoint
        if checkpoint_loader is None
        else checkpoint_loader
    )
    campaign = ledger.get("campaign")
    if not isinstance(campaign, dict):
        raise RuntimeError("sampled campaign manifest is absent")
    runtime_sha256 = _lower_sha256(
        campaign.get("execution_runtime_sha256"),
        name="execution_runtime_sha256",
    )
    source_sha256 = frozen_association_training_source_sha256()
    configuration_sha256 = frozen_association_training_configuration_sha256(
        source_sha256=source_sha256
    )
    fixture_sha256 = frozen_association_fixture_sha256()
    expected_campaign = _campaign_record(
        fixture_sha256=fixture_sha256,
        source_sha256=source_sha256,
        configuration_sha256=configuration_sha256,
        execution_runtime_sha256=runtime_sha256,
    )
    if campaign != expected_campaign:
        raise RuntimeError("sampled aggregate campaign has stale custody")
    coordinates = _canonical_sampled_coordinates()
    expected_run_keys = []
    for seed, budget, method in coordinates:
        request = FrozenAssociationSampledRunRequest(seed, budget, method)
        expected_run_keys.append(
            frozen_association_sampled_run_key(
                request,
                fixture_sha256=fixture_sha256,
                source_sha256=source_sha256,
                configuration_sha256=configuration_sha256,
                execution_runtime_sha256=runtime_sha256,
            )
        )
    if set(ledger.get("runs", {})) != set(expected_run_keys):
        raise RuntimeError(
            "sampled aggregate requires exactly 120 canonical run keys"
        )
    if len(ledger.get("launch_authorizations", {})) != len(coordinates):
        raise RuntimeError(
            "sampled aggregate requires exactly 120 launch authorizations"
        )

    wrappers = []
    members = []
    used_launch_authorizations = set()
    preflights = {}
    for ordinal, (coordinate, run_key) in enumerate(
        zip(coordinates, expected_run_keys)
    ):
        seed, budget, method = coordinate
        record = _validated_parent_observed_success_record(
            ledger["runs"].get(run_key)
        )
        request = FrozenAssociationSampledRunRequest(**record.get("request", {}))
        if (request.seed, request.budget, request.method) != coordinate:
            raise RuntimeError("sampled SUCCESS request order changed")
        runtime = _validated_runtime_record(record.get("runtime"))
        if runtime["sha256"] != runtime_sha256:
            raise RuntimeError("sampled SUCCESS runtime changed within campaign")
        session = _validated_worker_session_record(record.get("worker_session"))
        launch = _validated_launch_authorization_record(
            ledger["launch_authorizations"].get(
                session["launch_authorization_sha256"]
            )
        )
        if (
            launch["state"] != "CONSUMED"
            or launch["consumed_receipt_sha256"]
            != session["launch_receipt_sha256"]
            or launch["request"] != asdict(request)
            or launch["child_process_id"] != session["worker_pid"]
            or launch["parent_process_id"] != session["worker_parent_pid"]
            or launch["ledger_directory"] != str(directory.resolve())
        ):
            raise RuntimeError(
                "sampled SUCCESS launch/session custody is inconsistent"
            )
        used_launch_authorizations.add(
            session["launch_authorization_sha256"]
        )
        preflight_record = record.get("preflight")
        if not isinstance(preflight_record, dict):
            raise RuntimeError("sampled SUCCESS preflight is absent")
        derived_key = frozen_association_sampled_run_key(
            request,
            fixture_sha256=preflight_record.get("fixture_sha256"),
            source_sha256=preflight_record.get("source_sha256"),
            configuration_sha256=preflight_record.get("configuration_sha256"),
            execution_runtime_sha256=runtime_sha256,
        )
        if (
            derived_key != run_key
            or record.get("run_key_sha256") != run_key
            or preflight_record.get("source_sha256") != source_sha256
            or preflight_record.get("configuration_sha256")
            != configuration_sha256
            or preflight_record.get("fixture_sha256") != fixture_sha256
        ):
            raise RuntimeError("sampled SUCCESS run/preflight custody changed")
        completion = _validated_optimizer_completion_receipt_record(
            record.get("optimizer_completion_receipt")
        )
        if (
            completion["completion_receipt_sha256"]
            != record.get("optimizer_completion_receipt_sha256")
            or completion["campaign_sha256"] != campaign["campaign_sha256"]
        ):
            raise RuntimeError("sampled optimizer completion custody changed")
        wrapper = loader(run_key)
        if require_production_wrappers and type(
            wrapper
        ) is not LedgerVerifiedFittedAssociationCheckpoint:
            raise TypeError(
                "sampled aggregate loader returned a noncanonical checkpoint"
            )
        checkpoint = wrapper.checkpoint
        if require_production_wrappers:
            _require_fitted_checkpoint_integrity(checkpoint)
        if (
            wrapper.success_receipt_sha256 != record["success_ledger_sha256"]
            or wrapper.campaign_sha256 != campaign["campaign_sha256"]
            or _canonical_json(asdict(checkpoint.preflight))
            != _canonical_json(preflight_record)
            or checkpoint.run_key_sha256 != run_key
            or checkpoint.optimizer_completion_receipt.completion_receipt_sha256
            != completion["completion_receipt_sha256"]
        ):
            raise RuntimeError(
                "sampled checkpoint wrapper differs from SUCCESS custody"
            )
        preflights[coordinate] = checkpoint.preflight
        wrappers.append(wrapper)
        resources = {
            "preparation_cpu_seconds": wrapper.preparation_cpu_seconds,
            "preparation_wall_seconds": wrapper.preparation_wall_seconds,
            "optimizer_wall_seconds": checkpoint.elapsed_training_seconds,
            "total_cpu_seconds": checkpoint.total_cpu_seconds,
            "total_wall_seconds": checkpoint.total_wall_seconds,
            "process_peak_rss_bytes": checkpoint.process_peak_rss_bytes,
        }
        members.append(
            {
                "ordinal": ordinal,
                "seed": seed,
                "budget": budget,
                "method": method,
                "run_key_sha256": run_key,
                "preflight_sha256": checkpoint.preflight.preflight_sha256,
                "prepared_ledger_sha256": record["prepared_ledger_sha256"],
                "running_ledger_sha256": record["running_ledger_sha256"],
                "success_ledger_sha256": record["success_ledger_sha256"],
                "exit_observation_receipt_sha256": record[
                    "exit_observation_receipt_sha256"
                ],
                "worker_process_id": session["worker_pid"],
                "worker_parent_process_id": session["worker_parent_pid"],
                "worker_process_identity_sha256": (
                    _worker_process_identity_sha256(session)
                ),
                "worker_session_sha256": session["session_sha256"],
                "launch_authorization_sha256": session[
                    "launch_authorization_sha256"
                ],
                "launch_receipt_sha256": session["launch_receipt_sha256"],
                "execution_runtime_sha256": runtime_sha256,
                "campaign_sha256": campaign["campaign_sha256"],
                "optimizer_completion_receipt_sha256": completion[
                    "completion_receipt_sha256"
                ],
                "checkpoint_sha256": record["checkpoint_sha256"],
                "classifier_sha256": checkpoint.classifier_sha256,
                "parameter_sha256": checkpoint.final_snapshot.parameter_sha256,
                "certificate_sha256": (
                    checkpoint.certificate.certificate_sha256
                ),
                "optimizer_steps_taken": checkpoint.optimizer_steps_taken,
                "optimizer_transcript_sha256": (
                    checkpoint.optimizer_transcript_sha256
                ),
                "resources": resources,
                "resource_receipt_sha256": (
                    _aggregate_resource_receipt_sha256(resources)
                ),
                "completed_unix_ns": record["completed_unix_ns"],
            }
        )
    if used_launch_authorizations != set(ledger["launch_authorizations"]):
        raise RuntimeError("sampled aggregate has unused launch authorizations")

    # Re-establish the paired/nested design over canonical checkpoint content.
    for seed in _SEEDS:
        seed_preflights = [
            preflights[(seed, budget, method)]
            for budget in _BUDGETS
            for method in _METHODS
        ]
        for name in (
            "custody_sha256",
            "all_dataset_sha256",
            "all_batch_schedule_sha256",
        ):
            if len({getattr(value, name) for value in seed_preflights}) != 1:
                raise RuntimeError(
                    "sampled seed does not share one %s" % name
                )
        for method in _METHODS:
            if len(
                {
                    preflights[(seed, budget, method)].initial_parameter_sha256
                    for budget in _BUDGETS
                }
            ) != 1:
                raise RuntimeError(
                    "sampled method initialization changes across budgets"
                )
        for budget in _BUDGETS:
            group = [
                preflights[(seed, budget, method)] for method in _METHODS
            ]
            if len({value.dataset_sha256 for value in group}) != 1:
                raise RuntimeError("sampled paired methods use different datasets")
            scheduled = [
                preflights[(seed, budget, method)]
                for method in (
                    "direct",
                    "guided",
                    "guide_input",
                    "mismatch",
                )
            ]
            if len({value.batch_schedule_sha256 for value in scheduled}) != 1:
                raise RuntimeError("sampled primary schedules are not paired")
            initialized = [
                preflights[(seed, budget, method)]
                for method in ("direct", "guided", "mismatch")
            ]
            if len(
                {value.initial_parameter_sha256 for value in initialized}
            ) != 1:
                raise RuntimeError("sampled 21-input initializations are not paired")

    receipts_digest = _sha256_json(
        {
            "schema": "heterodiff-a1-sampled-ordered-success-receipts-v1",
            "receipts": members,
        }
    )
    ordered_checkpoint_sha256 = _sha256_json(
        {
            "schema": "heterodiff-a1-sampled-ordered-checkpoints-v1",
            "checkpoints": [
                {
                    "run_key_sha256": member["run_key_sha256"],
                    "checkpoint_sha256": member["checkpoint_sha256"],
                    "optimizer_completion_receipt_sha256": member[
                        "optimizer_completion_receipt_sha256"
                    ],
                }
                for member in members
            ],
        }
    )
    resource_totals = {
        "coordinate_count": len(members),
        "preparation_cpu_seconds": math.fsum(
            value["resources"]["preparation_cpu_seconds"] for value in members
        ),
        "preparation_wall_seconds": math.fsum(
            value["resources"]["preparation_wall_seconds"] for value in members
        ),
        "optimizer_wall_seconds": math.fsum(
            value["resources"]["optimizer_wall_seconds"] for value in members
        ),
        "total_cpu_seconds": math.fsum(
            value["resources"]["total_cpu_seconds"] for value in members
        ),
        "total_wall_seconds": math.fsum(
            value["resources"]["total_wall_seconds"] for value in members
        ),
        "maximum_process_peak_rss_bytes": max(
            value["resources"]["process_peak_rss_bytes"] for value in members
        ),
    }
    aggregate_body = {
        "schema": _AGGREGATE_SCHEMA,
        "campaign_sha256": campaign["campaign_sha256"],
        "coordinate_manifest_sha256": _coordinate_manifest_sha256(),
        "ordered_success_receipts": members,
        "ordered_success_receipts_sha256": receipts_digest,
        "ordered_checkpoint_sha256": ordered_checkpoint_sha256,
        "total_optimizer_steps_taken": sum(
            value["optimizer_steps_taken"] for value in members
        ),
        "resource_totals": resource_totals,
        "fresh_metric_recomputation_required": True,
        "execution_order_attested": False,
        "scientific_decision_eligible": False,
    }
    aggregate = dict(aggregate_body)
    aggregate["aggregate_sha256"] = _sha256_json(aggregate_body)
    _validated_aggregate_record(aggregate)
    return tuple(wrappers), aggregate


_VERIFIED_SAMPLED_CAMPAIGN_KEY = object()


class LedgerVerifiedFrozenAssociationSampledCampaign:
    """All 120 canonical checkpoints plus their durable aggregate receipt."""

    __slots__ = (
        "_checkpoints",
        "_checkpoint_identities",
        "_campaign_sha256",
        "_aggregate_sha256",
        "_ordered_success_receipts_sha256",
        "_ordered_checkpoint_sha256",
        "_locked",
    )

    def __init__(
        self,
        checkpoints: tuple,
        aggregate: dict,
        *,
        _construction_key: object,
    ) -> None:
        if _construction_key is not _VERIFIED_SAMPLED_CAMPAIGN_KEY:
            raise TypeError(
                "sampled campaign wrappers come only from the aggregate loader"
            )
        from heterodiff.experiments.finite_association_residual_training_torch import (
            LedgerVerifiedFittedAssociationCheckpoint,
            _require_fitted_checkpoint_integrity,
        )

        checked_aggregate = dict(_validated_aggregate_record(aggregate))
        if type(checkpoints) is not tuple or len(checkpoints) != 120 or any(
            type(value) is not LedgerVerifiedFittedAssociationCheckpoint
            for value in checkpoints
        ):
            raise TypeError("sampled campaign requires 120 canonical wrappers")
        identities = []
        for wrapper, member in zip(
            checkpoints, checked_aggregate["ordered_success_receipts"]
        ):
            checkpoint = wrapper.checkpoint
            _require_fitted_checkpoint_integrity(checkpoint)
            identity = (
                checkpoint.preflight.seed,
                checkpoint.preflight.budget,
                checkpoint.preflight.method,
                checkpoint.run_key_sha256,
                wrapper.success_receipt_sha256,
                checkpoint.optimizer_completion_receipt.completion_receipt_sha256,
                checkpoint.final_snapshot.parameter_sha256,
                checkpoint.classifier_sha256,
                checkpoint.certificate.certificate_sha256,
            )
            expected = (
                member["seed"],
                member["budget"],
                member["method"],
                member["run_key_sha256"],
                member["success_ledger_sha256"],
                member["optimizer_completion_receipt_sha256"],
                member["parameter_sha256"],
                member["classifier_sha256"],
                member["certificate_sha256"],
            )
            if identity != expected:
                raise RuntimeError(
                    "sampled aggregate wrapper identity is inconsistent"
                )
            identities.append(identity)
        object.__setattr__(self, "_checkpoints", checkpoints)
        object.__setattr__(self, "_checkpoint_identities", tuple(identities))
        object.__setattr__(
            self, "_campaign_sha256", checked_aggregate["campaign_sha256"]
        )
        object.__setattr__(
            self, "_aggregate_sha256", checked_aggregate["aggregate_sha256"]
        )
        object.__setattr__(
            self,
            "_ordered_success_receipts_sha256",
            checked_aggregate["ordered_success_receipts_sha256"],
        )
        object.__setattr__(
            self,
            "_ordered_checkpoint_sha256",
            checked_aggregate["ordered_checkpoint_sha256"],
        )
        object.__setattr__(self, "_locked", True)

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_locked", False):
            raise AttributeError("sampled campaign wrapper is immutable")
        object.__setattr__(self, name, value)

    def assert_integrity(self) -> None:
        from heterodiff.experiments.finite_association_residual_training_torch import (
            _require_fitted_checkpoint_integrity,
        )

        identities = []
        for wrapper in self._checkpoints:
            checkpoint = wrapper.checkpoint
            _require_fitted_checkpoint_integrity(checkpoint)
            identities.append(
                (
                    checkpoint.preflight.seed,
                    checkpoint.preflight.budget,
                    checkpoint.preflight.method,
                    checkpoint.run_key_sha256,
                    wrapper.success_receipt_sha256,
                    checkpoint.optimizer_completion_receipt.completion_receipt_sha256,
                    checkpoint.final_snapshot.parameter_sha256,
                    checkpoint.classifier_sha256,
                    checkpoint.certificate.certificate_sha256,
                )
            )
        if tuple(identities) != self._checkpoint_identities:
            raise RuntimeError("sampled campaign checkpoint changed after admission")

    @property
    def checkpoints(self) -> tuple:
        self.assert_integrity()
        return self._checkpoints

    @property
    def campaign_sha256(self) -> str:
        return self._campaign_sha256

    @property
    def aggregate_sha256(self) -> str:
        return self._aggregate_sha256

    @property
    def ordered_success_receipts_sha256(self) -> str:
        return self._ordered_success_receipts_sha256

    @property
    def ordered_checkpoint_sha256(self) -> str:
        return self._ordered_checkpoint_sha256

    @property
    def execution_order_attested(self) -> bool:
        return False

    @property
    def scientific_decision_eligible(self) -> bool:
        return False


    @property
    def fresh_metric_recomputation_required(self) -> bool:
        return True


def _admit_completed_sampled_campaign(
    checkpoints: tuple, aggregate: dict
) -> LedgerVerifiedFrozenAssociationSampledCampaign:
    return LedgerVerifiedFrozenAssociationSampledCampaign(
        checkpoints,
        aggregate,
        _construction_key=_VERIFIED_SAMPLED_CAMPAIGN_KEY,
    )


def _persist_sampled_aggregate(path: Path, ledger: dict, aggregate: dict) -> bool:
    """Write the aggregate exactly once; an identical retry is a no-op."""

    checked = dict(_validated_aggregate_record(aggregate))
    existing = ledger.get("aggregate")
    if existing is None:
        ledger["aggregate"] = checked
        _atomic_write_json(path, ledger)
        return True
    if existing != checked:
        raise RuntimeError(
            "existing sampled aggregate differs from canonical results"
        )
    return False


def finalize_frozen_association_sampled_campaign(
) -> LedgerVerifiedFrozenAssociationSampledCampaign:
    """Verify all 120 SUCCESS payloads and durably write their aggregate."""

    directory = _absolute_without_symlink_resolution(
        frozen_association_campaign_directory()
    )
    with _locked_ledger(directory) as (_, ledger):
        snapshot = ledger
        custody_sha256 = _sampled_aggregate_custody_sha256(snapshot)
    checkpoints, aggregate = _assemble_complete_frozen_association_sampled_campaign(
        directory, snapshot
    )
    with _locked_ledger(directory) as (path, current):
        if _sampled_aggregate_custody_sha256(current) != custody_sha256:
            raise RuntimeError(
                "sampled campaign custody changed during aggregate assembly"
            )
        _persist_sampled_aggregate(path, current, aggregate)
    return _admit_completed_sampled_campaign(checkpoints, aggregate)


def load_completed_frozen_association_sampled_campaign(
) -> LedgerVerifiedFrozenAssociationSampledCampaign:
    """Reload a complete v4 campaign with its durable aggregate receipt."""

    directory = _absolute_without_symlink_resolution(
        frozen_association_campaign_directory()
    )
    with _locked_ledger(directory, create=False) as (_, ledger):
        existing = ledger.get("aggregate")
        if not isinstance(existing, dict):
            raise RuntimeError("sampled campaign has no aggregate receipt")
        snapshot = ledger
        custody_sha256 = _sampled_aggregate_custody_sha256(snapshot)
    checkpoints, aggregate = _assemble_complete_frozen_association_sampled_campaign(
        directory, snapshot
    )
    if aggregate != existing:
        raise RuntimeError("sampled aggregate differs from current checkpoints")
    with _locked_ledger(directory, create=False) as (_, current):
        if (
            _sampled_aggregate_custody_sha256(current) != custody_sha256
            or current.get("aggregate") != aggregate
        ):
            raise RuntimeError("sampled aggregate changed while it was loading")
    return _admit_completed_sampled_campaign(checkpoints, aggregate)


def revalidate_completed_frozen_association_sampled_campaign(
    admitted: object,
) -> LedgerVerifiedFrozenAssociationSampledCampaign:
    """Reopen all canonical files and match them to an earlier admission."""

    if type(admitted) is not LedgerVerifiedFrozenAssociationSampledCampaign:
        raise TypeError("sampled campaign revalidation requires loader admission")
    admitted.assert_integrity()
    fresh = load_completed_frozen_association_sampled_campaign()
    if (
        fresh.campaign_sha256 != admitted.campaign_sha256
        or fresh.aggregate_sha256 != admitted.aggregate_sha256
        or fresh.ordered_success_receipts_sha256
        != admitted.ordered_success_receipts_sha256
        or fresh.ordered_checkpoint_sha256
        != admitted.ordered_checkpoint_sha256
    ):
        raise RuntimeError("canonical sampled aggregate changed on revalidation")
    return fresh


def _worker(
    request: FrozenAssociationSampledRunRequest,
    ledger_directory: Path,
    worker_session: _FrozenAssociationWorkerSession,
) -> dict:
    """Run the complete child lifecycle under durable failure custody."""

    total_wall_start = time.perf_counter()
    total_cpu_start = time.process_time()
    try:
        return _worker_under_failure_custody(
            request, ledger_directory, worker_session
        )
    except BaseException as error:
        if type(worker_session) is _FrozenAssociationWorkerSession:
            for attempt in (1, 2):
                try:
                    _terminalize_sampled_worker_failure(
                        ledger_directory,
                        worker_session,
                        error,
                        total_wall_start=total_wall_start,
                        total_cpu_start=total_cpu_start,
                    )
                    break
                except BaseException as terminalization_error:
                    error.add_note(
                        "worker failure-terminalization attempt %d failed: %r"
                        % (attempt, terminalization_error)
                    )
        raise


def _worker_under_failure_custody(
    request: FrozenAssociationSampledRunRequest,
    ledger_directory: Path,
    worker_session: _FrozenAssociationWorkerSession,
) -> dict:
    if type(worker_session) is not _FrozenAssociationWorkerSession:
        raise TypeError("worker requires the parent-handshaken session capability")
    worker_session.validate_current_process()
    if _absolute_without_symlink_resolution(
        ledger_directory
    ) != _absolute_without_symlink_resolution(
        frozen_association_campaign_directory()
    ):
        raise RuntimeError("worker ledger directory is not the frozen campaign path")
    thread_environment = _require_preimport_worker_environment()

    # The limit context remains active over preparation, optimization,
    # certification, and serialization.  Numerical imports occur only here.
    from threadpoolctl import threadpool_limits

    with threadpool_limits(limits=1):
        runtime_record = _runtime_record_after_import(thread_environment)
        from heterodiff.experiments.finite_association_guided_residual_pilot import (
            frozen_association_fixture_sha256,
        )
        from heterodiff.experiments.finite_association_residual_training_torch import (
            _issue_frozen_association_execution_permit,
            execute_frozen_association_residual_training,
            frozen_association_training_configuration_sha256,
            frozen_association_training_source_sha256,
            prepare_frozen_association_residual_training,
        )
        source_sha256 = frozen_association_training_source_sha256()
        configuration_sha256 = frozen_association_training_configuration_sha256(
            source_sha256=source_sha256
        )
        fixture_sha256 = frozen_association_fixture_sha256()
        run_key = frozen_association_sampled_run_key(
            request,
            fixture_sha256=fixture_sha256,
            source_sha256=source_sha256,
            configuration_sha256=configuration_sha256,
            execution_runtime_sha256=runtime_record["sha256"],
        )
        campaign = _ensure_frozen_campaign(
            ledger_directory,
            fixture_sha256=fixture_sha256,
            source_sha256=source_sha256,
            configuration_sha256=configuration_sha256,
            execution_runtime_sha256=runtime_record["sha256"],
        )
        _reserve_run(
            ledger_directory, run_key, request, runtime_record, worker_session
        )
        total_wall_start = time.perf_counter()
        total_cpu_start = time.process_time()
        try:
            preparation_wall_start = time.perf_counter()
            preparation_cpu_start = time.process_time()
            prepared = prepare_frozen_association_residual_training(
                request.seed, request.budget, request.method
            )
            if (
                prepared.preflight.fixture_sha256 != fixture_sha256
                or prepared.preflight.source_sha256 != source_sha256
                or prepared.preflight.configuration_sha256
                != configuration_sha256
            ):
                raise RuntimeError(
                    "prepared preflight differs from the reserved run custody"
                )
            prepared_run_key = frozen_association_sampled_run_key(
                request,
                fixture_sha256=prepared.preflight.fixture_sha256,
                source_sha256=prepared.preflight.source_sha256,
                configuration_sha256=prepared.preflight.configuration_sha256,
                execution_runtime_sha256=runtime_record["sha256"],
            )
            if prepared_run_key != run_key:
                raise RuntimeError("run key changed during preparation")
            preparation_wall = time.perf_counter() - preparation_wall_start
            preparation_cpu = time.process_time() - preparation_cpu_start
            prepared_base = {
                "state": "PREPARED",
                "request": asdict(request),
                "runtime": runtime_record,
                "worker_session": worker_session.record,
                "worker_session_run_sha256": _worker_session_run_sha256(
                    worker_session.session_sha256, run_key
                ),
                "worker_pid": os.getpid(),
                "run_key_sha256": run_key,
                "preflight": asdict(prepared.preflight),
                "preparation_wall_seconds": preparation_wall,
                "preparation_cpu_seconds": preparation_cpu,
                "prepared_unix_ns": time.time_ns(),
            }
            prepared_ledger_sha256 = _sha256_json(prepared_base)
            prepared_record = dict(prepared_base)
            prepared_record["prepared_ledger_sha256"] = prepared_ledger_sha256
            _transition_run(
                ledger_directory,
                run_key,
                expected_state="RESERVED",
                record=prepared_record,
            )
            permit = _issue_frozen_association_execution_permit(
                run_key_sha256=run_key,
                preflight_sha256=prepared.preflight.preflight_sha256,
                prepared_ledger_sha256=prepared_ledger_sha256,
                campaign_sha256=campaign["campaign_sha256"],
                execution_runtime_sha256=runtime_record["sha256"],
                ledger_directory=ledger_directory,
                total_wall_start=total_wall_start,
                total_cpu_start=total_cpu_start,
                worker_session=worker_session,
            )
            completed_training = execute_frozen_association_residual_training(
                prepared, execution_permit=permit
            )
            checkpoint = completed_training.checkpoint
            checkpoint_name = "%s.pt" % run_key
            checkpoint_path = (
                _absolute_without_symlink_resolution(ledger_directory)
                / checkpoint_name
            )
            checkpoint_sha256 = _atomic_torch_save(checkpoint, checkpoint_path)
            success = _complete_run_success(
                ledger_directory,
                run_key,
                completed_training=completed_training,
                checkpoint_path=checkpoint_path,
                checkpoint_sha256=checkpoint_sha256,
                worker_session=worker_session,
            )
            return success
        except BaseException:
            # The outer worker boundary owns terminalization so failures in
            # runtime capture, campaign admission, and reservation receive the
            # same custody as failures after reservation.
            raise


def _require_matching_terminal_exit_evidence(
    record: dict, child_returncode: int
) -> bool:
    """Reject conflicting evidence; return whether evidence was present."""

    if "exit_observation_receipt_sha256" in record:
        observed_returncode = record.get("exit_child_returncode")
    elif record.get("terminal_owner") == "PARENT_REAPER" or (
        record.get("terminal_owner") == "PARENT"
        and record.get("failed_stage") == "CHILD_EXIT_BEFORE_CONSUMPTION"
    ):
        observed_returncode = record.get("child_returncode")
    else:
        return False
    if observed_returncode != child_returncode:
        raise RuntimeError("confirmed child-exit evidence conflicts with custody")
    return True


def _reconcile_sampled_child_exit(
    ledger_directory: Path,
    launch_authorization_sha256: object,
    request: FrozenAssociationSampledRunRequest,
    *,
    child_process_id: object,
    child_returncode: object,
) -> Tuple[dict, Optional[dict]]:
    """Reconcile a confirmed child exit without regressing durable custody."""

    authorization = _lower_sha256(
        launch_authorization_sha256, name="launch_authorization_sha256"
    )
    if type(request) is not FrozenAssociationSampledRunRequest:
        raise TypeError("child-exit reconciliation requires an exact request")
    if (
        isinstance(child_process_id, bool)
        or type(child_process_id) is not int
        or child_process_id <= 0
    ):
        raise ValueError("child_process_id must be a positive integer")
    if isinstance(child_returncode, bool) or type(child_returncode) is not int:
        raise TypeError("child_returncode must be an integer")
    directory = _absolute_without_symlink_resolution(ledger_directory)
    exit_error = ChildProcessError(
        "sampled child exited with return code %d" % child_returncode
    )
    with _locked_ledger(directory) as (path, ledger):
        launch = _validated_launch_authorization_record(
            ledger["launch_authorizations"].get(authorization)
        )
        if (
            launch["launch_authorization_sha256"] != authorization
            or launch["request"] != asdict(request)
            or launch["ledger_directory"] != str(directory)
            or launch["parent_process_id"] != os.getpid()
        ):
            raise RuntimeError("child-exit reconciliation lacks parent ownership")
        known_child_process_id = launch.get(
            "child_process_id", launch.get("observed_child_process_id")
        )
        if (
            known_child_process_id is not None
            and known_child_process_id != child_process_id
        ):
            raise RuntimeError("child-exit process identity changed")
        matching_runs = []
        for run_key, run in ledger["runs"].items():
            session = run.get("worker_session") if type(run) is dict else None
            if (
                type(session) is dict
                and session.get("launch_authorization_sha256") == authorization
            ):
                matching_runs.append((run_key, run))
        if len(matching_runs) > 1:
            raise RuntimeError("one sampled launch owns multiple run records")

        if launch["state"] in ("FAILURE", "HOLD"):
            _require_matching_terminal_exit_evidence(
                launch, child_returncode
            )
            if launch.get("terminal_owner") in ("PARENT", "PARENT_REAPER"):
                if matching_runs:
                    raise RuntimeError(
                        "parent-terminal launch unexpectedly owns a run"
                    )
                return launch, None
            if launch.get("terminal_owner") == "CHILD":
                if matching_runs:
                    raise RuntimeError(
                        "child pre-reservation terminal unexpectedly owns a run"
                    )
                return launch, None
            raise RuntimeError("child-exit launch terminal ownership is invalid")
        if launch["state"] == "BOUND":
            raise RuntimeError(
                "unconsumed child exit was not parent-terminalized first"
            )
        if launch["state"] != "CONSUMED":
            raise RuntimeError("child-exit launch state is not reconcilable")

        if not matching_runs:
            terminal_launch = dict(launch)
            terminal_launch.update(
                {
                    "state": "FAILURE",
                    "terminal_owner": "PARENT_REAPER",
                    "terminal_process_id": os.getpid(),
                    "previous_state": "CONSUMED",
                    "previous_receipt_sha256": launch[
                        "consumed_receipt_sha256"
                    ],
                    "failed_stage": (
                        "CHILD_EXIT_AFTER_CONSUMPTION_NO_RUN"
                    ),
                    "error_type": type(exit_error).__name__,
                    "error_message": str(exit_error),
                    "failed_unix_ns": time.time_ns(),
                    "observed_child_process_id": child_process_id,
                    "child_returncode": child_returncode,
                    "child_signal": (
                        -child_returncode if child_returncode < 0 else None
                    ),
                }
            )
            terminal_launch["terminal_receipt_sha256"] = _sha256_json(
                terminal_launch
            )
            _validated_launch_authorization_record(terminal_launch)
            ledger["launch_authorizations"][authorization] = terminal_launch
            _atomic_write_json(path, ledger)
            return terminal_launch, None

        run_key, run = matching_runs[0]
        session = _validated_worker_session_record(run.get("worker_session"))
        if (
            session["launch_authorization_sha256"] != authorization
            or session["launch_receipt_sha256"]
            != launch["consumed_receipt_sha256"]
            or session["worker_pid"] != child_process_id
            or session["worker_parent_pid"] != os.getpid()
            or run.get("worker_pid") != child_process_id
            or run.get("request") != asdict(request)
            or run.get("worker_session_run_sha256")
            != _worker_session_run_sha256(session["session_sha256"], run_key)
        ):
            raise RuntimeError("child-exit run differs from launch custody")
        if run.get("state") in ("RESERVED", "PREPARED", "RUNNING"):
            active = _validated_active_run_for_parent_reaper(
                run_key, run, launch
            )
            previous_state = active["state"]
            reaped = dict(active)
            reaped.update(
                {
                    "state": "FAILURE",
                    "terminal_owner": "PARENT_REAPER",
                    "terminal_process_id": os.getpid(),
                    "previous_state": previous_state,
                    "previous_ledger_sha256": _active_run_receipt_sha256(
                        active
                    ),
                    "failed_stage": "CHILD_EXIT_AFTER_CONSUMPTION",
                    "error_type": type(exit_error).__name__,
                    "error_message": str(exit_error),
                    "observed_child_process_id": child_process_id,
                    "child_returncode": child_returncode,
                    "child_signal": (
                        -child_returncode if child_returncode < 0 else None
                    ),
                    "failed_unix_ns": time.time_ns(),
                }
            )
            reaped["terminal_ledger_sha256"] = _sha256_json(reaped)
            _validated_terminal_run_record(run_key, reaped, launch)
            ledger["runs"][run_key] = reaped
            _atomic_write_json(path, ledger)
            return launch, reaped
        if run.get("state") == "SUCCESS":
            return launch, _validated_success_record(run)
        if run.get("state") in ("FAILURE", "HOLD"):
            terminal_run = _validated_terminal_run_record(
                run_key, run, launch
            )
            _require_matching_terminal_exit_evidence(
                terminal_run, child_returncode
            )
            return launch, terminal_run
        raise RuntimeError("child-exit run state is invalid")


def _require_exact_success_for_zero_child_exit(
    child_returncode: object, run_after_exit: object
) -> None:
    """Require exact equivalence between a zero exit and valid SUCCESS."""

    if isinstance(child_returncode, bool) or type(child_returncode) is not int:
        raise TypeError("child_returncode must be an integer")
    is_success = (
        type(run_after_exit) is dict
        and run_after_exit.get("state") == "SUCCESS"
    )
    if not is_success and child_returncode != 0:
        return
    if not is_success:
        raise RuntimeError(
            "sampled child exited zero without an exact SUCCESS receipt"
        )
    try:
        _validated_success_record(run_after_exit)
    except (RuntimeError, TypeError, ValueError) as error:
        raise RuntimeError(
            "sampled child exited zero without an exact SUCCESS receipt"
        ) from error
    if child_returncode != 0:
        raise RuntimeError(
            "sampled child exited nonzero despite an exact SUCCESS receipt"
        )


def _reconcile_confirmed_sampled_child_exit(
    ledger_directory: Path,
    launch_authorization_sha256: object,
    request: FrozenAssociationSampledRunRequest,
    *,
    child_process_id: object,
    child_returncode: object,
) -> Tuple[dict, Optional[dict]]:
    """Reconcile a typed wait result and retain later parent exit evidence."""

    launch, run_after_exit = _reconcile_sampled_child_exit(
        ledger_directory,
        launch_authorization_sha256,
        request,
        child_process_id=child_process_id,
        child_returncode=child_returncode,
    )
    parent_terminal_needs_observation = (
        launch.get("terminal_owner") == "PARENT"
        and launch.get("failed_stage")
        in ("BIND", "TOKEN_DELIVERY", "CHILD_WAIT")
    )
    child_launch_needs_observation = (
        launch.get("terminal_owner") == "CHILD"
        and launch.get("failed_stage") == "PRE_RUN_RESERVATION"
    )
    if parent_terminal_needs_observation or child_launch_needs_observation:
        launch = _record_parent_launch_exit_observation(
            ledger_directory,
            launch_authorization_sha256,
            request,
            child_process_id=child_process_id,
            child_returncode=child_returncode,
        )
    if (
        type(run_after_exit) is dict
        and run_after_exit.get("terminal_owner") == "CHILD"
        and run_after_exit.get("state") in ("FAILURE", "HOLD")
    ):
        run_after_exit = _record_parent_run_exit_observation(
            ledger_directory,
            launch_authorization_sha256,
            request,
            child_process_id=child_process_id,
            child_returncode=child_returncode,
        )
    if (
        type(run_after_exit) is dict
        and run_after_exit.get("state") == "SUCCESS"
    ):
        _require_exact_success_for_zero_child_exit(
            child_returncode, run_after_exit
        )
        run_after_exit = _record_parent_success_exit_observation(
            ledger_directory,
            launch_authorization_sha256,
            request,
            child_process_id=child_process_id,
            child_returncode=child_returncode,
        )
    _require_exact_success_for_zero_child_exit(
        child_returncode, run_after_exit
    )
    return launch, run_after_exit


def _verify_sampled_child_exit_custody(
    ledger_directory: Path,
    launch_authorization_sha256: object,
    request: FrozenAssociationSampledRunRequest,
    *,
    child_process_id: object,
    child_returncode: Optional[int],
) -> Tuple[dict, Optional[dict]]:
    """Verify that parent cleanup ended in exact durable custody."""

    authorization = _lower_sha256(
        launch_authorization_sha256, name="launch_authorization_sha256"
    )
    if type(request) is not FrozenAssociationSampledRunRequest:
        raise TypeError("child-exit custody verification requires a request")
    if (
        isinstance(child_process_id, bool)
        or type(child_process_id) is not int
        or child_process_id <= 0
    ):
        raise ValueError("child_process_id must be a positive integer")
    if child_returncode is not None and (
        isinstance(child_returncode, bool) or type(child_returncode) is not int
    ):
        raise TypeError("child_returncode must be an integer or None")
    directory = _absolute_without_symlink_resolution(ledger_directory)
    with _locked_ledger(directory) as (_, ledger):
        launch = _validated_launch_authorization_record(
            ledger["launch_authorizations"].get(authorization)
        )
        if (
            launch["launch_authorization_sha256"] != authorization
            or launch["request"] != asdict(request)
            or launch["ledger_directory"] != str(directory)
            or launch["parent_process_id"] != os.getpid()
            or (
                "child_process_id" in launch
                and launch["child_process_id"] != child_process_id
            )
        ):
            raise RuntimeError("child-exit custody verification lacks ownership")
        matching = []
        for run_key, run in ledger["runs"].items():
            session = run.get("worker_session") if type(run) is dict else None
            if (
                type(session) is dict
                and session.get("launch_authorization_sha256")
                == authorization
            ):
                matching.append((run_key, run))
        if len(matching) > 1:
            raise RuntimeError("one sampled launch owns multiple run records")

        if launch["state"] in ("FAILURE", "HOLD"):
            if matching:
                raise RuntimeError("terminal launch unexpectedly owns a run")
            owner = launch.get("terminal_owner")
            if child_returncode is not None:
                if owner in ("PARENT", "CHILD") and launch.get(
                    "failed_stage"
                ) in (
                    "BIND",
                    "TOKEN_DELIVERY",
                    "CHILD_WAIT",
                    "PRE_RUN_RESERVATION",
                ):
                    if (
                        launch.get("exit_child_returncode")
                        != child_returncode
                        or launch.get("exit_child_signal")
                        != (
                            -child_returncode
                            if child_returncode < 0
                            else None
                        )
                    ):
                        raise RuntimeError(
                            "terminal launch lacks its confirmed exit observation"
                        )
                elif owner in ("PARENT", "PARENT_REAPER"):
                    if (
                        launch.get("child_returncode") != child_returncode
                        or launch.get("child_signal")
                        != (
                            -child_returncode
                            if child_returncode < 0
                            else None
                        )
                    ):
                        raise RuntimeError(
                            "terminal launch exit evidence changed"
                        )
                else:
                    raise RuntimeError(
                        "terminal launch has no parent exit evidence"
                    )
                _require_exact_success_for_zero_child_exit(
                    child_returncode, None
                )
            return launch, None

        if launch["state"] != "CONSUMED" or len(matching) != 1:
            raise RuntimeError("confirmed child exit has no terminal custody")
        run_key, run = matching[0]
        if run.get("state") == "SUCCESS":
            checked_run = (
                _validated_parent_observed_success_record(run)
                if child_returncode is not None
                else _validated_success_record(run)
            )
        elif run.get("state") in ("FAILURE", "HOLD"):
            checked_run = _validated_terminal_run_record(
                run_key, run, launch
            )
            if child_returncode is not None:
                if checked_run.get("terminal_owner") == "CHILD":
                    observed_returncode = checked_run.get(
                        "exit_child_returncode"
                    )
                    observed_signal = checked_run.get("exit_child_signal")
                else:
                    observed_returncode = checked_run.get("child_returncode")
                    observed_signal = checked_run.get("child_signal")
                if (
                    observed_returncode != child_returncode
                    or observed_signal
                    != (-child_returncode if child_returncode < 0 else None)
                ):
                    raise RuntimeError(
                        "terminal run lacks its confirmed exit observation"
                    )
        else:
            raise RuntimeError("confirmed child exit left an active run")
        if child_returncode is not None:
            _require_exact_success_for_zero_child_exit(
                child_returncode, checked_run
            )
        return launch, checked_run


def _reconcile_confirmed_exit_preserving_primary(
    primary_error: BaseException,
    label: str,
    ledger_directory: Path,
    launch_authorization_sha256: str,
    request: FrozenAssociationSampledRunRequest,
    *,
    child_process_id: int,
    child_returncode: int,
) -> None:
    """Retry confirmed-exit closure, preserve the primary, and verify it."""

    for attempt in (1, 2):
        try:
            _reconcile_confirmed_sampled_child_exit(
                ledger_directory,
                launch_authorization_sha256,
                request,
                child_process_id=child_process_id,
                child_returncode=child_returncode,
            )
            break
        except BaseException as reconciliation_error:
            primary_error.add_note(
                "%s confirmed-exit reconciliation attempt %d failed: %r"
                % (label, attempt, reconciliation_error)
            )
    try:
        _verify_sampled_child_exit_custody(
            ledger_directory,
            launch_authorization_sha256,
            request,
            child_process_id=child_process_id,
            child_returncode=child_returncode,
        )
    except BaseException as verification_error:
        primary_error.add_note(
            "%s durable terminal-custody verification failed: %r"
            % (label, verification_error)
        )


def _reconcile_parent_failure_preserving_primary(
    primary_error: BaseException,
    label: str,
    process: object,
    ledger_directory: Path,
    launch_authorization_sha256: str,
    request: FrozenAssociationSampledRunRequest,
) -> None:
    """Obtain an exit status twice at most, then retry and verify closure."""

    returncode = None
    for attempt in (1, 2):
        try:
            observed = process.wait()
            if isinstance(observed, bool) or type(observed) is not int:
                raise RuntimeError(
                    "sampled child wait returned an invalid status"
                )
            returncode = observed
            break
        except BaseException as wait_error:
            primary_error.add_note(
                "%s child-wait attempt %d failed: %r"
                % (label, attempt, wait_error)
            )
    if returncode is not None:
        _reconcile_confirmed_exit_preserving_primary(
            primary_error,
            label,
            ledger_directory,
            launch_authorization_sha256,
            request,
            child_process_id=process.pid,
            child_returncode=returncode,
        )
        return
    try:
        _verify_sampled_child_exit_custody(
            ledger_directory,
            launch_authorization_sha256,
            request,
            child_process_id=process.pid,
            child_returncode=None,
        )
    except BaseException as verification_error:
        primary_error.add_note(
            "%s durable terminal-custody verification failed: %r"
            % (label, verification_error)
        )


def _reconcile_after_parent_launch_failure(
    process: object,
    ledger_directory: Path,
    launch_authorization_sha256: str,
    request: FrozenAssociationSampledRunRequest,
) -> None:
    """Wait for the already-aborted child, then reconcile its final custody."""

    returncode = process.wait()
    if isinstance(returncode, bool) or type(returncode) is not int:
        raise RuntimeError("sampled child wait returned an invalid status")
    _reconcile_confirmed_sampled_child_exit(
        ledger_directory,
        launch_authorization_sha256,
        request,
        child_process_id=process.pid,
        child_returncode=returncode,
    )


def _bounded_final_child_wait(process: object, *, timeout_seconds: float = 5.0):
    """Bound cleanup after polling itself failed, escalating to the child only."""

    try:
        return process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            return process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            process.kill()
            return process.wait(timeout=timeout_seconds)


def launch_frozen_association_sampled_run(
    request: FrozenAssociationSampledRunRequest,
    *,
    python_executable: Optional[str] = None,
) -> subprocess.CompletedProcess:
    """Start the one allowed fresh worker; this function blocks until exit."""

    if type(request) is not FrozenAssociationSampledRunRequest:
        raise TypeError("request must be an exact sampled-run request")
    if python_executable is not None and type(python_executable) is not str:
        raise TypeError("python_executable must be a string path or None")
    directory = _absolute_without_symlink_resolution(
        frozen_association_campaign_directory()
    )
    executable = sys.executable if python_executable is None else python_executable
    worker_script = str(Path(__file__).resolve(strict=True))
    control_read, control_write = os.pipe()
    token = os.urandom(32)
    token_sha256 = hashlib.sha256(token).hexdigest()
    process = None
    launch_authorization_sha256 = None
    command = None
    try:
        launch_authorization_sha256 = _issue_launch_authorization(
            directory, request, token_sha256
        )
        command = (
            str(executable),
            worker_script,
            "--isolated-worker",
            "--worker-control-fd",
            str(control_read),
            "--worker-token-sha256",
            token_sha256,
            "--launch-authorization-sha256",
            launch_authorization_sha256,
            "--seed",
            str(request.seed),
            "--budget",
            str(request.budget),
            "--method",
            request.method,
            "--ledger-directory",
            str(directory),
        )
        try:
            process = subprocess.Popen(
                command,
                env=frozen_association_worker_environment(),
                text=True,
                pass_fds=(control_read,),
            )
        except BaseException as error:
            _terminalize_parent_launch_preserving_primary(
                error,
                "popen",
                directory,
                launch_authorization_sha256,
                request,
                failed_stage="POPEN",
                state=(
                    "HOLD"
                    if isinstance(error, (KeyboardInterrupt, SystemExit))
                    else "FAILURE"
                ),
            )
            raise
        try:
            os.close(control_read)
            control_read = -1
            _bind_launch_authorization_child(
                directory, launch_authorization_sha256, process.pid
            )
        except BaseException as error:
            _terminalize_parent_launch_preserving_primary(
                error,
                "bind",
                directory,
                launch_authorization_sha256,
                request,
                failed_stage="BIND",
                observed_child_process_id=process.pid,
                state=(
                    "HOLD"
                    if isinstance(error, (KeyboardInterrupt, SystemExit))
                    else "FAILURE"
                ),
            )
            try:
                if control_write >= 0:
                    os.close(control_write)
                    control_write = -1
            except BaseException as close_error:
                error.add_note(
                    "post-bind control close also failed: %r" % close_error
                )
            else:
                _reconcile_parent_failure_preserving_primary(
                    error,
                    "post-bind",
                    process,
                    directory,
                    launch_authorization_sha256,
                    request,
                )
            raise
        try:
            delivered = os.write(control_write, token)
            if delivered != len(token):
                raise RuntimeError(
                    "worker token delivery did not write exactly 32 bytes"
                )
            os.close(control_write)
            control_write = -1
        except BaseException as error:
            _terminalize_parent_launch_preserving_primary(
                error,
                "token-delivery",
                directory,
                launch_authorization_sha256,
                request,
                failed_stage="TOKEN_DELIVERY",
                observed_child_process_id=process.pid,
                state=(
                    "HOLD"
                    if isinstance(error, (KeyboardInterrupt, SystemExit))
                    else "FAILURE"
                ),
            )
            try:
                if control_write >= 0:
                    os.close(control_write)
                    control_write = -1
            except BaseException as close_error:
                error.add_note(
                    "post-token control close also failed: %r" % close_error
                )
            else:
                _reconcile_parent_failure_preserving_primary(
                    error,
                    "post-token",
                    process,
                    directory,
                    launch_authorization_sha256,
                    request,
                )
            raise
        try:
            returncode = process.wait()
        except BaseException as error:
            _terminalize_parent_launch_preserving_primary(
                error,
                "child-wait",
                directory,
                launch_authorization_sha256,
                request,
                failed_stage="CHILD_WAIT",
                observed_child_process_id=process.pid,
                state=(
                    "HOLD"
                    if isinstance(error, (KeyboardInterrupt, SystemExit))
                    else "FAILURE"
                ),
            )
            _reconcile_parent_failure_preserving_primary(
                error,
                "post-wait",
                process,
                directory,
                launch_authorization_sha256,
                request,
            )
            raise
        child_exit_error = ChildProcessError(
            "sampled child exited with return code %d" % returncode
        )
        terminal_launch = _terminalize_parent_launch_preserving_primary(
            child_exit_error,
            "child-exit",
            directory,
            launch_authorization_sha256,
            request,
            failed_stage="CHILD_EXIT_BEFORE_CONSUMPTION",
            observed_child_process_id=process.pid,
            child_returncode=returncode,
            state="FAILURE",
        )
        if terminal_launch is None:
            raise child_exit_error
        _reconcile_confirmed_sampled_child_exit(
            directory,
            launch_authorization_sha256,
            request,
            child_process_id=process.pid,
            child_returncode=returncode,
        )
        return subprocess.CompletedProcess(command, returncode)
    finally:
        active_error = sys.exc_info()[1]
        for descriptor in (control_read, control_write):
            if descriptor >= 0:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
        should_wait = False
        poll_failed = False
        final_returncode = None
        if process is not None:
            try:
                polled_returncode = process.poll()
                should_wait = polled_returncode is None
                if not should_wait:
                    if (
                        isinstance(polled_returncode, bool)
                        or type(polled_returncode) is not int
                    ):
                        raise RuntimeError(
                            "final sampled child poll returned an invalid status"
                        )
                    final_returncode = polled_returncode
            except BaseException as final_poll_error:
                if active_error is None:
                    raise
                active_error.add_note(
                    "final child poll also failed: %r" % final_poll_error
                )
                poll_failed = True
                should_wait = True
        if should_wait:
            try:
                final_returncode = (
                    _bounded_final_child_wait(process)
                    if poll_failed
                    else process.wait()
                )
                if (
                    isinstance(final_returncode, bool)
                    or type(final_returncode) is not int
                ):
                    raise RuntimeError(
                        "final sampled child wait returned an invalid status"
                    )
            except BaseException as final_wait_error:
                if active_error is None:
                    raise
                active_error.add_note(
                    "final child cleanup also failed: %r" % final_wait_error
                )
                final_returncode = None
        if (
            final_returncode is not None
            and launch_authorization_sha256 is not None
        ):
            if active_error is None:
                _reconcile_confirmed_sampled_child_exit(
                    directory,
                    launch_authorization_sha256,
                    request,
                    child_process_id=process.pid,
                    child_returncode=final_returncode,
                )
            else:
                _reconcile_confirmed_exit_preserving_primary(
                    active_error,
                    "final cleanup",
                    directory,
                    launch_authorization_sha256,
                    request,
                    child_process_id=process.pid,
                    child_returncode=final_returncode,
                )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Launch one frozen A1 sampled learner in a fresh process."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--execute-learner", action="store_true")
    mode.add_argument("--isolated-worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--budget", type=int, required=True)
    parser.add_argument("--method", required=True, choices=_METHODS)
    parser.add_argument("--ledger-directory", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--worker-control-fd", type=int, help=argparse.SUPPRESS)
    parser.add_argument("--worker-token-sha256", help=argparse.SUPPRESS)
    parser.add_argument(
        "--launch-authorization-sha256", help=argparse.SUPPRESS
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    arguments = _parser().parse_args(argv)
    request = FrozenAssociationSampledRunRequest(
        seed=arguments.seed,
        budget=arguments.budget,
        method=arguments.method,
    )
    if arguments.isolated_worker:
        if arguments.ledger_directory is None:
            raise RuntimeError("isolated worker is missing its ledger path")
        worker_session = _consume_parent_handshake(
            arguments.worker_control_fd,
            arguments.worker_token_sha256,
            request=request,
            ledger_directory=arguments.ledger_directory,
            launch_authorization_sha256=(
                arguments.launch_authorization_sha256
            ),
        )
        result = _worker(request, arguments.ledger_directory, worker_session)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    if arguments.ledger_directory is not None:
        raise RuntimeError("the public launcher uses one frozen campaign ledger")
    if (
        arguments.worker_control_fd is not None
        or arguments.worker_token_sha256 is not None
        or arguments.launch_authorization_sha256 is not None
    ):
        raise RuntimeError("worker handshake options are internal")
    completed = launch_frozen_association_sampled_run(request)
    return int(completed.returncode)


if __name__ == "__main__":  # pragma: no cover - exercised only by explicit CLI
    raise SystemExit(main())


__all__ = [
    "FrozenAssociationSampledRunRequest",
    "LedgerVerifiedFrozenAssociationPrimarySuccessSet",
    "LedgerVerifiedFrozenAssociationSampledCampaign",
    "finalize_frozen_association_sampled_campaign",
    "frozen_association_sampled_run_key",
    "frozen_association_campaign_directory",
    "frozen_association_worker_environment",
    "launch_frozen_association_sampled_run",
    "load_completed_frozen_association_primary_success_set",
    "load_completed_frozen_association_sampled_campaign",
    "load_successful_frozen_association_checkpoint",
    "revalidate_completed_frozen_association_primary_success_set",
    "revalidate_completed_frozen_association_sampled_campaign",
    "revalidate_successful_frozen_association_checkpoint",
    "main",
]
