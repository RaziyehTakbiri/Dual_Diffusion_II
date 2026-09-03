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
F151 or F152 receipt. The exact N1 overlay/lock-candidate notebook is now
independently accepted as
`PASS_N1_ISOLATED_OVERLAY_LOCK_CANDIDATE_BUILDER_V2_ZERO_DELTA`. Data-free
preflights have run, but no construction has succeeded. F151, F152, B08, and
Wave 2 remain open until bounded Databricks construction and separate
acceptance of its resulting evidence.

The operator helpers and templates are already present at their canonical
`requirements/`, `research/diagnostics/`, and `research/fixtures/` paths.
Preserve those paths when running or reviewing the bundle.

The data-free native-runtime discovery step in
`databricks/notebooks/b08_n1_native_runtime_discovery.py` is complete. The next
operator action is deliberately read-only:

1. commit and push the complete current repository, then pull that exact commit
   into the Databricks Git folder;
2. choose an existing Unity Catalog Volume and a new absent child such as
   `/Volumes/<catalog>/<schema>/<volume>/b08-n1-overlay-candidate-001`;
3. open `databricks/notebooks/b08_n1_isolated_overlay_lock_candidate.py`, attach
   the same DBR 17.3 x86_64 cluster, and enter only that destination path;
4. leave execution mode at `PREFLIGHT_ONLY`, network/build authorization at
   `false`, and acknowledgement at `NOT_AUTHORIZED`;
5. use **Run all** once and retain the complete JSON output for review.

That preflight performs no network access, package resolution, installation,
Spark/REST operation, data access, calibration, training, or inference. Do not
enable the construction gates or reuse a candidate path before the preflight
output is reviewed. With those three gates deliberately left off, the expected
top-level decision is `HOLD_PREFLIGHT_INPUTS_OR_AUTHORITY_INCOMPLETE`; that is
the safe preflight state, not a runtime-profile failure.

## Repository hygiene

Do not commit datasets, secrets, credentials, virtual environments, caches,
historical custody archives, private cluster exports, raw capture receipts, or
runtime outputs. Sanitized reviewed receipts may be added only through the
applicable project contract.

This tree was initialized from the active revision workspace on 2026-09-02.
Its predecessor music-diffusion working tree was moved to a recoverable sibling
backup and is not part of this revision checkout. No Git commit or remote push
is implied by this initialization.
