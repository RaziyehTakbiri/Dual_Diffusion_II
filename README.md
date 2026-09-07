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
  managed `%pip` installation, runtime verification, targeted integration
  tests, and synthetic whole-method smoke route in one Run all.
- `databricks/notebooks/b08_conventional_runtime_support.py`: the ordinary
  Python support module reloaded after each managed Python restart.
- `requirements/b08-conventional-runtime-controller-anchor-v1.json`: the exact
  content binding for the active notebook and support module. The notebook
  verifies this anchor before installation and before its final receipt.
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

**User-approved scope adjustment (2026-09-07):** resume the conventional
runtime and current-model integration route with one explicitly deferred
historical compatibility obligation, recorded as `OPEN_DEFERRED`:
`tests/unit/test_configuration_totalized_jump_potential_composer_torch.py::test_checkpoint17_module_keeps_checkpoint14_source_and_api_isolated`.
That unchanged test requires the absent historical source
`src/heterodiff/models/configuration_potential_composer_torch.py` with SHA-256
`2b1d60e4da640edb0e5be5bcfe90012d9b08a1f48af56f8240dcbdb1d4abe0cf`.
The [C17 crosswalk](PROJECT_C17_FORK_B_ASSUMPTIONS_PROOF_CODE_CROSSWALK_DRAFT.md)
records this historical source conflict as unresolved; no matching artifact
was recovered. The test and its expected hash remain unchanged. It is
explicitly deselected from this current execution scope, not passed or closed.
Of the previously selected 236 cases, the remaining 235 remain mandatory.
The 18 historical validator exclusions already defined by the runner are a
separate prior scope boundary; this approval adds no other exclusion.
The deferred check remains an open obligation to revisit when the exact
historical artifact is recovered or its scientific compatibility obligation
is separately resolved. Neither this scope adjustment nor a successful
current-scope run establishes full historical compatibility, B08 closure,
Wave 2 closure, or project completion.

1. Commit/push the controller notebook, support module, matching controller
   anchor, source manifest, README, timetable, and tests as one revision. Pull it into the
   existing Databricks Git folder. Remove the temporary diagnostic `%run` cell
   if it is still present; do not retain manual edits in the controller.
2. Open `databricks/notebooks/b08_conventional_runtime_integration.py`, attach
   the existing DBR 17.3 x86_64 CPU cluster, and choose **Run all once**.
3. The notebook uses seven cells: prepare the verified source, install the
   locked dependencies with `%pip`, restart Python, verify dependencies and
   build the wheel, install the project wheel with `%pip`, restart Python,
   then verify installed versions/origins and run the tests and synthetic integration.
   Allow both automatic Python restarts to complete.
   The historical B12 source-contract tests run first in a separate process
   importing the staged source. The remaining tests use the installed package.
   Both groups remain mandatory and are reported separately; only the exact
   user-approved historical check above is deselected, and no path assertion
   is relaxed. Failure output includes readable per-test summaries and the
   path to a complete local test log.
4. Return the final JSON. Success is
   `PASS_CURRENT_SCOPE_WITH_DEFERRED_HISTORICAL_CHECK`: the installed-runtime
   checks, all 235 required current-scope cases, and synthetic integration
   passed, while the historical obligation remains `OPEN_DEFERRED`.
   This is not a full-suite, scientific-execution, or B08-completion claim.
   An error instead reports the failing phase; return that output before
   trying again. These instructions do not imply that changes have already
   been committed, pushed, or run in Databricks.

The old subprocess installer reported completion in an environment that was
subsequently replaced; the diagnostic found a changed `python_prefix`, missing
PyTorch/heterodiff, and reverted dependency versions. Its old `/tmp` marker is
preserved and is not used by this route. The managed route records environment
path changes, requires fresh interpreter PIDs after restart, and verifies the
actual current packages and imports rather than requiring an unchanged path.
Notebook-scoped packages still need installation when starting a new session;
run the complete notebook for each qualification run.

This sequence requires no Docker, ECR, new cluster settings, widgets, copied
code, or new Candidate 004 namespace. Platform guidance:
https://docs.databricks.com/aws/en/libraries/notebooks-python-libraries

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
