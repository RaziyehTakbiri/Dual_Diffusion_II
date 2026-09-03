# Dual Diffusion II — manuscript revision workspace

This repository is the clean working tree for the current Dual Diffusion
manuscript revision and its AWS Databricks execution handoff.

## Contents

- `manuscript_v3/`: current manuscript and claim/method audit material.
- `src/heterodiff/`: revision implementation.
- `tests/unit/`: unit, regression, custody, and package-validation tests.
- `research/`: preregistrations, fixtures, diagnostics, and production helpers.
- `PROJECT_COMPLETION_TIMETABLE.md`: marked project plan.
- `PROJECT_EVIDENCE_LEDGER.md`: authoritative additive evidence view.
- `PROJECT_B08_DATABRICKS_AWS_QUALIFICATION_BUNDLE.md`: current data-free
  Databricks qualification-readiness history.
- `PROJECT_B08_NATIVE_DATABRICKS_RUNTIME_SUCCESSOR_V1.md`: active prospective
  native-DBR, lockfile-based B08 route; no custom container or ECR is required.
- `PROJECT_B08_NATIVE_DATABRICKS_RUNTIME_SUCCESSOR_V1_INDEPENDENT_REVIEW.md`:
  independently accepted bounded Stage-N0 construction-readiness review.
- `PROJECT_B08_NATIVE_DATABRICKS_RUNTIME_TARGET_SUCCESSOR_V2.md`: accepted
  Ubuntu-24.04.4 target correction for the observed DBR 17.3 runtime.
- `PROJECT_B08_NATIVE_DATABRICKS_RUNTIME_TARGET_SUCCESSOR_V2_INDEPENDENT_REVIEW.md`:
  independent zero-delta acceptance of the V2 target correction.
- `databricks/notebooks/b08_n1_isolated_overlay_lock_candidate.py`: exact
  independently accepted N1 V2 isolated-overlay/F152-lock candidate builder.
- `PROJECT_B08_N1_ISOLATED_OVERLAY_LOCK_CANDIDATE_BUILDER_V1_INDEPENDENT_REVIEW.md`:
  historical exact-byte review of the superseded V1 builder.
- `PROJECT_B08_N1_ISOLATED_OVERLAY_LOCK_CANDIDATE_BUILDER_V2_INDEPENDENT_REVIEW.md`:
  active hostile zero-delta acceptance of the exact N1 V2 notebook and tests.
- `PROJECT_B08_N1_CANDIDATE_002_TERMINAL_NO_GO.md`: frozen record of the spent
  candidate-002 construction failure before any network or package operation.
- `PROJECT_B08_N1_CANDIDATE_002_FORENSIC_V1_BINDING_MISMATCH.md`: preserved V1
  forensic mismatch caused by applying device/inode semantics to managed object
  storage.
- `PROJECT_B08_N1_CANDIDATE_002_OBJECT_SNAPSHOT_FORENSICS_V2_OUTCOME.md`: the
  successful two-snapshot classification of candidate-002 as
  `STABLY_COMPLETE_EXPECTED_INTENT_VISIBLE`.
- `databricks/notebooks/b08_n1_candidate_002_object_snapshot_forensics_v2.py`
  and `PROJECT_B08_N1_CANDIDATE_002_OBJECT_SNAPSHOT_FORENSICS_V2_INDEPENDENT_REVIEW.md`:
  the exact accepted read-only forensic source and its hostile review.
- `databricks/notebooks/b08_n1_uc_volume_write_capability_probe.py`: exact
  bounded, data-free successor capability probe for the selected Unity Catalog
  Volume path.
- `PROJECT_B08_N1_UC_VOLUME_WRITE_CAPABILITY_PROBE_INDEPENDENT_REVIEW.md`:
  independent source acceptance for one exact authorized probe run.
- `PROJECT_B08_N1_UC_VOLUME_WRITE_CAPABILITY_PROBE_001_OUTCOME.md`: recorded
  PASS from the one authorized probe-001 execution; both exact leaves are
  retained and permanently spent.
- `databricks/notebooks/b08_n1_uc_native_overlay_lock_candidate_launcher.py`:
  hash-first entrypoint for the UC Volume-native candidate-003 builder.
- `databricks/notebooks/b08_n1_uc_native_overlay_lock_candidate.py`: bounded,
  default-off, flat append-only UC Volume-native overlay/lock candidate builder.
- `PROJECT_B08_N1_UC_NATIVE_OVERLAY_LOCK_CANDIDATE_BUILDER_V1.md` and its
  independent review: exact successor contract, source bindings, hostile-test
  acceptance, operator gates, and zero-delta project boundary.

## Databricks boundary

AWS Databricks is a candidate final study-execution environment. The data-free
qualification-readiness package and the bounded native-DBR Stage-N0 package are
independently accepted; the latter disposition is exactly
`GO_NATIVE_DBR_N0_CONSTRUCTION_READINESS_ZERO_DELTA`. B08 and Wave 2 remain
open. The active prospective route uses native Databricks Runtime plus an exact
dependency lock and observed runtime manifest; the draft Docker/ECR route is
superseded and supplies no active prerequisite. N0 proves offline construction
readiness only: it does not resolve F151/F152, prove transitive or payload
closure, establish effective whole-runtime F153 controls, capture production
runtime, reserve capacity/storage, or authorize any provider or scientific
operation. Do not mount, inspect, copy, or run study/test data; do not calibrate,
train, infer, or inspect outcomes until the required native runtime, lock,
capacity, and physical storage-reservation receipts pass their separate gates.

The completed read-only discovery observed DBR 17.3, CPython 3.12.3, x86_64,
Ubuntu `24.04.4 LTS`, and all 15 deterministic environment values exactly. The
independently accepted V2 target successor corrects only the prospective Ubuntu
patch release. The base-runtime package differences and absent Torch are the
expected reason for constructing a separate native overlay; they are not an
F151 or F152 receipt. The earlier N1 V2 overlay/lock-candidate notebook remains
accepted only as historical source evidence and must not be reused on this
Unity Catalog Volume. Candidate-002 is permanently spent: its repeatable
path-visible snapshots contain exactly the expected intent and failure receipt.
F151, F152, B08, and Wave 2 remain open.

The operator helpers and templates are already present at their canonical
`requirements/`, `research/diagnostics/`, and `research/fixtures/` paths.
Preserve those paths when running or reviewing the bundle.

The native-runtime discovery, candidate-002 forensics, and the one authorized
Unity Catalog Volume capability probe are complete. Probe-001 passed exact
exclusive-create, non-overwriting collision, exactly-one-winner process-race,
and repeated content-bound readback checks. Its two exact 4 KiB leaves are
retained evidence and permanently spent: do not rerun, delete, rename, repair,
replace, or reuse them.

This PASS clears only the observed storage-behavior prerequisite. It does not
make the existing POSIX-oriented builder safe, create an F151/F152 value, or
establish physical durability, capacity, runtime, or scientific readiness. A
replacement candidate-003 builder and hash-first launcher now implement the
verified flat append-only protocol and are locally accepted for a default-off,
data-free Databricks preflight. No candidate construction has run or is
authorized by that source acceptance.

The next operator action is to commit and push the complete current source,
including every Python file under `src/heterodiff/data/` and
`src/heterodiff/artifacts/`, then pull that exact commit into Databricks. Open
only the hash-first launcher and use **Run all** once with its default
`NOT_AUTHORIZED` value; this creates the launcher widget and must return
`HOLD_REVIEWED_BUILDER_SHA256_REQUIRED` without executing the builder. Enter
the exact builder SHA-256 listed in the independent review, leave all four
builder construction gates at their defaults when they appear, and use
**Run all** once more for the default-off builder preflight. Return that complete
JSON for review. Do not authorize construction, and do not run the builder
directly.

## Repository hygiene

Do not commit datasets, secrets, credentials, virtual environments, caches,
historical custody archives, private cluster exports, raw capture receipts, or
runtime outputs. The `src/heterodiff/data/` and `src/heterodiff/artifacts/`
directories contain Python package source—not datasets or generated runtime
artifacts—and must be tracked. Sanitized reviewed receipts may be added only
through the applicable project contract.

This tree was initialized from the active revision workspace on 2026-09-02.
Its predecessor music-diffusion working tree was moved to a recoverable sibling
backup and is not part of this revision checkout. No Git commit or remote push
is implied by this initialization.
