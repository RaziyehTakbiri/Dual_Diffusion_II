# B08 local-host capacity-gap and three-field policy freeze

**Reported:** 2026-09-01  
**Subject state:** `B08_LOCAL_HOST_PARTIAL_POLICY_FREEZE_CAPACITY_NO_GO`  
**Global project state:** `DRAFT_NOT_EXECUTABLE`  
**Control predicate:** `B08_THREE_LOCALLY_DEFENSIBLE_FIELDS_FROZEN_CAPACITY_HOLD`  
**Package kind:** `ADDITIVE_PREOUTCOME_THREE_FIELD_B08_POLICY_FREEZE_WITH_EXACT_RESIDUAL_GAP`

## 1. Decision

This additive candidate freezes exactly three pre-execution fields whose values
are already determined by accepted policy and do not require an invented
production-capacity claim:

1. F153, `/compute_and_fairness_plan/deterministic_settings`;
2. F158, `/compute_and_fairness_plan/pilot_compute_allocation`; and
3. F161, `/compute_and_fairness_plan/failure_reserve`.

The candidate does **not** close B08. It leaves exactly F150--F152,
F154--F157, F159--F160, and F162 open and null. It records a current local-host
observation and two deterministic synthetic calibration receipts, but expressly
does not reinterpret them as a selected production environment, an F104 weight
calibration, a scalar or hard-axis ceiling, a storage reservation, a capacity
receipt, a domain-scale runtime, or a B08 acceptance.

Independent acceptance of the exact five-file package would move PRE from
33 open / 133 closed to 30 open / 136 closed. POST remains 1 open / 5 closed,
so the total moves from 34 open / 138 closed to 31 open / 141 closed. The
method/runtime/compute workstream moves from 20 open / 45 closed to 17 open /
48 closed. Blockers remain 7 open / 5 closed, Gate A remains 5/8, and B08
remains open.

The package does not edit the completion timetable or evidence ledger. It
contains evidence-ready registration wording only for a later authorized
integration after a separate independent review accepts the exact bytes.

## 2. Exact F153 deterministic settings

F153 is frozen to
`B08_CPU_SINGLE_THREAD_FAIL_CLOSED_DETERMINISM_V1`.

The exact policy:

- permits only the CPU execution route; CUDA and MPS are disabled;
- fixes `BLIS_NUM_THREADS`, `MKL_NUM_THREADS`, `NUMEXPR_NUM_THREADS`,
  `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, and
  `VECLIB_MAXIMUM_THREADS` to the ASCII string `1`;
- fixes locale and startup controls to `LANG=C`, `LC_ALL=C`, `TZ=UTC`,
  `PYTHONHASHSEED=0`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONNOUSERSITE=1`,
  `PYTHONSAFEPATH=1`, and `PYTHONUTF8=1`, with
  `CUDA_VISIBLE_DEVICES` the exact empty string;
- requires `torch.use_deterministic_algorithms(True, warn_only=False)`, one
  intra-operation thread, one inter-operation thread, and disabled cuDNN
  benchmarking;
- takes the seed registry only from accepted B07;
- leaves precision owned by still-open F141; and
- makes any unavailable, unsupported, or nondeterministic operation a terminal
  pre-execution no-go with no accelerator fallback, warning-only downgrade,
  replacement, retry, or alternate implementation.

This freezes the policy, not its whole-method satisfaction. B12 must later
produce an operation-level determinism receipt over the actual complete
runtime. The present package makes no production-determinism claim.

## 3. Exact F158 zero empirical-pilot allocation

F158 is frozen to
`B08_ZERO_EMPIRICAL_PILOT_DISTRIBUTION_FREE_B07_V1`.

Every scientific/empirical pilot quantity is exactly zero:

- zero scheduled empirical-pilot runs;
- zero wall-time seconds;
- zero accelerator hours;
- zero model evaluations;
- zero persistent bytes; and
- every F104 `PILOT` resource-event count is zero.

This follows the accepted B07 distribution-free route: F131 requires no
empirical pilot, and the accepted B06 primary budgets already contain zero in
every `PILOT` event cell. The two local synthetic diagnostics in this package
are environment observations, not empirical-pilot runs or scientific evidence.
They do not consume or create F158 allocation and do not calibrate an F104
resource-event weight.

No pilot allocation may be transferred, topped up, or relabeled as tuning or
final allocation.

## 4. Exact F161 zero failure reserve

F161 is frozen to
`B08_ZERO_FAILURE_RESERVE_NO_RERUN_NO_REPLACEMENT_V1`.

The additional reserve is exactly zero attempts, zero wall-time seconds, zero
accelerator hours, zero model evaluations, and zero persistent bytes. The
accepted F148 predicate is `NEVER_TRUE_NO_INFRASTRUCTURE_RERUN`; the accepted
five-status roster keeps algorithmic failures, nonfinite outcomes,
OOM/timeouts, and infrastructure aborts as terminal scheduled outcomes. B07,
F104, B06, and F145 jointly forbid replacement, favorable-seed selection,
retry, resume, transfer, adaptive extension, and post-result top-up.

Zero reserve does not make failures free. Every failed or aborted scheduled
attempt, author extension, and unique preprocessing operation is charged to
the original prospective allocation. Once that allocation is spent, the row
terminates; no extra reserve exists.

## 5. Read-only local-host observation

The current host observation is deliberately redacted but device-bound. Its
public profile is:

- Apple MacBook Pro, model `MacBookPro18,1`;
- Apple M1 Pro, arm64;
- ten CPU cores: eight performance and two efficiency;
- 16-core integrated Apple M1 Pro GPU with Metal support; and
- 16 GiB LPDDR5 memory.

The package does not store the serial number, hardware UUID, provisioning
identifier, user name, or host name. It stores only a domain-separated SHA-256
binding over the private device identifiers:
`5e1227315f8c2c82be651c4dad8087a69bb2ca98966a04484546da2e012fe85d`.
That digest is a local custody binding, not a hardware attestation, signature,
ownership proof, or availability reservation.

The observed smoke environment is macOS 26.3.1 build 25D2128, Darwin 25.3.0,
arm64 CPython 3.11.5 ABI `cpython-311-darwin`, NumPy 2.4.6, SciPy 1.17.1,
PyTorch 2.12.1, and the complete exact distribution roster in the machine
record. PyTorch was built with MPS support but reported MPS unavailable to the
capture process. The current lockfile is
`requirements/m1-reference-macos-arm64-py311.lock`, raw SHA-256
`ba373a4f7ef687e55d6f0a5cbc1f14eaf9db03ab1cf001cc8d6009e85adbbc5d`.
Its own comments call it a fixed-grid reference smoke-test environment and
explicitly state that it is not the future Linux/CUDA large-training lock.

The storage snapshot observed 39,564,700 available 1,024-byte blocks
(40,514,252,800 bytes), with the filesystem reporting 96% capacity. Exactly
zero bytes were reserved. This volatile observation is not a future
availability guarantee.

For those reasons the observation does not populate F150, F151, or F152. The
hardware is not selected or reserved for production; the environment is not a
complete B12 runtime; the external baseline runtime dependencies are absent;
and the current lock explicitly disclaims the large-training role.

## 6. Honest synthetic calibration receipts

Two non-scientific diagnostics were run locally with no random input, domain
data, model, learner, optimizer, inference runner, or external process.

The standard-library receipt hashes 64 MiB of all-zero bytes five times. Every
row produces SHA-256
`3b6a07d0d404fab4e23b6d34bc6696a6a312dd92821332385e5af7c01c421351`.
Observed wall times range from 32,996,958 ns to 33,081,709 ns. These timings
are load-dependent observations, not deterministic ceilings.

The PyTorch receipt applies a fixed 512-by-512 CPU matrix product three times
after enabling deterministic algorithms and one thread. Every output produces
SHA-256
`94816432ec6b2c0dda21ed9420dfad8ea5cf0f6d987dd20fef54500d9825f43d`.
The capture observed `mps_built=true` and `mps_available=false`.

Both receipts are exact, self-digested, and validated by the pure source and
independent package validator. They demonstrate only that the stated tiny
synthetic operations ran and repeated their output bytes. They do not establish
domain-scale throughput, stable timing, peak production memory, filesystem
durability, accelerator access, B12 compatibility, an F104 event weight,
production determinism, or sufficient confirmatory capacity.

## 7. Exact residual field roster

The following ten fields remain open and null:

| Field | Pointer | Exact reason |
|---|---|---|
| F150 | `/compute_and_fairness_plan/hardware` | The observed host is not selected or reserved production hardware. |
| F151 | `/compute_and_fairness_plan/software_environment_sha256` | The observed smoke environment is not the complete B12 production runtime. |
| F152 | `/compute_and_fairness_plan/container_or_lockfile_sha256` | The current lock explicitly disclaims future large-training use. |
| F154 | `/compute_and_fairness_plan/per_run_wall_time_ceiling` | No domain-scale run unit or capacity timing receipt exists. |
| F155 | `/compute_and_fairness_plan/per_run_accelerator_hour_ceiling` | MPS is unavailable and the production accelerator route is not selected. |
| F156 | `/compute_and_fairness_plan/per_run_peak_memory_ceiling` | No whole-method device, host, or persistent-memory receipt exists. |
| F157 | `/compute_and_fairness_plan/per_run_model_evaluation_ceiling` | The B12 run unit is absent and F143/F147 remain open. |
| F159 | `/compute_and_fairness_plan/tuning_compute_allocation` | F147, F104 weights, scalar ceilings, and capacity are absent. |
| F160 | `/compute_and_fairness_plan/final_compute_allocation` | The complete run schedule, F104 weights, scalar ceilings, and capacity are absent. |
| F162 | `/compute_and_fairness_plan/total_compute_ceiling` | F104 weights, both scalar ceilings, all hard axes, and a reservation receipt are absent. |

No numeric ceiling is guessed from the tiny synthetic diagnostics. In
particular, a zero accelerator observation is not promoted into F155, and the
current free disk count is not promoted into a persistent-storage ceiling.

## 8. Why B08 remains open

The accepted B06 contract gives B08 four all-or-nothing requirements:

1. `HARDWARE_AND_RUNTIME_IDENTITY`;
2. `CALIBRATION_WEIGHTS`;
3. `SCALAR_AND_HARD_AXIS_CEILING_VALUES`; and
4. `CAPACITY_RESERVATION_RECEIPT`.

The future per-domain records must populate the accepted
`B06-{DOMAIN}-FUTURE-B08-WEIGHTS-V1` and
`B06-{DOMAIN}-FUTURE-B08-SCALAR-CEILING-V1` identifiers for
`ONLINE-RETAIL-II` and `PHYSIONET-CHALLENGE-2012`. The weights must be strictly
positive exact rationals calibrated once on the selected frozen production
environment before test access and shared across methods within a domain.

Each domain must also populate all eight accepted hard-axis IDs:
`WALL_TIME`, `ACCELERATOR_TIME`, `PEAK_DEVICE_MEMORY`, `PEAK_HOST_MEMORY`,
`MODEL_EVALUATION_COUNT`, `PERSISTENT_BYTES`, `FAILURE_COUNT`, and
`PARAMETER_COUNT`. F104 scalar equality is necessary but insufficient; every
hard axis is independently binding.

This package satisfies none of those four compound requirements. An observed
host class is not a selected and approved production runtime. A synthetic hash
or matrix product is not an event-specific F104 calibration. No scalar or hard
axis is populated. No capacity is reserved, and no accountable resource
receipt exists. B08 therefore remains terminally open even if the three field
values are independently accepted.

The open Test-28 development preregistration contains only a future capacity-
receipt schema. Its actual capacity receipt, freeze receipt, and independent
signoff are absent; its synthetic/development schema is not evidence for this
package or B08.

## 9. Fairness, attempt charging, and failure policy preserved

The accepted F104 formula remains
`C[m,d] = sum_p sum_k n[m,d,p,k] * w[d,k]` over the exact four phases and ten
resource events. Nothing here selects a weight or scalar operand.

Within a domain the primary pair continues to require equal prospective scalar
ceilings, equal hard-axis opportunities, the same frozen group/case/draw
rosters, base checkpoint, precision policy, and metric workload. All scheduled
and failed attempts, author extensions, and unique preprocessing are charged.
Unused allocation is not transferable, realized equality is not claimed, and
no post-result top-up is permitted. Planned and realized use must later be
reported.

## 10. Package and qualification boundary

The candidate package contains exactly:

1. `PROJECT_B08_LOCAL_HOST_CAPACITY_GAP_FREEZE.md`;
2. `src/heterodiff/experiments/b08_local_host_capacity_gap.py`;
3. `research/fixtures/manuscript_v3_b08_local_host_capacity_gap_freeze_v1.json`;
4. `research/diagnostics/manuscript_v3_b08_local_host_capacity_gap_freeze_v1.py`; and
5. `tests/unit/test_manuscript_v3_b08_local_host_capacity_gap_freeze_v1.py`.

The source is standard-library-only and pure. It contains exact JSON-native
values and strict built-in-type validators. The package validator uses stable,
no-follow, read-only file access; verifies exact package and predecessor byte
bindings; requires duplicate-free canonical ASCII JSON; independently checks
the three-field scope, ten-field residual roster, count arithmetic, B08 no-go,
synthetic receipt self-digests, and accepted predecessor semantics; and performs
no capture or benchmark.

Hostile tests mutate only disposable copies. They cover field additions,
removals and substitution; false B08/capacity claims; changed counts; changed
host and synthetic observations; forged receipt self-digests; Boolean/integer
aliases; malformed/noncanonical/duplicate-key JSON; missing, extra, reordered,
symlinked, hard-linked, and permission-changed files; and static source-effect
surface exclusions.

Neither validation nor testing modifies an accepted predecessor. No source
file under `sources/`, tracker, ledger, result, runtime identity manifest,
capacity reservation, or operational approval is created or edited.

## 11. Authority and nonclaims

The standing instruction authorizes bounded offline local construction and
synthetic qualification only. It does not authorize network access, external
contact, purchasing, cloud or external model execution, data access, test-data
opening, hardware or storage reservation, scientific execution, entropy,
training, inference, claim promotion, release, submission, or tracker/ledger
mutation.

The package does not claim that capture time is externally attested, that the
private device digest authenticates an owner or institution, that the current
host will remain available, or that this host can execute the confirmatory
campaign. It does not self-review. A separate independent read-only review is
required before any three-field registration; a later actual B08 capacity
package requires its own independent review.

## 12. Evidence-ready bounded registration wording

If and only if a separate independent review accepts the exact five-file
package with no unresolved material finding, a later authorized integration
may record only:

> F153, F158, and F161 close through the additive B08 local-host capacity-gap
> policy package. F153 is the exact CPU-only, single-thread, fail-closed
> deterministic policy `B08_CPU_SINGLE_THREAD_FAIL_CLOSED_DETERMINISM_V1`;
> F158 is the exact zero empirical-pilot allocation
> `B08_ZERO_EMPIRICAL_PILOT_DISTRIBUTION_FREE_B07_V1`; and F161 is the exact
> zero failure reserve `B08_ZERO_FAILURE_RESERVE_NO_RERUN_NO_REPLACEMENT_V1`.
> PRE moves from 33 open / 133 closed to 30 open / 136 closed; POST remains
> 1 open / 5 closed; total fields move from 34 open / 138 closed to 31 open /
> 141 closed. F150--F152, F154--F157, F159--F160, and F162 remain open and
> null. B08 remains open because production hardware/runtime identity, F104
> calibration weights, scalar and all eight hard-axis ceilings, and an actual
> capacity reservation/resource receipt are absent. Blockers remain 7 open /
> 5 closed, Gate A remains 5/8, Formal Tests and all results remain unchanged,
> and no runtime, data, training, science, claim, release, or submission occurs.

That paragraph is prospective registration text, not a tracker edit,
independent acceptance, capacity receipt, or execution authority.
