# Shared-FP64 BASE precision: conditional pipeline integration

Date: 2026-09-13

**COMPLETE — opt-in precision propagation and bounded local CPU qualification.**
This follows the separately reported T4 BASE-only pass. It does not qualify the
complete candidate pipeline on GPU or replace the historical installed release.

## Delivered behavior

`BASE_GRAPH_FP64_SHARED_V1` now reaches physical BASE energy evaluation,
frozen learned-BASE population generation, the source paths used to train both
conditional methods, and conditional sampling. The public helper is
`precision_stable_base_energy(model, batch)`. Physical potential, BASE population
and conditional sampling accept the explicit `precision_policy` keyword.
The default remains `LEGACY_FP32`; invalid or inconsistent policies stop before
sampling or optimizer work.

The scientific energy/objective, observation rules, AdamW settings and acceptance
tolerances are unchanged. The conditioner, observation encoder, nuisance,
trainable parameters and optimizer moments remain FP32. The analytic guide
remains CPU FP64. Initialization excludes BASE and nuisance as before.

There is an important precision boundary: physical coordinates start on CPU in
FP64, pass through the existing FP32 input encoding, then enter the candidate
FP64 BASE graph. Physical gradients return through that FP32 cast. This is **not
an end-to-end FP64 physical derivative**; the tests explicitly validate the
actual chain and preserved input quantization. The BASE training objective's
promoted-coordinate derivative has a different boundary, as before.

Candidate population IDs and conditional stream namespaces bind the precision
policy. Legacy IDs, streams and path diagnostics are unchanged; an independent
before/after check reproduced both domains' legacy population/pair identities
and complete path hashes exactly. Equal seeds across different population
identities are not advertised as common random inputs. Fixed-state/fixed-noise
controls and same-route exact replay are used instead.

## Actual local check

The [CPU-only harness](src/heterodiff/experiments/factorized_precision_pipeline_qualification.py)
uses invented Physio/Retail fixtures, both G+R and DIR, two BASE updates followed
by two conditional updates, and one fresh replay of each entire case. The
[recorded result](research/fixtures/factorized_precision_pipeline_local_check_2026_09_13.json)
is `PASS_LOCAL_CPU_PRECISION_PIPELINE_ONLY`; SHA-256:
`ba636c85cf079dfca8648f228b19a3e45f002dd0de00adf652143ec25daed24c`.

- Four cases pass with exact fresh-run replay, including state grids, full
  path diagnostics/jump journals/stream requests, parameters and moments.
- 16 BASE plus 16 conditional updates complete. Learned BASE remains frozen
  during conditional work; sampling does not mutate either model.
- 48 generated BASE paths and 16 conditional paths complete, including replay.
  Conditional paths cover retained and overflow observations; source paths
  refine off-grid queries. All preserve the cap and exact clean hold.
- A fixed canonical state with duplicate continuous occurrences and explicit
  Brownian increments exercises actual physical gradients and Heun motion.
- The 32 first-run paths have **0 accepted births, 2 deaths and 546 jump
  candidates**. These counts are not hidden. A separate 16 single-jump diagnostic
  operations, including replay, exercise accepted birth and death via real BASE
  energies, proposals and acceptance calculations. Their scripted wait/accept
  streams are branch controls, not scientific draws or conditional jump rates.
- Parameters/moments remain FP32. Per-parameter optimizer steps match actual
  non-None gradients; conditionally unused branches are not falsely required
  to update on every example.
- This execution took 23.259 seconds, with process-lifetime peak RSS 386,416,640
  bytes, on local Python 3.11.5 / Torch 2.12.1 CPU. It is not the Databricks
  Python 3.12.3 / Torch 2.7.0+cu126 environment or a speed benchmark.

The fixed local harness has soft 120-second/2-GiB observations, a 20,000
per-path jump-candidate ceiling, 256 initialization trials and a four-event cap.
No hard process quota is claimed. During harness development, the initial
128-candidate guard stopped an overflow path that requires 136 candidates; it
was replaced with the existing local full-path tests' 20,000 ceiling. This
changes a diagnostic resource guard, not an objective, seed, acceptance tolerance
or scientific schedule. No retry or bound adjustment occurs inside the harness.

## Verification and preserved evidence

The new physical-path and population-path suites cover input/ownership/resource
refusal, snapshot isolation, clean-hold and nuisance/initializer boundaries,
policy identities, exact legacy defaults and global RNG preservation. The
pipeline suite includes actual execution and fail-closed report tests.
The final combined regression passed **765 tests in 92.09 seconds**: 670
preceding tests plus 36 physical-path, 32 population-path and 27 pipeline
qualification tests. This includes the real four-case CPU/replay workload.
Static checks and the repository whitespace check also passed. Independent
review reproduced exact legacy identities/paths and accepted the precision
boundary, source-path instrumentation and separately scripted jump controls.
An independent fresh CPU check also passed all four cases and reproduced every
archived full-run hash exactly, with Torch/NumPy/Python global random states
and thread/determinism settings preserved. Final review found no blocker to
this bounded local milestone.

All 323 historical CPU manifest payloads remain exact. The dependency lock,
legacy GPU notebook/harness and BASE-only candidate notebook/harness remain
unchanged. No package install, restart, real data, GPU execution or paid/cloud
job was performed in this step. The new harness itself writes no files; this
local archival step writes the result and documentation.

## Plan status and next step

This local integration milestone is complete. Compound timetable totals remain
**61 checked / 102 open / 163 total**; fields **31 open / 141 closed**; blockers
**8 open / 4 closed**. Formal Tests 28/29/30 remain OPEN/OPEN/PENDING and
scientific results remain 0/4. No broad scientific obligation is relabelled.

The subsequent [separate bounded GPU-check preparation](PROJECT_FACTORIZED_PRECISION_PIPELINE_GPU_CHECK_PREPARATION.md)
is now COMPLETE: a new inspection-first notebook, common-input CPU/GPU controls,
same-device replay and complete tiny paths, with fixed tolerances and visible
legacy controls. Its actual CPU notebook rehearsal passed; selected-GPU
execution is still pending separate authorization. This local harness remains
CPU-only; neither earlier GPU notebook selects the complete candidate path.
Do not rerun an earlier notebook as a substitute. Full training,
trajectory/checkpoint qualification, installed-release validation, candidate
F105 checkpoint integration,
real-data admission and production resource budgets remain open.
