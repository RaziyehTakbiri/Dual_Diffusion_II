"""Fresh-interpreter branch worker for the bounded restart-evidence gate.

The worker emits one comparison artifact and one canonical execution summary.
It never creates a receipt, audit, evidence bundle, or gate decision; those are
separate parent and independent-review responsibilities.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import stat
import sys
from typing import Mapping, Optional, Sequence

import numpy as np
import torch

from heterodiff.cross_domain_gate.atomic_counting_training_torch import (
    AtomicCountingResourceMonitor,
    AtomicCountingTrainingStep,
    M_ACG_1_TRAINING_CONFIG,
    P_ACG_1_TRAINING_CONFIG,
    adapt_counting_task_set,
    build_atomic_counting_trainer,
    build_checkpoint_bindings,
    configure_atomic_counting_deterministic_runtime,
    load_atomic_counting_checkpoint,
    local_gate_external_digests,
    preflight_atomic_counting_pinned_runtime,
    save_atomic_counting_checkpoint,
    write_training_manifest_no_replace,
)
from heterodiff.cross_domain_gate.counting_windows import (
    build_m_acg_1_task_set,
    build_p_acg_1_task_set,
)


_CLI_OPTIONS = frozenset(
    {
        "--checkpoint",
        "--domain",
        "--expected-checkpoint-sha",
        "--mode",
        "--output",
        "--prior-output",
    }
)
_OUTPUT_NAME_BY_MODE = {
    "continuous": "continuous.json",
    "prefix": "prefix.json",
    "resume": "resumed.json",
}
_LOWER_HEX = frozenset("0123456789abcdef")


def _scalar(record: Mapping[str, object], name: str) -> torch.Tensor:
    value = record[name]
    if type(value) is not dict or set(value) != {"data_hex", "dtype", "shape"}:
        raise ValueError("prior scalar manifest is malformed")
    if value["dtype"] != "float32" or value["shape"] != []:
        raise ValueError("prior scalar dtype or shape is invalid")
    try:
        raw = bytes.fromhex(value["data_hex"])
    except (TypeError, ValueError) as error:
        raise ValueError("prior scalar bytes are invalid") from error
    if len(raw) != 4:
        raise ValueError("prior scalar byte length is invalid")
    array = np.frombuffer(raw, dtype=np.dtype(np.float32)).copy()
    result = torch.from_numpy(array).reshape(())
    if not bool(torch.isfinite(result).item()):
        raise ValueError("prior scalar is nonfinite")
    return result


def _records_from_prior(path: Path, monitor: AtomicCountingResourceMonitor):
    size = path.stat().st_size
    monitor.check_output_size(size)
    raw = path.read_bytes()
    if len(raw) != size:
        raise ValueError("prior comparison output changed while reading")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("prior comparison output is invalid JSON") from error
    records = value.get("step_records") if type(value) is dict else None
    if type(records) is not list or len(records) != 5:
        raise ValueError("prior comparison output must contain steps one through five")
    result = []
    for expected_step, record in enumerate(records, start=1):
        if type(record) is not dict:
            raise ValueError("prior step record is malformed")
        result.append(
            AtomicCountingTrainingStep(
                completed_step=record["completed_step"],
                task_index=record["task_index"],
                task_id=record["task_id"],
                total_loss=_scalar(record, "total_loss"),
                count_loss=_scalar(record, "count_loss"),
                presence_loss=_scalar(record, "presence_loss"),
                continuous_loss=_scalar(record, "continuous_loss"),
                occupied_count=record["occupied_count"],
                empty_count=record["empty_count"],
                present_count=record["present_count"],
                absent_count=record["absent_count"],
                continuous_count=record["continuous_count"],
            )
        )
        if result[-1].completed_step != expected_step:
            raise ValueError("prior step records are not consecutive")
    return tuple(result)


def _remove_owned_artifact(path: Path, expected_sha256: str) -> None:
    """Remove only the unchanged regular file created by this worker."""

    try:
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode):
            return
        raw = path.read_bytes()
        after = path.lstat()
    except FileNotFoundError:
        return
    identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if (
        identity_before == identity_after
        and hashlib.sha256(raw).hexdigest() == expected_sha256
    ):
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="bounded atomic-counting restart comparison worker",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--domain", choices=("music", "clinical_style"), required=True
    )
    parser.add_argument(
        "--mode", choices=("continuous", "prefix", "resume"), required=True
    )
    # Preserve the path tokens until the complete frozen CLI grammar has been
    # checked.  ``Path`` normalizes spellings such as ``runs//music`` and would
    # otherwise erase the evidence that a caller supplied a noncanonical path.
    parser.add_argument("--output", required=True)
    parser.add_argument("--checkpoint")
    parser.add_argument("--expected-checkpoint-sha")
    parser.add_argument("--prior-output")
    return parser


def _argument_tokens(arguments: Optional[Sequence[str]]) -> tuple[str, ...]:
    tokens = tuple(sys.argv[1:] if arguments is None else arguments)
    if any(type(token) is not str for token in tokens):
        raise TypeError("worker arguments must be exact strings")
    seen = set()
    for token in tokens:
        option = token.split("=", 1)[0]
        if option in _CLI_OPTIONS:
            if option in seen:
                raise ValueError("duplicate worker option: {}".format(option))
            seen.add(option)
    return tokens


def _validate_mode_arguments(args: argparse.Namespace) -> None:
    if args.mode in ("prefix", "resume") and args.checkpoint is None:
        raise ValueError("prefix and resume modes require --checkpoint")
    if args.mode == "continuous" and any(
        value is not None
        for value in (
            args.checkpoint,
            args.expected_checkpoint_sha,
            args.prior_output,
        )
    ):
        raise ValueError("continuous mode rejects checkpoint/resume arguments")
    if args.mode == "prefix" and any(
        value is not None
        for value in (args.expected_checkpoint_sha, args.prior_output)
    ):
        raise ValueError("prefix mode rejects resume-only arguments")
    if args.mode == "resume" and (
        args.expected_checkpoint_sha is None or args.prior_output is None
    ):
        raise ValueError(
            "resume mode requires --expected-checkpoint-sha and --prior-output"
        )


def _canonical_worker_arguments(args: argparse.Namespace) -> tuple[str, ...]:
    directory = "runs/{}".format(args.domain)
    common = (
        "--domain",
        args.domain,
        "--mode",
        args.mode,
        "--output",
        "{}/{}".format(directory, _OUTPUT_NAME_BY_MODE[args.mode]),
    )
    if args.mode == "continuous":
        return common
    checkpoint = directory + "/step5.ckpt"
    if args.mode == "prefix":
        return common + ("--checkpoint", checkpoint)
    digest = args.expected_checkpoint_sha
    if (
        type(digest) is not str
        or len(digest) != 64
        or any(character not in _LOWER_HEX for character in digest)
    ):
        raise ValueError(
            "resume mode requires a canonical lowercase SHA-256 digest"
        )
    return common + (
        "--checkpoint",
        checkpoint,
        "--expected-checkpoint-sha",
        digest,
        "--prior-output",
        directory + "/prefix.json",
    )


def _parse_arguments(arguments: Optional[Sequence[str]]) -> argparse.Namespace:
    tokens = _argument_tokens(arguments)
    args = _parser().parse_args(tokens)
    # Retain the established, mode-specific diagnostics before checking the
    # stricter spelling/order grammar.
    _validate_mode_arguments(args)
    expected = _canonical_worker_arguments(args)
    if tokens != expected:
        raise ValueError(
            "worker arguments must use the exact frozen grammar and canonical "
            "relative runs/<domain> paths"
        )
    args.output = Path(args.output)
    args.checkpoint = Path(args.checkpoint) if args.checkpoint is not None else None
    args.prior_output = (
        Path(args.prior_output) if args.prior_output is not None else None
    )
    return args


def main(arguments: Optional[Sequence[str]] = None) -> int:
    args = _parse_arguments(arguments)
    configure_atomic_counting_deterministic_runtime()
    monitor = AtomicCountingResourceMonitor()
    if args.domain == "music":
        task_set = build_m_acg_1_task_set()
        config = M_ACG_1_TRAINING_CONFIG
    else:
        task_set = build_p_acg_1_task_set()
        config = P_ACG_1_TRAINING_CONFIG
    monitor.check("fixture-parse-and-task-construction")
    tasks = adapt_counting_task_set(task_set)
    monitor.check("reference-and-task-conversion")
    bindings = build_checkpoint_bindings(
        tasks,
        config,
        external_digests=dict(local_gate_external_digests()),
    )
    trainer = build_atomic_counting_trainer(
        tasks, config, bindings, monitor=monitor
    )
    published = []
    try:
        checkpoint_sha = None
        if args.mode == "continuous":
            records = trainer.train_until(12)
        elif args.mode == "prefix":
            records = trainer.train_until(5)
            checkpoint_sha = save_atomic_counting_checkpoint(
                trainer, args.checkpoint
            )
            published.append((args.checkpoint, checkpoint_sha))
        else:
            prior = _records_from_prior(args.prior_output, monitor)
            load_atomic_counting_checkpoint(
                trainer,
                args.checkpoint,
                expected_sha256=args.expected_checkpoint_sha,
                minimum_step_exclusive=0,
            )
            records = prior + trainer.train_until(12)
            checkpoint_sha = args.expected_checkpoint_sha
        output_sha = write_training_manifest_no_replace(
            trainer, records, args.output
        )
        published.append((args.output, output_sha))
        summary = {
            "checkpoint_bindings": bindings.as_dict(),
            "checkpoint_sha256": checkpoint_sha,
            "completed_step": trainer.completed_step,
            "domain": args.domain,
            "elapsed_seconds": monitor.maximum_elapsed_seconds,
            "environment": dict(preflight_atomic_counting_pinned_runtime()),
            "maximum_rss_bytes": monitor.maximum_rss_bytes,
            "mode": args.mode,
            "output_sha256": output_sha,
            "stages": list(monitor.stage_observation_manifest()),
            "status": "restart-comparison-only",
        }
        encoded = json.dumps(
            summary,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        monitor.check_log_size(len(encoded) + 1)
        sys.stdout.buffer.write(encoded + b"\n")
        sys.stdout.buffer.flush()
        return 0
    except BaseException:
        for path, digest in reversed(published):
            _remove_owned_artifact(path, digest)
        raise


if __name__ == "__main__":  # pragma: no cover - exercised by subprocess tests
    raise SystemExit(main())
