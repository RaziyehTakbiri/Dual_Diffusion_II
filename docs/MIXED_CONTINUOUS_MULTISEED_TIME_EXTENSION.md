# Authorized completion of the fixed multi-seed roster

Date: 2026-09-13. This note is recorded before the completion run. It is an
execution-time amendment, not a replacement of the original scientific protocol.

## Authority and purpose

After the first local run stopped at its declared 2,400-second deadline with
20 of 22 routes complete, the user authorized additional local CPU time:
“Yes, take any additional time required.” The preceding request concerned
finishing only the missing seed pair, without GPU or paid jobs.

The [original protocol](MIXED_CONTINUOUS_MULTISEED_PROTOCOL.md), original
`protocol.json`, 20 completed route files, partial review and verification
record remain unchanged. The original single-attempt deadline result remains
incomplete. Completion will be reported as a fixed scientific roster completed
with an authorized time extension, never as success within the original limit.

## Work allowed by this amendment

Only these two previously declared routes are computed:

1. Higher-pressure/shifted-observation setting, seed 1203,
   association-aware guide plus residual (route 21).
2. The same setting and seed, unified direct conditioner (route 22).

Route 21 has no saved complete result or resumable checkpoint. Its interrupted
calculation is recomputed from the original seed and initial weights. Unknown
work from that interrupted attempt is disclosed rather than inferred. Route
22 was not reached in the original attempt. None of the first 20 completed
routes is rerun or replaced. No successful sample is selected because it looks
favorable and no new seed, checkpoint, training setting or evaluation draw is
introduced.

The original two-setting/three-seed roster, neural architecture, optimizer,
32 updates, two pairs per update, validation pairs/checkpoints, numerical grid,
512 final draws per fit, exact target, seed namespaces and record identifiers
remain fixed. The original uncertainty allocations and family sizes 22/4/2
remain fixed. The observed partial results do not change the model or metric.

## Execution and checks

A separate completion runner reuses the original scientific helpers, checks
the saved prefix and preserves it, and writes into a new output directory:
`research/fixtures/continuous_multiseed_completion_cpu_2026_09_13`.
It records an intent before computation, saves each newly completed route,
then combines all 22 unique declared routes for the final report. Focused
tests compare its reduced neural procedure with the original procedure before
the full missing pair is run.

The continuation uses one local CPU child and one intra-operation thread. A
separate 1,800-second supervisor limit protects against an unexpectedly stuck
child; it is not a new scientific sample budget. No automatic retry is
implemented. If it is insufficient, the result remains explicitly incomplete
until its execution is reviewed. The user has authorized additional local time,
not a change of scientific settings or external resource use.

Reduced tests finish before the full continuation starts. Original-run timing
already includes overlap with local verification work. Timing from two separate
processes is reported separately; neither is a matched-quality speedup claim.
The completed-record workload excludes unknown additional interrupted work.

No package downloads, GPU/cloud/paid jobs, real-data reads, commits, pushes or
publication are part of this completion step. Completion of the roster is not
evidence of general method superiority or posterior recovery.
