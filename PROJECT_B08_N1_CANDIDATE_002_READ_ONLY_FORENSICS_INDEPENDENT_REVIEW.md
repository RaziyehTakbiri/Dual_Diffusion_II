# Independent review: B08 N1 candidate-002 read-only forensics

## Review disposition

**`PASS_READ_ONLY_FORENSIC_PACKAGE_ZERO_DELTA`.** The exact notebook, focused
tests, and terminal no-go freeze bound below are accepted for one bounded,
control-evidence-only inspection of the exact spent `candidate-002` root.

- P0: 0
- P1: 0
- P2: 0
- Exact eligible project-state and completion-timetable delta: **zero**
- Successor construction remains prohibited pending the forensic output and a
  separately reviewed Unity Catalog Volume-native writer.

## Exact bytes reviewed

| File | Bytes | SHA-256 |
|---|---:|---|
| `databricks/notebooks/b08_n1_candidate_002_read_only_forensics.py` | 12,302 | `c77aea6bea5a4c41dabc7cb2103ef86a43f099333f6dd9658ef691ee60abcb69` |
| `tests/unit/test_b08_n1_candidate_002_read_only_forensics.py` | 9,364 | `0e884df866ef08471be91f6eae0ab6929f6f583f25e21f6bb85210720e106726` |
| `PROJECT_B08_N1_CANDIDATE_002_TERMINAL_NO_GO.md` | 5,360 | `5657a4811ae7f9ee2212690e15bd1497b461f706dac6f59b829aca8c70823215` |

The predecessor builder remains bound to Git revision
`929fb4f8a34df0804c051d00bd8c2cd1ceaa4f3c`, builder notebook SHA-256
`f001b81be1a419f796b17041bbbb6411304308fa878b40d9891f6584121f5f89`,
and builder V2 independent-review SHA-256
`041d00d81e9df40b715fb16eb6f9b964c2bbf24191a3536338621fc2d9b78fa6`.

## Scope and safety findings

The notebook has no widget, ambient environment override, or alternate
production target. Its `main()` binds only:

- `/Volumes/development/team_eds_supplychain/b08_runtime_output/b08-n1-overlay-candidate-002`;
- reported device `86`; and
- reported inode `8`.

A mismatch stops before enumeration. The root must be a physical directory;
the retained descriptor and declared path are rebound after inspection. Visible
names and name lengths are bounded. Unexpected leaves receive metadata-only
inspection and cannot be opened. Only `attempt-intent.json` and
`construction-failure-receipt.json` may be opened read-only, and each payload
read is capped at 1 MiB. Symlink roots are rejected, symlink leaves remain
unopened, and leaf binding, size, mode, and modification time must remain stable
through each read.

The safety record does not pretend that `/Volumes` is network-free. It reports
Databricks-managed storage I/O through FUSE separately from direct external
endpoint access. It distinguishes confirmed from possibly begun control-leaf
payload reads on late failures and claims only that no study/test-data *path*
is requested. No mutating filesystem operation, chmod/chown, direct external
endpoint, package resolution/build/install, Spark, Databricks REST, study/test
path, calibration, training, or inference is requested.

The prior execution's root-binding metadata might change across a FUSE remount
or cluster restart. A resulting
`REPORTED_SPENT_ATTEMPT_ROOT_BINDING_MISMATCH` is a safe HOLD rather than proof
of path replacement. The operator must not weaken or edit the reader after such
a result.

## Verification

- focused forensic suite: `14 passed`;
- forensic plus predecessor builder suite: `76 passed`;
- focused suite also passed from unrelated `/private/tmp`;
- Python AST parse: clean;
- `pyflakes`: clean;
- duplicate literal dictionary-key inspection: clean;
- trailing-whitespace and `git diff --check`: clean.

## Authorized next action

Commit, push, and pull these exact bytes, then run only
`databricks/notebooks/b08_n1_candidate_002_read_only_forensics.py` once on the
same Databricks cluster. Preserve and return the complete JSON output. Do not
delete or modify `candidate-002`, do not select `candidate-003`, and do not run
the construction notebook.

This review grants no network/build, installation, canonical-lock, F151/F152,
scientific execution, data access, calibration, training, inference, blocker
closure, Wave-2 closure, or tracker authority.
