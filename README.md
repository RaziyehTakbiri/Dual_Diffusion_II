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
- `PROJECT_B08_N1_CANDIDATE_003_FORENSIC_OUTCOME_AND_RUNTIME_ROUTE_PIVOT.md`:
  current operator-facing Databricks decision and conventional B08 route.
- `databricks/notebooks/b08_conventional_runtime_integration.py`: the only
  active B08 Databricks notebook. It performs the conventional, data-free
  two-pass install, runtime verification, targeted integration tests, and
  synthetic whole-method smoke route.
- `requirements/b08-conventional-runtime-controller-anchor-v1.json`: the exact
  content binding for that active notebook. The notebook requires and verifies
  this anchor before installation and again before issuing its final receipt.
- `requirements/b08-databricks-aws-dbr17.3-x86_64-cpu-py312.lock`: the exact
  21-wheel, hash-pinned DBR 17.3 / CPython 3.12 / Linux x86_64 CPU dependency
  lock used by that notebook.
- `requirements/b08-conventional-runtime-source-manifest-v1.json`: the
  content-addressed source/test/evidence bundle used by that notebook. This
  replaces any need for command-line Git inside a Databricks Git folder.
- `PROJECT_B08_DATABRICKS_AWS_QUALIFICATION_BUNDLE.md` and the native-runtime,
  isolated-overlay, Unity Catalog probe, and Candidate 002/003 records:
  preserved historical B08 qualification and diagnostic evidence. Their
  source-review verdicts remain historical, but their prospective overlay and
  one-shot custody instructions are superseded by the route-pivot record.
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
  historical hash-first entrypoint for the spent candidate-003 builder; do not
  run it again.
- `databricks/notebooks/b08_n1_uc_native_overlay_lock_candidate.py`: bounded,
  historical flat append-only candidate-003 builder; do not run it again.
- `PROJECT_B08_N1_UC_NATIVE_OVERLAY_LOCK_CANDIDATE_BUILDER_V1.md` and its
  independent review: exact successor contract, source bindings, hostile-test
  acceptance, operator gates, and zero-delta project boundary.

## Databricks boundary

AWS Databricks is the selected development compute venue. B08, F151, F152, and
Wave 2 remain open. The current route is conventional and project-scoped:

1. check in a fully resolved, hash-pinned dependency lock and a separately
   content-addressed source manifest;
2. install it on the selected DBR runtime and, from a fresh or restarted
   notebook interpreter, bind the source-manifest, dependency-lock, and built
   project-wheel digests in one receipt, capture a sanitized runtime,
   installed-version, distribution-root, and import-origin manifest, and run
   `pip check`;
3. run the relevant unit/integration suites and one tiny data-free or synthetic
   whole-method smoke test; and
4. before confirmatory work, freeze the prospective time, accelerator, memory,
   evaluation, tuning, final-run, total-compute, and durable-output ceilings,
   supported by documented Unity Catalog quota or accountable administrative
   capacity assurance plus projected-output and local-scratch fail-fast checks.

Docker/ECR, custom containers, bitwise Databricks infrastructure identity,
disabled auto-termination, B08 overlay namespaces, and B08 one-shot runtime
custody are not requirements unless a later external obligation specifically
requires them. Separate Gate-C preregistration and scientific-custody controls
are unchanged.

Candidate 003 is permanently spent unresolved. Preserve its namespace and all
historical records; do not rerun, reuse, repair, rename, replace, or delete it.
Candidate 004 is neither authorized nor planned. Do not run the historical
Candidate 002/003 builders, launchers, probes, or forensic notebooks again.

The existing F153 closure is CPU-only, single-threaded, and CUDA-hidden. Any GPU
or multithreaded scientific route must explicitly supersede or reopen F153
before execution. No real-data access, calibration, training, inference, or
confirmatory outcome inspection is authorized merely by completing the
conventional environment and synthetic integration checks above.

### Exact operator sequence for the active B08 notebook

1. Commit and push the complete handoff as one revision: the active controller
   notebook, its controller anchor, the dependency lock, the source manifest,
   and every file selected by that source manifest. Then pull that same revision
   into the existing Databricks Git folder.
2. Open only
   `databricks/notebooks/b08_conventional_runtime_integration.py`, attach the
   existing DBR 17.3 x86_64 CPU cluster, and choose **Run all**. Do not edit the
   notebook or enter any parameters.
3. The first pass verifies the checked-in source manifest, installs the exact
   hash-pinned lock, builds and installs the project wheel from a verified
   `/tmp` copy, and restarts Python. Wait for the restart to finish.
4. Choose **Run all** exactly once more. The second pass verifies the installed
   environment, runs the targeted tests and data-free synthetic whole-method
   route, and writes then prints one final JSON receipt.
5. Return that JSON for review. Its successful decision is
   `PASS_CONVENTIONAL_RUNTIME_AND_SYNTHETIC_INTEGRATION`. If it instead reports
   `STOP_CONVENTIONAL_RUNTIME_OR_INTEGRATION_FAILED`, do not rerun blindly;
   return the failure JSON for diagnosis.

This sequence does not require Docker, ECR, command-line Git, new cluster
settings, widgets, copied code, or a new Candidate 004 namespace.

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
