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
  Databricks qualification and operator instructions.

## Databricks boundary

AWS Databricks is a candidate final study-execution environment. The data-free
qualification package is independently accepted, but B08 and Wave 2 remain
open. Do not mount, inspect, copy, or run study/test data; do not calibrate,
train, infer, or inspect outcomes until the required cluster, runtime,
container, and physical storage-reservation receipts pass the separate review
gate.

The exact operator helper and empty templates are already present at their
canonical `research/diagnostics/` and `research/fixtures/` paths. Preserve
those paths when running or reviewing the bundle.

## Repository hygiene

Do not commit datasets, secrets, credentials, virtual environments, caches,
historical custody archives, private cluster exports, raw capture receipts, or
runtime outputs. Sanitized reviewed receipts may be added only through the
applicable project contract.

This tree was initialized from the active revision workspace on 2026-09-02.
Its predecessor music-diffusion working tree was moved to a recoverable sibling
backup and is not part of this revision checkout. No Git commit or remote push
is implied by this initialization.
