# B08 AWS Databricks runtime successor v1

**State:** `DRAFT_DATA_FREE_CONSTRUCTION_ONLY_ZERO_DELTA`  
**Runtime profile:** `b08-databricks-aws-dbr17.3-linux-x86_64-cpu-py312`  
**Execution lifecycle:** `B08_CLASSIC_JOB_COMPUTE_SINGLE_AUTHORIZED_RUN_LIFECYCLE_V1`

## Purpose

This additive successor package prepares the Linux x86-64 runtime and bounded
Databricks Jobs lifecycle needed for later B08 qualification.  It does not
rewrite or invalidate the historical macOS ARM reference profile.  It does not
authorize data access, calibration, training, inference, capture, reservation,
or scientific execution, and it closes no field, blocker, formal test, result
slot, or timetable task.

## Observed compatibility facts

The data-free successor preflight observed all of the following on the target
AWS Databricks compute:

- Databricks Runtime `17.3.x-scala2.13`;
- `DATA_SECURITY_MODE_DEDICATED`;
- Linux `x86_64` with 32 logical CPUs;
- Python `3.12.3` before custom-container activation;
- the exact 15-variable deterministic environment, including an explicitly
  present empty `CUDA_VISIBLE_DEVICES`; and
- no Spark, study/test-data, calibration, capture, Databricks REST, or network
  operation performed by the preflight.

These observations establish only a compatible construction surface.  They do
not establish a frozen production image, dependency lock, worker equivalence,
capacity, durability, lifecycle, or administrator authority.

## Successor construction components

The successor is complete only when all of the following versioned components
exist and validate together:

1. a Linux x86-64 CPython 3.12 runtime-profile record with exact DBR, base-image,
   final-image, dependency-lock, wheel-manifest, project-wheel, and source
   digests;
2. a single-platform custom image derived from a full immutable digest of the
   Databricks `17.3-LTS` standard base and installed only from a captured,
   hash-verified offline wheelhouse;
3. a secret-free Databricks Jobs definition satisfying the single-authorized-
   run lifecycle contract;
4. a same-region private Amazon ECR repository whose pull authorization is
   supplied through the compute instance profile, without credentials in the
   repository;
5. a successful data-free launch whose effective cluster JSON preserves the
   final `repository@sha256:<digest>` image reference;
6. durable log delivery and attempt-bound evidence handoff completed before the
   sole synchronous job task returns success; and
7. administrator-completed capacity, availability, and physical-storage
   reservation evidence followed by independent Stage-C review.

## Lifecycle successor

`autotermination_minutes` is captured for audit but is not required to be zero
and is not accepted as continuity, durability, or completion evidence.  The
eligible execution surface is new classic dedicated job compute created from
one hash-bound job definition for exactly one manually authorized run.

The job definition must disable queueing, schedules, event triggers, continuous
execution, overlapping runs, task and job retries, retry-on-timeout, repairs,
and partial reruns.  It must set `max_concurrent_runs=1`, contain exactly one
synchronous task, and impose explicit positive timeout bounds within the
approved availability window.  Existing all-purpose compute, detached or
background processes, silent restart, resize, replacement, spot or fallback
capacity, and source or configuration drift are ineligible.

Any timeout, cancellation, compute loss or replacement, retry or repair
history, non-success result, or definition mismatch is terminal `NO_GO`.  A
started attempt remains charged and creates no successor attempt.

## Transient custody

`/tmp` and `/local_disk0` are private transient staging only.  Before the sole
job task returns success, the local receipt must pass its independent local
validation, be copied under exclusive no-clobber semantics into the approved
private durable evidence channel, be reopened and rehashed there, and be
committed by an attempt-bound manifest written last.  Notebook output, Jobs
output, Workspace files, Git, DBFS, Unity Catalog Volumes, `/tmp`, and
`/local_disk0` are not physical storage-reservation evidence.

## Current blockers

- The Linux dependency lock and wheel manifest are unresolved.
- No immutable custom image has been built or pushed.
- No approved ECR repository or final image digest has been supplied.
- The current production runtime bindings still select the historical macOS
  ARM profile and require additive successor integration.
- No canonical job definition, durable handoff receipt, or post-termination
  lifecycle receipt has been accepted.
- Durable logging and the administrator storage reservation remain absent.

Until every successor component is complete and independently accepted, the
controlling disposition remains
`DATABRICKS_AWS_QUALIFICATION_INCOMPLETE_B08_REMAINS_OPEN`.
