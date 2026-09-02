"""Production CLI for atomic-counting evidence publication and verification.

The CLI is Torch-free.  ``publish`` consumes the continuous, five-step prefix,
fresh-process resumed, and checkpoint outputs for both domains, plus their
executor receipts and independent audit reports.  Synthetic receipts are never
accepted by this production surface.  ``status`` performs no artifact I/O and
reports the repository's honest pre-execution state.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Optional, Sequence

from heterodiff.cross_domain_gate.atomic_counting_evidence import (
    AtomicCountingEvidenceError,
    CompletedDomainRun,
    publish_cross_domain_evidence,
    repository_evidence_status,
    verify_published_cross_domain_evidence,
)
from heterodiff.data.cross_domain_counting_fixtures import CountingFixtureDomain


def _canonical_line(value: object) -> str:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )


def _add_domain_inputs(parser: argparse.ArgumentParser, prefix: str) -> None:
    label = prefix.replace("_", "-")
    for field, description in (
        ("continuous", "12-step continuous comparison manifest"),
        ("prefix", "five-step prefix comparison manifest"),
        ("resumed", "fresh-process resumed 12-step comparison manifest"),
        ("checkpoint", "five-step bounded checkpoint container"),
        ("receipt", "canonical completed-run executor receipt"),
        ("audit", "canonical independent PASS audit report"),
    ):
        parser.add_argument(
            "--{}-{}".format(label, field),
            type=Path,
            required=True,
            help=description,
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Torch-free durable cross-domain atomic-counting evidence runner"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "status", help="report NOT_EXECUTED/HOLD without reading run artifacts"
    )
    for command in ("publish", "verify"):
        child = commands.add_parser(
            command,
            help=(
                "validate completed runs and publish durably"
                if command == "publish"
                else "independently rebuild and byte-verify a published directory"
            ),
        )
        child.add_argument("--output", type=Path, required=True)
        _add_domain_inputs(child, "music")
        _add_domain_inputs(child, "clinical_style")
    return parser


def _runs(args: argparse.Namespace) -> tuple[CompletedDomainRun, CompletedDomainRun]:
    return (
        CompletedDomainRun(
            CountingFixtureDomain.MUSIC,
            args.music_continuous,
            args.music_prefix,
            args.music_resumed,
            args.music_checkpoint,
            args.music_receipt,
            args.music_audit,
        ),
        CompletedDomainRun(
            CountingFixtureDomain.CLINICAL_STYLE,
            args.clinical_style_continuous,
            args.clinical_style_prefix,
            args.clinical_style_resumed,
            args.clinical_style_checkpoint,
            args.clinical_style_receipt,
            args.clinical_style_audit,
        ),
    )


def main(arguments: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(arguments)
    if args.command == "status":
        sys.stdout.write(_canonical_line(dict(repository_evidence_status())) + "\n")
        return 0
    try:
        if args.command == "publish":
            result = publish_cross_domain_evidence(_runs(args), args.output)
            payload = {
                "execution_class": result.execution_class,
                "gate_decision": "NOT_MADE_BY_EVIDENCE_PUBLISHER",
                "manifest_sha256": result.manifest_sha256,
                "output_directory": str(result.output_directory),
                "public_bundle_digests": dict(result.public_bundle_digests),
                "status": result.status,
            }
        else:
            result = verify_published_cross_domain_evidence(_runs(args), args.output)
            payload = {
                "execution_class": result.execution_class,
                "gate_decision": "NOT_MADE_BY_EVIDENCE_VERIFIER",
                "manifest_sha256": result.manifest_sha256,
                "output_directory": str(result.output_directory),
                "public_bundle_digests": dict(result.public_bundle_digests),
                "status": result.status,
            }
        sys.stdout.write(_canonical_line(payload) + "\n")
        return 0
    except (AtomicCountingEvidenceError, OSError, ValueError, TypeError) as error:
        payload = {
            "error_type": type(error).__name__,
            "message": str(error),
            "status": "HOLD",
        }
        sys.stderr.write(_canonical_line(payload) + "\n")
        return 2


if __name__ == "__main__":  # pragma: no cover - exercised via subprocess
    raise SystemExit(main())

