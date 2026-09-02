"""Isolated, exactly-once runner for the frozen A1 exact-population lane.

The public process imports only the Python standard library.  Each of the
eight seeds crossed with the three frozen methods is executed in a separate
child interpreter whose native thread limits are installed before NumPy,
SciPy, or PyTorch is imported.  A hash-chained ledger transition to RUNNING is
fsynced immediately before optimizer construction.  Importing this module or
using its custody helpers never takes an optimizer step.

Training requires the literal CLI authorization
``--execute-exact-population`` (one coordinate) or
``--execute-exact-population-campaign`` (all 24 coordinates).  The oracle
product-positive check is part of result-independent preparation only and is
never submitted to an optimizer.

Before spawning, the parent durably issues a launch authorization bound to the
coordinate, canonical path, random pipe-token digest, parent process identity,
and launch ID.  The child atomically consumes it while adding its own process
identity; only that durable receipt plus the inherited token yields a typed,
PID-bound, single-use worker-session capability.  These receipts and the stage
ledger enforce the intended launcher and ordering on a non-hostile host.
Parent-side issuance/spawn/pipe/wait failures, child-side pre-reservation
failures, and post-exit parent-reaper failures have separate, owner-bound,
hash-chained receipts.  A later parent-observed exit extends rather than
replaces an earlier parent- or child-owned launch/run terminal receipt.  Exit
zero is accepted only when the consumed launch has exactly one strictly
validated SUCCESS run; missing or nonterminal custody is durably failed, while
an existing child terminal or SUCCESS is never overwritten.  This is
API/custody enforcement, not
cryptographic identity authentication against a malicious local user with
arbitrary process or filesystem access.

After the final update, certification, snapshot, and split evaluation, the
executor mints a private single-use completion receipt containing the expected
and observed step counts plus a rolling update transcript.  SUCCESS can be
written only after the result file is serialized, digest-gated, reopened, and
matched to that receipt; the generic stage-transition helper cannot write
SUCCESS.
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
import subprocess
import sys
import tempfile
import time
from typing import Dict, Iterator, Mapping, Optional, Sequence, Tuple


_SEEDS = (1_729, 3_253, 5_003, 7_411, 10_007, 13_007, 16_001, 20_011)
_METHODS = ("direct", "guided", "strong_direct")
_METHOD_UPDATES = {"direct": 3_000, "guided": 3_000, "strong_direct": 4_500}
_EXPECTED_TOTAL_STEPS = 84_000
_THREAD_ENVIRONMENT = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "BLIS_NUM_THREADS",
)
_PREIMPORT_ENVIRONMENT = _THREAD_ENVIRONMENT + (
    "PYTHONHASHSEED",
    "CUDA_VISIBLE_DEVICES",
)
_LEDGER_SCHEMA = "heterodiff-a1-exact-population-ledger-v6"
_CAMPAIGN_SCHEMA = "heterodiff-a1-exact-population-campaign-v4"
_RUN_KEY_SCHEMA = "heterodiff-a1-exact-population-run-key-v1"
_RUNTIME_SCHEMA = "heterodiff-a1-isolated-runtime-v3"
_PREFLIGHT_RECEIPT_SCHEMA = "heterodiff-a1-exact-population-preflight-receipt-v1"
_WORKER_SESSION_SCHEMA = "heterodiff-a1-exact-worker-session-v2"
_LAUNCH_LEDGER_SCHEMA = "heterodiff-a1-exact-launch-ledger-v3"
_LAUNCH_AUTHORIZATION_SCHEMA = "heterodiff-a1-exact-launch-authorization-v3"
_PROCESS_IDENTITY_SCHEMA = "heterodiff-a1-process-identity-v1"
_OPTIMIZER_COMPLETION_SCHEMA = "heterodiff-a1-exact-optimizer-completion-v2"
_AGGREGATE_SCHEMA = "heterodiff-a1-exact-population-aggregate-v5"
_PROCESS_FALLBACK_START_MARKER = "%s:%s:%s" % (
    time.monotonic_ns(),
    time.process_time_ns(),
    str(Path(sys.executable).resolve()),
)
_ALL_STATES = frozenset(("RESERVED", "PREPARED", "RUNNING", "SUCCESS", "FAILURE", "HOLD"))
_SUCCESS_FIELDS = frozenset(
    (
        "method_result_sha256",
        "classifier_sha256",
        "certificate_sha256",
        "parameter_sha256",
        "trace_sha256",
        "split_diagnostic_sha256",
        "resource_sha256",
        "optimizer_completion",
        "optimizer_completion_sha256",
        "optimizer_wall_seconds",
        "total_cpu_seconds",
        "total_wall_seconds",
        "peak_rss_bytes",
        "optimizer_steps",
        "result_file",
        "result_file_sha256",
        "completed_unix_ns",
    )
)
_TEST_ONLY_SUCCESS_ADDITION_FIELDS = _SUCCESS_FIELDS.difference(
    ("optimizer_completion", "optimizer_completion_sha256")
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


def _lower_sha256(value: object, *, name: str) -> str:
    if type(value) is not str or len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError("%s must be a lowercase SHA-256 digest" % name)
    return value


def _validated_child_process_id(value: object, *, name: str) -> int:
    if isinstance(value, bool) or type(value) is not int or value <= 0:
        raise ValueError("%s must be a positive process ID" % name)
    return value


def _child_signal_from_returncode(returncode: object) -> Optional[int]:
    if isinstance(returncode, bool) or type(returncode) is not int:
        raise TypeError("child return code must be an integer")
    return -returncode if returncode < 0 else None


def _sha256_file(path: Path, *, maximum_bytes: int = 32 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    consumed = 0
    with path.open("rb") as handle:
        while True:
            block = handle.read(min(1024 * 1024, maximum_bytes + 1 - consumed))
            if not block:
                break
            consumed += len(block)
            if consumed > maximum_bytes:
                raise ValueError("exact method-result file exceeds the byte limit")
            digest.update(block)
    return digest.hexdigest()


def _peak_rss_bytes() -> int:
    native = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return native if sys.platform == "darwin" else native * 1024


@dataclass(frozen=True)
class FrozenExactPopulationRunRequest:
    seed: int
    method: str

    def __post_init__(self) -> None:
        if isinstance(self.seed, bool) or type(self.seed) is not int:
            raise TypeError("seed must be an integer non-boolean value")
        if self.seed not in _SEEDS:
            raise ValueError("seed is not one of the eight frozen paired seeds")
        if type(self.method) is not str or self.method not in _METHODS:
            raise ValueError("method is not a frozen exact-population method")


def _cpu_identity_record() -> dict:
    """Return a nonempty CPU identity with platform-specific fallbacks."""

    value = platform.processor().strip()
    source = "platform.processor"
    if not value and sys.platform.startswith("linux"):
        try:
            with open("/proc/cpuinfo", "r", encoding="utf-8") as handle:
                for line in handle:
                    name, separator, candidate = line.partition(":")
                    if separator and name.strip().lower() in (
                        "model name",
                        "hardware",
                        "processor",
                    ) and candidate.strip():
                        value = candidate.strip()
                        source = "/proc/cpuinfo:%s" % name.strip().lower()
                        break
        except OSError:
            pass
    if not value and sys.platform == "darwin":
        try:
            completed = subprocess.run(
                ["/usr/sbin/sysctl", "-n", "machdep.cpu.brand_string"],
                check=False,
                capture_output=True,
                text=True,
            )
            if completed.returncode == 0 and completed.stdout.strip():
                value = completed.stdout.strip()
                source = "sysctl:machdep.cpu.brand_string"
        except OSError:
            pass
    if not value:
        value = platform.machine().strip() or os.uname().machine.strip()
        source = "platform.machine"
    if not value:
        raise RuntimeError("a nonempty CPU identity could not be established")
    return {"value": value, "source": source}


def _current_process_identity_record() -> dict:
    """Return one child-process identity including a start marker."""

    pid = os.getpid()
    parent_pid = os.getppid()
    start_marker = ""
    source = ""
    if sys.platform.startswith("linux"):
        try:
            with open("/proc/self/stat", "r", encoding="ascii") as handle:
                stat = handle.read().strip()
            remainder = stat[stat.rfind(")") + 2 :].split()
            start_ticks = remainder[19]
            boot_id = ""
            try:
                with open(
                    "/proc/sys/kernel/random/boot_id", "r", encoding="ascii"
                ) as handle:
                    boot_id = handle.read().strip()
            except OSError:
                pass
            start_marker = "%s:%s" % (boot_id, start_ticks)
            source = "linux-proc-starttime"
        except (OSError, IndexError):
            pass
    elif sys.platform == "darwin":
        try:
            completed = subprocess.run(
                ["/bin/ps", "-o", "lstart=", "-p", str(pid)],
                check=False,
                capture_output=True,
                text=True,
            )
            if completed.returncode == 0 and completed.stdout.strip():
                start_marker = completed.stdout.strip()
                source = "darwin-ps-lstart"
        except OSError:
            pass
    if not start_marker:
        start_marker = _PROCESS_FALLBACK_START_MARKER
        source = "portable-monotonic-process-fallback"
    record = {
        "schema": _PROCESS_IDENTITY_SCHEMA,
        "pid": pid,
        "parent_pid": parent_pid,
        "start_marker": start_marker,
        "start_marker_source": source,
        "executable": str(Path(sys.executable).resolve()),
    }
    record["process_identity_sha256"] = _sha256_json(record)
    return record


def _validated_process_identity_record(value: object) -> dict:
    expected = {
        "schema",
        "pid",
        "parent_pid",
        "start_marker",
        "start_marker_source",
        "executable",
        "process_identity_sha256",
    }
    if type(value) is not dict or set(value) != expected:
        raise RuntimeError("child process identity schema is invalid")
    body = dict(value)
    claimed = _lower_sha256(
        body.pop("process_identity_sha256"), name="process_identity_sha256"
    )
    if _sha256_json(body) != claimed:
        raise RuntimeError("child process identity digest is inconsistent")
    if (
        value.get("schema") != _PROCESS_IDENTITY_SCHEMA
        or type(value.get("pid")) is not int
        or value["pid"] <= 0
        or type(value.get("parent_pid")) is not int
        or value["parent_pid"] <= 0
        or any(
            type(value.get(name)) is not str or not value[name]
            for name in ("start_marker", "start_marker_source", "executable")
        )
    ):
        raise RuntimeError("child process identity contents are invalid")
    return value


_WORKER_LAUNCH_CAPABILITY_CONSTRUCTION_KEY = object()


class FrozenExactWorkerLaunchCapability:
    """Typed one-worker session issued by a consumed parent pipe handshake.

    The capability is bound to the current worker PID, its parent PID, one
    coordinate, and one canonical ledger directory.  It can enter the worker,
    issue one optimizer permit, and consume that permit exactly once.  Private
    construction is API hygiene for a non-hostile host, not authentication
    against a local adversary able to inspect or modify Python process state.
    """

    __slots__ = (
        "request",
        "ledger_directory",
        "worker_process_id",
        "parent_process_id",
        "launch_id_sha256",
        "launch_authorization_sha256",
        "child_process_identity_sha256",
        "production_eligible",
        "launch_mode",
        "_receipt_bytes",
        "worker_session_sha256",
        "_worker_entered",
        "_bound_run_key_sha256",
        "_permit_issued",
        "_permit_consumed",
        "_success_completed",
        "_locked",
    )

    def __init__(
        self,
        *,
        request: object,
        ledger_directory: object,
        token_sha256: object,
        launch_id_sha256: object,
        launch_authorization_sha256: object,
        child_process_identity: object,
        launch_mode: object,
        production_eligible: object,
        _construction_key: object,
    ) -> None:
        if _construction_key is not _WORKER_LAUNCH_CAPABILITY_CONSTRUCTION_KEY:
            raise TypeError(
                "exact worker launch capabilities come only from a handshake"
            )
        if type(request) is not FrozenExactPopulationRunRequest:
            raise TypeError("worker capability requires a frozen run request")
        if type(launch_mode) is not str or launch_mode not in (
            "parent-pipe-handshake",
            "test-only-emulated",
        ):
            raise ValueError("worker capability launch mode is invalid")
        if type(production_eligible) is not bool:
            raise TypeError("production_eligible must be boolean")
        if production_eligible != (launch_mode == "parent-pipe-handshake"):
            raise ValueError("worker capability mode/eligibility is inconsistent")
        resolved = str(Path(ledger_directory).resolve())
        token_digest = _lower_sha256(token_sha256, name="worker_token_sha256")
        launch_id = _lower_sha256(launch_id_sha256, name="launch_id_sha256")
        launch_authorization = _lower_sha256(
            launch_authorization_sha256,
            name="launch_authorization_sha256",
        )
        child_identity = _validated_process_identity_record(
            child_process_identity
        )
        worker_pid = os.getpid()
        parent_pid = os.getppid()
        if worker_pid <= 0 or parent_pid <= 0:
            raise RuntimeError("worker capability process identity is invalid")
        receipt = {
            "schema": _WORKER_SESSION_SCHEMA,
            "launch_mode": launch_mode,
            "production_eligible": production_eligible,
            "worker_process_id": worker_pid,
            "parent_process_id": parent_pid,
            "request": asdict(request),
            "ledger_directory": resolved,
            "worker_token_sha256": token_digest,
            "launch_id_sha256": launch_id,
            "launch_authorization_sha256": launch_authorization,
            "child_process_identity": child_identity,
            "child_process_identity_sha256": child_identity[
                "process_identity_sha256"
            ],
            "issued_unix_ns": time.time_ns(),
        }
        receipt["worker_session_sha256"] = _sha256_json(receipt)
        object.__setattr__(self, "request", request)
        object.__setattr__(self, "ledger_directory", resolved)
        object.__setattr__(self, "worker_process_id", worker_pid)
        object.__setattr__(self, "parent_process_id", parent_pid)
        object.__setattr__(self, "launch_id_sha256", launch_id)
        object.__setattr__(
            self, "launch_authorization_sha256", launch_authorization
        )
        object.__setattr__(
            self,
            "child_process_identity_sha256",
            child_identity["process_identity_sha256"],
        )
        object.__setattr__(self, "production_eligible", production_eligible)
        object.__setattr__(self, "launch_mode", launch_mode)
        object.__setattr__(self, "_receipt_bytes", _canonical_json(receipt))
        object.__setattr__(
            self, "worker_session_sha256", receipt["worker_session_sha256"]
        )
        object.__setattr__(self, "_worker_entered", False)
        object.__setattr__(self, "_bound_run_key_sha256", None)
        object.__setattr__(self, "_permit_issued", False)
        object.__setattr__(self, "_permit_consumed", False)
        object.__setattr__(self, "_success_completed", False)
        object.__setattr__(self, "_locked", True)

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_locked", False):
            raise AttributeError("exact worker launch capability is immutable")
        object.__setattr__(self, name, value)

    @property
    def session_receipt(self) -> dict:
        return json.loads(self._receipt_bytes.decode("ascii"))

    def _assert_process_and_coordinate(
        self, request: object, ledger_directory: object
    ) -> None:
        if os.getpid() != self.worker_process_id or os.getppid() != self.parent_process_id:
            raise RuntimeError("exact worker capability belongs to another process session")
        if (
            type(request) is not FrozenExactPopulationRunRequest
            or request != self.request
            or str(Path(ledger_directory).resolve()) != self.ledger_directory
        ):
            raise RuntimeError("exact worker capability coordinate/path changed")

    def enter_worker(
        self, request: FrozenExactPopulationRunRequest, ledger_directory: object
    ) -> None:
        self._assert_process_and_coordinate(request, ledger_directory)
        if self._worker_entered:
            raise RuntimeError("exact worker capability was already entered")
        object.__setattr__(self, "_worker_entered", True)

    def authorize_permit(self) -> None:
        self._assert_process_and_coordinate(self.request, self.ledger_directory)
        if (
            not self._worker_entered
            or self._bound_run_key_sha256 is None
            or self._permit_issued
            or self._permit_consumed
        ):
            raise RuntimeError("exact worker session cannot issue another permit")
        object.__setattr__(self, "_permit_issued", True)

    def bind_run_key(self, run_key_sha256: object) -> None:
        self._assert_process_and_coordinate(self.request, self.ledger_directory)
        checked = _lower_sha256(run_key_sha256, name="run_key_sha256")
        if not self._worker_entered or self._bound_run_key_sha256 is not None:
            raise RuntimeError("exact worker session is already bound to a run key")
        object.__setattr__(self, "_bound_run_key_sha256", checked)

    def assert_run_key(self, run_key_sha256: object) -> None:
        checked = _lower_sha256(run_key_sha256, name="run_key_sha256")
        if checked != self._bound_run_key_sha256:
            raise RuntimeError("exact worker session run key changed")

    def assert_permit_active(self, worker_session_sha256: object) -> None:
        self._assert_process_and_coordinate(self.request, self.ledger_directory)
        if (
            not self._worker_entered
            or not self._permit_issued
            or self._permit_consumed
            or _lower_sha256(
                worker_session_sha256, name="worker_session_sha256"
            )
            != self.worker_session_sha256
        ):
            raise RuntimeError("exact worker session permit is not active")

    def consume_permit(self, worker_session_sha256: object) -> None:
        self.assert_permit_active(worker_session_sha256)
        object.__setattr__(self, "_permit_consumed", True)

    def authorize_success(
        self, run_key_sha256: object, worker_session_sha256: object
    ) -> None:
        self._assert_process_and_coordinate(self.request, self.ledger_directory)
        self.assert_run_key(run_key_sha256)
        if (
            _lower_sha256(
                worker_session_sha256, name="worker_session_sha256"
            )
            != self.worker_session_sha256
            or not self._permit_consumed
            or self._success_completed
        ):
            raise RuntimeError("exact worker session cannot complete SUCCESS")
        object.__setattr__(self, "_success_completed", True)


def _issue_test_only_emulated_exact_worker_launch_capability(
    request: FrozenExactPopulationRunRequest, ledger_directory: object
) -> FrozenExactWorkerLaunchCapability:
    """Issue an optimizer-ineligible capability for no-update custody tests."""

    child_identity = _current_process_identity_record()
    child_body = dict(child_identity)
    child_body.pop("process_identity_sha256")
    child_body["start_marker"] = "%s:test-only:%s" % (
        child_body["start_marker"],
        hashlib.sha256(os.urandom(32)).hexdigest(),
    )
    child_body["process_identity_sha256"] = _sha256_json(child_body)
    return FrozenExactWorkerLaunchCapability(
        request=request,
        ledger_directory=ledger_directory,
        token_sha256=hashlib.sha256(os.urandom(32)).hexdigest(),
        launch_id_sha256=hashlib.sha256(os.urandom(32)).hexdigest(),
        launch_authorization_sha256=hashlib.sha256(os.urandom(32)).hexdigest(),
        child_process_identity=child_body,
        launch_mode="test-only-emulated",
        production_eligible=False,
        _construction_key=_WORKER_LAUNCH_CAPABILITY_CONSTRUCTION_KEY,
    )


def frozen_exact_population_campaign_directory() -> Path:
    """Return the sole repository-local exact-population campaign path."""

    return (
        Path(__file__).resolve().parents[3]
        / "artifacts"
        / "a1_exact_population_campaign_v4"
    )


def frozen_exact_population_worker_environment(
    base: Optional[Mapping[str, str]] = None,
) -> Dict[str, str]:
    source = os.environ if base is None else base
    result = {str(key): str(value) for key, value in source.items()}
    for name in _THREAD_ENVIRONMENT:
        result[name] = "1"
    result["PYTHONHASHSEED"] = "0"
    result["CUDA_VISIBLE_DEVICES"] = ""
    return result


def _require_preimport_worker_environment() -> Dict[str, str]:
    observed = {name: os.environ.get(name) for name in _PREIMPORT_ENVIRONMENT}
    if any(observed[name] != "1" for name in _THREAD_ENVIRONMENT):
        raise RuntimeError("every BLAS/OpenMP thread variable must equal one before import")
    if observed["PYTHONHASHSEED"] != "0":
        raise RuntimeError("PYTHONHASHSEED must equal zero in the worker")
    if observed["CUDA_VISIBLE_DEVICES"] != "":
        raise RuntimeError("CUDA_VISIBLE_DEVICES must be empty in the CPU worker")
    return {name: str(value) for name, value in observed.items()}


def _runtime_record_after_import(thread_environment: Dict[str, str]) -> dict:
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
            str(value["user_api"]), str(value["internal_api"]), str(value["prefix"])
        )
    )
    numpy_configuration = getattr(np.__config__, "CONFIG", None)
    if not isinstance(numpy_configuration, dict):
        raise RuntimeError("NumPy build configuration is unavailable")
    cpu_identity = _cpu_identity_record()
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
        "processor": cpu_identity["value"],
        "processor_source": cpu_identity["source"],
        "thread_environment": thread_environment,
        "native_pools": normalized_pools,
        "numpy_configuration": numpy_configuration,
        "torch_environment": asdict(environment),
    }
    record["sha256"] = _sha256_json(record)
    return record


def _consume_parent_handshake(
    control_fd: object,
    token_sha256: object,
    request: FrozenExactPopulationRunRequest,
    ledger_directory: object,
    launch_id_sha256: object,
) -> FrozenExactWorkerLaunchCapability:
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
    authorization = _consume_durable_launch_authorization(
        Path(ledger_directory).resolve(),
        request,
        launch_id_sha256=launch_id_sha256,
        worker_token_sha256=expected,
    )
    return FrozenExactWorkerLaunchCapability(
        request=request,
        ledger_directory=ledger_directory,
        token_sha256=expected,
        launch_id_sha256=authorization["launch_id_sha256"],
        launch_authorization_sha256=authorization[
            "launch_authorization_sha256"
        ],
        child_process_identity=authorization["child_process_identity"],
        launch_mode="parent-pipe-handshake",
        production_eligible=True,
        _construction_key=_WORKER_LAUNCH_CAPABILITY_CONSTRUCTION_KEY,
    )


def frozen_exact_population_run_key(
    request: FrozenExactPopulationRunRequest,
    *,
    fixture_sha256: object,
    source_sha256: object,
    exact_configuration_sha256: object,
    preflight_sha256: object,
    execution_runtime_sha256: object,
) -> str:
    if type(request) is not FrozenExactPopulationRunRequest:
        raise TypeError("request must be an exact-population run request")
    return _sha256_json(
        {
            "schema": _RUN_KEY_SCHEMA,
            "seed": request.seed,
            "method": request.method,
            "fixture_sha256": _lower_sha256(fixture_sha256, name="fixture_sha256"),
            "source_sha256": _lower_sha256(source_sha256, name="source_sha256"),
            "exact_configuration_sha256": _lower_sha256(
                exact_configuration_sha256, name="exact_configuration_sha256"
            ),
            "preflight_sha256": _lower_sha256(preflight_sha256, name="preflight_sha256"),
            "execution_runtime_sha256": _lower_sha256(
                execution_runtime_sha256, name="execution_runtime_sha256"
            ),
        }
    )


def _seal_ledger(value: dict) -> dict:
    sealed = dict(value)
    sealed.pop("ledger_sha256", None)
    sealed["ledger_sha256"] = _sha256_json(sealed)
    return sealed


def _empty_ledger() -> dict:
    return _seal_ledger({"schema": _LEDGER_SCHEMA, "runs": {}})


def _validated_ledger(value: object) -> dict:
    if not isinstance(value, dict) or value.get("schema") != _LEDGER_SCHEMA:
        raise ValueError("exact-population ledger schema is invalid")
    runs = value.get("runs")
    if not isinstance(runs, dict):
        raise ValueError("exact-population ledger runs must be a mapping")
    for key, record in runs.items():
        _lower_sha256(key, name="ledger run key")
        if not isinstance(record, dict) or record.get("state") not in _ALL_STATES:
            raise ValueError("exact-population ledger has an invalid run record")
        try:
            validated = _validated_stage_record(record)
        except RuntimeError as error:
            raise ValueError("exact-population ledger stage receipt is invalid") from error
        if validated.get("run_key_sha256") != key:
            raise ValueError("exact-population ledger key differs from its receipt")
    campaign = value.get("campaign")
    if campaign is not None:
        if not isinstance(campaign, dict) or campaign.get("schema") != _CAMPAIGN_SCHEMA:
            raise ValueError("exact-population campaign schema is invalid")
        claimed = _lower_sha256(campaign.get("campaign_sha256"), name="campaign_sha256")
        body = dict(campaign)
        body.pop("campaign_sha256")
        if _sha256_json(body) != claimed:
            raise ValueError("exact-population campaign digest is inconsistent")
    aggregate = value.get("aggregate")
    if aggregate is not None:
        if not isinstance(aggregate, dict) or aggregate.get("schema") != _AGGREGATE_SCHEMA:
            raise ValueError("exact-population aggregate schema is invalid")
        claimed = _lower_sha256(aggregate.get("aggregate_sha256"), name="aggregate_sha256")
        body = dict(aggregate)
        body.pop("aggregate_sha256")
        if _sha256_json(body) != claimed:
            raise ValueError("exact-population aggregate digest is inconsistent")
    claimed_ledger = _lower_sha256(value.get("ledger_sha256"), name="ledger_sha256")
    body = dict(value)
    body.pop("ledger_sha256")
    if _sha256_json(body) != claimed_ledger:
        raise ValueError("exact-population ledger digest is inconsistent")
    return value


def _read_ledger(path: Path) -> dict:
    if not path.exists():
        return _empty_ledger()
    with path.open("rb") as handle:
        payload = handle.read(16 * 1024 * 1024 + 1)
    if not payload:
        raise ValueError("existing exact-population ledger is empty")
    if len(payload) > 16 * 1024 * 1024:
        raise ValueError("exact-population ledger exceeds its byte limit")
    return _validated_ledger(json.loads(payload.decode("utf-8")))


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _atomic_write_json(path: Path, value: object) -> None:
    if not isinstance(value, dict) or value.get("schema") != _LEDGER_SCHEMA:
        raise TypeError("only an exact-population ledger may be written")
    payload = _canonical_json(_seal_ledger(value)) + b"\n"
    temporary_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=str(path.parent), prefix=".exact-ledger-", delete=False
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


def _seal_launch_ledger(value: dict) -> dict:
    sealed = dict(value)
    sealed.pop("launch_ledger_sha256", None)
    sealed["launch_ledger_sha256"] = _sha256_json(sealed)
    return sealed


def _validated_issued_launch_authorization(value: object) -> dict:
    expected = {
        "schema",
        "state",
        "launch_id_sha256",
        "request",
        "ledger_directory",
        "worker_token_sha256",
        "parent_pid",
        "parent_process_identity",
        "issued_unix_ns",
        "issued_authorization_sha256",
    }
    if type(value) is not dict or set(value) != expected or value.get("state") != "ISSUED":
        raise RuntimeError("exact launch authorization is not strictly ISSUED")
    body = dict(value)
    claimed = _lower_sha256(
        body.pop("issued_authorization_sha256"),
        name="issued_authorization_sha256",
    )
    if _sha256_json(body) != claimed:
        raise RuntimeError("exact ISSUED launch authorization digest is inconsistent")
    _lower_sha256(value.get("launch_id_sha256"), name="launch_id_sha256")
    _lower_sha256(value.get("worker_token_sha256"), name="worker_token_sha256")
    request = value.get("request")
    if type(request) is not dict or set(request) != {"seed", "method"}:
        raise RuntimeError("exact launch authorization request is invalid")
    FrozenExactPopulationRunRequest(**request)
    parent_identity = _validated_process_identity_record(
        value.get("parent_process_identity")
    )
    if (
        value.get("schema") != _LAUNCH_AUTHORIZATION_SCHEMA
        or type(value.get("ledger_directory")) is not str
        or str(Path(value["ledger_directory"]).resolve())
        != value["ledger_directory"]
        or type(value.get("parent_pid")) is not int
        or value["parent_pid"] <= 0
        or value["parent_pid"] != parent_identity["pid"]
        or type(value.get("issued_unix_ns")) is not int
        or value["issued_unix_ns"] <= 0
    ):
        raise RuntimeError("exact ISSUED launch authorization contents are invalid")
    return value


def _validated_consumed_launch_authorization(value: object) -> dict:
    if type(value) is not dict or value.get("state") != "CONSUMED":
        raise RuntimeError("exact launch authorization is not CONSUMED")
    body = dict(value)
    claimed = _lower_sha256(
        body.pop("launch_authorization_sha256"),
        name="launch_authorization_sha256",
    )
    if _sha256_json(body) != claimed:
        raise RuntimeError("exact CONSUMED launch authorization digest is inconsistent")
    issued = dict(body)
    issued["state"] = "ISSUED"
    for name in (
        "child_pid",
        "child_process_identity",
        "child_process_identity_sha256",
        "consumed_unix_ns",
    ):
        if name not in issued:
            raise RuntimeError("exact CONSUMED launch authorization is incomplete")
        issued.pop(name)
    _validated_issued_launch_authorization(issued)
    child = _validated_process_identity_record(value["child_process_identity"])
    if (
        value.get("child_pid") != child["pid"]
        or value.get("child_process_identity_sha256")
        != child["process_identity_sha256"]
        or child["parent_pid"] != value["parent_pid"]
        or value["child_pid"] == value["parent_pid"]
        or type(value.get("consumed_unix_ns")) is not int
        or value["consumed_unix_ns"] < value["issued_unix_ns"]
    ):
        raise RuntimeError("exact CONSUMED launch process identity is inconsistent")
    return value


_TERMINAL_LAUNCH_ADDITION_FIELDS = frozenset(
    (
        "failed_stage",
        "error_type",
        "error_message",
        "failed_unix_ns",
        "terminal_owner",
        "terminal_process_identity_sha256",
    )
)
_PARENT_TERMINAL_LAUNCH_ADDITION_FIELDS = frozenset(
    (
        "observed_child_pid",
        "child_returncode",
        "child_signal",
    )
)
_PARENT_CLEANUP_OBSERVATION_ADDITION_FIELDS = frozenset(
    (
        "cleanup_owner",
        "cleanup_process_identity_sha256",
        "cleanup_observed_child_pid",
        "cleanup_child_returncode",
        "cleanup_child_signal",
        "cleanup_observed_unix_ns",
        "previous_terminal_launch_authorization_sha256",
    )
)
_PARENT_TERMINAL_LAUNCH_STAGES = frozenset(
    (
        "PARENT_ISSUANCE_COMMIT",
        "PARENT_SPAWN",
        "PARENT_CHILD_PID",
        "PARENT_READ_FD_CLOSE",
        "PARENT_TOKEN_DELIVERY",
        "PARENT_TOKEN_FD_CLOSE",
        "PARENT_WAIT",
        "CHILD_EXIT_BEFORE_CONSUMPTION",
    )
)
_PARENT_REAPER_TERMINAL_LAUNCH_STAGE = (
    "CHILD_EXIT_AFTER_CONSUMPTION_NO_RUN"
)


class _DurableExactLaunchIssuanceError(RuntimeError):
    """An issuance write raised after its ISSUED receipt became observable."""

    def __init__(self, authorization: dict, original_error: BaseException) -> None:
        super().__init__(
            "exact launch issuance raised after the ISSUED receipt committed: %s"
            % original_error
        )
        self.authorization = dict(authorization)
        self.original_error = original_error


def _validated_terminal_launch_authorization(value: object) -> dict:
    if type(value) is not dict or value.get("state") not in ("FAILURE", "HOLD"):
        raise RuntimeError("exact launch authorization is not terminal")
    if "cleanup_observation_sha256" in value:
        cleanup_body = dict(value)
        cleanup_claimed = _lower_sha256(
            cleanup_body.pop("cleanup_observation_sha256"),
            name="cleanup_observation_sha256",
        )
        if _sha256_json(cleanup_body) != cleanup_claimed:
            raise RuntimeError(
                "exact cleanup observation digest is inconsistent"
            )
        predecessor = dict(cleanup_body)
        for name in _PARENT_CLEANUP_OBSERVATION_ADDITION_FIELDS:
            if name not in predecessor:
                raise RuntimeError(
                    "exact cleanup observation is incomplete"
                )
            predecessor.pop(name)
        terminal = _validated_terminal_launch_authorization(predecessor)
        terminal_owner = terminal.get("terminal_owner")
        if terminal_owner == "PARENT":
            predecessor_is_eligible = (
                terminal.get("failed_stage")
                in (
                    "PARENT_READ_FD_CLOSE",
                    "PARENT_TOKEN_DELIVERY",
                    "PARENT_TOKEN_FD_CLOSE",
                    "PARENT_WAIT",
                )
                and terminal.get("observed_child_pid") is not None
                and terminal.get("child_returncode") is None
                and terminal.get("child_signal") is None
            )
            expected_child_pid = terminal.get("observed_child_pid")
            expected_observer_identity = terminal.get(
                "terminal_process_identity_sha256"
            )
        elif terminal_owner == "CHILD":
            predecessor_is_eligible = (
                terminal.get("failed_stage") == "PRE_RUN_RESERVATION"
            )
            expected_child_pid = terminal.get("child_pid")
            expected_observer_identity = terminal.get(
                "parent_process_identity", {}
            ).get("process_identity_sha256")
        else:
            predecessor_is_eligible = False
            expected_child_pid = None
            expected_observer_identity = None
        if (
            not predecessor_is_eligible
            or value.get("cleanup_owner") != "PARENT"
            or value.get("cleanup_process_identity_sha256")
            != expected_observer_identity
            or value.get("previous_terminal_launch_authorization_sha256")
            != terminal["terminal_launch_authorization_sha256"]
        ):
            raise RuntimeError(
                "exact cleanup observation predecessor/ownership is invalid"
            )
        try:
            observed_pid = _validated_child_process_id(
                value.get("cleanup_observed_child_pid"),
                name="cleanup_observed_child_pid",
            )
            expected_signal = _child_signal_from_returncode(
                value.get("cleanup_child_returncode")
            )
        except (TypeError, ValueError) as error:
            raise RuntimeError(
                "exact cleanup child exit observation is invalid"
            ) from error
        if (
            observed_pid != expected_child_pid
            or value.get("cleanup_child_signal") != expected_signal
            or type(value.get("cleanup_observed_unix_ns")) is not int
            or value["cleanup_observed_unix_ns"] < terminal["failed_unix_ns"]
        ):
            raise RuntimeError(
                "exact cleanup child exit observation is inconsistent"
            )
        return value
    body = dict(value)
    claimed = _lower_sha256(
        body.pop("terminal_launch_authorization_sha256"),
        name="terminal_launch_authorization_sha256",
    )
    if _sha256_json(body) != claimed:
        raise RuntimeError("exact terminal launch authorization digest is inconsistent")
    predecessor = dict(body)
    for name in _TERMINAL_LAUNCH_ADDITION_FIELDS:
        if name not in predecessor:
            raise RuntimeError("exact terminal launch authorization is incomplete")
        predecessor.pop(name)
    stage = value.get("failed_stage")
    owner = value.get("terminal_owner")
    owner_identity = _lower_sha256(
        value.get("terminal_process_identity_sha256"),
        name="terminal_process_identity_sha256",
    )
    if stage == "PRE_RUN_RESERVATION":
        predecessor["state"] = "CONSUMED"
        _validated_consumed_launch_authorization(predecessor)
        if (
            owner != "CHILD"
            or owner_identity
            != predecessor["child_process_identity_sha256"]
        ):
            raise RuntimeError("exact terminal launch child ownership is invalid")
        predecessor_timestamp = predecessor["consumed_unix_ns"]
    elif owner == "PARENT" and stage in _PARENT_TERMINAL_LAUNCH_STAGES:
        for name in _PARENT_TERMINAL_LAUNCH_ADDITION_FIELDS:
            if name not in predecessor:
                raise RuntimeError(
                    "exact parent terminal launch observation is incomplete"
                )
            predecessor.pop(name)
        predecessor["state"] = "ISSUED"
        _validated_issued_launch_authorization(predecessor)
        parent_identity = _validated_process_identity_record(
            predecessor["parent_process_identity"]
        )
        if (
            owner != "PARENT"
            or owner_identity != parent_identity["process_identity_sha256"]
        ):
            raise RuntimeError("exact terminal launch parent ownership is invalid")
        observed_pid = value.get("observed_child_pid")
        returncode = value.get("child_returncode")
        child_signal = value.get("child_signal")
        if stage in (
            "PARENT_ISSUANCE_COMMIT",
            "PARENT_SPAWN",
            "PARENT_CHILD_PID",
        ):
            if any(
                observed is not None
                for observed in (observed_pid, returncode, child_signal)
            ):
                raise RuntimeError(
                    "exact pre-PID parent terminal observation is invalid"
                )
        else:
            try:
                _validated_child_process_id(
                    observed_pid, name="observed_child_pid"
                )
            except ValueError as error:
                raise RuntimeError(
                    "exact parent terminal child PID is invalid"
                ) from error
            if stage == "CHILD_EXIT_BEFORE_CONSUMPTION":
                try:
                    expected_signal = _child_signal_from_returncode(returncode)
                except TypeError as error:
                    raise RuntimeError(
                        "exact parent terminal return code is invalid"
                    ) from error
                if child_signal != expected_signal:
                    raise RuntimeError(
                        "exact parent terminal child signal is inconsistent"
                    )
            elif returncode is not None or child_signal is not None:
                raise RuntimeError(
                    "exact non-exit parent terminal claimed a child outcome"
                )
        predecessor_timestamp = predecessor["issued_unix_ns"]
    elif (
        owner == "PARENT_REAPER"
        and stage == _PARENT_REAPER_TERMINAL_LAUNCH_STAGE
    ):
        if value.get("state") != "FAILURE":
            raise RuntimeError(
                "exact parent-reaper launch state must be FAILURE"
            )
        for name in _PARENT_TERMINAL_LAUNCH_ADDITION_FIELDS:
            if name not in predecessor:
                raise RuntimeError(
                    "exact parent-reaper terminal observation is incomplete"
                )
            predecessor.pop(name)
        predecessor["state"] = "CONSUMED"
        _validated_consumed_launch_authorization(predecessor)
        parent_identity = _validated_process_identity_record(
            predecessor["parent_process_identity"]
        )
        try:
            observed_pid = _validated_child_process_id(
                value.get("observed_child_pid"), name="observed_child_pid"
            )
            expected_signal = _child_signal_from_returncode(
                value.get("child_returncode")
            )
        except (TypeError, ValueError) as error:
            raise RuntimeError(
                "exact parent-reaper child exit observation is invalid"
            ) from error
        if (
            owner_identity != parent_identity["process_identity_sha256"]
            or observed_pid != predecessor["child_pid"]
            or value.get("child_signal") != expected_signal
        ):
            raise RuntimeError(
                "exact parent-reaper child exit observation is inconsistent"
            )
        predecessor_timestamp = predecessor["consumed_unix_ns"]
    else:
        raise RuntimeError("exact terminal launch stage is invalid")
    if type(value.get("error_type")) is not str or not value["error_type"]:
        raise RuntimeError("exact terminal launch error type is invalid")
    if type(value.get("error_message")) is not str:
        raise RuntimeError("exact terminal launch error message is invalid")
    failed_ns = value.get("failed_unix_ns")
    if (
        type(failed_ns) is not int
        or failed_ns < predecessor_timestamp
    ):
        raise RuntimeError("exact terminal launch timestamp is invalid")
    return value


def _issued_predecessor_from_launch_authorization(value: object) -> dict:
    """Recover and validate the immutable ISSUED receipt from any state."""

    if type(value) is not dict:
        raise RuntimeError("exact launch authorization is not a mapping")
    state = value.get("state")
    if state == "ISSUED":
        return dict(_validated_issued_launch_authorization(value))
    candidate = dict(value)
    if "cleanup_observation_sha256" in candidate:
        _validated_terminal_launch_authorization(candidate)
        candidate.pop("cleanup_observation_sha256")
        for name in _PARENT_CLEANUP_OBSERVATION_ADDITION_FIELDS:
            candidate.pop(name)
    if state == "CONSUMED":
        _validated_consumed_launch_authorization(candidate)
    elif state in ("FAILURE", "HOLD"):
        _validated_terminal_launch_authorization(candidate)
        candidate.pop("terminal_launch_authorization_sha256")
        for name in _TERMINAL_LAUNCH_ADDITION_FIELDS:
            candidate.pop(name)
        if value.get("terminal_owner") in ("PARENT", "PARENT_REAPER"):
            for name in _PARENT_TERMINAL_LAUNCH_ADDITION_FIELDS:
                candidate.pop(name)
        if value.get("terminal_owner") == "PARENT":
            candidate["state"] = "ISSUED"
            return dict(_validated_issued_launch_authorization(candidate))
        candidate["state"] = "CONSUMED"
        _validated_consumed_launch_authorization(candidate)
    else:
        raise RuntimeError("exact launch authorization state is invalid")
    candidate.pop("launch_authorization_sha256")
    for name in (
        "child_pid",
        "child_process_identity",
        "child_process_identity_sha256",
        "consumed_unix_ns",
    ):
        candidate.pop(name)
    candidate["state"] = "ISSUED"
    return dict(_validated_issued_launch_authorization(candidate))


def _validated_launch_ledger(value: object) -> dict:
    if type(value) is not dict or set(value) != {
        "schema",
        "launches",
        "launch_ledger_sha256",
    } or value.get("schema") != _LAUNCH_LEDGER_SCHEMA:
        raise RuntimeError("exact launch ledger schema is invalid")
    body = dict(value)
    claimed = _lower_sha256(
        body.pop("launch_ledger_sha256"), name="launch_ledger_sha256"
    )
    if _sha256_json(body) != claimed:
        raise RuntimeError("exact launch ledger digest is inconsistent")
    launches = value.get("launches")
    if type(launches) is not dict:
        raise RuntimeError("exact launch ledger launches are invalid")
    for launch_id, record in launches.items():
        _lower_sha256(launch_id, name="launch_id_sha256")
        if record.get("state") == "ISSUED":
            _validated_issued_launch_authorization(record)
        elif record.get("state") == "CONSUMED":
            _validated_consumed_launch_authorization(record)
        elif record.get("state") in ("FAILURE", "HOLD"):
            _validated_terminal_launch_authorization(record)
        else:
            raise RuntimeError("exact launch authorization state is invalid")
        if record.get("launch_id_sha256") != launch_id:
            raise RuntimeError("exact launch ledger key differs from its receipt")
    return value


def _read_launch_ledger(path: Path) -> dict:
    if not path.exists():
        return _seal_launch_ledger(
            {"schema": _LAUNCH_LEDGER_SCHEMA, "launches": {}}
        )
    with path.open("rb") as handle:
        payload = handle.read(16 * 1024 * 1024 + 1)
    if not payload or len(payload) > 16 * 1024 * 1024:
        raise RuntimeError("exact launch ledger size is invalid")
    return _validated_launch_ledger(json.loads(payload.decode("utf-8")))


def _atomic_write_launch_ledger(path: Path, value: dict) -> None:
    payload = _canonical_json(_seal_launch_ledger(value)) + b"\n"
    temporary_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=str(path.parent), prefix=".exact-launch-", delete=False
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


@contextmanager
def _locked_launch_ledger(directory: Path) -> Iterator[Tuple[Path, dict]]:
    resolved = directory.resolve()
    resolved.mkdir(parents=True, exist_ok=True)
    with (resolved / "launches.lock").open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            path = resolved / "launches.json"
            yield path, _read_launch_ledger(path)
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def _issue_parent_launch_authorization(
    directory: Path,
    request: FrozenExactPopulationRunRequest,
    worker_token_sha256: object,
) -> dict:
    if directory.resolve() != frozen_exact_population_campaign_directory().resolve():
        raise RuntimeError("exact launch authorization path is not canonical")
    token_digest = _lower_sha256(
        worker_token_sha256, name="worker_token_sha256"
    )
    launch_id = hashlib.sha256(os.urandom(32)).hexdigest()
    parent_identity = _current_process_identity_record()
    issued = {
        "schema": _LAUNCH_AUTHORIZATION_SCHEMA,
        "state": "ISSUED",
        "launch_id_sha256": launch_id,
        "request": asdict(request),
        "ledger_directory": str(directory.resolve()),
        "worker_token_sha256": token_digest,
        "parent_pid": os.getpid(),
        "parent_process_identity": parent_identity,
        "issued_unix_ns": time.time_ns(),
    }
    issued["issued_authorization_sha256"] = _sha256_json(issued)
    _validated_issued_launch_authorization(issued)
    with _locked_launch_ledger(directory) as (path, ledger):
        if launch_id in ledger["launches"]:
            raise RuntimeError("exact launch ID unexpectedly already exists")
        ledger["launches"][launch_id] = issued
        try:
            _atomic_write_launch_ledger(path, ledger)
        except BaseException as error:
            try:
                durable = _read_launch_ledger(path)["launches"].get(launch_id)
            except BaseException as read_error:
                raise RuntimeError(
                    "exact launch issuance commit state is unreadable"
                ) from read_error
            if durable == issued:
                raise _DurableExactLaunchIssuanceError(
                    issued, error
                ) from error
            if durable is None:
                raise
            raise RuntimeError(
                "exact launch issuance commit differs from its candidate"
            ) from error
    return issued


def _consume_durable_launch_authorization(
    directory: Path,
    request: FrozenExactPopulationRunRequest,
    *,
    launch_id_sha256: object,
    worker_token_sha256: object,
) -> dict:
    launch_id = _lower_sha256(launch_id_sha256, name="launch_id_sha256")
    token_digest = _lower_sha256(
        worker_token_sha256, name="worker_token_sha256"
    )
    child_identity = _current_process_identity_record()
    with _locked_launch_ledger(directory) as (path, ledger):
        issued = _validated_issued_launch_authorization(
            ledger["launches"].get(launch_id)
        )
        if (
            issued["request"] != asdict(request)
            or issued["ledger_directory"] != str(directory.resolve())
            or issued["worker_token_sha256"] != token_digest
            or issued["parent_pid"] != os.getppid()
            or child_identity["parent_pid"] != issued["parent_pid"]
        ):
            raise RuntimeError("exact durable launch authorization does not match child")
        consumed = dict(issued)
        consumed.update(
            {
                "state": "CONSUMED",
                "child_pid": os.getpid(),
                "child_process_identity": child_identity,
                "child_process_identity_sha256": child_identity[
                    "process_identity_sha256"
                ],
                "consumed_unix_ns": time.time_ns(),
            }
        )
        consumed["launch_authorization_sha256"] = _sha256_json(consumed)
        _validated_consumed_launch_authorization(consumed)
        ledger["launches"][launch_id] = consumed
        _atomic_write_launch_ledger(path, ledger)
    return consumed


def _load_consumed_launch_authorization(
    directory: Path, launch_id_sha256: object
) -> dict:
    launch_id = _lower_sha256(launch_id_sha256, name="launch_id_sha256")
    with _locked_launch_ledger(directory) as (_, ledger):
        return _validated_consumed_launch_authorization(
            ledger["launches"].get(launch_id)
        )


def _terminalize_consumed_launch_authorization(
    directory: Path,
    launch_id_sha256: object,
    *,
    state: object,
    error: BaseException,
) -> dict:
    """Durably record a post-handshake failure before main-run reservation."""

    if type(state) is not str or state not in ("FAILURE", "HOLD"):
        raise ValueError("exact terminal launch state must be FAILURE or HOLD")
    if not isinstance(error, BaseException):
        raise TypeError("exact terminal launch error must be an exception")
    launch_id = _lower_sha256(launch_id_sha256, name="launch_id_sha256")
    with _locked_launch_ledger(directory) as (path, ledger):
        consumed = _validated_consumed_launch_authorization(
            ledger["launches"].get(launch_id)
        )
        if consumed["child_pid"] != os.getpid():
            raise RuntimeError("only the authorized child may terminalize its launch")
        terminal = dict(consumed)
        terminal.update(
            {
                "state": state,
                "failed_stage": "PRE_RUN_RESERVATION",
                "error_type": type(error).__name__,
                "error_message": str(error),
                "failed_unix_ns": time.time_ns(),
                "terminal_owner": "CHILD",
                "terminal_process_identity_sha256": consumed[
                    "child_process_identity_sha256"
                ],
            }
        )
        terminal["terminal_launch_authorization_sha256"] = _sha256_json(
            terminal
        )
        _validated_terminal_launch_authorization(terminal)
        ledger["launches"][launch_id] = terminal
        _atomic_write_launch_ledger(path, ledger)
    return terminal


def _terminalize_parent_launch_authorization(
    directory: Path,
    authorization: object,
    request: FrozenExactPopulationRunRequest,
    *,
    state: object,
    failed_stage: object,
    error: BaseException,
    observed_child_pid: Optional[int] = None,
    child_returncode: Optional[int] = None,
) -> Optional[dict]:
    """Close an authorization only while its issuing parent still owns it."""

    if type(request) is not FrozenExactPopulationRunRequest:
        raise TypeError("parent launch terminalization requires an exact request")
    if type(state) is not str or state not in ("FAILURE", "HOLD"):
        raise ValueError("exact terminal launch state must be FAILURE or HOLD")
    if (
        type(failed_stage) is not str
        or failed_stage not in _PARENT_TERMINAL_LAUNCH_STAGES
    ):
        raise ValueError("exact parent terminal launch stage is invalid")
    if not isinstance(error, BaseException):
        raise TypeError("exact terminal launch error must be an exception")
    if observed_child_pid is not None:
        _validated_child_process_id(
            observed_child_pid, name="observed_child_pid"
        )
    child_signal = (
        None
        if child_returncode is None
        else _child_signal_from_returncode(child_returncode)
    )
    if failed_stage in (
        "PARENT_ISSUANCE_COMMIT",
        "PARENT_SPAWN",
        "PARENT_CHILD_PID",
    ):
        if any(
            observed is not None
            for observed in (
                observed_child_pid,
                child_returncode,
                child_signal,
            )
        ):
            raise ValueError(
                "exact pre-PID parent failure cannot claim a child outcome"
            )
    else:
        if observed_child_pid is None:
            raise ValueError(
                "exact post-spawn parent failure requires the observed child PID"
            )
        if failed_stage == "CHILD_EXIT_BEFORE_CONSUMPTION":
            if child_returncode is None:
                raise ValueError(
                    "exact child-exit failure requires a return code"
                )
        elif child_returncode is not None or child_signal is not None:
            raise ValueError(
                "exact non-exit parent failure cannot claim a child outcome"
            )
    issued_snapshot = dict(_validated_issued_launch_authorization(authorization))
    launch_id = issued_snapshot["launch_id_sha256"]
    resolved = directory.resolve()
    parent_identity = _current_process_identity_record()
    with _locked_launch_ledger(resolved) as (path, ledger):
        current = ledger["launches"].get(launch_id)
        if type(current) is not dict:
            raise RuntimeError("exact parent launch authorization is absent")
        current_issued = _issued_predecessor_from_launch_authorization(current)
        if (
            current_issued != issued_snapshot
            or current_issued["request"] != asdict(request)
            or current_issued["ledger_directory"] != str(resolved)
            or current_issued["parent_pid"] != os.getpid()
            or current_issued["parent_process_identity"] != parent_identity
        ):
            raise RuntimeError(
                "exact parent cannot terminalize another launch authorization"
            )
        current_state = current.get("state")
        if current_state != "ISSUED":
            if current_state == "CONSUMED":
                _validated_consumed_launch_authorization(current)
                return None
            if current_state in ("FAILURE", "HOLD"):
                _validated_terminal_launch_authorization(current)
                return current
            raise RuntimeError("exact parent launch authorization state is invalid")
        issued = _validated_issued_launch_authorization(current)
        if issued != issued_snapshot:
            raise RuntimeError("exact parent launch authorization changed")
        terminal = dict(issued)
        terminal.update(
            {
                "state": state,
                "failed_stage": failed_stage,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "failed_unix_ns": time.time_ns(),
                "terminal_owner": "PARENT",
                "terminal_process_identity_sha256": parent_identity[
                    "process_identity_sha256"
                ],
                "observed_child_pid": observed_child_pid,
                "child_returncode": child_returncode,
                "child_signal": child_signal,
            }
        )
        terminal["terminal_launch_authorization_sha256"] = _sha256_json(
            terminal
        )
        _validated_terminal_launch_authorization(terminal)
        ledger["launches"][launch_id] = terminal
        _atomic_write_launch_ledger(path, ledger)
    return terminal


def _append_parent_cleanup_exit_observation(
    directory: Path,
    authorization: object,
    request: FrozenExactPopulationRunRequest,
    *,
    observed_child_pid: object,
    child_returncode: object,
) -> dict:
    """Append a second receipt when cleanup later observes child exit."""

    issued_snapshot = dict(_validated_issued_launch_authorization(authorization))
    observed_pid = _validated_child_process_id(
        observed_child_pid, name="observed_child_pid"
    )
    child_signal = _child_signal_from_returncode(child_returncode)
    if (
        type(request) is not FrozenExactPopulationRunRequest
        or issued_snapshot["request"] != asdict(request)
        or issued_snapshot["ledger_directory"] != str(directory.resolve())
    ):
        raise RuntimeError("exact cleanup observation request/path is invalid")
    parent_identity = _current_process_identity_record()
    if parent_identity != issued_snapshot["parent_process_identity"]:
        raise RuntimeError("exact cleanup observer does not own this launch")
    with _locked_launch_ledger(directory) as (path, ledger):
        current = ledger["launches"].get(issued_snapshot["launch_id_sha256"])
        if type(current) is not dict:
            raise RuntimeError("exact cleanup launch authorization is absent")
        if _issued_predecessor_from_launch_authorization(current) != issued_snapshot:
            raise RuntimeError("exact cleanup launch authorization changed")
        terminal = _validated_terminal_launch_authorization(current)
        if "cleanup_observation_sha256" in terminal:
            if (
                terminal.get("cleanup_observed_child_pid") != observed_pid
                or terminal.get("cleanup_child_returncode") != child_returncode
                or terminal.get("cleanup_child_signal") != child_signal
            ):
                raise RuntimeError("exact cleanup exit observation changed")
            return terminal
        if terminal.get("terminal_owner") == "PARENT":
            eligible = (
                terminal.get("failed_stage")
                in (
                    "PARENT_READ_FD_CLOSE",
                    "PARENT_TOKEN_DELIVERY",
                    "PARENT_TOKEN_FD_CLOSE",
                    "PARENT_WAIT",
                )
                and terminal.get("observed_child_pid") == observed_pid
                and terminal.get("child_returncode") is None
                and terminal.get("child_signal") is None
            )
        elif terminal.get("terminal_owner") == "CHILD":
            eligible = (
                terminal.get("failed_stage") == "PRE_RUN_RESERVATION"
                and terminal.get("child_pid") == observed_pid
            )
        else:
            eligible = False
        if not eligible:
            raise RuntimeError(
                "exact parent terminal is not cleanup-observation eligible"
            )
        observation = dict(terminal)
        observation.update(
            {
                "cleanup_owner": "PARENT",
                "cleanup_process_identity_sha256": parent_identity[
                    "process_identity_sha256"
                ],
                "cleanup_observed_child_pid": observed_pid,
                "cleanup_child_returncode": child_returncode,
                "cleanup_child_signal": child_signal,
                "cleanup_observed_unix_ns": time.time_ns(),
                "previous_terminal_launch_authorization_sha256": terminal[
                    "terminal_launch_authorization_sha256"
                ],
            }
        )
        observation["cleanup_observation_sha256"] = _sha256_json(observation)
        _validated_terminal_launch_authorization(observation)
        ledger["launches"][issued_snapshot["launch_id_sha256"]] = observation
        _atomic_write_launch_ledger(path, ledger)
        return observation


def _require_durable_launch_for_capability(
    capability: FrozenExactWorkerLaunchCapability,
) -> Optional[dict]:
    if capability.production_eligible is not True:
        return None
    authorization = _load_consumed_launch_authorization(
        Path(capability.ledger_directory), capability.launch_id_sha256
    )
    receipt = capability.session_receipt
    if (
        authorization["launch_authorization_sha256"]
        != capability.launch_authorization_sha256
        or authorization["request"] != asdict(capability.request)
        or authorization["ledger_directory"] != capability.ledger_directory
        or authorization["child_pid"] != capability.worker_process_id
        or authorization["child_process_identity_sha256"]
        != capability.child_process_identity_sha256
        or receipt["worker_token_sha256"]
        != authorization["worker_token_sha256"]
    ):
        raise RuntimeError("exact worker capability differs from durable launch custody")
    return authorization


@contextmanager
def _locked_ledger(directory: Path) -> Iterator[Tuple[Path, dict]]:
    resolved = directory.resolve()
    resolved.mkdir(parents=True, exist_ok=True)
    with (resolved / "ledger.lock").open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            path = resolved / "ledger.json"
            yield path, _read_ledger(path)
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def _terminalize_launch_if_main_run_unreserved(
    directory: Path,
    launch_capability: object,
    error: BaseException,
) -> Optional[dict]:
    """Close launch custody only when no main-run receipt owns the session."""

    if type(launch_capability) is not FrozenExactWorkerLaunchCapability:
        raise TypeError("pre-reservation terminalization requires a worker capability")
    with _locked_ledger(directory) as (_, ledger):
        session_has_run = any(
            type(record) is dict
            and record.get("worker_session_sha256")
            == launch_capability.worker_session_sha256
            for record in ledger["runs"].values()
        )
    if session_has_run:
        return None
    state = (
        "HOLD"
        if type(error).__name__ == "ContinuousCorrectionCertificateError"
        else "FAILURE"
    )
    return _terminalize_consumed_launch_authorization(
        directory,
        launch_capability.launch_id_sha256,
        state=state,
        error=error,
    )


def _campaign_record(prepared: object, runtime_sha256: object) -> dict:
    runtime = _lower_sha256(runtime_sha256, name="execution_runtime_sha256")
    record = {
        "schema": _CAMPAIGN_SCHEMA,
        "fixture_sha256": prepared.train_population.fixture_sha256,
        "source_sha256": prepared.source_sha256,
        "exact_configuration_sha256": prepared.exact_configuration_sha256,
        "preflight_sha256": prepared.preflight_sha256,
        "execution_contract_sha256": prepared.execution_contract.digest,
        "split_custody_sha256": [value.custody_sha256 for value in prepared.populations],
        "oracle_product_control_custody_sha256": prepared.oracle_product_control.custody_sha256,
        "execution_runtime_sha256": runtime,
        "expected_coordinates": [
            {"seed": seed, "method": method}
            for seed in _SEEDS
            for method in _METHODS
        ],
        "expected_total_optimizer_steps": _EXPECTED_TOTAL_STEPS,
        "product_control_optimized": False,
    }
    record["campaign_sha256"] = _sha256_json(record)
    return record


def _ensure_campaign(directory: Path, prepared: object, runtime_sha256: str) -> dict:
    expected = _campaign_record(prepared, runtime_sha256)
    with _locked_ledger(directory) as (path, ledger):
        existing = ledger.get("campaign")
        if existing is None:
            ledger["campaign"] = expected
            _atomic_write_json(path, ledger)
        elif existing != expected:
            raise RuntimeError("exact-population campaign custody is already frozen differently")
    return expected


def _preflight_receipt(prepared: object, request: FrozenExactPopulationRunRequest) -> dict:
    seed_custody = next(value for value in prepared.seed_custodies if value.seed == request.seed)
    initial = (
        seed_custody.stronger_direct_initial_parameter_sha256
        if request.method == "strong_direct"
        else seed_custody.primary_initial_parameter_sha256
    )
    width = 40 if request.method == "strong_direct" else 32
    return {
        "schema": _PREFLIGHT_RECEIPT_SCHEMA,
        "seed": request.seed,
        "method": request.method,
        "preflight_sha256": prepared.preflight_sha256,
        "fixture_sha256": prepared.train_population.fixture_sha256,
        "source_sha256": prepared.source_sha256,
        "sampled_configuration_sha256": prepared.sampled_configuration_sha256,
        "exact_configuration_sha256": prepared.exact_configuration_sha256,
        "execution_contract_sha256": prepared.execution_contract.digest,
        "split_custody_sha256": [value.custody_sha256 for value in prepared.populations],
        "oracle_product_control_custody_sha256": prepared.oracle_product_control.custody_sha256,
        "oracle_product_control_passed": prepared.oracle_product_control.passed,
        "oracle_product_control_optimized": False,
        "seed_custody_sha256": seed_custody.custody_sha256,
        "initial_parameter_sha256": initial,
        "updates": _METHOD_UPDATES[request.method],
        "parameter_count": 21 * width + width + width * width + width + width + 1,
        "forward_multiply_add_count": 21 * width + width * width + width,
    }


def _validated_worker_session_receipt(receipt: object) -> dict:
    expected_fields = {
        "schema",
        "launch_mode",
        "production_eligible",
        "worker_process_id",
        "parent_process_id",
        "request",
        "ledger_directory",
        "worker_token_sha256",
        "launch_id_sha256",
        "launch_authorization_sha256",
        "child_process_identity",
        "child_process_identity_sha256",
        "issued_unix_ns",
        "worker_session_sha256",
    }
    if type(receipt) is not dict or set(receipt) != expected_fields:
        raise RuntimeError("exact worker-session receipt schema is invalid")
    body = dict(receipt)
    claimed = _lower_sha256(
        body.pop("worker_session_sha256"), name="worker_session_sha256"
    )
    if _sha256_json(body) != claimed:
        raise RuntimeError("exact worker-session receipt digest is inconsistent")
    launch_mode = receipt.get("launch_mode")
    production = receipt.get("production_eligible")
    if (
        receipt.get("schema") != _WORKER_SESSION_SCHEMA
        or launch_mode not in ("parent-pipe-handshake", "test-only-emulated")
        or type(production) is not bool
        or production != (launch_mode == "parent-pipe-handshake")
        or type(receipt.get("worker_process_id")) is not int
        or receipt["worker_process_id"] <= 0
        or type(receipt.get("parent_process_id")) is not int
        or receipt["parent_process_id"] <= 0
        or type(receipt.get("issued_unix_ns")) is not int
        or receipt["issued_unix_ns"] <= 0
        or type(receipt.get("ledger_directory")) is not str
        or str(Path(receipt["ledger_directory"]).resolve())
        != receipt["ledger_directory"]
    ):
        raise RuntimeError("exact worker-session receipt contents are invalid")
    _lower_sha256(receipt.get("worker_token_sha256"), name="worker_token_sha256")
    _lower_sha256(receipt.get("launch_id_sha256"), name="launch_id_sha256")
    _lower_sha256(
        receipt.get("launch_authorization_sha256"),
        name="launch_authorization_sha256",
    )
    child_identity = _validated_process_identity_record(
        receipt.get("child_process_identity")
    )
    if (
        receipt.get("child_process_identity_sha256")
        != child_identity["process_identity_sha256"]
        or receipt.get("worker_process_id") != child_identity["pid"]
        or receipt.get("parent_process_id") != child_identity["parent_pid"]
    ):
        raise RuntimeError("exact worker-session child identity is inconsistent")
    request_value = receipt.get("request")
    if type(request_value) is not dict or set(request_value) != {"seed", "method"}:
        raise RuntimeError("exact worker-session request is invalid")
    FrozenExactPopulationRunRequest(**request_value)
    return receipt


def _validated_reserved_record(record: object) -> dict:
    expected_fields = {
        "state",
        "request",
        "runtime",
        "worker_pid",
        "run_key_sha256",
        "campaign_sha256",
        "worker_session",
        "worker_session_sha256",
        "reserved_unix_ns",
        "reserved_ledger_sha256",
    }
    if type(record) is not dict or set(record) != expected_fields or record.get("state") != "RESERVED":
        raise RuntimeError("exact-population ledger run is not a strict RESERVED receipt")
    body = dict(record)
    claimed = _lower_sha256(
        body.pop("reserved_ledger_sha256"), name="reserved_ledger_sha256"
    )
    if _sha256_json(body) != claimed:
        raise RuntimeError("exact-population RESERVED receipt digest is inconsistent")
    runtime = _validated_runtime(record.get("runtime"))
    session = _validated_worker_session_receipt(record.get("worker_session"))
    request = record.get("request")
    if type(request) is not dict or set(request) != {"seed", "method"}:
        raise RuntimeError("exact-population RESERVED request is invalid")
    FrozenExactPopulationRunRequest(**request)
    if (
        record.get("worker_pid") != session["worker_process_id"]
        or request != session["request"]
        or record.get("worker_session_sha256")
        != session["worker_session_sha256"]
        or runtime.get("sha256")
        != record.get("runtime", {}).get("sha256")
    ):
        raise RuntimeError("exact-population RESERVED session/runtime is inconsistent")
    _lower_sha256(record.get("run_key_sha256"), name="run_key_sha256")
    _lower_sha256(record.get("campaign_sha256"), name="campaign_sha256")
    reserved_ns = record.get("reserved_unix_ns")
    if type(reserved_ns) is not int or reserved_ns <= 0:
        raise RuntimeError("exact-population RESERVED timestamp is invalid")
    return record


_PREPARED_ADDITION_FIELDS = frozenset(
    (
        "preflight",
        "preparation_wall_seconds",
        "preparation_cpu_seconds",
        "prepared_unix_ns",
    )
)


def _validated_prepared_chain(record: object) -> dict:
    if not isinstance(record, dict) or record.get("state") != "PREPARED":
        raise RuntimeError("exact-population ledger run is not PREPARED")
    body = dict(record)
    claimed = _lower_sha256(
        body.pop("prepared_ledger_sha256"), name="prepared_ledger_sha256"
    )
    if _sha256_json(body) != claimed:
        raise RuntimeError("exact-population PREPARED receipt digest is inconsistent")
    reserved = dict(body)
    reserved["state"] = "RESERVED"
    for name in _PREPARED_ADDITION_FIELDS:
        if name not in reserved:
            raise RuntimeError("exact-population PREPARED receipt is incomplete")
        reserved.pop(name)
    _validated_reserved_record(reserved)
    prepared_ns = record.get("prepared_unix_ns")
    if type(prepared_ns) is not int or prepared_ns < reserved["reserved_unix_ns"]:
        raise RuntimeError("exact-population PREPARED timestamp is invalid")
    for name in ("preparation_wall_seconds", "preparation_cpu_seconds"):
        value = record.get(name)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or float(value) <= 0.0
        ):
            raise RuntimeError("exact-population PREPARED resource timing is invalid")
    return record


def _reserve_run(
    directory: Path,
    run_key: str,
    request: FrozenExactPopulationRunRequest,
    runtime: dict,
    campaign_sha256: object,
    launch_capability: object,
) -> dict:
    if type(launch_capability) is not FrozenExactWorkerLaunchCapability:
        raise TypeError("exact reservation requires a typed worker-session capability")
    launch_capability._assert_process_and_coordinate(request, directory)
    if not launch_capability._worker_entered:
        raise RuntimeError("exact reservation requires an entered worker session")
    _require_durable_launch_for_capability(launch_capability)
    checked_runtime = _validated_runtime(runtime)
    session_receipt = launch_capability.session_receipt
    _validated_worker_session_receipt(session_receipt)
    campaign_digest = _lower_sha256(campaign_sha256, name="campaign_sha256")
    launch_capability.bind_run_key(run_key)
    with _locked_ledger(directory) as (path, ledger):
        existing = ledger["runs"].get(run_key)
        if existing is not None:
            raise RuntimeError(
                "exact-population run key already exists in state %s"
                % existing.get("state")
            )
        campaign = ledger.get("campaign")
        if (
            not isinstance(campaign, dict)
            or campaign.get("campaign_sha256") != campaign_digest
            or campaign.get("execution_runtime_sha256") != checked_runtime["sha256"]
        ):
            raise RuntimeError("exact reservation campaign/runtime is inconsistent")
        reserved = {
            "state": "RESERVED",
            "request": asdict(request),
            "runtime": checked_runtime,
            "worker_pid": os.getpid(),
            "run_key_sha256": run_key,
            "campaign_sha256": campaign_digest,
            "worker_session": session_receipt,
            "worker_session_sha256": launch_capability.worker_session_sha256,
            "reserved_unix_ns": time.time_ns(),
        }
        reserved["reserved_ledger_sha256"] = _sha256_json(reserved)
        _validated_reserved_record(reserved)
        ledger["runs"][run_key] = reserved
        _atomic_write_json(path, ledger)
    return reserved


_ALLOWED_TRANSITIONS = {
    "RESERVED": frozenset(("PREPARED", "FAILURE", "HOLD")),
    "PREPARED": frozenset(("RUNNING", "FAILURE", "HOLD")),
    # SUCCESS is deliberately absent: only the executor-completion finalizer
    # may write it after reopening the serialized result and consuming the
    # private single-use completion object.
    "RUNNING": frozenset(("FAILURE", "HOLD")),
    "SUCCESS": frozenset(),
    "FAILURE": frozenset(),
    "HOLD": frozenset(),
}


def _stage_receipt_sha256(record: dict) -> str:
    field = {
        "RESERVED": "reserved_ledger_sha256",
        "PREPARED": "prepared_ledger_sha256",
        "RUNNING": "running_ledger_sha256",
        "SUCCESS": "success_ledger_sha256",
        "FAILURE": "terminal_ledger_sha256",
        "HOLD": "terminal_ledger_sha256",
    }[record["state"]]
    return _lower_sha256(record.get(field), name=field)


def _transition(
    directory: Path,
    run_key: str,
    expected: str,
    record: dict,
    *,
    expected_prior_sha256: object,
) -> None:
    target = record.get("state")
    if expected not in _ALLOWED_TRANSITIONS or target not in _ALLOWED_TRANSITIONS[expected]:
        raise ValueError("exact-population transition state is invalid")
    expected_digest = _lower_sha256(
        expected_prior_sha256, name="expected_prior_sha256"
    )
    with _locked_ledger(directory) as (path, ledger):
        current = ledger["runs"].get(run_key)
        if not isinstance(current, dict) or current.get("state") != expected:
            raise RuntimeError("exact-population ledger state changed before transition")
        _validated_stage_record(current)
        if _stage_receipt_sha256(current) != expected_digest:
            raise RuntimeError("exact-population prior receipt identity changed")
        _validated_stage_record(record)
        if (
            record.get("worker_session_sha256")
            != current.get("worker_session_sha256")
        ):
            raise RuntimeError("exact-population worker session changed at transition")
        ledger["runs"][run_key] = record
        _atomic_write_json(path, ledger)


def _validated_prepared_record(record: object, permit: object, expected_preflight: dict) -> dict:
    _validated_prepared_chain(record)
    if (
        record.get("run_key_sha256") != permit.run_key_sha256
        or record.get("worker_pid") != permit.worker_process_id
        or record.get("runtime", {}).get("sha256") != permit.execution_runtime_sha256
        or _canonical_json(record.get("preflight")) != _canonical_json(expected_preflight)
        or record.get("prepared_ledger_sha256") != permit.prepared_ledger_sha256
        or record.get("campaign_sha256") != permit.campaign_sha256
        or record.get("worker_session_sha256")
        != permit.worker_session_sha256
        or record.get("preparation_wall_seconds")
        != permit.preparation_wall_seconds
        or record.get("preparation_cpu_seconds")
        != permit.preparation_cpu_seconds
        or record.get("request")
        != {
            "seed": expected_preflight["seed"],
            "method": expected_preflight["method"],
        }
    ):
        raise RuntimeError("exact-population PREPARED receipt differs from its permit")
    return record


def _validated_running_record(record: object) -> dict:
    if not isinstance(record, dict) or record.get("state") != "RUNNING":
        raise RuntimeError("exact-population ledger run is not RUNNING")
    body = dict(record)
    claimed = _lower_sha256(body.pop("running_ledger_sha256"), name="running_ledger_sha256")
    if _sha256_json(body) != claimed:
        raise RuntimeError("exact-population RUNNING receipt digest is inconsistent")
    prepared = dict(body)
    prepared["state"] = "PREPARED"
    prepared.pop("update_started_unix_ns")
    prepared.pop("running_ledger_sha256", None)
    try:
        _validated_prepared_chain(prepared)
    except RuntimeError as error:
        raise RuntimeError(
            "exact-population RUNNING breaks the PREPARED receipt chain"
        ) from error
    reserved_ns = prepared.get("reserved_unix_ns")
    prepared_ns = prepared.get("prepared_unix_ns")
    started_ns = body.get("update_started_unix_ns")
    if (
        isinstance(reserved_ns, bool)
        or not isinstance(reserved_ns, int)
        or reserved_ns <= 0
        or isinstance(prepared_ns, bool)
        or not isinstance(prepared_ns, int)
        or prepared_ns < reserved_ns
        or isinstance(started_ns, bool)
        or not isinstance(started_ns, int)
        or started_ns < prepared_ns
    ):
        raise RuntimeError("exact-population RUNNING timestamps are invalid")
    return record


_TERMINAL_ADDITION_FIELDS = frozenset(
    (
        "error_type",
        "error_message",
        "failed_stage",
        "failure_total_wall_seconds",
        "failure_total_cpu_seconds",
        "failure_process_peak_rss_bytes",
        "failed_unix_ns",
        "terminal_owner",
        "terminal_process_identity",
        "terminal_process_identity_sha256",
        "failure_origin",
        "observed_child_pid",
        "child_returncode",
        "child_signal",
        "previous_receipt_sha256",
    )
)
_PARENT_EXIT_MAIN_OBSERVATION_ADDITION_FIELDS = frozenset(
    (
        "parent_exit_observer",
        "parent_exit_process_identity",
        "parent_exit_process_identity_sha256",
        "parent_exit_observed_child_pid",
        "parent_exit_child_returncode",
        "parent_exit_child_signal",
        "parent_exit_observed_unix_ns",
        "previous_terminal_ledger_sha256",
    )
)
_PARENT_EXIT_SUCCESS_OBSERVATION_ADDITION_FIELDS = frozenset(
    (
        "parent_exit_observer",
        "parent_exit_process_identity",
        "parent_exit_process_identity_sha256",
        "parent_exit_observed_child_pid",
        "parent_exit_child_returncode",
        "parent_exit_child_signal",
        "parent_exit_observed_unix_ns",
        "previous_success_ledger_sha256",
    )
)


def _validated_terminal_record(record: object) -> dict:
    if not isinstance(record, dict) or record.get("state") not in ("FAILURE", "HOLD"):
        raise RuntimeError("exact-population ledger run is not terminal")
    if "parent_exit_observation_sha256" in record:
        observation_body = dict(record)
        observation_claimed = _lower_sha256(
            observation_body.pop("parent_exit_observation_sha256"),
            name="parent_exit_observation_sha256",
        )
        if _sha256_json(observation_body) != observation_claimed:
            raise RuntimeError(
                "exact parent exit observation digest is inconsistent"
            )
        predecessor = dict(observation_body)
        for name in _PARENT_EXIT_MAIN_OBSERVATION_ADDITION_FIELDS:
            if name not in predecessor:
                raise RuntimeError(
                    "exact parent exit observation is incomplete"
                )
            predecessor.pop(name)
        terminal = _validated_terminal_record(predecessor)
        session = _validated_worker_session_receipt(
            terminal["worker_session"]
        )
        parent_identity = _validated_process_identity_record(
            record.get("parent_exit_process_identity")
        )
        try:
            observed_pid = _validated_child_process_id(
                record.get("parent_exit_observed_child_pid"),
                name="parent_exit_observed_child_pid",
            )
            expected_signal = _child_signal_from_returncode(
                record.get("parent_exit_child_returncode")
            )
        except (TypeError, ValueError) as error:
            raise RuntimeError(
                "exact parent exit observation is invalid"
            ) from error
        if (
            terminal.get("terminal_owner") != "CHILD"
            or record.get("parent_exit_observer") != "PARENT"
            or parent_identity["pid"] != session["parent_process_id"]
            or record.get("parent_exit_process_identity_sha256")
            != parent_identity["process_identity_sha256"]
            or observed_pid != session["worker_process_id"]
            or record.get("parent_exit_child_signal") != expected_signal
            or record.get("previous_terminal_ledger_sha256")
            != terminal["terminal_ledger_sha256"]
            or type(record.get("parent_exit_observed_unix_ns")) is not int
            or record["parent_exit_observed_unix_ns"]
            < terminal["failed_unix_ns"]
        ):
            raise RuntimeError(
                "exact parent exit observation custody is inconsistent"
            )
        return record
    body = dict(record)
    claimed = _lower_sha256(
        body.pop("terminal_ledger_sha256"), name="terminal_ledger_sha256"
    )
    if _sha256_json(body) != claimed:
        raise RuntimeError("exact-population terminal receipt digest is inconsistent")
    prior_state = record.get("failed_stage")
    if prior_state not in ("RESERVED", "PREPARED", "RUNNING"):
        raise RuntimeError("exact-population terminal prior stage is invalid")
    prior = dict(body)
    prior["state"] = prior_state
    for name in _TERMINAL_ADDITION_FIELDS:
        if name not in prior:
            raise RuntimeError("exact-population terminal receipt is incomplete")
        prior.pop(name)
    _validated_stage_record(prior)
    previous_receipt = _lower_sha256(
        record.get("previous_receipt_sha256"),
        name="previous_receipt_sha256",
    )
    if previous_receipt != _stage_receipt_sha256(prior):
        raise RuntimeError(
            "exact-population terminal predecessor identity changed"
        )
    session = _validated_worker_session_receipt(prior["worker_session"])
    terminal_identity = _validated_process_identity_record(
        record.get("terminal_process_identity")
    )
    if (
        record.get("terminal_process_identity_sha256")
        != terminal_identity["process_identity_sha256"]
    ):
        raise RuntimeError(
            "exact-population terminal process identity is inconsistent"
        )
    owner = record.get("terminal_owner")
    origin = record.get("failure_origin")
    observed_child_pid = record.get("observed_child_pid")
    returncode = record.get("child_returncode")
    child_signal = record.get("child_signal")
    if owner == "CHILD":
        if (
            origin != "CHILD_EXCEPTION"
            or terminal_identity != session["child_process_identity"]
            or observed_child_pid != session["worker_process_id"]
            or returncode is not None
            or child_signal is not None
        ):
            raise RuntimeError(
                "exact-population child terminal ownership is inconsistent"
            )
    elif owner == "PARENT_REAPER":
        try:
            observed_child_pid = _validated_child_process_id(
                observed_child_pid, name="observed_child_pid"
            )
            expected_signal = _child_signal_from_returncode(returncode)
        except (TypeError, ValueError) as error:
            raise RuntimeError(
                "exact-population parent-reaper exit observation is invalid"
            ) from error
        if (
            record.get("state") != "FAILURE"
            or origin != "PARENT_REAPER_CHILD_EXIT"
            or terminal_identity["pid"] != session["parent_process_id"]
            or observed_child_pid != session["worker_process_id"]
            or child_signal != expected_signal
        ):
            raise RuntimeError(
                "exact-population parent-reaper state/ownership is inconsistent"
            )
    else:
        raise RuntimeError("exact-population terminal owner is invalid")
    failed_ns = record.get("failed_unix_ns")
    prior_ns = prior.get(
        {
            "RESERVED": "reserved_unix_ns",
            "PREPARED": "prepared_unix_ns",
            "RUNNING": "update_started_unix_ns",
        }[prior_state]
    )
    if type(failed_ns) is not int or failed_ns < prior_ns:
        raise RuntimeError("exact-population terminal timestamp is invalid")
    for name in ("failure_total_wall_seconds", "failure_total_cpu_seconds"):
        value = record.get(name)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or float(value) < 0.0
        ):
            raise RuntimeError("exact-population terminal resource timing is invalid")
    peak = record.get("failure_process_peak_rss_bytes")
    if isinstance(peak, bool) or not isinstance(peak, int) or peak <= 0:
        raise RuntimeError("exact-population terminal peak RSS is invalid")
    if type(record.get("error_type")) is not str or not record["error_type"]:
        raise RuntimeError("exact-population terminal error type is invalid")
    if type(record.get("error_message")) is not str:
        raise RuntimeError("exact-population terminal error message is invalid")
    return record


def _validated_stage_record(record: object) -> dict:
    if not isinstance(record, dict):
        raise RuntimeError("exact-population stage receipt is not a mapping")
    state = record.get("state")
    if state == "RESERVED":
        return _validated_reserved_record(record)
    if state == "PREPARED":
        return _validated_prepared_chain(record)
    if state == "RUNNING":
        return _validated_running_record(record)
    if state == "SUCCESS":
        return _validated_success_record(record)
    if state in ("FAILURE", "HOLD"):
        return _validated_terminal_record(record)
    raise RuntimeError("exact-population stage state is invalid")


def _validated_success_record(record: object) -> dict:
    if not isinstance(record, dict) or record.get("state") != "SUCCESS":
        raise RuntimeError("exact-population ledger run is not SUCCESS")
    if "parent_exit_observation_sha256" in record:
        observation_body = dict(record)
        observation_claimed = _lower_sha256(
            observation_body.pop("parent_exit_observation_sha256"),
            name="parent_exit_observation_sha256",
        )
        if _sha256_json(observation_body) != observation_claimed:
            raise RuntimeError(
                "exact SUCCESS parent exit observation digest is inconsistent"
            )
        predecessor = dict(observation_body)
        for name in _PARENT_EXIT_SUCCESS_OBSERVATION_ADDITION_FIELDS:
            if name not in predecessor:
                raise RuntimeError(
                    "exact SUCCESS parent exit observation is incomplete"
                )
            predecessor.pop(name)
        success = _validated_success_record(predecessor)
        session = _validated_worker_session_receipt(
            success["worker_session"]
        )
        parent_identity = _validated_process_identity_record(
            record.get("parent_exit_process_identity")
        )
        try:
            observed_pid = _validated_child_process_id(
                record.get("parent_exit_observed_child_pid"),
                name="parent_exit_observed_child_pid",
            )
            expected_signal = _child_signal_from_returncode(
                record.get("parent_exit_child_returncode")
            )
        except (TypeError, ValueError) as error:
            raise RuntimeError(
                "exact SUCCESS parent exit observation is invalid"
            ) from error
        if (
            record.get("parent_exit_observer") != "PARENT"
            or parent_identity["pid"] != session["parent_process_id"]
            or record.get("parent_exit_process_identity_sha256")
            != parent_identity["process_identity_sha256"]
            or observed_pid != session["worker_process_id"]
            or record.get("parent_exit_child_signal") != expected_signal
            or record.get("previous_success_ledger_sha256")
            != success["success_ledger_sha256"]
            or type(record.get("parent_exit_observed_unix_ns")) is not int
            or record["parent_exit_observed_unix_ns"]
            < success["completed_unix_ns"]
        ):
            raise RuntimeError(
                "exact SUCCESS parent exit observation custody is inconsistent"
            )
        return record
    body = dict(record)
    claimed = _lower_sha256(body.pop("success_ledger_sha256"), name="success_ledger_sha256")
    if _sha256_json(body) != claimed:
        raise RuntimeError("exact-population SUCCESS receipt digest is inconsistent")
    if any(name not in body for name in _SUCCESS_FIELDS):
        raise RuntimeError("exact-population SUCCESS receipt is incomplete")
    completion = _validated_optimizer_completion_receipt(
        body.get("optimizer_completion")
    )
    if (
        body.get("optimizer_completion_sha256")
        != completion["optimizer_completion_sha256"]
        or body.get("method_result_sha256") != completion["result_sha256"]
        or body.get("trace_sha256") != completion["trace_sha256"]
        or body.get("certificate_sha256") != completion["certificate_sha256"]
        or body.get("classifier_sha256") != completion["classifier_sha256"]
        or body.get("split_diagnostic_sha256")
        != completion["split_diagnostic_sha256"]
        or body.get("resource_sha256") != completion["resource_sha256"]
        or body.get("optimizer_steps") != completion["observed_optimizer_steps"]
        or body.get("parameter_sha256") != completion["final_parameter_sha256"]
    ):
        raise RuntimeError("exact-population SUCCESS completion binding is inconsistent")
    _lower_sha256(body.get("result_file_sha256"), name="result_file_sha256")
    if (
        type(body.get("result_file")) is not str
        or not body["result_file"]
        or Path(body["result_file"]).name != body["result_file"]
    ):
        raise RuntimeError("exact-population SUCCESS result filename is invalid")
    for name in (
        "preparation_cpu_seconds",
        "preparation_wall_seconds",
        "optimizer_wall_seconds",
        "total_cpu_seconds",
        "total_wall_seconds",
    ):
        value = body.get(name)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or float(value) <= 0.0
        ):
            raise RuntimeError("exact-population SUCCESS resource timing is invalid")
    if (
        float(body["preparation_cpu_seconds"]) > float(body["total_cpu_seconds"]) + 1.0e-9
        or float(body["preparation_wall_seconds"])
        + float(body["optimizer_wall_seconds"])
        > float(body["total_wall_seconds"]) + 1.0e-9
        or isinstance(body.get("peak_rss_bytes"), bool)
        or not isinstance(body.get("peak_rss_bytes"), int)
        or body["peak_rss_bytes"] <= 0
    ):
        raise RuntimeError("exact-population SUCCESS total resources are inconsistent")
    running = dict(body)
    running["state"] = "RUNNING"
    for name in _SUCCESS_FIELDS:
        running.pop(name)
    _validated_running_record(running)
    _completion_matches_running(completion, running)
    session = _validated_worker_session_receipt(running["worker_session"])
    if (
        completion["seed"] != running["request"]["seed"]
        or completion["method"] != running["request"]["method"]
        or completion["production_eligible"]
        != session["production_eligible"]
        or completion["initial_parameter_sha256"]
        != running["preflight"]["initial_parameter_sha256"]
    ):
        raise RuntimeError("exact-population SUCCESS completion custody is inconsistent")
    completed_ns = body["completed_unix_ns"]
    if (
        isinstance(completed_ns, bool)
        or not isinstance(completed_ns, int)
        or completed_ns < running["update_started_unix_ns"]
        or completion["completed_unix_ns"] < running["update_started_unix_ns"]
        or completion["completed_unix_ns"] > completed_ns
    ):
        raise RuntimeError("exact-population SUCCESS timestamps are invalid")
    return record


def _validated_parent_confirmed_success_record(record: object) -> dict:
    success = _validated_success_record(record)
    if "parent_exit_observation_sha256" not in success:
        raise RuntimeError(
            "exact SUCCESS lacks a parent-confirmed exit observation"
        )
    if (
        success.get("parent_exit_child_returncode") != 0
        or success.get("parent_exit_child_signal") is not None
    ):
        raise RuntimeError(
            "exact SUCCESS lacks a parent-confirmed zero exit"
        )
    return success


def _matching_main_runs_for_launch(
    ledger: dict, launch_id_sha256: object
) -> Tuple[Tuple[str, dict], ...]:
    launch_id = _lower_sha256(
        launch_id_sha256, name="launch_id_sha256"
    )
    matches = []
    for run_key, record in ledger["runs"].items():
        session = record.get("worker_session") if type(record) is dict else None
        if (
            type(session) is dict
            and session.get("launch_id_sha256") == launch_id
        ):
            matches.append((run_key, record))
    return tuple(matches)


def _validated_main_run_for_consumed_launch(
    record: object, consumed: object, directory: Path
) -> dict:
    run = _validated_stage_record(record)
    authorization = _validated_consumed_launch_authorization(consumed)
    session = _validated_worker_session_receipt(run["worker_session"])
    if (
        session["production_eligible"] is not True
        or session["launch_mode"] != "parent-pipe-handshake"
        or session["request"] != authorization["request"]
        or run["request"] != authorization["request"]
        or session["ledger_directory"] != str(directory.resolve())
        or session["ledger_directory"] != authorization["ledger_directory"]
        or session["launch_id_sha256"]
        != authorization["launch_id_sha256"]
        or session["launch_authorization_sha256"]
        != authorization["launch_authorization_sha256"]
        or session["child_process_identity"]
        != authorization["child_process_identity"]
        or session["child_process_identity_sha256"]
        != authorization["child_process_identity_sha256"]
        or session["worker_process_id"] != authorization["child_pid"]
        or session["parent_process_id"] != authorization["parent_pid"]
        or run["worker_pid"] != authorization["child_pid"]
        or session["issued_unix_ns"] < authorization["consumed_unix_ns"]
        or run["reserved_unix_ns"] < session["issued_unix_ns"]
    ):
        raise RuntimeError(
            "exact main-run custody differs from its consumed launch"
        )
    return run


def _terminalize_parent_reaper_main_run(
    directory: Path,
    consumed: object,
    *,
    observed_child_pid: object,
    child_returncode: object,
    error: BaseException,
) -> dict:
    """Terminalize exactly one orphaned nonterminal run after child exit."""

    authorization = dict(
        _validated_consumed_launch_authorization(consumed)
    )
    observed_pid = _validated_child_process_id(
        observed_child_pid, name="observed_child_pid"
    )
    child_signal = _child_signal_from_returncode(child_returncode)
    if not isinstance(error, BaseException):
        raise TypeError("exact parent-reaper error must be an exception")
    parent_identity = _current_process_identity_record()
    if (
        parent_identity != authorization["parent_process_identity"]
        or observed_pid != authorization["child_pid"]
    ):
        raise RuntimeError(
            "exact parent reaper does not own the consumed launch"
        )
    with _locked_ledger(directory) as (path, ledger):
        matches = _matching_main_runs_for_launch(
            ledger, authorization["launch_id_sha256"]
        )
        if len(matches) != 1:
            raise RuntimeError(
                "exact parent reaper requires exactly one matching main run"
            )
        run_key, current = matches[0]
        current = _validated_main_run_for_consumed_launch(
            current, authorization, directory
        )
        if current["state"] in ("SUCCESS", "FAILURE", "HOLD"):
            if (
                current.get("terminal_owner") == "PARENT_REAPER"
                and (
                    current.get("observed_child_pid") != observed_pid
                    or current.get("child_returncode") != child_returncode
                    or current.get("child_signal") != child_signal
                )
            ):
                raise RuntimeError(
                    "exact parent-reaper run exit observation changed"
                )
            return current
        if current["state"] not in ("RESERVED", "PREPARED", "RUNNING"):
            raise RuntimeError("exact parent reaper found an invalid run stage")
        failed_unix_ns = time.time_ns()
        failure = dict(current)
        failure.update(
            {
                "state": "FAILURE",
                "error_type": type(error).__name__,
                "error_message": str(error),
                "failed_stage": current["state"],
                "failure_total_wall_seconds": max(
                    0.0,
                    (failed_unix_ns - current["reserved_unix_ns"])
                    / 1_000_000_000.0,
                ),
                "failure_total_cpu_seconds": 0.0,
                "failure_process_peak_rss_bytes": max(_peak_rss_bytes(), 1),
                "failed_unix_ns": failed_unix_ns,
                "terminal_owner": "PARENT_REAPER",
                "terminal_process_identity": parent_identity,
                "terminal_process_identity_sha256": parent_identity[
                    "process_identity_sha256"
                ],
                "failure_origin": "PARENT_REAPER_CHILD_EXIT",
                "observed_child_pid": observed_pid,
                "child_returncode": child_returncode,
                "child_signal": child_signal,
                "previous_receipt_sha256": _stage_receipt_sha256(current),
            }
        )
        failure["terminal_ledger_sha256"] = _sha256_json(failure)
        _validated_terminal_record(failure)
        ledger["runs"][run_key] = failure
        _atomic_write_json(path, ledger)
        return failure


def _append_parent_exit_observation_to_child_main_terminal(
    directory: Path,
    consumed: object,
    *,
    observed_child_pid: object,
    child_returncode: object,
) -> dict:
    """Hash-chain parent exit evidence onto a child-owned run terminal."""

    authorization = dict(
        _validated_consumed_launch_authorization(consumed)
    )
    observed_pid = _validated_child_process_id(
        observed_child_pid, name="observed_child_pid"
    )
    child_signal = _child_signal_from_returncode(child_returncode)
    parent_identity = _current_process_identity_record()
    if (
        parent_identity != authorization["parent_process_identity"]
        or observed_pid != authorization["child_pid"]
    ):
        raise RuntimeError(
            "exact parent exit observer does not own the consumed launch"
        )
    with _locked_ledger(directory) as (path, ledger):
        matches = _matching_main_runs_for_launch(
            ledger, authorization["launch_id_sha256"]
        )
        if len(matches) != 1:
            raise RuntimeError(
                "exact parent exit observation requires one matching main run"
            )
        run_key, current = matches[0]
        current = _validated_main_run_for_consumed_launch(
            current, authorization, directory
        )
        if "parent_exit_observation_sha256" in current:
            if (
                current.get("parent_exit_observed_child_pid") != observed_pid
                or current.get("parent_exit_child_returncode")
                != child_returncode
                or current.get("parent_exit_child_signal") != child_signal
            ):
                raise RuntimeError(
                    "exact parent main-run exit observation changed"
                )
            return current
        if (
            current.get("state") not in ("FAILURE", "HOLD")
            or current.get("terminal_owner") != "CHILD"
        ):
            raise RuntimeError(
                "exact main run is not a child-owned terminal receipt"
            )
        observation = dict(current)
        observation.update(
            {
                "parent_exit_observer": "PARENT",
                "parent_exit_process_identity": parent_identity,
                "parent_exit_process_identity_sha256": parent_identity[
                    "process_identity_sha256"
                ],
                "parent_exit_observed_child_pid": observed_pid,
                "parent_exit_child_returncode": child_returncode,
                "parent_exit_child_signal": child_signal,
                "parent_exit_observed_unix_ns": max(
                    time.time_ns(), current["failed_unix_ns"]
                ),
                "previous_terminal_ledger_sha256": current[
                    "terminal_ledger_sha256"
                ],
            }
        )
        observation["parent_exit_observation_sha256"] = _sha256_json(
            observation
        )
        _validated_terminal_record(observation)
        ledger["runs"][run_key] = observation
        _atomic_write_json(path, ledger)
        return observation


def _append_parent_exit_observation_to_success(
    directory: Path,
    consumed: object,
    *,
    observed_child_pid: object,
    child_returncode: object,
) -> dict:
    """Hash-chain the parent's process outcome onto a child SUCCESS."""

    authorization = dict(
        _validated_consumed_launch_authorization(consumed)
    )
    observed_pid = _validated_child_process_id(
        observed_child_pid, name="observed_child_pid"
    )
    child_signal = _child_signal_from_returncode(child_returncode)
    parent_identity = _current_process_identity_record()
    if (
        parent_identity != authorization["parent_process_identity"]
        or observed_pid != authorization["child_pid"]
    ):
        raise RuntimeError(
            "exact SUCCESS exit observer does not own the consumed launch"
        )
    with _locked_ledger(directory) as (path, ledger):
        matches = _matching_main_runs_for_launch(
            ledger, authorization["launch_id_sha256"]
        )
        if len(matches) != 1:
            raise RuntimeError(
                "exact SUCCESS exit observation requires one matching main run"
            )
        run_key, current = matches[0]
        current = _validated_main_run_for_consumed_launch(
            current, authorization, directory
        )
        if "parent_exit_observation_sha256" in current:
            if (
                current.get("parent_exit_observed_child_pid") != observed_pid
                or current.get("parent_exit_child_returncode")
                != child_returncode
                or current.get("parent_exit_child_signal") != child_signal
            ):
                raise RuntimeError(
                    "exact SUCCESS parent exit observation changed"
                )
            return current
        success = _validated_success_record(current)
        observation = dict(success)
        observation.update(
            {
                "parent_exit_observer": "PARENT",
                "parent_exit_process_identity": parent_identity,
                "parent_exit_process_identity_sha256": parent_identity[
                    "process_identity_sha256"
                ],
                "parent_exit_observed_child_pid": observed_pid,
                "parent_exit_child_returncode": child_returncode,
                "parent_exit_child_signal": child_signal,
                "parent_exit_observed_unix_ns": max(
                    time.time_ns(), success["completed_unix_ns"]
                ),
                "previous_success_ledger_sha256": success[
                    "success_ledger_sha256"
                ],
            }
        )
        observation["parent_exit_observation_sha256"] = _sha256_json(
            observation
        )
        _validated_success_record(observation)
        ledger["runs"][run_key] = observation
        _atomic_write_json(path, ledger)
        return observation


def _terminalize_parent_reaper_consumed_launch_authorization(
    directory: Path,
    consumed: object,
    *,
    observed_child_pid: object,
    child_returncode: object,
    error: BaseException,
) -> dict:
    """Close consumed launch custody only when no main run exists."""

    authorization = dict(
        _validated_consumed_launch_authorization(consumed)
    )
    observed_pid = _validated_child_process_id(
        observed_child_pid, name="observed_child_pid"
    )
    child_signal = _child_signal_from_returncode(child_returncode)
    if not isinstance(error, BaseException):
        raise TypeError("exact parent-reaper error must be an exception")
    parent_identity = _current_process_identity_record()
    if (
        parent_identity != authorization["parent_process_identity"]
        or observed_pid != authorization["child_pid"]
    ):
        raise RuntimeError(
            "exact parent reaper does not own the consumed launch"
        )
    with _locked_ledger(directory) as (_, main_ledger):
        if _matching_main_runs_for_launch(
            main_ledger, authorization["launch_id_sha256"]
        ):
            raise RuntimeError(
                "exact parent reaper cannot terminalize launch after run custody"
            )
        with _locked_launch_ledger(directory) as (path, launch_ledger):
            current = launch_ledger["launches"].get(
                authorization["launch_id_sha256"]
            )
            if type(current) is not dict:
                raise RuntimeError("exact consumed launch authorization is absent")
            current_issued = _issued_predecessor_from_launch_authorization(
                current
            )
            expected_issued = _issued_predecessor_from_launch_authorization(
                authorization
            )
            if (
                current_issued != expected_issued
                or current_issued["parent_process_identity"] != parent_identity
            ):
                raise RuntimeError(
                    "exact parent reaper launch authorization changed"
                )
            if current.get("state") in ("FAILURE", "HOLD"):
                terminal = _validated_terminal_launch_authorization(current)
                if terminal.get("terminal_owner") not in (
                    "CHILD",
                    "PARENT_REAPER",
                ):
                    raise RuntimeError(
                        "exact consumed launch has incompatible terminal ownership"
                    )
                if terminal.get("child_pid") != observed_pid:
                    raise RuntimeError(
                        "exact consumed terminal child PID changed"
                    )
                if terminal.get("terminal_owner") == "PARENT_REAPER" and (
                    terminal.get("observed_child_pid") != observed_pid
                    or terminal.get("child_returncode") != child_returncode
                    or terminal.get("child_signal") != child_signal
                ):
                    raise RuntimeError(
                        "exact parent-reaper launch exit observation changed"
                    )
                return terminal
            current = _validated_consumed_launch_authorization(current)
            if current != authorization or current["child_pid"] != observed_pid:
                raise RuntimeError(
                    "exact consumed launch changed before parent reaping"
                )
            terminal = dict(current)
            terminal.update(
                {
                    "state": "FAILURE",
                    "failed_stage": _PARENT_REAPER_TERMINAL_LAUNCH_STAGE,
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                    "failed_unix_ns": time.time_ns(),
                    "terminal_owner": "PARENT_REAPER",
                    "terminal_process_identity_sha256": parent_identity[
                        "process_identity_sha256"
                    ],
                    "observed_child_pid": observed_pid,
                    "child_returncode": child_returncode,
                    "child_signal": child_signal,
                }
            )
            terminal["terminal_launch_authorization_sha256"] = _sha256_json(
                terminal
            )
            _validated_terminal_launch_authorization(terminal)
            launch_ledger["launches"][authorization["launch_id_sha256"]] = (
                terminal
            )
            _atomic_write_launch_ledger(path, launch_ledger)
            return terminal


def _close_exact_child_exit_custody(
    directory: Path,
    authorization: object,
    request: FrozenExactPopulationRunRequest,
    *,
    observed_child_pid: object,
    child_returncode: object,
) -> Tuple[str, dict]:
    """Durably close process-exit custody without interpreting exit success."""

    issued = dict(_validated_issued_launch_authorization(authorization))
    observed_pid = _validated_child_process_id(
        observed_child_pid, name="observed_child_pid"
    )
    returncode = child_returncode
    _child_signal_from_returncode(returncode)
    parent_identity = _current_process_identity_record()
    if (
        type(request) is not FrozenExactPopulationRunRequest
        or issued["request"] != asdict(request)
        or issued["ledger_directory"] != str(directory.resolve())
        or issued["parent_pid"] != os.getpid()
        or issued["parent_process_identity"] != parent_identity
    ):
        raise RuntimeError(
            "exact child-exit request/path/parent custody is invalid"
        )
    with _locked_launch_ledger(directory) as (_, launch_ledger):
        current = launch_ledger["launches"].get(issued["launch_id_sha256"])
        if type(current) is not dict:
            raise RuntimeError("exact child-exit launch authorization is absent")
        if _issued_predecessor_from_launch_authorization(current) != issued:
            raise RuntimeError("exact child-exit launch authorization changed")
        current = dict(current)
    child_exit_error = ChildProcessError(
        "exact child %d exited with return code %d"
        % (observed_pid, returncode)
    )
    state = current["state"]
    if state == "ISSUED":
        terminal = _terminalize_parent_launch_authorization(
            directory,
            issued,
            request,
            state="FAILURE",
            failed_stage="CHILD_EXIT_BEFORE_CONSUMPTION",
            error=child_exit_error,
            observed_child_pid=observed_pid,
            child_returncode=returncode,
        )
        if terminal is None:
            return _close_exact_child_exit_custody(
                directory,
                issued,
                request,
                observed_child_pid=observed_pid,
                child_returncode=returncode,
            )
        custody_kind, custody = "LAUNCH", terminal
    elif state in ("FAILURE", "HOLD"):
        terminal = _validated_terminal_launch_authorization(current)
        if (
            "cleanup_observation_sha256" not in terminal
            and (
                (
                    terminal.get("terminal_owner") == "PARENT"
                    and terminal.get("observed_child_pid") is not None
                    and terminal.get("child_returncode") is None
                )
                or terminal.get("terminal_owner") == "CHILD"
            )
        ):
            terminal = _append_parent_cleanup_exit_observation(
                directory,
                issued,
                request,
                observed_child_pid=observed_pid,
                child_returncode=returncode,
            )
        effective_observed_pid = terminal.get(
            "cleanup_observed_child_pid",
            terminal.get("observed_child_pid"),
        )
        effective_returncode = terminal.get(
            "cleanup_child_returncode",
            terminal.get("child_returncode"),
        )
        if terminal.get("child_pid") not in (None, observed_pid):
            raise RuntimeError(
                "exact terminal launch child PID differs from observation"
            )
        if (
            effective_observed_pid is not None
            and effective_observed_pid != observed_pid
        ):
            raise RuntimeError(
                "exact terminal launch observed child PID changed"
            )
        if (
            effective_returncode is not None
            and effective_returncode != returncode
        ):
            raise RuntimeError(
                "exact terminal launch child return code changed"
            )
        with _locked_ledger(directory) as (_, main_ledger):
            if _matching_main_runs_for_launch(
                main_ledger, issued["launch_id_sha256"]
            ):
                raise RuntimeError(
                    "exact terminal launch unexpectedly has main-run custody"
                )
        custody_kind, custody = "LAUNCH", terminal
    elif state == "CONSUMED":
        consumed = _validated_consumed_launch_authorization(current)
        if consumed["child_pid"] != observed_pid:
            raise RuntimeError("exact observed child PID differs from consumption")
        with _locked_ledger(directory) as (_, main_ledger):
            matches = _matching_main_runs_for_launch(
                main_ledger, issued["launch_id_sha256"]
            )
            if len(matches) > 1:
                raise RuntimeError(
                    "exact consumed launch has multiple matching main runs"
                )
            if matches:
                _validated_main_run_for_consumed_launch(
                    matches[0][1], consumed, directory
                )
        if not matches:
            custody = _terminalize_parent_reaper_consumed_launch_authorization(
                directory,
                consumed,
                observed_child_pid=observed_pid,
                child_returncode=returncode,
                error=child_exit_error,
            )
            custody_kind = "LAUNCH"
        else:
            custody = _terminalize_parent_reaper_main_run(
                directory,
                consumed,
                observed_child_pid=observed_pid,
                child_returncode=returncode,
                error=child_exit_error,
            )
            if custody.get("state") == "SUCCESS":
                custody = _append_parent_exit_observation_to_success(
                    directory,
                    consumed,
                    observed_child_pid=observed_pid,
                    child_returncode=returncode,
                )
            elif (
                custody.get("terminal_owner") == "CHILD"
                and "parent_exit_observation_sha256" not in custody
            ):
                custody = (
                    _append_parent_exit_observation_to_child_main_terminal(
                        directory,
                        consumed,
                        observed_child_pid=observed_pid,
                        child_returncode=returncode,
                    )
                )
            custody_kind = "RUN"
    else:
        raise RuntimeError("exact child-exit launch state is invalid")
    return custody_kind, custody


def _require_durable_exact_exit_custody(
    directory: Path, custody_kind: object, custody: object
) -> dict:
    """Reopen and strictly validate the exact receipt returned by closure."""

    if custody_kind == "LAUNCH":
        terminal = _validated_terminal_launch_authorization(custody)
        launch_id = _lower_sha256(
            terminal.get("launch_id_sha256"), name="launch_id_sha256"
        )
        with _locked_launch_ledger(directory) as (_, ledger):
            durable = ledger["launches"].get(launch_id)
        if durable != terminal:
            raise RuntimeError(
                "exact launch terminal is not the durable exit receipt"
            )
        owner = terminal.get("terminal_owner")
        has_parent_exit = (
            "cleanup_observation_sha256" in terminal
            or (
                owner in ("PARENT", "PARENT_REAPER")
                and terminal.get("child_returncode") is not None
            )
        )
        if owner == "CHILD" and "cleanup_observation_sha256" not in terminal:
            has_parent_exit = False
        if not has_parent_exit:
            raise RuntimeError(
                "exact terminal launch lacks parent-confirmed exit evidence"
            )
        return terminal
    if custody_kind == "RUN":
        record = _validated_stage_record(custody)
        run_key = _lower_sha256(
            record.get("run_key_sha256"), name="run_key_sha256"
        )
        with _locked_ledger(directory) as (_, ledger):
            durable = ledger["runs"].get(run_key)
        if durable != record:
            raise RuntimeError(
                "exact main-run terminal is not the durable exit receipt"
            )
        if record.get("state") == "SUCCESS":
            success = _validated_success_record(record)
            if "parent_exit_observation_sha256" not in success:
                raise RuntimeError(
                    "exact SUCCESS lacks durable parent exit evidence"
                )
            return success
        terminal = _validated_terminal_record(record)
        if (
            terminal.get("terminal_owner") == "CHILD"
            and "parent_exit_observation_sha256" not in terminal
        ):
            raise RuntimeError(
                "exact child-owned main terminal lacks parent exit evidence"
            )
        return terminal
    raise ValueError("exact exit custody kind is invalid")


def _reconcile_exact_child_exit(
    directory: Path,
    authorization: object,
    request: FrozenExactPopulationRunRequest,
    *,
    observed_child_pid: object,
    child_returncode: object,
) -> Tuple[str, dict]:
    """Close exit custody and accept zero only for one validated SUCCESS."""

    custody_kind, custody = _close_exact_child_exit_custody(
        directory,
        authorization,
        request,
        observed_child_pid=observed_child_pid,
        child_returncode=child_returncode,
    )
    _require_durable_exact_exit_custody(directory, custody_kind, custody)
    returncode = child_returncode
    _child_signal_from_returncode(returncode)
    if returncode == 0:
        if custody_kind != "RUN" or custody.get("state") != "SUCCESS":
            raise RuntimeError(
                "exact zero-exit child lacks exactly one validated SUCCESS run"
            )
        _validated_parent_confirmed_success_record(custody)
    elif custody_kind == "RUN" and custody.get("state") == "SUCCESS":
        _validated_success_record(custody)
        raise RuntimeError(
            "exact nonzero-exit child conflicts with durable SUCCESS"
        )
    return custody_kind, custody


def _validated_optimizer_completion_receipt(value: object) -> dict:
    expected = {
        "schema",
        "production_eligible",
        "seed",
        "method",
        "launch_id_sha256",
        "launch_authorization_sha256",
        "child_process_identity_sha256",
        "worker_session_sha256",
        "run_key_sha256",
        "campaign_sha256",
        "execution_runtime_sha256",
        "preflight_sha256",
        "prepared_ledger_sha256",
        "running_ledger_sha256",
        "expected_optimizer_steps",
        "observed_optimizer_steps",
        "initial_parameter_sha256",
        "final_parameter_sha256",
        "rolling_optimizer_transcript_sha256",
        "trace_sha256",
        "certificate_sha256",
        "classifier_sha256",
        "split_diagnostic_sha256",
        "resource_sha256",
        "result_sha256",
        "worker_process_id",
        "completed_unix_ns",
        "optimizer_completion_sha256",
    }
    if type(value) is not dict or set(value) != expected:
        raise RuntimeError("exact optimizer-completion schema is invalid")
    body = dict(value)
    claimed = _lower_sha256(
        body.pop("optimizer_completion_sha256"),
        name="optimizer_completion_sha256",
    )
    if _sha256_json(body) != claimed:
        raise RuntimeError("exact optimizer-completion digest is inconsistent")
    if (
        value.get("schema") != _OPTIMIZER_COMPLETION_SCHEMA
        or type(value.get("production_eligible")) is not bool
        or type(value.get("seed")) is not int
        or type(value.get("method")) is not str
        or type(value.get("worker_process_id")) is not int
        or value["worker_process_id"] <= 0
        or type(value.get("completed_unix_ns")) is not int
        or value["completed_unix_ns"] <= 0
        or type(value.get("expected_optimizer_steps")) is not int
        or type(value.get("observed_optimizer_steps")) is not int
        or value["expected_optimizer_steps"] != value["observed_optimizer_steps"]
        or value["expected_optimizer_steps"]
        != _METHOD_UPDATES.get(value["method"])
    ):
        raise RuntimeError("exact optimizer-completion contents are invalid")
    FrozenExactPopulationRunRequest(value["seed"], value["method"])
    for name in (
        "launch_id_sha256",
        "launch_authorization_sha256",
        "child_process_identity_sha256",
        "worker_session_sha256",
        "run_key_sha256",
        "campaign_sha256",
        "execution_runtime_sha256",
        "preflight_sha256",
        "prepared_ledger_sha256",
        "running_ledger_sha256",
        "initial_parameter_sha256",
        "final_parameter_sha256",
        "rolling_optimizer_transcript_sha256",
        "trace_sha256",
        "certificate_sha256",
        "classifier_sha256",
        "resource_sha256",
        "result_sha256",
    ):
        _lower_sha256(value.get(name), name=name)
    splits = value.get("split_diagnostic_sha256")
    if type(splits) is not list or len(splits) != 3:
        raise RuntimeError("exact optimizer-completion split receipts are invalid")
    for digest in splits:
        _lower_sha256(digest, name="split_diagnostic_sha256")
    return value


def _completion_matches_running(completion: dict, running: dict) -> None:
    session = _validated_worker_session_receipt(running["worker_session"])
    comparisons = {
        "launch_id_sha256": session["launch_id_sha256"],
        "launch_authorization_sha256": session[
            "launch_authorization_sha256"
        ],
        "child_process_identity_sha256": session[
            "child_process_identity_sha256"
        ],
        "worker_session_sha256": running["worker_session_sha256"],
        "run_key_sha256": running["run_key_sha256"],
        "campaign_sha256": running["campaign_sha256"],
        "execution_runtime_sha256": running["runtime"]["sha256"],
        "preflight_sha256": running["preflight"]["preflight_sha256"],
        "prepared_ledger_sha256": running["prepared_ledger_sha256"],
        "running_ledger_sha256": running["running_ledger_sha256"],
        "worker_process_id": running["worker_pid"],
    }
    if any(completion.get(name) != expected for name, expected in comparisons.items()):
        raise RuntimeError("exact optimizer completion differs from RUNNING custody")


def _finalize_completed_exact_execution(
    directory: Path,
    run_key: str,
    completed_execution: object,
    *,
    result_file: str,
    result_file_sha256: object,
    worker_session_capability: object,
) -> dict:
    from heterodiff.experiments.finite_association_exact_population_torch import (
        CompletedExactPopulationExecution,
        _OPTIMIZER_COMPLETION_FINALIZER_KEY,
        load_exact_population_method_result,
    )

    if type(completed_execution) is not CompletedExactPopulationExecution:
        raise TypeError("exact SUCCESS requires an executor completion object")
    if type(worker_session_capability) is not FrozenExactWorkerLaunchCapability:
        raise TypeError("exact SUCCESS requires its typed worker session")
    if type(result_file) is not str or result_file != "%s.pt" % run_key:
        raise RuntimeError("exact SUCCESS result filename is invalid")
    file_sha256 = _lower_sha256(
        result_file_sha256, name="result_file_sha256"
    )
    result_path = (directory.resolve() / result_file).resolve()
    if result_path.parent != directory.resolve():
        raise RuntimeError("exact SUCCESS result path escapes the campaign")
    reopened = load_exact_population_method_result(
        result_path, expected_sha256=file_sha256
    )
    result = completed_execution.result
    if reopened.digest != result.digest:
        raise RuntimeError("serialized exact result differs before SUCCESS")
    completion_object = completed_execution.optimizer_completion
    completion = _validated_optimizer_completion_receipt(
        completion_object.receipt
    )
    if completion["result_sha256"] != reopened.digest:
        raise RuntimeError("optimizer completion differs from reopened result")
    _require_durable_launch_for_capability(worker_session_capability)
    with _locked_ledger(directory) as (path, ledger):
        running = _validated_running_record(ledger["runs"].get(run_key))
        _completion_matches_running(completion, running)
        if (
            completion["production_eligible"] is not True
            or running["worker_session_sha256"]
            != worker_session_capability.worker_session_sha256
            or running["worker_session"]
            != worker_session_capability.session_receipt
        ):
            raise RuntimeError("exact SUCCESS production session is inconsistent")
        consumed_completion = completion_object._consume_for_finalization(
            reopened, _finalizer_key=_OPTIMIZER_COMPLETION_FINALIZER_KEY
        )
        worker_session_capability.authorize_success(
            run_key, running["worker_session_sha256"]
        )
        additions = {
            "method_result_sha256": reopened.digest,
            "classifier_sha256": reopened.classifier_sha256,
            "certificate_sha256": reopened.continuous_certificate.certificate_sha256,
            "parameter_sha256": reopened.final_snapshot.parameter_sha256,
            "trace_sha256": reopened.optimization_trace.trace_sha256,
            "split_diagnostic_sha256": [
                value.digest for value in reopened.split_diagnostics
            ],
            "resource_sha256": reopened.resources.digest,
            "optimizer_completion": consumed_completion,
            "optimizer_completion_sha256": consumed_completion[
                "optimizer_completion_sha256"
            ],
            "optimizer_wall_seconds": reopened.resources.optimizer_wall_seconds,
            "total_cpu_seconds": reopened.resources.elapsed_cpu_seconds,
            "total_wall_seconds": reopened.resources.elapsed_wall_seconds,
            "peak_rss_bytes": reopened.resources.peak_rss_bytes,
            "optimizer_steps": reopened.optimization_trace.optimizer_updates,
            "result_file": result_file,
            "result_file_sha256": file_sha256,
            "completed_unix_ns": time.time_ns(),
        }
        success = dict(running)
        success["state"] = "SUCCESS"
        success.update(additions)
        success["success_ledger_sha256"] = _sha256_json(success)
        _validated_success_record(success)
        ledger["runs"][run_key] = success
        _atomic_write_json(path, ledger)
    return success


def _complete_test_only_emulated_success(
    directory: Path,
    run_key: str,
    additions: dict,
    *,
    worker_session_capability: object,
) -> dict:
    """Build synthetic SUCCESS only for no-update tests; never admissible."""

    if (
        type(worker_session_capability) is not FrozenExactWorkerLaunchCapability
        or worker_session_capability.production_eligible is not False
    ):
        raise RuntimeError("test-only SUCCESS requires an emulated worker session")
    if type(additions) is not dict or set(additions) != _TEST_ONLY_SUCCESS_ADDITION_FIELDS:
        raise ValueError("test-only SUCCESS additions do not match the schema")
    with _locked_ledger(directory) as (path, ledger):
        running = _validated_running_record(ledger["runs"].get(run_key))
        session = _validated_worker_session_receipt(running["worker_session"])
        completion = {
            "schema": _OPTIMIZER_COMPLETION_SCHEMA,
            "production_eligible": False,
            "seed": running["request"]["seed"],
            "method": running["request"]["method"],
            "launch_id_sha256": session["launch_id_sha256"],
            "launch_authorization_sha256": session[
                "launch_authorization_sha256"
            ],
            "child_process_identity_sha256": session[
                "child_process_identity_sha256"
            ],
            "worker_session_sha256": running["worker_session_sha256"],
            "run_key_sha256": run_key,
            "campaign_sha256": running["campaign_sha256"],
            "execution_runtime_sha256": running["runtime"]["sha256"],
            "preflight_sha256": running["preflight"]["preflight_sha256"],
            "prepared_ledger_sha256": running["prepared_ledger_sha256"],
            "running_ledger_sha256": running["running_ledger_sha256"],
            "expected_optimizer_steps": additions["optimizer_steps"],
            "observed_optimizer_steps": additions["optimizer_steps"],
            "initial_parameter_sha256": running["preflight"][
                "initial_parameter_sha256"
            ],
            "final_parameter_sha256": additions["parameter_sha256"],
            "rolling_optimizer_transcript_sha256": hashlib.sha256(
                b"test-only-emulated-no-update-transcript"
            ).hexdigest(),
            "trace_sha256": additions["trace_sha256"],
            "certificate_sha256": additions["certificate_sha256"],
            "classifier_sha256": additions["classifier_sha256"],
            "split_diagnostic_sha256": additions[
                "split_diagnostic_sha256"
            ],
            "resource_sha256": additions["resource_sha256"],
            "result_sha256": additions["method_result_sha256"],
            "worker_process_id": running["worker_pid"],
            "completed_unix_ns": additions["completed_unix_ns"],
        }
        completion["optimizer_completion_sha256"] = _sha256_json(completion)
        _validated_optimizer_completion_receipt(completion)
        worker_session_capability.authorize_success(
            run_key, running["worker_session_sha256"]
        )
        success = dict(running)
        success["state"] = "SUCCESS"
        success.update(additions)
        success["optimizer_completion"] = completion
        success["optimizer_completion_sha256"] = completion[
            "optimizer_completion_sha256"
        ]
        success["success_ledger_sha256"] = _sha256_json(success)
        _validated_success_record(success)
        ledger["runs"][run_key] = success
        _atomic_write_json(path, ledger)
    return success


def _validate_permit_campaign(ledger: dict, permit: object, prepared: object) -> None:
    directory = Path(permit.ledger_directory).resolve()
    if directory != frozen_exact_population_campaign_directory().resolve():
        raise RuntimeError("exact execution permit is outside the canonical campaign")
    expected_campaign = _campaign_record(prepared, permit.execution_runtime_sha256)
    if ledger.get("campaign") != expected_campaign:
        raise RuntimeError("exact execution permit campaign differs from preparation")
    if expected_campaign["campaign_sha256"] != permit.campaign_sha256:
        raise RuntimeError("exact execution permit campaign digest changed")
    capability = permit._worker_session_capability
    if type(capability) is not FrozenExactWorkerLaunchCapability:
        raise RuntimeError("exact execution permit has no typed worker session")
    capability.assert_run_key(permit.run_key_sha256)
    capability.assert_permit_active(permit.worker_session_sha256)
    if (
        capability.launch_id_sha256 != permit.launch_id_sha256
        or capability.launch_authorization_sha256
        != permit.launch_authorization_sha256
        or capability.child_process_identity_sha256
        != permit.child_process_identity_sha256
    ):
        raise RuntimeError("exact execution permit launch identity changed")
    request = FrozenExactPopulationRunRequest(permit.seed, permit.method)
    expected_key = frozen_exact_population_run_key(
        request,
        fixture_sha256=prepared.train_population.fixture_sha256,
        source_sha256=prepared.source_sha256,
        exact_configuration_sha256=prepared.exact_configuration_sha256,
        preflight_sha256=prepared.preflight_sha256,
        execution_runtime_sha256=permit.execution_runtime_sha256,
    )
    if expected_key != permit.run_key_sha256:
        raise RuntimeError("exact execution permit run key is not derivable")


def _authorize_exact_execution_permit_session(
    launch_capability: object,
    *,
    ledger_directory: object,
    run_key_sha256: object,
    prepared_ledger_sha256: object,
    execution_runtime_sha256: object,
    campaign_sha256: object,
) -> Tuple[str, bool, str, str, str]:
    """Authorize one permit from one entered, run-key-bound worker session."""

    if type(launch_capability) is not FrozenExactWorkerLaunchCapability:
        raise TypeError("exact permit issuance requires a typed worker session")
    directory = Path(ledger_directory).resolve()
    launch_capability._assert_process_and_coordinate(
        launch_capability.request, directory
    )
    _require_durable_launch_for_capability(launch_capability)
    checked_run_key = _lower_sha256(run_key_sha256, name="run_key_sha256")
    checked_prepared = _lower_sha256(
        prepared_ledger_sha256, name="prepared_ledger_sha256"
    )
    checked_runtime = _lower_sha256(
        execution_runtime_sha256, name="execution_runtime_sha256"
    )
    checked_campaign = _lower_sha256(campaign_sha256, name="campaign_sha256")
    launch_capability.assert_run_key(checked_run_key)
    with _locked_ledger(directory) as (_, ledger):
        record = _validated_prepared_chain(ledger["runs"].get(checked_run_key))
        runtime = _validated_runtime(record.get("runtime"))
        if (
            record.get("prepared_ledger_sha256") != checked_prepared
            or runtime.get("sha256") != checked_runtime
            or record.get("campaign_sha256") != checked_campaign
            or record.get("worker_session_sha256")
            != launch_capability.worker_session_sha256
            or record.get("worker_session")
            != launch_capability.session_receipt
            or ledger.get("campaign", {}).get("campaign_sha256")
            != checked_campaign
        ):
            raise RuntimeError("exact permit issuance custody is inconsistent")
    launch_capability.authorize_permit()
    return (
        launch_capability.worker_session_sha256,
        launch_capability.production_eligible,
        launch_capability.launch_id_sha256,
        launch_capability.launch_authorization_sha256,
        launch_capability.child_process_identity_sha256,
    )


def _verify_prepared_exact_execution_permit(
    permit: object, prepared: object, seed: object, method: object
) -> None:
    request = FrozenExactPopulationRunRequest(int(seed), str(method))
    if request.seed != permit.seed or request.method != permit.method:
        raise RuntimeError("exact execution permit coordinate changed")
    directory = Path(permit.ledger_directory).resolve()
    with _locked_ledger(directory) as (_, ledger):
        _validate_permit_campaign(ledger, permit, prepared)
        record = _validated_prepared_record(
            ledger["runs"].get(permit.run_key_sha256),
            permit,
            _preflight_receipt(prepared, request),
        )
        if record.get("campaign_sha256") != ledger["campaign"]["campaign_sha256"]:
            raise RuntimeError("exact PREPARED receipt has the wrong campaign")
        if _validated_runtime(record.get("runtime"))["sha256"] != (
            permit.execution_runtime_sha256
        ):
            raise RuntimeError("exact PREPARED runtime differs from its permit")


def _consume_prepared_exact_execution_permit(
    permit: object, prepared: object, seed: object, method: object
) -> str:
    request = FrozenExactPopulationRunRequest(int(seed), str(method))
    directory = Path(permit.ledger_directory).resolve()
    with _locked_ledger(directory) as (path, ledger):
        _validate_permit_campaign(ledger, permit, prepared)
        current = _validated_prepared_record(
            ledger["runs"].get(permit.run_key_sha256),
            permit,
            _preflight_receipt(prepared, request),
        )
        if current.get("campaign_sha256") != ledger["campaign"]["campaign_sha256"]:
            raise RuntimeError("exact PREPARED receipt has the wrong campaign")
        running = dict(current)
        running["state"] = "RUNNING"
        running["update_started_unix_ns"] = time.time_ns()
        running["running_ledger_sha256"] = _sha256_json(running)
        _validated_running_record(running)
        ledger["runs"][permit.run_key_sha256] = running
        _atomic_write_json(path, ledger)
    permit._worker_session_capability.consume_permit(
        permit.worker_session_sha256
    )
    return running["running_ledger_sha256"]


def _atomic_save_method_result(result: object, destination: Path) -> str:
    import torch
    from heterodiff.experiments.finite_association_exact_population_torch import (
        exact_population_method_result_payload,
    )

    payload = exact_population_method_result_payload(result)
    temporary_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w+b", dir=str(destination.parent), prefix=".exact-result-", delete=False
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


def _worker(
    request: FrozenExactPopulationRunRequest,
    directory: Path,
    *,
    launch_capability: Optional[object] = None,
) -> dict:
    if type(launch_capability) is not FrozenExactWorkerLaunchCapability:
        raise RuntimeError(
            "exact worker entry requires a typed parent-handshake capability"
        )
    if launch_capability.production_eligible is not True:
        raise RuntimeError("exact worker rejects a test-only emulated session")
    launch_capability.enter_worker(request, directory)
    if directory.resolve() != frozen_exact_population_campaign_directory().resolve():
        raise RuntimeError("exact worker ledger path is not canonical")
    thread_environment = _require_preimport_worker_environment()
    from threadpoolctl import threadpool_limits

    with threadpool_limits(limits=1):
        runtime = _runtime_record_after_import(thread_environment)
        from heterodiff.experiments.finite_association_exact_population_torch import (
            _issue_frozen_exact_population_execution_permit,
            execute_frozen_association_exact_population_diagnostic,
            prepare_frozen_association_exact_population_diagnostic,
        )
        from heterodiff.models.finite_association_residual_torch import (
            ContinuousCorrectionCertificateError,
        )

        total_wall_start = time.perf_counter()
        total_cpu_start = time.process_time()
        prepared = prepare_frozen_association_exact_population_diagnostic()
        campaign = _ensure_campaign(directory, prepared, runtime["sha256"])
        run_key = frozen_exact_population_run_key(
            request,
            fixture_sha256=prepared.train_population.fixture_sha256,
            source_sha256=prepared.source_sha256,
            exact_configuration_sha256=prepared.exact_configuration_sha256,
            preflight_sha256=prepared.preflight_sha256,
            execution_runtime_sha256=runtime["sha256"],
        )
        try:
            reserved_record = _reserve_run(
                directory,
                run_key,
                request,
                runtime,
                campaign["campaign_sha256"],
                launch_capability,
            )
            preflight = _preflight_receipt(prepared, request)
            preparation_wall_seconds = time.perf_counter() - total_wall_start
            preparation_cpu_seconds = time.process_time() - total_cpu_start
            prepared_base = dict(reserved_record)
            prepared_base.update({
                "state": "PREPARED",
                "preflight": preflight,
                "preparation_wall_seconds": preparation_wall_seconds,
                "preparation_cpu_seconds": preparation_cpu_seconds,
                "prepared_unix_ns": time.time_ns(),
            })
            prepared_sha = _sha256_json(prepared_base)
            prepared_record = dict(prepared_base)
            prepared_record["prepared_ledger_sha256"] = prepared_sha
            _transition(
                directory,
                run_key,
                "RESERVED",
                prepared_record,
                expected_prior_sha256=reserved_record[
                    "reserved_ledger_sha256"
                ],
            )
            permit = _issue_frozen_exact_population_execution_permit(
                seed=request.seed,
                method=request.method,
                run_key_sha256=run_key,
                preflight_sha256=prepared.preflight_sha256,
                prepared_ledger_sha256=prepared_sha,
                execution_runtime_sha256=runtime["sha256"],
                campaign_sha256=campaign["campaign_sha256"],
                ledger_directory=directory,
                total_wall_start=total_wall_start,
                total_cpu_start=total_cpu_start,
                preparation_wall_seconds=preparation_wall_seconds,
                preparation_cpu_seconds=preparation_cpu_seconds,
                worker_session_capability=launch_capability,
            )
            completed_execution = execute_frozen_association_exact_population_diagnostic(
                prepared, permit=permit
            )
            result = completed_execution.result
            filename = "%s.pt" % run_key
            file_sha = _atomic_save_method_result(result, directory / filename)
            return _finalize_completed_exact_execution(
                directory,
                run_key,
                completed_execution,
                result_file=filename,
                result_file_sha256=file_sha,
                worker_session_capability=launch_capability,
            )
        except BaseException as error:
            state = "HOLD" if isinstance(error, ContinuousCorrectionCertificateError) else "FAILURE"
            try:
                with _locked_ledger(directory) as (path, ledger):
                    existing = ledger["runs"].get(run_key)
                    if (
                        isinstance(existing, dict)
                        and existing.get("state")
                        in ("RESERVED", "PREPARED", "RUNNING")
                        and existing.get("worker_session_sha256")
                        == launch_capability.worker_session_sha256
                    ):
                        _validated_stage_record(existing)
                        failure = dict(existing)
                        failure.update(
                            {
                                "state": state,
                                "error_type": type(error).__name__,
                                "error_message": str(error),
                                "failed_stage": existing["state"],
                                "failure_total_wall_seconds": time.perf_counter() - total_wall_start,
                                "failure_total_cpu_seconds": time.process_time() - total_cpu_start,
                                "failure_process_peak_rss_bytes": _peak_rss_bytes(),
                                "failed_unix_ns": time.time_ns(),
                                "terminal_owner": "CHILD",
                                "terminal_process_identity": existing[
                                    "worker_session"
                                ]["child_process_identity"],
                                "terminal_process_identity_sha256": existing[
                                    "worker_session"
                                ]["child_process_identity_sha256"],
                                "failure_origin": "CHILD_EXCEPTION",
                                "observed_child_pid": existing["worker_pid"],
                                "child_returncode": None,
                                "child_signal": None,
                                "previous_receipt_sha256": (
                                    _stage_receipt_sha256(existing)
                                ),
                            }
                        )
                        failure["terminal_ledger_sha256"] = _sha256_json(failure)
                        _validated_terminal_record(failure)
                        ledger["runs"][run_key] = failure
                        _atomic_write_json(path, ledger)
            except BaseException as custody_error:
                _attach_exact_secondary_failure(
                    error,
                    "exact worker main-run terminalization failed",
                    custody_error,
                )
            raise


def _validated_runtime(record: object) -> dict:
    if not isinstance(record, dict):
        raise RuntimeError("exact SUCCESS receipt has no runtime custody")
    expected_fields = {
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
        "processor_source",
        "thread_environment",
        "native_pools",
        "numpy_configuration",
        "torch_environment",
        "sha256",
    }
    if set(record) != expected_fields:
        raise RuntimeError("exact SUCCESS runtime schema is incomplete or extended")
    body = dict(record)
    claimed = _lower_sha256(body.pop("sha256", None), name="execution_runtime_sha256")
    if _sha256_json(body) != claimed:
        raise RuntimeError("exact SUCCESS runtime digest is inconsistent")
    expected_preimport = {
        **{name: "1" for name in _THREAD_ENVIRONMENT},
        "PYTHONHASHSEED": "0",
        "CUDA_VISIBLE_DEVICES": "",
    }
    exact_versions = {
        "python": "3.11.5",
        "numpy": "2.4.6",
        "scipy": "1.17.1",
        "torch": "2.12.1",
        "threadpoolctl": "3.6.0",
    }
    identity_fields = (
        "python_implementation",
        "platform",
        "system",
        "release",
        "machine",
    )
    pools = record.get("native_pools")
    pool_keys = {"user_api", "internal_api", "prefix", "version", "num_threads"}
    torch_environment = record.get("torch_environment")
    torch_keys = {
        "python_version",
        "numpy_version",
        "scipy_version",
        "torch_version",
        "torch_cpu_only",
        "torch_threads",
        "torch_interop_threads",
        "deterministic_algorithms",
    }
    if (
        record.get("schema") != _RUNTIME_SCHEMA
        or any(record.get(name) != value for name, value in exact_versions.items())
        or any(type(record.get(name)) is not str or not record[name] for name in identity_fields)
        or type(record.get("processor")) is not str
        or not record["processor"]
        or type(record.get("processor_source")) is not str
        or not record["processor_source"]
        or record.get("thread_environment") != expected_preimport
        or type(record.get("numpy_configuration")) is not dict
        or not record["numpy_configuration"]
        or type(torch_environment) is not dict
        or set(torch_environment) != torch_keys
        or torch_environment.get("python_version") != exact_versions["python"]
        or torch_environment.get("numpy_version") != exact_versions["numpy"]
        or torch_environment.get("scipy_version") != exact_versions["scipy"]
        or torch_environment.get("torch_version") != exact_versions["torch"]
        or torch_environment.get("torch_cpu_only") is not True
        or type(torch_environment.get("torch_threads")) is not int
        or torch_environment.get("torch_threads") != 1
        or type(torch_environment.get("torch_interop_threads")) is not int
        or torch_environment.get("torch_interop_threads") != 1
        or torch_environment.get("deterministic_algorithms") is not True
        or type(pools) is not list
        or not pools
        or any(
            type(pool) is not dict
            or set(pool) != pool_keys
            or any(
                type(pool.get(name)) is not str or not pool[name]
                for name in ("user_api", "internal_api", "prefix")
            )
            or (
                pool.get("version") is not None
                and (
                    type(pool.get("version")) is not str
                    or not pool["version"]
                )
            )
            or type(pool.get("num_threads")) is not int
            or pool.get("num_threads") != 1
            for pool in pools
        )
    ):
        raise RuntimeError("exact SUCCESS runtime is not frozen single-thread custody")
    _canonical_json(record["numpy_configuration"])
    return record


def _require_fresh_child_process_identity(
    worker_session: object, observed_identities: set
) -> str:
    """Register process-start identity; a recycled numeric PID is permitted."""

    session = _validated_worker_session_receipt(worker_session)
    if type(observed_identities) is not set:
        raise TypeError("observed child process identities must be a set")
    identity = session["child_process_identity_sha256"]
    if identity in observed_identities:
        raise RuntimeError(
            "exact aggregate contains a duplicate child process identity receipt"
        )
    observed_identities.add(identity)
    return identity


def _assemble_complete_result(
    directory: Path,
    ledger: dict,
    *,
    require_production_sessions: bool = True,
):
    """Reopen all coordinates; emulated mode is test-only pure assembly.

    Both production finalization/load paths leave ``require_production_sessions``
    at its fail-closed default.  Passing ``False`` can exercise deterministic
    assembly in no-update tests, but this helper never creates the
    ``LedgerVerifiedExactPopulationDiagnostic`` admission wrapper.
    """
    if type(require_production_sessions) is not bool:
        raise TypeError("require_production_sessions must be boolean")
    from heterodiff.experiments.finite_association_exact_population_torch import (
        AssociationExactPopulationDiagnosticResult,
        EXACT_EXPECTED_TOTAL_OPTIMIZER_STEPS,
        load_exact_population_method_result,
        prepare_frozen_association_exact_population_diagnostic,
    )
    from heterodiff.experiments.finite_association_residual_training_torch import (
        FrozenAssociationTrainingEnvironment,
    )

    prepared = prepare_frozen_association_exact_population_diagnostic()
    campaign = _campaign_record(prepared, ledger.get("campaign", {}).get("execution_runtime_sha256"))
    if ledger.get("campaign") != campaign:
        raise RuntimeError("exact aggregate campaign differs from current custody")
    results = []
    success_receipts = []
    observed_worker_sessions = set()
    observed_launch_ids = set()
    observed_launch_authorizations = set()
    observed_child_process_identities = set()
    observed_optimizer_completions = set()
    observed_run_keys = set()
    runtime_record = None
    for seed in _SEEDS:
        for method in _METHODS:
            request = FrozenExactPopulationRunRequest(seed, method)
            run_key = frozen_exact_population_run_key(
                request,
                fixture_sha256=prepared.train_population.fixture_sha256,
                source_sha256=prepared.source_sha256,
                exact_configuration_sha256=prepared.exact_configuration_sha256,
                preflight_sha256=prepared.preflight_sha256,
                execution_runtime_sha256=campaign["execution_runtime_sha256"],
            )
            record = _validated_success_record(ledger["runs"].get(run_key))
            observed_run_keys.add(run_key)
            observed_runtime = _validated_runtime(record.get("runtime"))
            worker_session = _validated_worker_session_receipt(
                record.get("worker_session")
            )
            completion = _validated_optimizer_completion_receipt(
                record.get("optimizer_completion")
            )
            _completion_matches_running(completion, record)
            worker_session_sha256 = worker_session["worker_session_sha256"]
            unique_receipts = (
                (
                    "worker-session",
                    worker_session_sha256,
                    observed_worker_sessions,
                ),
                (
                    "launch ID",
                    worker_session["launch_id_sha256"],
                    observed_launch_ids,
                ),
                (
                    "launch authorization",
                    worker_session["launch_authorization_sha256"],
                    observed_launch_authorizations,
                ),
                (
                    "optimizer completion",
                    completion["optimizer_completion_sha256"],
                    observed_optimizer_completions,
                ),
            )
            for label, identifier, observed in unique_receipts:
                if identifier in observed:
                    raise RuntimeError(
                        "exact aggregate contains a duplicate %s receipt" % label
                    )
                observed.add(identifier)
            _require_fresh_child_process_identity(
                worker_session, observed_child_process_identities
            )
            if (
                require_production_sessions
                and worker_session.get("production_eligible") is not True
            ):
                raise RuntimeError(
                    "exact production aggregate rejects emulated worker sessions"
                )
            if require_production_sessions:
                record = _validated_parent_confirmed_success_record(record)
            if (
                completion["production_eligible"]
                != worker_session["production_eligible"]
            ):
                raise RuntimeError(
                    "exact aggregate completion/session eligibility is inconsistent"
                )
            parent_process_identity_sha256 = None
            if worker_session["production_eligible"]:
                authorization = _load_consumed_launch_authorization(
                    directory, worker_session["launch_id_sha256"]
                )
                parent_identity = _validated_process_identity_record(
                    authorization["parent_process_identity"]
                )
                parent_process_identity_sha256 = parent_identity[
                    "process_identity_sha256"
                ]
                if (
                    authorization["launch_authorization_sha256"]
                    != worker_session["launch_authorization_sha256"]
                    or authorization["request"] != asdict(request)
                    or authorization["ledger_directory"]
                    != str(directory.resolve())
                    or authorization["worker_token_sha256"]
                    != worker_session["worker_token_sha256"]
                    or authorization["parent_pid"]
                    != worker_session["parent_process_id"]
                    or record["parent_exit_process_identity"]
                    != authorization["parent_process_identity"]
                    or record["parent_exit_process_identity_sha256"]
                    != parent_process_identity_sha256
                    or record["parent_exit_observed_child_pid"]
                    != authorization["child_pid"]
                    or record["parent_exit_child_returncode"] != 0
                    or record["parent_exit_child_signal"] is not None
                    or authorization["child_pid"]
                    != worker_session["worker_process_id"]
                    or authorization["child_process_identity"]
                    != worker_session["child_process_identity"]
                    or authorization["child_process_identity_sha256"]
                    != worker_session["child_process_identity_sha256"]
                    or authorization["consumed_unix_ns"]
                    > worker_session["issued_unix_ns"]
                    or worker_session["issued_unix_ns"]
                    > record["reserved_unix_ns"]
                ):
                    raise RuntimeError(
                        "exact aggregate durable launch custody is inconsistent"
                    )
            if (
                observed_runtime["sha256"]
                != campaign["execution_runtime_sha256"]
                or record.get("campaign_sha256")
                != campaign["campaign_sha256"]
            ):
                raise RuntimeError(
                    "exact SUCCESS runtime/campaign receipt is inconsistent"
                )
            if runtime_record is None:
                runtime_record = observed_runtime
            elif _canonical_json(runtime_record) != _canonical_json(observed_runtime):
                raise RuntimeError("exact workers do not share identical runtime custody")
            if record.get("request") != asdict(request) or record.get("preflight") != _preflight_receipt(prepared, request):
                raise RuntimeError("exact SUCCESS request/preflight custody is inconsistent")
            filename = "%s.pt" % run_key
            if record.get("result_file") != filename:
                raise RuntimeError("exact SUCCESS result filename is inconsistent")
            result_path = (directory / filename).resolve()
            if result_path.parent != directory.resolve():
                raise RuntimeError("exact SUCCESS result path escapes the campaign")
            result = load_exact_population_method_result(
                result_path,
                expected_sha256=record.get("result_file_sha256"),
            )
            comparisons = {
                "method_result_sha256": result.digest,
                "classifier_sha256": result.classifier_sha256,
                "certificate_sha256": result.continuous_certificate.certificate_sha256,
                "parameter_sha256": result.final_snapshot.parameter_sha256,
                "trace_sha256": result.optimization_trace.trace_sha256,
                "split_diagnostic_sha256": [value.digest for value in result.split_diagnostics],
                "resource_sha256": result.resources.digest,
                "preparation_cpu_seconds": result.resources.preparation_cpu_seconds,
                "preparation_wall_seconds": result.resources.preparation_wall_seconds,
                "optimizer_wall_seconds": result.resources.optimizer_wall_seconds,
                "total_cpu_seconds": result.resources.elapsed_cpu_seconds,
                "total_wall_seconds": result.resources.elapsed_wall_seconds,
                "peak_rss_bytes": result.resources.peak_rss_bytes,
                "optimizer_steps": result.optimization_trace.optimizer_updates,
            }
            if any(record.get(name) != value for name, value in comparisons.items()):
                raise RuntimeError("exact saved result differs from its SUCCESS receipt")
            if (
                (result.seed, result.method) != (seed, method)
                or result.run_key_sha256 != run_key
                or result.execution_runtime_sha256
                != observed_runtime["sha256"]
                or result.campaign_sha256 != campaign["campaign_sha256"]
                or result.preflight_sha256 != prepared.preflight_sha256
                or result.prepared_ledger_sha256
                != record["prepared_ledger_sha256"]
                or result.running_ledger_sha256
                != record["running_ledger_sha256"]
                or result.worker_session_sha256 != worker_session_sha256
                or result.launch_id_sha256
                != worker_session["launch_id_sha256"]
                or result.launch_authorization_sha256
                != worker_session["launch_authorization_sha256"]
                or result.child_process_identity_sha256
                != worker_session["child_process_identity_sha256"]
                or result.production_session
                != worker_session["production_eligible"]
                or result.initial_parameter_sha256
                != completion["initial_parameter_sha256"]
                or result.final_snapshot.parameter_sha256
                != completion["final_parameter_sha256"]
                or result.digest != completion["result_sha256"]
                or result.fixture_sha256 != prepared.train_population.fixture_sha256
                or result.exact_configuration_sha256 != prepared.exact_configuration_sha256
            ):
                raise RuntimeError("exact saved result differs from campaign custody")
            results.append(result)
            success_receipts.append(
                {
                    "run_key_sha256": run_key,
                    "success_ledger_sha256": record["success_ledger_sha256"],
                    "parent_exit_observation_sha256": record.get(
                        "parent_exit_observation_sha256"
                    ),
                    "parent_exit_child_returncode": record.get(
                        "parent_exit_child_returncode"
                    ),
                    "prepared_ledger_sha256": record["prepared_ledger_sha256"],
                    "running_ledger_sha256": record["running_ledger_sha256"],
                    "execution_runtime_sha256": observed_runtime["sha256"],
                    "campaign_sha256": campaign["campaign_sha256"],
                    "worker_session_sha256": worker_session_sha256,
                    "launch_id_sha256": worker_session["launch_id_sha256"],
                    "launch_authorization_sha256": worker_session[
                        "launch_authorization_sha256"
                    ],
                    "parent_process_identity_sha256": (
                        parent_process_identity_sha256
                    ),
                    "child_process_identity_sha256": worker_session[
                        "child_process_identity_sha256"
                    ],
                    "child_process_id": worker_session["worker_process_id"],
                    "optimizer_completion_sha256": completion[
                        "optimizer_completion_sha256"
                    ],
                    "production_session": worker_session["production_eligible"],
                    "resource_sha256": result.resources.digest,
                    "preparation_cpu_seconds": result.resources.preparation_cpu_seconds,
                    "preparation_wall_seconds": result.resources.preparation_wall_seconds,
                    "optimizer_wall_seconds": result.resources.optimizer_wall_seconds,
                    "total_cpu_seconds": result.resources.elapsed_cpu_seconds,
                    "total_wall_seconds": result.resources.elapsed_wall_seconds,
                    "peak_rss_bytes": result.resources.peak_rss_bytes,
                }
            )
    if set(ledger["runs"]) != observed_run_keys:
        raise RuntimeError(
            "exact aggregate ledger contains coordinates outside the frozen campaign"
        )
    if require_production_sessions:
        with _locked_launch_ledger(directory) as (_, launch_ledger):
            if set(launch_ledger["launches"]) != observed_launch_ids:
                raise RuntimeError(
                    "exact aggregate launch ledger differs from successful coordinates"
                )
    assert runtime_record is not None
    environment_fields = runtime_record["torch_environment"]
    environment = FrozenAssociationTrainingEnvironment(**environment_fields)
    runtime_environment = {
        "python_version": runtime_record.get("python"),
        "numpy_version": runtime_record.get("numpy"),
        "scipy_version": runtime_record.get("scipy"),
        "torch_version": runtime_record.get("torch"),
        "torch_cpu_only": environment_fields.get("torch_cpu_only"),
        "torch_threads": environment_fields.get("torch_threads"),
        "torch_interop_threads": environment_fields.get(
            "torch_interop_threads"
        ),
        "deterministic_algorithms": environment_fields.get(
            "deterministic_algorithms"
        ),
    }
    if (
        runtime_environment != environment_fields
        or not environment.versions_match
        or not environment.execution_mode_matches
    ):
        raise RuntimeError("exact aggregate runtime is not the frozen environment")
    complete = AssociationExactPopulationDiagnosticResult(
        preflight_sha256=prepared.preflight_sha256,
        execution_contract_sha256=prepared.execution_contract.digest,
        source_sha256=prepared.source_sha256,
        exact_configuration_sha256=prepared.exact_configuration_sha256,
        fixture_sha256=prepared.train_population.fixture_sha256,
        split_custody_sha256=tuple(value.custody_sha256 for value in prepared.populations),
        oracle_product_control_custody_sha256=prepared.oracle_product_control.custody_sha256,
        oracle_product_positive_maximum_absolute_logit=prepared.oracle_product_control.maximum_absolute_logit,
        oracle_product_control_passed=prepared.oracle_product_control.passed,
        seed_custodies=prepared.seed_custodies,
        environment=environment,
        executed=True,
        optimizer_steps_taken=EXACT_EXPECTED_TOTAL_OPTIMIZER_STEPS,
        method_results=tuple(results),
        status="DIAGNOSTIC_COMPLETE_NONDECISION",
        notes=(
            "Exact-population lane is diagnostic only and cannot determine A1 PASS or STOP.",
            "All 24 isolated SUCCESS receipts and result payloads were verified.",
        ),
        scientific_decision_eligible=False,
        product_control_optimized=False,
    )
    resource_totals = {
        "coordinate_count": len(results),
        "preparation_cpu_seconds": math.fsum(
            value.resources.preparation_cpu_seconds for value in results
        ),
        "preparation_wall_seconds": math.fsum(
            value.resources.preparation_wall_seconds for value in results
        ),
        "optimizer_wall_seconds": math.fsum(
            value.resources.optimizer_wall_seconds for value in results
        ),
        "total_cpu_seconds": math.fsum(
            value.resources.elapsed_cpu_seconds for value in results
        ),
        "total_wall_seconds": math.fsum(
            value.resources.elapsed_wall_seconds for value in results
        ),
        "maximum_peak_rss_bytes": max(
            value.resources.peak_rss_bytes for value in results
        ),
    }
    return complete, tuple(success_receipts), resource_totals


def _aggregate_custody_totals(receipts: Sequence[dict]) -> dict:
    return {
        "coordinate_count": len(receipts),
        "production_session_count": sum(
            receipt["production_session"] is True for receipt in receipts
        ),
        "unique_launch_id_count": len(
            {receipt["launch_id_sha256"] for receipt in receipts}
        ),
        "unique_launch_authorization_count": len(
            {receipt["launch_authorization_sha256"] for receipt in receipts}
        ),
        "unique_child_process_identity_count": len(
            {receipt["child_process_identity_sha256"] for receipt in receipts}
        ),
        "unique_child_process_id_count": len(
            {receipt["child_process_id"] for receipt in receipts}
        ),
        "unique_worker_session_count": len(
            {receipt["worker_session_sha256"] for receipt in receipts}
        ),
        "unique_optimizer_completion_count": len(
            {receipt["optimizer_completion_sha256"] for receipt in receipts}
        ),
        "parent_confirmed_zero_exit_count": sum(
            receipt.get("parent_exit_child_returncode") == 0
            and receipt.get("parent_exit_observation_sha256") is not None
            for receipt in receipts
        ),
        "unique_parent_exit_observation_count": len(
            {
                receipt["parent_exit_observation_sha256"]
                for receipt in receipts
                if receipt.get("parent_exit_observation_sha256") is not None
            }
        ),
    }


_VERIFIED_CONSTRUCTION_KEY = object()


class LedgerVerifiedExactPopulationDiagnostic:
    """Complete result exposed only with its durable aggregate receipt."""

    __slots__ = (
        "_result",
        "_complete_result_sha256",
        "_campaign_sha256",
        "_aggregate_sha256",
        "_locked",
    )

    def __init__(self, result: object, campaign_sha256: str, aggregate_sha256: str, *, _key: object) -> None:
        if _key is not _VERIFIED_CONSTRUCTION_KEY:
            raise TypeError("ledger-verified exact results come only from the aggregate loader")
        from heterodiff.experiments.finite_association_exact_population_torch import (
            AssociationExactPopulationDiagnosticResult,
        )

        if type(result) is not AssociationExactPopulationDiagnosticResult:
            raise TypeError("result must be the complete exact-population dataclass")
        result.__post_init__()
        if not result.executed or result.status != "DIAGNOSTIC_COMPLETE_NONDECISION":
            raise ValueError("ledger admission requires a complete executed diagnostic")
        object.__setattr__(self, "_result", result)
        object.__setattr__(self, "_complete_result_sha256", result.digest)
        object.__setattr__(self, "_campaign_sha256", _lower_sha256(campaign_sha256, name="campaign_sha256"))
        object.__setattr__(self, "_aggregate_sha256", _lower_sha256(aggregate_sha256, name="aggregate_sha256"))
        object.__setattr__(self, "_locked", True)

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_locked", False):
            raise AttributeError("ledger-verified exact diagnostic is immutable")
        object.__setattr__(self, name, value)

    def assert_integrity(self) -> None:
        self._result.__post_init__()
        if self._result.digest != self._complete_result_sha256:
            raise RuntimeError("ledger-verified exact result changed after admission")

    @property
    def result(self):
        self.assert_integrity()
        return self._result

    @property
    def complete_result_sha256(self) -> str:
        return self._complete_result_sha256

    @property
    def campaign_sha256(self) -> str:
        return self._campaign_sha256

    @property
    def aggregate_sha256(self) -> str:
        return self._aggregate_sha256


def finalize_frozen_exact_population_campaign() -> LedgerVerifiedExactPopulationDiagnostic:
    """Fail closed unless all 24 SUCCESS results exist, then fsync aggregate."""

    directory = frozen_exact_population_campaign_directory().resolve()
    with _locked_ledger(directory) as (path, ledger):
        complete, receipts, resource_totals = _assemble_complete_result(
            directory, ledger
        )
        campaign = ledger["campaign"]
        aggregate_body = {
            "schema": _AGGREGATE_SCHEMA,
            "campaign_sha256": campaign["campaign_sha256"],
            "ordered_success_receipts": list(receipts),
            "complete_result_sha256": complete.digest,
            "optimizer_steps_taken": complete.optimizer_steps_taken,
            "resource_totals": resource_totals,
            "custody_totals": _aggregate_custody_totals(receipts),
            "scientific_decision_eligible": False,
            "product_control_optimized": False,
        }
        aggregate = dict(aggregate_body)
        aggregate["aggregate_sha256"] = _sha256_json(aggregate_body)
        existing = ledger.get("aggregate")
        if existing is None:
            ledger["aggregate"] = aggregate
            _atomic_write_json(path, ledger)
        elif existing != aggregate:
            raise RuntimeError("existing exact aggregate receipt differs from verified results")
    return LedgerVerifiedExactPopulationDiagnostic(
        complete,
        campaign["campaign_sha256"],
        aggregate["aggregate_sha256"],
        _key=_VERIFIED_CONSTRUCTION_KEY,
    )


def load_completed_frozen_exact_population_campaign() -> LedgerVerifiedExactPopulationDiagnostic:
    """Load only a complete campaign with an already durable aggregate receipt."""

    directory = frozen_exact_population_campaign_directory().resolve()
    with _locked_ledger(directory) as (_, ledger):
        aggregate = ledger.get("aggregate")
        if not isinstance(aggregate, dict):
            raise RuntimeError("exact-population campaign has no aggregate receipt")
        complete, receipts, resource_totals = _assemble_complete_result(
            directory, ledger
        )
        expected_body = {
            "schema": _AGGREGATE_SCHEMA,
            "campaign_sha256": ledger["campaign"]["campaign_sha256"],
            "ordered_success_receipts": list(receipts),
            "complete_result_sha256": complete.digest,
            "optimizer_steps_taken": complete.optimizer_steps_taken,
            "resource_totals": resource_totals,
            "custody_totals": _aggregate_custody_totals(receipts),
            "scientific_decision_eligible": False,
            "product_control_optimized": False,
        }
        expected = dict(expected_body)
        expected["aggregate_sha256"] = _sha256_json(expected_body)
        if aggregate != expected:
            raise RuntimeError("exact aggregate receipt does not match current results")
    return LedgerVerifiedExactPopulationDiagnostic(
        complete,
        ledger["campaign"]["campaign_sha256"],
        aggregate["aggregate_sha256"],
        _key=_VERIFIED_CONSTRUCTION_KEY,
    )


def revalidate_completed_frozen_exact_population_diagnostic(
    admitted: object,
) -> LedgerVerifiedExactPopulationDiagnostic:
    """Reload canonical evidence and match it to an earlier admission wrapper.

    The private-construction wrapper is API hygiene, not provenance or caller
    authentication.  This boundary reopens the canonical ledger and all 24
    digest-gated result files, reconstructs their aggregate, and returns the
    freshly admitted wrapper only when all receipt identities match.
    """

    if type(admitted) is not LedgerVerifiedExactPopulationDiagnostic:
        raise TypeError(
            "exact diagnostic revalidation requires canonical ledger admission"
        )
    admitted.assert_integrity()
    fresh = load_completed_frozen_exact_population_campaign()
    if (
        fresh.campaign_sha256 != admitted.campaign_sha256
        or fresh.aggregate_sha256 != admitted.aggregate_sha256
        or fresh.complete_result_sha256 != admitted.complete_result_sha256
        or fresh.result.digest != admitted.result.digest
    ):
        raise RuntimeError(
            "canonical exact-population admission changed during revalidation"
        )
    return fresh


def _terminate_and_reap_owned_child(process: object) -> Optional[int]:
    """Best-effort bounded cleanup after a parent-side launch failure."""

    try:
        outcome = process.poll()
    except BaseException:
        try:
            outcome = process.wait(timeout=5.0)
        except (subprocess.TimeoutExpired, TimeoutError):
            outcome = None
        except BaseException:
            outcome = None
    if outcome is not None:
        _child_signal_from_returncode(outcome)
        return outcome
    for action_name in ("terminate", "kill"):
        try:
            getattr(process, action_name)()
        except BaseException:
            continue
        try:
            outcome = process.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            continue
        except BaseException:
            continue
        _child_signal_from_returncode(outcome)
        return outcome
    try:
        outcome = process.poll()
    except BaseException:
        try:
            outcome = process.wait(timeout=5.0)
        except BaseException:
            return None
    if outcome is not None:
        _child_signal_from_returncode(outcome)
    return outcome


def _resolved_exact_worker_script_path() -> Path:
    worker_script = Path(__file__).resolve(strict=True)
    if not worker_script.is_file():
        raise RuntimeError("exact worker script path is not a regular file")
    return worker_script


def _attach_exact_secondary_failure(
    primary: BaseException, label: str, secondary: BaseException
) -> None:
    try:
        message = "%s: %s: %s" % (
            label,
            type(secondary).__name__,
            secondary,
        )
    except BaseException:
        message = "%s: secondary failure could not be rendered" % label
    try:
        add_note = getattr(primary, "add_note", None)
        if callable(add_note):
            add_note(message)
    except BaseException:
        pass
    try:
        previous = tuple(
            getattr(primary, "exact_secondary_failures", ())
        )
        setattr(primary, "exact_secondary_failures", previous + (message,))
    except BaseException:
        pass


def _require_durable_parent_launch_closure(
    directory: Path,
    authorization: object,
    request: FrozenExactPopulationRunRequest,
) -> dict:
    """Reopen one parent launch and require consumed or terminal custody."""

    issued = dict(_validated_issued_launch_authorization(authorization))
    resolved = directory.resolve()
    parent_identity = _current_process_identity_record()
    with _locked_launch_ledger(resolved) as (_, ledger):
        current = ledger["launches"].get(issued["launch_id_sha256"])
    if type(current) is not dict:
        raise RuntimeError("exact parent launch closure is absent")
    if (
        _issued_predecessor_from_launch_authorization(current) != issued
        or issued["request"] != asdict(request)
        or issued["ledger_directory"] != str(resolved)
        or issued["parent_pid"] != os.getpid()
        or issued["parent_process_identity"] != parent_identity
    ):
        raise RuntimeError("exact durable parent launch closure changed")
    if current.get("state") == "CONSUMED":
        return _validated_consumed_launch_authorization(current)
    if current.get("state") in ("FAILURE", "HOLD"):
        return _validated_terminal_launch_authorization(current)
    raise RuntimeError("exact parent launch remains outside closed custody")


def _terminalize_parent_launch_preserving_primary(
    primary: BaseException,
    directory: Path,
    authorization: object,
    request: FrozenExactPopulationRunRequest,
    *,
    state: str,
    failed_stage: str,
    observed_child_pid: Optional[int] = None,
) -> Optional[dict]:
    """Retry parent terminalization and reopen it without masking primary."""

    terminal = None
    for attempt in (1, 2):
        try:
            terminal = _terminalize_parent_launch_authorization(
                directory,
                authorization,
                request,
                state=state,
                failed_stage=failed_stage,
                error=primary,
                observed_child_pid=observed_child_pid,
            )
            break
        except BaseException as custody_error:
            _attach_exact_secondary_failure(
                primary,
                "exact launch terminalization attempt %d failed" % attempt,
                custody_error,
            )
    for attempt in (1, 2):
        try:
            durable = _require_durable_parent_launch_closure(
                directory, authorization, request
            )
            if terminal is not None and durable != terminal:
                raise RuntimeError(
                    "exact reopened parent launch differs from terminalization"
                )
            return durable
        except BaseException as verification_error:
            _attach_exact_secondary_failure(
                primary,
                "exact durable launch closure verification attempt %d failed"
                % attempt,
                verification_error,
            )
    return None


def _launch_child(request: FrozenExactPopulationRunRequest) -> subprocess.CompletedProcess:
    directory = frozen_exact_population_campaign_directory().resolve()
    worker_script = _resolved_exact_worker_script_path()
    read_fd, write_fd = os.pipe()
    token = os.urandom(32)
    token_sha256 = hashlib.sha256(token).hexdigest()
    authorization = None
    process = None
    observed_child_pid = None
    returncode = None
    command: Tuple[str, ...] = ()
    pending_error = None

    def record_parent_error(
        error: BaseException,
        failed_stage: str,
        *,
        observed_pid: Optional[int] = None,
    ) -> None:
        nonlocal pending_error
        if pending_error is None:
            pending_error = (error, error.__traceback__)
        if authorization is None:
            return
        _terminalize_parent_launch_preserving_primary(
            pending_error[0],
            directory,
            authorization,
            request,
            state=(
                "HOLD"
                if isinstance(error, (KeyboardInterrupt, SystemExit))
                else "FAILURE"
            ),
            failed_stage=failed_stage,
            observed_child_pid=observed_pid,
        )

    try:
        authorization = _issue_parent_launch_authorization(
            directory, request, token_sha256
        )
    except _DurableExactLaunchIssuanceError as error:
        authorization = error.authorization
        record_parent_error(
            error.original_error,
            "PARENT_ISSUANCE_COMMIT",
        )
    except BaseException as error:
        pending_error = (error, error.__traceback__)
    if pending_error is None:
        command = (
            sys.executable,
            str(worker_script),
            "--isolated-worker",
            "--worker-control-fd", str(read_fd),
            "--worker-token-sha256", token_sha256,
            "--launch-id-sha256", authorization["launch_id_sha256"],
            "--seed", str(request.seed),
            "--method", request.method,
            "--ledger-directory", str(directory),
        )
        try:
            process = subprocess.Popen(
                command,
                env=frozen_exact_population_worker_environment(),
                text=True,
                pass_fds=(read_fd,),
            )
        except BaseException as error:
            record_parent_error(error, "PARENT_SPAWN")
    if pending_error is None:
        try:
            observed_child_pid = _validated_child_process_id(
                process.pid, name="observed_child_pid"
            )
        except BaseException as error:
            record_parent_error(error, "PARENT_CHILD_PID")
    if pending_error is None:
        try:
            os.close(read_fd)
            read_fd = -1
        except BaseException as error:
            record_parent_error(
                error,
                "PARENT_READ_FD_CLOSE",
                observed_pid=observed_child_pid,
            )
    if pending_error is None:
        try:
            delivered = os.write(write_fd, token)
            if delivered != len(token):
                raise RuntimeError(
                    "exact worker token delivery did not write exactly 32 bytes"
                )
        except BaseException as error:
            record_parent_error(
                error,
                "PARENT_TOKEN_DELIVERY",
                observed_pid=observed_child_pid,
            )
    if pending_error is None:
        try:
            os.close(write_fd)
            write_fd = -1
        except BaseException as error:
            record_parent_error(
                error,
                "PARENT_TOKEN_FD_CLOSE",
                observed_pid=observed_child_pid,
            )
    if pending_error is None:
        try:
            returncode = process.wait()
            _child_signal_from_returncode(returncode)
        except BaseException as error:
            returncode = None
            record_parent_error(
                error,
                "PARENT_WAIT",
                observed_pid=observed_child_pid,
            )

    for descriptor_name in ("read_fd", "write_fd"):
        descriptor = read_fd if descriptor_name == "read_fd" else write_fd
        if descriptor >= 0:
            try:
                os.close(descriptor)
            except BaseException as error:
                if pending_error is None:
                    record_parent_error(
                        error,
                        (
                            "PARENT_READ_FD_CLOSE"
                            if descriptor_name == "read_fd"
                            else "PARENT_TOKEN_FD_CLOSE"
                        ),
                        observed_pid=observed_child_pid,
                    )
            if descriptor_name == "read_fd":
                read_fd = -1
            else:
                write_fd = -1
    if process is not None and returncode is None:
        if pending_error is not None:
            try:
                returncode = _terminate_and_reap_owned_child(process)
            except BaseException as cleanup_error:
                _attach_exact_secondary_failure(
                    pending_error[0],
                    "exact child cleanup failed",
                    cleanup_error,
                )
        else:
            try:
                polled = process.poll()
                if polled is None:
                    polled = process.wait()
                _child_signal_from_returncode(polled)
                returncode = polled
            except BaseException as error:
                if pending_error is None:
                    record_parent_error(
                        error,
                        "PARENT_WAIT",
                        observed_pid=observed_child_pid,
                    )
    if process is not None and returncode is None and pending_error is not None:
        try:
            returncode = _terminate_and_reap_owned_child(process)
        except BaseException as cleanup_error:
            primary = pending_error[0]
            _attach_exact_secondary_failure(
                primary,
                "exact child cleanup retry failed",
                cleanup_error,
            )
    if (
        authorization is not None
        and observed_child_pid is not None
        and returncode is not None
    ):
        try:
            _reconcile_exact_child_exit(
                directory,
                authorization,
                request,
                observed_child_pid=observed_child_pid,
                child_returncode=returncode,
            )
        except BaseException as error:
            if pending_error is None:
                pending_error = (error, error.__traceback__)
            else:
                _attach_exact_secondary_failure(
                    pending_error[0],
                    "exact child-exit reconciliation failed",
                    error,
                )
            primary = pending_error[0]
            try:
                custody_kind, custody = _close_exact_child_exit_custody(
                    directory,
                    authorization,
                    request,
                    observed_child_pid=observed_child_pid,
                    child_returncode=returncode,
                )
                _require_durable_exact_exit_custody(
                    directory, custody_kind, custody
                )
            except BaseException as repair_error:
                _attach_exact_secondary_failure(
                    primary,
                    "exact fallback exit-custody closure failed",
                    repair_error,
                )
    if pending_error is not None:
        error, traceback = pending_error
        raise error.with_traceback(traceback)
    if returncode is None:
        raise RuntimeError("exact child process outcome is unavailable")
    return subprocess.CompletedProcess(command, returncode)


def launch_frozen_exact_population_run(request: FrozenExactPopulationRunRequest) -> subprocess.CompletedProcess:
    """Launch exactly one authorized coordinate in a fresh worker process."""

    if type(request) is not FrozenExactPopulationRunRequest:
        raise TypeError("request must be an exact-population run request")
    return _launch_child(request)


def launch_frozen_exact_population_campaign() -> Tuple[subprocess.CompletedProcess, ...]:
    """Launch all 24 coordinates; any duplicate ledger key fails closed."""

    completed = []
    for seed in _SEEDS:
        for method in _METHODS:
            run = _launch_child(FrozenExactPopulationRunRequest(seed, method))
            completed.append(run)
            if run.returncode != 0:
                break
        if completed[-1].returncode != 0:
            break
    return tuple(completed)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the frozen A1 exact-population diagnostic.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--execute-exact-population", action="store_true")
    mode.add_argument("--execute-exact-population-campaign", action="store_true")
    mode.add_argument("--aggregate-exact-population", action="store_true")
    mode.add_argument("--isolated-worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--method", choices=_METHODS)
    parser.add_argument("--ledger-directory", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--worker-control-fd", type=int, help=argparse.SUPPRESS)
    parser.add_argument("--worker-token-sha256", help=argparse.SUPPRESS)
    parser.add_argument("--launch-id-sha256", help=argparse.SUPPRESS)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    arguments = _parser().parse_args(argv)
    if arguments.isolated_worker:
        if arguments.seed is None or arguments.method is None or arguments.ledger_directory is None:
            raise RuntimeError("isolated exact worker is missing its frozen coordinate/path")
        request = FrozenExactPopulationRunRequest(
            arguments.seed, arguments.method
        )
        launch_capability = _consume_parent_handshake(
            arguments.worker_control_fd,
            arguments.worker_token_sha256,
            request,
            arguments.ledger_directory,
            arguments.launch_id_sha256,
        )
        try:
            result = _worker(
                request,
                arguments.ledger_directory,
                launch_capability=launch_capability,
            )
        except BaseException as error:
            try:
                _terminalize_launch_if_main_run_unreserved(
                    arguments.ledger_directory,
                    launch_capability,
                    error,
                )
            except BaseException as custody_error:
                _attach_exact_secondary_failure(
                    error,
                    "exact worker launch terminalization failed",
                    custody_error,
                )
            raise
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    if any(
        value is not None
        for value in (
            arguments.ledger_directory,
            arguments.worker_control_fd,
            arguments.worker_token_sha256,
            arguments.launch_id_sha256,
        )
    ):
        raise RuntimeError("hidden exact-worker options are not public")
    if arguments.execute_exact_population:
        if arguments.seed is None or arguments.method is None:
            raise RuntimeError("single exact execution requires --seed and --method")
        return int(
            launch_frozen_exact_population_run(
                FrozenExactPopulationRunRequest(arguments.seed, arguments.method)
            ).returncode
        )
    if arguments.seed is not None or arguments.method is not None:
        raise RuntimeError("campaign/aggregation mode does not accept one coordinate")
    if arguments.execute_exact_population_campaign:
        completed = launch_frozen_exact_population_campaign()
        if len(completed) != 24 or any(value.returncode != 0 for value in completed):
            return 1
        # A campaign execution is successful only after all serialized
        # payloads have been reopened, all SUCCESS receipts have been
        # revalidated, and the aggregate receipt has been durably written.
        finalize_frozen_exact_population_campaign()
        return 0
    verified = finalize_frozen_exact_population_campaign()
    print(
        json.dumps(
            {
                "campaign_sha256": verified.campaign_sha256,
                "aggregate_sha256": verified.aggregate_sha256,
                "complete_result_sha256": verified.result.digest,
                "status": verified.result.status,
                "scientific_decision_eligible": False,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - explicit user CLI only
    raise SystemExit(main())


__all__ = [
    "FrozenExactPopulationRunRequest",
    "FrozenExactWorkerLaunchCapability",
    "LedgerVerifiedExactPopulationDiagnostic",
    "finalize_frozen_exact_population_campaign",
    "frozen_exact_population_campaign_directory",
    "frozen_exact_population_run_key",
    "frozen_exact_population_worker_environment",
    "launch_frozen_exact_population_campaign",
    "launch_frozen_exact_population_run",
    "load_completed_frozen_exact_population_campaign",
    "revalidate_completed_frozen_exact_population_diagnostic",
    "main",
]
