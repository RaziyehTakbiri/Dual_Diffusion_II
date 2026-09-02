# B08 AWS Databricks data-free production qualification bundle

**Reported:** 2026-09-02  
**Candidate state:** `B08_DATABRICKS_AWS_QUALIFICATION_CONTRACT_READY_ZERO_DELTA`  
**Target role:** final study execution environment  
**Application-deployment role:** none  
**Scientific or confirmatory execution:** none  
**Proposed field, blocker, Formal-Test, or timetable delta:** zero

## 1. Decision and boundary

AWS Databricks is the intended platform for qualifying the final study
execution environment. This is a research-compute qualification, not an app,
website, model-serving endpoint, dashboard, or other deployment project.
Interactive convenience is not evidence: only the frozen cluster, runtime,
storage, and independently reviewed receipts described below may later support
B08.

The user has confirmed that AWS Databricks is available. That confirmation does
not by itself authenticate workspace administration, select a cluster, reserve
capacity, approve expenditure, freeze a runtime, or prove storage. This document
therefore defines an operator contract only. It performs no provider action and
does not claim that any production resource exists.

The current accepted project state remains controlling:

- the [B08 local-host partial freeze](PROJECT_B08_LOCAL_HOST_CAPACITY_GAP_FREEZE.md)
  closes only F153, F158, and F161;
- the [Wave-2 capacity preflight](PROJECT_B08_WAVE2_CAPACITY_PREFLIGHT_NO_GO.md)
  proves that the local Mac cannot supply the required capacity;
- the [F104 formula freeze](PROJECT_F104_MATCHED_TOTAL_COMPUTE_FORMULA_FREEZE.md)
  fixes exact accounting semantics but supplies no measured weight or ceiling;
- the [B06 baseline and matched-compute freeze](PROJECT_B06_BASELINE_IDENTITIES_MATCHED_COMPUTE_FREEZE.md)
  fixes prospective event-count budgets but leaves hardware, runtime, weights,
  ceilings, and capacity to B08; and
- the current [Test-28 production contract](research/preregistrations/cp50_test28_mixed_initializer_v26.md)
  supplies the exact storage predicate used below.

Nothing in this bundle permits study-data access, test-data access, scientific
entropy, training, inference, result inspection, calibration, claim promotion,
release, or submission. No study or test path may be mounted, listed, opened, or
copied during this qualification.

## 2. Required Databricks execution profile

The candidate must be one exact, reproducible AWS Databricks classic-compute
configuration with all effective values captured after policy resolution. The
recommended and required profile is:

1. **Classic compute.** Serverless compute is not eligible for this contract.
2. **Dedicated access.** The study cluster must not be a shared, multi-user
   execution surface. The accountable study operator or service identity must
   be explicit in the private administrative record.
3. **Fixed size.** Driver type, worker type, and worker count must be explicit
   constants. Autoscaling is disabled. No value is guessed in this document.
4. **On-demand capacity only.** Spot, preemptible, fleet fallback, and mixed
   on-demand/spot policies are disabled. Provider rescheduling or capacity-type
   substitution cannot silently change the environment.
5. **CPU route only.** No GPU instance or GPU runtime is eligible. CUDA and MPS
   are disabled in accordance with accepted F153.
6. **Photon disabled.** The execution engine must not silently substitute a
   Photon path for the frozen CPU software path.
7. **Pinned Databricks Runtime.** An exact DBR version and build identity must
   be supplied by the administrator and captured; `latest`, an unversioned
   channel, or an assumed default is ineligible.
8. **Immutable custom container.** The exact custom image must be addressed and
   verified by immutable content digest, not by a mutable tag. Its source/base
   lineage and the production dependency lock must be bound into the capture.
9. **Fixed process topology.** Every scientific process remains CPU-only and
   single-threaded. Any allowed multi-process or multi-worker topology must be
   explicitly frozen and must not change dynamically during a run.
10. **No automatic scientific retry.** Job retry count is zero. Speculative
    execution, task duplication, fallback, replacement, and post-result top-up
    are disabled or made terminally detectable. A provider interruption or
    unsupported deterministic operation terminates the scheduled attempt under
    the accepted failure policy; it does not create a replacement attempt.

This profile is a selection rule, not a claim that an unspecified Databricks
node type, worker count, DBR version, memory size, lease duration, or budget is
sufficient. Those values must come from the user/administrator and must survive
the complete-run qualification. There is no authority here to invent them.

## 3. Deterministic-control contract

The effective driver and worker environments must reproduce accepted F153,
`B08_CPU_SINGLE_THREAD_FAIL_CLOSED_DETERMINISM_V1`. At minimum, every eligible
study process must capture and enforce:

| Control | Exact value |
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
| `CUDA_VISIBLE_DEVICES` | exact empty string |

PyTorch must use deterministic algorithms with `warn_only=false`, one
intra-operation thread, one inter-operation thread, and disabled cuDNN
benchmarking. Any unavailable, unsupported, or nondeterministic operation is a
terminal pre-execution no-go. Warning-only downgrade, accelerator fallback,
alternate implementation, retry, and replacement are forbidden.

The cluster policy, cluster JSON, job definition, Spark configuration, init
scripts, container, and effective process environment must agree. A value in a
requested cluster specification is insufficient when the effective runtime
differs. The capture must also expose any provider or Spark mechanism capable
of retrying, speculating, duplicating, rescheduling, or changing a task so that
the independent review can confirm fail-closed behavior.

## 4. Storage reservation predicate

The Test-28 storage requirement is exact:

| Reservation component | Required bytes |
|---|---:|
| Exclusive destination | 1,099,511,627,776 |
| Separate auxiliary/metadata | 34,359,738,368 |
| **Combined effective reservation** | **1,133,871,366,144** |

Both components must be established on one qualified storage root and one
filesystem. The reservation evidence must show all of the following:

- destination and auxiliary reservations are exclusive and disjoint;
- the full applicable floors are physically allocated as non-sparse storage;
- an enforced quota meets the applicable floors both before and after the
  reservation operation;
- at least 4,096 inodes remain available after reservation;
- the two components are same-root and same-filesystem;
- bytes are not double-counted against another reservation or quota;
- reserved objects are consumed in place rather than replaced by unreserved
  paths;
- the reservation remains in force through the required commit boundary;
- filesystem identity, reservation identity, ownership, term, and durability
  checks are recorded; and
- all frozen filesystem/reservation operations pass without symlink, hardlink,
  overwrite, or cross-filesystem substitution.

### 4.1 Databricks and AWS storage nonclaim

A Databricks Unity Catalog Volume, DBFS path, cloud-object prefix, bucket,
catalog entry, free-space display, billing entitlement, or logical quota is not
by itself proof of this physical reservation. In particular, an empty object
prefix does not preallocate future bytes, object storage does not expose the
required inode predicate, and a Volume's access-control record does not prove
exclusive non-sparse allocation on one filesystem.

The workspace/storage administrator must provide an accountable reservation
mechanism for a root on which every frozen predicate above is meaningful and
verifiable. The Databricks cluster must be able to use that root without
silently redirecting mandatory study artifacts to ephemeral driver storage or
another object prefix. Administrative assurance must be accompanied by the
operational before/after, quota, allocation, filesystem, inode, exclusivity,
and durability receipts; a prose assurance alone is insufficient.

Databricks log delivery may additionally target an administrator-controlled
object-storage location for audit retention. That copy does not count toward
the combined storage floor unless it is itself within the qualified root and
all predicates are proved. If AWS Databricks cannot expose or administratively
attest a storage root meeting every predicate, this candidate terminates
`NO_GO_STORAGE_RESERVATION_UNPROVEN`; a UC Volume or bucket must not be promoted
as a substitute.

## 5. Stage A — user and administrator inputs

Before cluster construction, the user and the accountable Databricks/AWS
administrator must supply the following exact values through an approved secure
administrative channel. Secrets must never be placed in this document, a
notebook, a cluster JSON export, a log, or the public evidence package.

- confirmation that the target is final study execution, not app deployment;
- accountable workspace and infrastructure owners and their authority scopes;
- the exact AWS region and Databricks workspace identity in a sanitizable form;
- the exact classic-compute policy identity and immutable policy revision;
- the exact dedicated-access setting;
- exact driver type, worker type, fixed worker count, and resulting CPU/memory
  capacity;
- explicit on-demand-only and no-autoscaling configuration;
- explicit CPU-only, no-GPU, no-Photon configuration;
- the exact DBR version/build;
- the immutable custom-container digest and production lock digest;
- approved availability window and retention window;
- an approved spending ceiling and accountable billing/cost-center owner;
- the qualified storage-root design and the administrator responsible for the
  reservation receipt;
- the exact non-secret log-delivery configuration and custodian;
- the source/package transfer method that cannot import study or test data; and
- approval to perform only the data-free environment capture described here.

No node type, runtime version, worker count, duration, reservation technology,
or budget value is defaulted by this contract. Missing values make Stage A
incomplete. Tokens, passwords, secret keys, role credentials, signed URLs, and
private connection material remain outside all project artifacts.

## 6. Stage B — frozen capture bundle

After Stage A is complete, construct the candidate environment without mounting
or opening any study/test dataset. Freeze first, then collect one content-bound
capture bundle containing at least the following.

### 6.1 Effective cluster and policy capture

- sanitized export of the effective cluster JSON after policy resolution;
- sanitized export of the immutable cluster-policy revision;
- effective dedicated-access, fixed-size, on-demand, no-autoscale, no-spot,
  no-GPU, and no-Photon values;
- driver/worker instance types and counts, observed CPU identities, observed
  memory, and confirmation that no accelerator is exposed;
- workspace, cluster, policy, and administrative reservation identities in the
  permitted sanitized or domain-separated form;
- effective Spark and job retry/speculation/fallback controls;
- exact init-script bytes and SHA-256 digests; and
- cluster event-log delivery configuration plus evidence that driver, executor,
  init-script, and cluster lifecycle logs reach the declared durable sink.

The sanitized export must remove secrets but retain every scientific and
qualification-relevant effective value. If a private full export is needed for
administrative custody, publish only its cryptographic binding and an exact
redaction manifest; do not copy secret bytes into this project.

### 6.2 Runtime and source capture

- exact DBR release/build identity;
- custom-container manifest and immutable image digest;
- complete production dependency lock and canonical digest;
- OS, architecture, kernel, Python implementation/version/ABI, JVM, Spark,
  Scala, framework, standard-library, NumPy, SciPy, and compiled-ABI manifests;
- complete installed-distribution roster and file/payload closures;
- complete project-source manifest and immutable source digest;
- every B12 primary, comparator, baseline, author extension, adapter, runner,
  ledger, measurement, and independent-recomputation dependency;
- effective driver and worker environment variables;
- a pre-import receipt followed by a loaded-source/runtime receipt; and
- an operation-level receipt showing that the F153 controls are actually
  enforced across the complete no-data runtime surface.

A custom-image tag, desired package list, notebook display, or partial driver
manifest is not a production-runtime receipt. Driver and worker payloads must
match, or their intended differences must be declared and qualified exactly.

### 6.3 Capacity and availability capture

- accountable host/cluster availability or reservation receipt for the approved
  study window;
- accountable compute-capacity receipt showing that the fixed environment can
  support the complete accepted B06 schedule;
- storage administrator's signed or otherwise authenticated reservation record;
- exact storage-root and filesystem identities;
- exact destination and auxiliary reservation identities;
- before/after physical-allocation, quota, free-capacity, and inode evidence;
- proof of exclusivity, disjointness, same-root/same-filesystem placement,
  non-sparse allocation, no double counting, retention, and durability; and
- a closed manifest binding all administrative and operational receipts to the
  exact cluster/runtime candidate.

The current local shortfall must not be reused as a Databricks capacity value.
The Databricks candidate must produce its own observed and accountable receipts.

### 6.4 Data-free qualification record

The capture may execute deterministic environment checks with fixed, synthetic,
nonrandom inputs only after the environment bytes are frozen. It must record
that no dataset, test split, scientific seed, model checkpoint, training path,
inference path, or outcome was accessed. These checks establish environment
identity and control enforcement only. They are not F104 calibration, complete-
run timing, a resource ceiling, or scientific execution.

## 7. Stage C — independent review gate

An independent reviewer must reopen the exact capture bytes and recompute every
raw and semantic digest from both the project root and an unrelated working
directory. The reviewer must verify:

1. all Stage-A inputs are present without secret disclosure;
2. the effective cluster is classic, dedicated, fixed-size, on-demand, CPU-only,
   non-Photon, and non-autoscaling;
3. DBR, custom container, source, lock, and complete runtime manifests are exact
   and mutually consistent;
4. every F153 deterministic control is effective on the driver and workers;
5. retries, speculation, fallback, replacement, and dynamic topology changes
   fail closed;
6. the storage receipt proves every frozen predicate and does not substitute a
   UC Volume, bucket, free-space figure, or logical quota for physical
   reservation;
7. compute availability supports the complete B06 schedule;
8. no study/test data, scientific entropy, calibration, training, inference,
   result, or claim entered the bundle; and
9. the candidate remains bound to the exact administrator-approved availability
   and reservation window.

The strongest eligible disposition at this stage is
`GO_DATABRICKS_AWS_ENVIRONMENT_FROZEN_FOR_SEPARATE_DATA_FREE_F104_CALIBRATION`.
It is not B08 closure. Any missing or ambiguous item returns a scoped `NO_GO`,
and no calibration may begin on that candidate.

## 8. Stage D — separate data-free F104 calibration

Only after Stage C returns GO may a new, separately frozen and authorized
calibration package be constructed. Before executing it, predeclare the exact
data-free microbenchmark, input shapes, operation definitions, repetitions,
measurement units, rationalization rule, resource monitors, complete-run unit,
and refusal conditions. Do not use study data, test data, scientific seeds, or
outcomes.

The separate package must calibrate exactly once on the frozen Databricks
environment the strictly positive exact rational weights `w[d,k]` for both
domains and all ten ordered F104 resource-event classes:

1. `BASE_FORWARD`;
2. `BASE_BACKWARD`;
3. `CONDITIONER_FORWARD`;
4. `CONDITIONER_BACKWARD`;
5. `GUIDE_EVALUATION`;
6. `RESAMPLING_STEP`;
7. `ODE_OR_SDE_STEP`;
8. `DATA_ADAPTER_RECORD`;
9. `METRIC_DRAW_EVALUATION`; and
10. `OTHER_DECLARED_OPERATION`.

That produces twenty domain/event weights, not floating-point estimates. Each
weight is shared by methods within its domain and may not be changed per method
or after an outcome. The package must then qualify the complete run unit and
freeze the scalar ceilings plus all eight independently binding hard axes:
wall time, accelerator time, peak device memory, peak host memory, model-
evaluation count, persistent bytes, failure count, and parameter count.

Because the selected route is CPU-only, an exact zero accelerator-hour ceiling
is eligible only after the frozen environment and complete run unit demonstrate
that no accelerator route exists or is used. The calibration must instantiate
the tuning allocation, final-training/confirmatory-inference allocation, and
total compute ceiling from accepted B06 counts, exact F104 weights, every hard
axis, and the accountable reservation. Failed and aborted scheduled attempts
remain charged; no retry, replacement, transfer, resume, or post-result top-up
is created.

Stage D requires its own validator and independent review. Stage-C acceptance
cannot be reused as evidence that any weight, ceiling, or allocation exists.

## 9. Exact residual B08 field roster

This qualification contract leaves all ten residual fields open and null:

| Field | Pointer | Evidence eventually required |
|---|---|---|
| F150 | `/compute_and_fairness_plan/hardware` | Selected Databricks/AWS production-hardware identity bound to accountable availability and reservation evidence. |
| F151 | `/compute_and_fairness_plan/software_environment_sha256` | Complete observed DBR/container/source/runtime manifest and canonical digest. |
| F152 | `/compute_and_fairness_plan/container_or_lockfile_sha256` | Immutable custom-container and production-lock digest matching the selected environment. |
| F154 | `/compute_and_fairness_plan/per_run_wall_time_ceiling` | Pre-test ceiling from the separately qualified complete run unit. |
| F155 | `/compute_and_fairness_plan/per_run_accelerator_hour_ceiling` | Pre-test ceiling from the selected CPU-only route; zero only after qualification. |
| F156 | `/compute_and_fairness_plan/per_run_peak_memory_ceiling` | Peak device-memory, host-memory, and persistent-byte ceilings from complete-run qualification. |
| F157 | `/compute_and_fairness_plan/per_run_model_evaluation_ceiling` | Exact complete-run model-evaluation mapping and per-run ceiling. |
| F159 | `/compute_and_fairness_plan/tuning_compute_allocation` | Exact accepted-grid allocation using weights, scalar/hard-axis ceilings, and reserved capacity. |
| F160 | `/compute_and_fairness_plan/final_compute_allocation` | Exact final-training and confirmatory-inference allocation using the complete schedule and reservation. |
| F162 | `/compute_and_fairness_plan/total_compute_ceiling` | Total scalar and eight-axis ceiling across every scheduled and charged attempt, with feasibility receipt. |

F153 deterministic settings, F158 zero empirical-pilot allocation, and F161
zero failure reserve remain closed exactly as previously accepted. They must not
be reopened, weakened, or silently reinterpreted by a Databricks default.

## 10. Zero-delta and safety statement

This file creates no Databricks cluster, policy, job, volume, bucket, mount,
container, reservation, billing commitment, calibration, receipt, or runtime.
It does not contact AWS or Databricks and contains no credential. It does not
edit the completion timetable, evidence ledger, fixture, validator, or test.

Accordingly:

- F150--F152, F154--F157, F159--F160, and F162 remain `OPEN` and null;
- B08 remains `OPEN`;
- the timetable item `Hardware, Test-28 storage, and compute capacity are
  reserved.` remains unchecked;
- Gate A gains no closure;
- Formal Tests 28 and 29 remain `OPEN`, and Formal Test 30 remains `PENDING`;
- no result slot is populated; and
- no data, runtime, science, claim, release, or submission state changes.

The first future eligible transition is only Stage-C authorization to run the
separate data-free calibration. B08 may close later only through one coherent,
independently accepted package that supplies all four compound requirements:
`HARDWARE_AND_RUNTIME_IDENTITY`, `CALIBRATION_WEIGHTS`,
`SCALAR_AND_HARD_AXIS_CEILING_VALUES`, and
`CAPACITY_RESERVATION_RECEIPT`.

## 11. Data-free capture helper

The bounded operator helper is
`research/diagnostics/b08_databricks_aws_qualification_capture_v1.py`. It uses
only the Python standard library and performs no Databricks REST call, Spark
operation, network request, subprocess launch, DBFS or Unity Catalog
enumeration, calibration, or study-data access. It accepts only:

1. a sanitized, canonical JSON export of the effective cluster;
2. an administrator-completed storage-reservation JSON derived from
   `research/fixtures/manuscript_v3_b08_databricks_aws_admin_storage_reservation_template_v1.json`;
3. the optional immutable container digest in exact
   `sha256:<64-lowercase-hex>` form; and
4. an explicit physical local output path that does not already exist.

For dedicated access, the helper accepts the current Databricks API value
`DATA_SECURITY_MODE_DEDICATED`, its legacy API alias `SINGLE_USER`, and the
project's earlier sanitized-input alias `DEDICATED`. The current API enum is
normalized to `DEDICATED`; the two earlier spellings retain their established
receipt representations so historical receipts remain verifiable. Shared,
standard, automatic, and `NONE` modes fail closed. A raw workspace export must
not be used directly when it contains operator identity, cluster identity,
policy identity, custom organizational tags, or other fields outside the
approved sanitized record.

The two JSON inputs must be canonical ASCII JSON with sorted keys, compact
separators, and exactly one terminal line feed. They must reside in ordinary
physical local-driver custody for capture. `/dbfs/...` and `/Volumes/...`
paths are rejected, as are `/Workspace/...` FUSE paths, symlinks, multiple hard
links, group/world-writable inputs, duplicate JSON keys, nonfinite values,
secret-bearing or private-identity key names, and recognizable credential
values. On Databricks the preferred staging root is a private directory under
`/local_disk0`. A physical `/tmp` file may be used only as transient capture
staging when the no-follow, single-link, non-writable-input and exclusive
`0600` output checks pass; it is never durable evidence and never contributes
to the storage reservation. The receipt must be transferred immediately into
the approved private evidence channel and rehashed there.

The operator runs, from the exact frozen target driver:

```text
python3 b08_databricks_aws_qualification_capture_v1.py \
  --cluster-json /local_disk0/heterodiff-b08/cluster.canonical.json \
  --storage-reservation-json /local_disk0/heterodiff-b08/storage-reservation.canonical.json \
  --container-digest-text sha256:<64-lowercase-hex> \
  --output /local_disk0/heterodiff-b08/b08-databricks-capture.json
```

The output is created once, without clobbering, as a single-link regular file
with mode `0600`, followed by file and parent-directory synchronization. The
operator repeats the same command with `--validate-only` and transfers the
receipt through the approved private evidence channel. The helper records
only allowlisted deterministic environment variables, local platform/Python
facts, and installed distribution name/version pairs. It deliberately does
not authenticate the platform or administrator, and its strongest result is
`REQUIRES_LATER_NORMALIZATION_AND_EXTERNAL_REVIEW`.

The public machine template
`research/fixtures/manuscript_v3_b08_databricks_aws_qualification_template_v1.json`
remains `HOLD_INCOMPLETE` until the returned capture and external
administrative evidence are normalized and independently reviewed. Neither
the capture nor the template permits calibration or closes a field.

## 12. Operator handoff checklist

- [ ] User confirms final-study-execution role and supplies the secure admin
      contact route.
- [ ] User/admin supplies every exact Stage-A value, including an approved
      spending ceiling and study window, without exposing credentials.
- [ ] Admin proves that classic dedicated fixed-size on-demand CPU compute with
      pinned DBR, immutable custom container, no Photon, no GPU, no spot, and no
      autoscaling is available.
- [ ] Admin identifies a storage root capable of satisfying the physical
      reservation and inode predicates; a UC Volume or object prefix alone is
      explicitly rejected.
- [ ] No study/test data is connected or accessed.
- [ ] Cluster/runtime/source bytes are frozen before any qualification check.
- [ ] Sanitized effective cluster JSON and complete log-delivery evidence are
      exported.
- [ ] Complete runtime, deterministic-control, availability, compute, and
      storage-reservation receipts are captured and content-bound.
- [ ] Independent Stage-C review returns GO with no unresolved finding.
- [ ] A new predeclared, separately authorized data-free F104 calibration
      package is frozen only after that GO.
- [ ] Calibration, complete-run ceilings, allocations, validator, and
      independent review complete before any B08 field or timetable mark changes.

Until every applicable box is supported by evidence, the correct disposition
is `DATABRICKS_AWS_QUALIFICATION_INCOMPLETE_B08_REMAINS_OPEN`.
