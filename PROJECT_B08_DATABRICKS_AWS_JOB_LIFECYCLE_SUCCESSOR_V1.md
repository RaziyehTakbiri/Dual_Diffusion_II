# B08 AWS Databricks Jobs-lifecycle successor v1

**State:** `ADDITIVE_DATA_FREE_CONTRACT_READY_ZERO_DELTA`  
**Schema:** `heterodiff-b08-databricks-aws-job-lifecycle-v1`  
**Policy:** `B08_CLASSIC_JOB_COMPUTE_SINGLE_AUTHORIZED_RUN_LIFECYCLE_V1`

## 1. Decision and scope

This package adds a fail-closed record and validator for a lifecycle-bound AWS
Databricks Jobs route. It does not alter or supersede any historical B08
artifact, operational receipt, failed attempt, qualification record, tracker,
or evidence ledger. It performs no Databricks call, network access, filesystem
operation, authentication, reservation, capture, calibration, study/test-data
access, training, inference, or scientific execution.

The package addresses one construction gap: lifecycle continuity is supplied
by new job compute created for and terminated with one authorized Jobs run, not
by requiring `autotermination_minutes=0` on an interactive cluster.
`autotermination_minutes` remains an observed audit value. Zero is neither
required nor accepted as continuity, durability, or successful-termination
evidence.

## 2. Exact eligible invariant

An eligible v1 record binds exactly one manually authorized run to one
secret-free, canonical Databricks Jobs definition that creates new AWS classic
dedicated job compute for that run and contains no existing-cluster reference.
Queueing is false, `max_concurrent_runs=1`, and schedule, continuous, and event
triggers are absent. The definition contains exactly one synchronous,
non-detached task; job and task retry counts are zero; retry-on-timeout,
repairs, partial reruns, restarts, and replacement attempts are false; and both
timeouts are positive, no greater than 86,400 seconds, with the task timeout no
greater than the job timeout. The container image is addressed by exactly one
lowercase `@sha256:<64-hex>` digest, and the canonical job definition, cluster
specification, cluster policy, and source manifest are each SHA-256 bound.

Only original attempt zero is eligible. The observed authorization/run count,
compute identity count, and task-run count are each exactly one. A queued
state, interruption, timeout, repair history, restart, replacement compute,
definition drift, source drift, non-success result, missing termination, or
automatic successor run makes the record ineligible. A started attempt is
charged and supplies no authority for another attempt.

Before the sole task returns, its local receipt is validated and handed off
under exclusive no-clobber semantics to the approved private durable
destination. The durable copy is reopened and rehashed, its positive byte
count and SHA-256 digest equal the local receipt, and an attempt-bound commit
manifest is written last. Durable lifecycle logs then support a terminal
`TERMINATED`/`SUCCESS` run record and a distinct job-compute termination
receipt. Post-termination independent external review remains mandatory.

## 3. Two-phase evidence custody

The lifecycle has two evidence phases because the task cannot itself observe
its later terminal run state or the subsequent compute termination.

1. **In-task handoff.** The private local-driver staging area is transient and
   never counts as durable evidence or storage reservation. The task validates
   its local receipt, performs the exclusive durable copy, reopens and rehashes
   that copy, writes the commit manifest last, and returns only after this
   commit succeeds.
2. **Post-task lifecycle evidence.** The configured durable sink retains the
   lifecycle event log. After the task returns, the terminal run record and
   compute-termination receipt are captured and cryptographically bound. An
   independent reviewer confirms the canonical job/source bindings, original
   attempt, absence of retry/repair/replacement, terminal success, termination,
   and absence of an automatic successor run.

Workspace files, Git, notebook output, Jobs output, `/tmp`, and `/local_disk0`
are not durable evidence under this contract. The approved private durable
destination is represented only by a non-secret binding digest in the record;
credentials, signed URLs, tokens, and private connection material must remain
outside project artifacts.

## 4. Machine contract and dispositions

The canonical empty record is
`research/fixtures/manuscript_v3_b08_databricks_aws_job_lifecycle_template_v1.json`.
Its semantic disposition is `HOLD_INCOMPLETE`; unknown observations remain
`null`, all effects remain zero, and its `record_sha256` covers the canonical
semantic projection excluding only the digest carrier itself.

The pure validator is
`src/heterodiff/experiments/b08_databricks_aws_job_lifecycle.py`. It requires an
exact key set, exact JSON-native scalar types, lowercase SHA-256 digests,
canonical digest agreement, exact fixed nonclaims, and every eligible
predicate above. Unknown keys, omitted keys, booleans passed as integers,
unbounded or invalid timeouts, mutable image tags, any missing evidence, and
any project-effect claim fail closed.

`ELIGIBLE_FOR_DATA_FREE_JOB_LIFECYCLE_REVIEW_ONLY` means only that the supplied
record satisfies this local structural contract. The validator neither
authenticates the record nor queries Databricks. The disposition is not Stage-C
acceptance, execution authority, calibration authority, physical-capacity
proof, scientific evidence, or B08 closure.

## 5. Terminal refusal conditions

The run is terminally ineligible if it is launched from existing/all-purpose,
shared, serverless, scheduled, continuous, event-triggered, queued, or
overlapping compute; if more than one task or run is observed; if any retry,
repair, restart, replacement, detached process, or successor attempt occurs;
if an effective definition or source differs from its frozen digest; if the
image is not digest addressed; if either timeout is absent, nonpositive, above
the policy bound, or ordered incorrectly; or if durable handoff or terminal
lifecycle evidence is incomplete.

Failure, timeout, cancellation, provider interruption, or compute loss does not
restore the one-run budget. No repair, restart, rerun, or replacement is
authorized by this package.

## 6. Additive package roster and project effect

This successor consists only of:

- `PROJECT_B08_DATABRICKS_AWS_JOB_LIFECYCLE_SUCCESSOR_V1.md`;
- `src/heterodiff/experiments/b08_databricks_aws_job_lifecycle.py`;
- `research/fixtures/manuscript_v3_b08_databricks_aws_job_lifecycle_template_v1.json`;
  and
- `tests/unit/test_b08_databricks_aws_job_lifecycle.py`.

The tests exercise the canonical HOLD fixture, eligible zero and nonzero
autotermination observations, semantic-digest integrity, exact-type rules,
absence of an effect surface, and hostile mutations across job topology,
triggering, concurrency, timeout, retry, repair, replacement, image binding,
run observation, durable custody, authority, and project effects.

This construction closes no field, blocker, formal test, result slot, or
timetable task. It does not edit the tracker or evidence ledger. B08 remains
open until a separately authorized run produces complete external evidence and
that evidence passes the required independent review.
