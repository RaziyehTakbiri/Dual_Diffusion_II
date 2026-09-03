# Independent review: B08 N1 candidate-002 object-snapshot forensics V2

## Review disposition

**`PASS_OBJECT_SNAPSHOT_FORENSICS_V2_ZERO_DELTA`.** The exact V2 notebook,
tests, and V1 safe-HOLD record bound below are accepted for one bounded,
read-only run against the exact spent `candidate-002` Unity Catalog Volume
path.

- P0: 0
- P1: 0
- P2: 0
- Exact project-state and completion-timetable delta: **zero**
- `candidate-003` construction remains prohibited.

## Exact bytes reviewed

| File | Bytes | SHA-256 |
|---|---:|---|
| `databricks/notebooks/b08_n1_candidate_002_object_snapshot_forensics_v2.py` | 16,247 | `121c60d3ba9ecb43d79c6560137d703a0643236e054e8fdae41d77fae116cc8d` |
| `tests/unit/test_b08_n1_candidate_002_object_snapshot_forensics_v2.py` | 16,235 | `dfbbd2720116b4c58fabb2a04ea83d82c00c6372c606f8223b9198ba7940323a` |
| `PROJECT_B08_N1_CANDIDATE_002_FORENSIC_V1_BINDING_MISMATCH.md` | 2,366 | `4d37c20e280d931b7f8caf3c505e5e404c8c54bc7e7b1588aeb8775bfc53164f` |

## Findings

The notebook has one hardcoded production target and no widget, environment,
argument, or alternate-path override. It performs two independent snapshots;
each opens and closes a fresh root descriptor, bounded-lists at most eight
validated names, records name/kind/size metadata, and opens only the exact two
allowlisted operational-control leaves. Each control read is capped at 1 MiB.
Unexpected payloads, symlinks, and other nonregular leaves are never opened.

Each snapshot requires an unchanged pre/post roster. The two fully closed
snapshots must then have identical canonical projections and SHA-256 digests.
Present but unread allowlisted leaves produce an explicit HOLD. Disagreement
between snapshots produces an explicit nonrepeatable-snapshot HOLD. File,
directory, and iterator descriptors close on normal and injected failure paths.

Device, inode, permission bits, and timestamps are excluded from custody
acceptance. File-type bits are used only to require a visible non-symlink root
directory and regular allowlisted payload leaves. The output expressly denies
historical root lineage, between-snapshot object identity, atomicity, freshness,
cache coherence, and future-stability claims. A match means only that two
sequential path-visible observations agreed.

Failure telemetry distinguishes attempted, possibly performed, partially read,
and completely read control payloads. Definite managed-storage completion is
not falsely emitted on a failed inventory. Successful output truthfully records
that `/Volumes` access uses Databricks-managed storage I/O while direct external
endpoint access remains false.

## Verification

- V2 forensic suite: `22 passed`;
- V2 plus V1 forensic plus predecessor-builder suites: `98 passed`;
- Python AST parse: clean;
- `pyflakes`: clean;
- duplicate literal dictionary-key inspection: clean;
- trailing-whitespace and `git diff --check`: clean.

## Exact next action

Commit, push, and pull these exact bytes. Run only
`databricks/notebooks/b08_n1_candidate_002_object_snapshot_forensics_v2.py`
once on Databricks and return the complete JSON. Do not edit or remove any
`candidate-002` object, do not create `candidate-003`, and do not rerun the
construction notebook.

This review grants no network/build, Databricks REST mutation, package
installation, canonical-lock, F151/F152, data, calibration, training,
inference, scientific-result, blocker-closure, B08/Wave-2 closure, or tracker
authority.
