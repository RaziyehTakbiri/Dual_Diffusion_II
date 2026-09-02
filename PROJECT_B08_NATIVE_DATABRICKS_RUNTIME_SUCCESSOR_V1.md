# B08 native AWS Databricks runtime successor v1

**State:** `DRAFT_DATA_FREE_NATIVE_RUNTIME_GOVERNANCE_SUCCESSOR_ZERO_DELTA`  
**Policy:** `B08_NATIVE_DBR_EFFECTIVE_RUNTIME_CAPTURE_V1`  
**Profile ID:** `b08-databricks-aws-native-dbr17.3-linux-x86_64-cpu-py312`  
**Profile schema:** `heterodiff-b08-databricks-native-runtime-profile-v1`  
**Capture-receipt schema:** `heterodiff-b08-databricks-native-runtime-capture-v1`  
**Execution role:** final-study research-compute candidate  
**Application-deployment role:** none  
**Scientific or confirmatory execution:** none  
**Eligible field, blocker, Formal-Test, or timetable delta:** zero

## 1. Decision and exact supersession boundary

The selected prospective B08 implementation route is native AWS Databricks
Runtime with no Databricks custom container and no Amazon ECR image used as the
scientific Python runtime. This document supersedes only the still-draft active
Docker/ECR implementation candidate described by
[`PROJECT_B08_DATABRICKS_AWS_RUNTIME_SUCCESSOR_V1.md`](PROJECT_B08_DATABRICKS_AWS_RUNTIME_SUCCESSOR_V1.md).
It does not delete, rewrite, invalidate, or reinterpret that file, the accepted
AWS Databricks qualification-readiness package, the existing-cluster no-go, the
local-host capacity no-go, any receipt, or any other historical artifact. Those
records remain immutable evidence of what was proposed or observed at their
respective checkpoints.

The following route-specific requirements are prospectively retired from the
active native-runtime candidate:

- building or qualifying `databricks/container/Dockerfile.dbr17.3-cpu`;
- resolving an offline container wheelhouse solely to build that image;
- selecting and digest-binding a Databricks base image;
- building, pushing, or pulling a final custom-image digest;
- provisioning private Amazon ECR for the scientific runtime;
- supplying an EC2 instance profile solely for private-ECR image pull; and
- proving Docker, Container Services, `ENTRYPOINT`, or `CMD` behavior.

The existing Dockerfile, unresolved requirement input, lock/wheel-manifest
template, runtime-profile candidate, tests, and related prose remain historical
or draft project artifacts. They are not evidence for the native candidate and
must not be represented as a resolved lock, built image, operational receipt,
or B08 closure.

This successor is additive and prospective. It performs no Databricks or AWS
call, creates no cluster or storage, accesses no data, executes no capture or
calibration, and authorizes no training, inference, result inspection, or
scientific entropy. It closes no field, blocker, Formal Test, result slot, or
timetable task.

## 2. Controlling requirements that remain unchanged

Native runtime adoption changes the environment-packaging mechanism, not the
scientific or custody obligations. The following remain controlling:

1. The [main execution preregistration](manuscript_v3/execution_preregistration.md)
   still requires hardware,
   software/environment digests, precision, deterministic settings, parameter
   counts, optimizer budgets, tuning trials, per-run resource ceilings, exact
   pilot/tuning/final allocations, failure reserve, matched-compute accounting,
   and complete planned/realized compute reporting before result promotion.
2. The accepted [B08 partial freeze](PROJECT_B08_LOCAL_HOST_CAPACITY_GAP_FREEZE.md)
   retains F153 exactly as
   `B08_CPU_SINGLE_THREAD_FAIL_CLOSED_DETERMINISM_V1`, F158 as zero empirical
   pilot allocation, and F161 as zero additional failure reserve. No native DBR
   default may weaken or silently reinterpret those closed fields.
3. The [Test-28 production contract](research/preregistrations/cp50_test28_mixed_initializer_v26.md)
   still requires an attempt- and freeze-bound
   exact dependency/runtime record, loaded source and compiled-ABI closure,
   complete durable raw retention, and its exact capacity predicate. In
   particular, the combined reservation floor remains
   `1,133,871,366,144` bytes unless Test 28 is separately and formally
   superseded. Free `/local_disk0`, DBFS, a bucket, or a Unity Catalog Volume is
   not by itself the already-frozen physical reservation receipt.
4. Fixed hardware/topology, accountable availability, no automatic scientific
   retry or result-dependent top-up, complete-run calibration, F104 weights,
   hard resource axes, capacity feasibility, durable evidence handoff, and
   independent review remain required.
5. Under the [completion timetable](PROJECT_COMPLETION_TIMETABLE.md), B08 and
   Wave 2 remain open. Native runtime selection supplies no authority
   to mount, list, open, or copy study or test data.

If the native service cannot expose evidence satisfying a controlling frozen
predicate, the result is a scoped `NO_GO`. Convenience, raw free capacity, or a
successful notebook import must not be promoted into compliance.

## 3. Exact native-runtime candidate invariant

An eligible candidate must be one exact AWS Databricks classic dedicated job-
compute configuration. Before any data-free qualification run, the effective
configuration after policy resolution must be frozen and must establish all of
the following without relying on a custom container:

- exact workspace/region, accountable operator, cluster-policy identity and
  revision, DBR release and build, runtime engine, and access mode;
- fixed driver/worker instance types and counts, fixed CPU/memory topology,
  autoscaling disabled, on-demand only, no spot/fleet fallback, no GPU, and
  Photon disabled;
- one exact operating-system, kernel, architecture, Java, Scala, Spark, Python
  implementation/version/ABI, and Python executable identity for every
  scientific process;
- an exact native installed-distribution inventory and payload closure,
  including NumPy, SciPy, threadpool controls, PyTorch, standard-library and
  compiled-library/ABI identities relevant to the production path;
- an exact immutable project-source or project-wheel manifest and all B12
  primary/comparator/baseline/adapter/runner/ledger/recomputation dependencies;
- no user-site, notebook-scoped, mutable-tag, editable, unrecorded, or
  run-time network installation in the frozen candidate;
- driver and worker equivalence, or an exact predeclared and qualified
  difference manifest;
- the retained F153 environment and PyTorch deterministic controls on every
  scientific process; and
- a single authorized, synchronous Jobs run with fixed timeouts, no queueing,
  overlap, schedule, trigger, repair, retry, partial rerun, replacement,
  detached child, dynamic resize, speculation, or silent fallback.

The profile ID declares the prospective DBR 17.3/Linux/x86-64/CPython-3.12/CPU
target family. It does not attest an exact DBR build, effective OS/kernel,
architecture, Python executable, package version, or node type. Those are
external evidence values. The previously reported cluster and environment-
variable output are useful operator inputs but are not authenticated runtime,
policy, worker-equivalence, capacity, or reservation receipts.

## 4. Native interpretation of F151 and F152

The machine schema already names F152
`/compute_and_fairness_plan/container_or_lockfile_sha256`; therefore a custom
container is not structurally required. Under this successor the two fields
have distinct native meanings:

| Field | Native-runtime interpretation | Evidence boundary |
|---|---|---|
| F151 | SHA-256 of one canonical, observed production-environment manifest binding the effective cluster/policy configuration, DBR build, OS/kernel/architecture, Python/Java/Scala/Spark identities, deterministic environment, installed runtime, source closure, loaded payloads, compiled ABI map, and driver/worker relation. | Remains `OPEN` and null until the complete external capture is validated and independently accepted. |
| F152 | SHA-256 of one canonical native production dependency-lock record binding the exact installed distributions and payload hashes, every project-provided wheel/artifact and hash, dependency provenance, native-versus-project ownership, and its equality to the environment observed in F151. | Remains `OPEN` and null until the lock is complete, matches the frozen native candidate, and is independently accepted. |

A package-name list, `pip freeze` alone, notebook display, desired requirements
file, unresolved template, cluster UI screenshot, DBR marketing version, or
source-only digest is insufficient for either field. F151 and F152 must refer to
the same production candidate and must fail closed on native package drift,
notebook-scoped installs, changed init scripts, changed policy values, loaded
payload mismatch, or ABI mismatch.

Project-provided packages may be installed before the freeze only through the
separately governed native bootstrap path. Their exact artifacts and hashes
must appear in F152 and in the observed F151 manifest. The native DBR packages
need not be reinstalled merely to imitate a wheelhouse; they must instead be
observed, payload-bound, and qualified in place.

## 5. F153 is retained without reinterpretation

The following exact environment remains required on the driver and every
worker process:

| Variable | Exact value |
|---|---|
| `BLIS_NUM_THREADS` | `1` |
| `MKL_NUM_THREADS` | `1` |
| `NUMEXPR_NUM_THREADS` | `1` |
| `OMP_NUM_THREADS` | `1` |
| `OPENBLAS_NUM_THREADS` | `1` |
| `VECLIB_MAXIMUM_THREADS` | `1` |
| `LANG` | `C` |
| `LC_ALL` | `C` |
| `TZ` | `UTC` |
| `PYTHONHASHSEED` | `0` |
| `PYTHONDONTWRITEBYTECODE` | `1` |
| `PYTHONNOUSERSITE` | `1` |
| `PYTHONSAFEPATH` | `1` |
| `PYTHONUTF8` | `1` |
| `CUDA_VISIBLE_DEVICES` | exact present empty string |

PyTorch deterministic algorithms remain enabled with `warn_only=false`, one
intra-operation thread, one inter-operation thread, disabled cuDNN benchmarking,
and no CUDA or MPS route. A requested Spark environment is not evidence of the
effective Python process environment. The data-free capture must observe the
values before project import and again in the loaded runtime on every eligible
process surface. Unsupported or nondeterministic behavior is terminal `NO_GO`;
it does not authorize fallback or replacement.

## 6. Prospective stage gates

### Stage N0 — additive native package readiness

Before operator action, a machine-readable native capture template, hash-first
validator, data-free capture helper, and focused hostile tests must exist. They
must encode this successor, distinguish requested from effective configuration,
leave all operational evidence null, and validate from both the project root
and an unrelated working directory. N0 can establish construction readiness
only; it cannot close F151, F152, B08, or any timetable task.

The planned N0 identities are exact:

- profile ID `b08-databricks-aws-native-dbr17.3-linux-x86_64-cpu-py312`;
- profile schema `heterodiff-b08-databricks-native-runtime-profile-v1`;
- initial profile state `DRAFT_UNRESOLVED_F152_LOCK`;
- capture schema `heterodiff-b08-databricks-native-runtime-capture-v1`;
- template
  `requirements/b08-databricks-aws-dbr17.3-x86_64-cpu-py312.native-runtime-profile.template.json`;
- validator/source
  `src/heterodiff/experiments/b08_databricks_native_runtime_profile.py`;
- operator capture helper
  `research/diagnostics/b08_databricks_native_runtime_capture_v1.py`; and
- focused same-stem profile and capture test modules.

Their first eligible transition is
`VALIDATE_NATIVE_PROFILE_TEMPLATE`. Validation must leave the F152 lock
unresolved and operational evidence null; it must not manufacture eligibility.

### Stage N1 — accountable inputs and freeze

Through approved administrative channels, obtain the non-secret identities and
authorities for the workspace, region, policy revision, fixed node topology,
on-demand capacity, DBR build, availability window, spending ceiling, durable
logging, native bootstrap artifacts, and the Test-28 storage-reservation design.
Secrets remain outside project artifacts. Freeze and hash the canonical job,
cluster, policy, bootstrap, source, native-lock, log-delivery, and reservation-
request inputs before launch. Any missing value returns `HOLD`.

### Stage N2 — one data-free native capture

Create new classic dedicated job compute from the frozen definition without
mounting or inspecting study/test data. Perform only fixed, nonrandom,
synthetic environment checks. Capture effective policy/cluster/job values,
hardware, driver and workers, DBR/native runtime, installed payloads, source and
ABI closure, F153 controls, retry/fallback controls, logs, and the accountable
capacity/storage receipts. Validate the local receipt, copy it under exclusive
no-clobber semantics to the approved durable evidence destination, reopen and
rehash it there, and write the attempt-bound commit manifest last before the
task returns. A started attempt is charged under the frozen lifecycle.

### Stage N3 — post-termination capture and independent review

After the task returns, capture the terminal Jobs result, lifecycle log binding,
and distinct job-compute termination receipt. An independent reviewer must
recompute all raw and semantic digests, inspect the exact bytes from two working
directories, verify the native F151/F152 relation and every retained F153
control, confirm absence of data/science and retry/repair/replacement, and verify
the complete hardware, availability, custody, and Test-28 storage predicates.
The strongest eligible disposition is
`GO_NATIVE_DBR_ENVIRONMENT_FROZEN_FOR_SEPARATE_DATA_FREE_F104_CALIBRATION`.
It is not B08 closure.

### Stage N4 — separately authorized data-free calibration

Only an accepted N3 `GO` permits a separately frozen and independently reviewed
F104/complete-run calibration. N4 must derive the twenty domain/event weights,
per-run ceilings, eight hard axes, tuning and final allocations, and total
compute ceiling on the exact N3 candidate. It may not use study/test data,
scientific seeds, outcomes, or result-dependent adaptation. N3 evidence cannot
be reused as proof that any calibration value or ceiling exists.

## 7. Exact current blockers

At publication of this draft, all of the following remain unresolved:

- no independently accepted native-runtime machine schema, capture template,
  helper, validator, or lifecycle successor is registered as active evidence;
- no complete native dependency-lock record or observed installed-payload/ABI
  manifest exists;
- no sanitized effective cluster, job, or policy capture is accepted;
- no driver/worker equivalence, native package stability, or complete B12
  production-runtime receipt is accepted;
- no durable in-task handoff, terminal-run receipt, compute-termination receipt,
  or independent N3 review exists;
- no administrator-authenticated availability, compute-capacity, or exact
  Test-28 physical-storage reservation receipt exists;
- no complete-run calibration supplies F104 weights or F154--F157/F159--F160/
  F162; and
- the prior [existing-cluster no-go](PROJECT_B08_DATABRICKS_AWS_EXISTING_CLUSTER_PREFLIGHT_NO_GO.md)
  is historical, but native adoption alone
  does not convert that cluster or any replacement cluster to `GO`.

Therefore F150--F152, F154--F157, F159--F160, and F162 remain `OPEN` and null;
F153, F158, and F161 retain their accepted values; B08 and Wave 2 remain open;
and the timetable tasks for hardware/Test-28 storage/compute reservation,
environment locks/resource ceilings, and B08 closure remain unchecked.

## 8. Exact next operator sequence

The next eligible sequence is strictly ordered:

1. Complete `VALIDATE_NATIVE_PROFILE_TEMPLATE` and independently review the N0
   native schema/helper/validator and native Jobs-lifecycle package; register
   only a zero-delta readiness result.
2. Obtain every N1 administrator input, including the exact native bootstrap
   method and a storage design capable of proving the unchanged Test-28
   reservation predicate; do not place secrets in the repository.
3. Resolve and independently review the exact F152 native dependency-lock
   record, then freeze the project artifact
   hashes, source manifest, effective cluster/policy/job definitions, init or
   bootstrap bytes, log sink, availability window, and reservation request.
4. Run all local hash-first and hostile validation before any Databricks launch.
5. Request explicit authority for exactly one
   `CAPTURE_NATIVE_RUNTIME_DATA_FREE` N2 attempt; create new job compute from
   the frozen definition and perform no study/test-data or scientific operation.
6. Complete the durable in-task handoff before success, then collect the
   terminal Jobs and compute-termination evidence without retry or repair.
7. Obtain independent N3 review. On any mismatch, terminalize the scoped
   `NO_GO`; do not patch the receipt or launch a replacement attempt.
8. Only after N3 `GO`, construct, authorize, execute, and independently review
   the separate N4 data-free calibration package.
9. Propose B08 field and timetable transitions only from one coherent,
   independently accepted package containing the exact external evidence.

No later step may be treated as authority to skip an earlier gate. Until N0 is
independently accepted, the immediate project action is offline construction
and review only.

## 9. Zero-delta statement

This governance successor records a route decision and an exact future evidence
contract only. It creates no operational fact and makes no change to the
authoritative timetable or evidence ledger. An independent review must inspect
the final bytes and cross-file identities before this document can be cited as
an accepted native-runtime readiness control.
