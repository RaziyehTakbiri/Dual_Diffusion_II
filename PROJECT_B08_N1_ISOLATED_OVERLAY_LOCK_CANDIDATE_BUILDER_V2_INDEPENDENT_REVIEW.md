# Independent hostile review: B08 N1 isolated overlay/lock candidate builder V2

## Review disposition

**`PASS_N1_ISOLATED_OVERLAY_LOCK_CANDIDATE_BUILDER_V2_ZERO_DELTA`.** The
exact notebook and focused tests bound below are accepted as a narrowly scoped,
data-free builder for one review-pending native overlay and F152-lock candidate.

- P0: 0
- P1: 0
- P2: 0
- Exact eligible project, field, blocker, result, and timetable delta: **zero**
- F151, F152, B08, and Wave 2 remain `OPEN`.

This review grants no standing or reusable network, installation, runtime,
data, calibration, training, inference, scientific-execution, field-closure,
blocker-closure, B08-closure, or tracker authority. A constructed candidate
still requires a separate exact-artifact and runtime-evidence review.

## Exact bytes reviewed

| File | Bytes | SHA-256 |
|---|---:|---|
| `databricks/notebooks/b08_n1_isolated_overlay_lock_candidate.py` | 146,362 | `f001b81be1a419f796b17041bbbb6411304308fa878b40d9891f6584121f5f89` |
| `tests/unit/test_b08_n1_isolated_overlay_lock_candidate.py` | 101,850 | `471b29c3d080aa2c8d24ca906b49fb5a1df6ec3309171596bb6b8acb7ce26579` |

All findings apply only to these exact bytes. The historical
`PROJECT_B08_N1_ISOLATED_OVERLAY_LOCK_CANDIDATE_BUILDER_V1_INDEPENDENT_REVIEW.md`
remains unchanged at SHA-256
`2a8d2928539b1be87838188f722b118dfe78f1e70ae4fc3310bfd460927a27e5`.
V2 supersedes V1 only as the active builder for future execution.

## Databricks preflight diagnosis and runtime repair

The supplied Databricks output proves that the previous run stopped before
construction. Its safety record reports no write, network/contact, package
resolution, project-wheel build, Spark/REST access, study/test-data access,
calibration, training, or inference. No durable output directory was supplied.

The other hold was a representation defect in the builder, not a cluster
defect. The accepted V2 profile stores `24.04.4 LTS`, while
`/etc/os-release` exposes `PRETTY_NAME` as `Ubuntu 24.04.4 LTS`. The successor
accepts only the exact profile release or the exact expected-distribution prefix
plus that release. It preserves the raw observed value and continues to reject
another distribution, another patch release, empty input, or a non-string.

## Ensurepip-independent bootstrap

The pulled user revision correctly established the necessary direction:
construct a pip-free private virtual environment rather than installing into
the Databricks base runtime. The reviewed successor completes that route as
follows:

1. observes rather than hardcodes whether `ensurepip` is available;
2. selects the current notebook interpreter's `pip==25.0.1` and binds its
   interpreter, installation prefix, distribution root, module, RECORD, and
   complete installed payload;
3. verifies every RECORD-declared file, SHA-256, and size; rejects symlinks,
   nonregular objects, escapes, duplicate resolved paths, missing payloads, and
   unrecorded non-bytecode files; and hashes any unrecorded `__pycache__`
   bytecode into the canonical full-payload binding;
4. invokes host Python with explicit `-I -B`, preventing configuration leakage
   and bytecode mutation while the identity is bound;
5. downloads only the exact pip wheel from the fixed primary index into the
   retained build-tool wheelhouse, inspects its archive identity and embedded
   RECORD closure, and creates a local SHA-256 requirements lock;
6. rebinds the complete host-pip identity before mutation and fails if any
   bound value changed;
7. uses pip's supported `--python` target mode with `--no-index`,
   `--no-deps`, `--only-binary=:all:`, and `--require-hashes` to seed only the
   private pip-free virtual environment; and
8. binds the resulting pip installation inside that private environment before
   any subsequent dependency operation.

The bootstrap wheel and lock remain in the candidate and are included in the
later build-tool artifact set. Failure telemetry marks network/resolution and
bootstrap/build-tool installation attempts truthfully and retains the host,
wheel, lock, and target-pip bindings reached before failure.

## Verification

The exact focused suite passed from the repository root:

```text
62 passed
```

The same exact suite passed from an unrelated `/private/tmp` working directory:

```text
62 passed
```

The V1-profile, V2-profile, and N1-builder suites passed together:

```text
109 passed
```

The independent broader B08 selection passed:

```text
361 passed
```

An expanded B08/Databricks compatibility selection also passed 427 tests.
Python AST parsing, duplicate-literal-dictionary-key inspection, `pyflakes`,
trailing-whitespace inspection, and `git diff --check` were clean. A separate
pip-free-venv exercise confirmed that the selected `--python` form installs pip
only into the target virtual environment. A bind/invoke/rebind exercise with
explicit `-I -B` retained an identical full-payload digest.

## Remaining boundary and next eligible action

No construction has succeeded. No candidate lock, overlay, manifest, success
receipt, F151 production-runtime record, F152 canonical value, capacity or
storage-reservation receipt, calibration, data access, scientific result, or
claim exists.

After these exact bytes are committed, pushed, and pulled into Databricks, the
next eligible action is one default read-only preflight with a newly selected,
absent child below an existing Unity Catalog Volume. Construction gates remain
off until that preflight output is reviewed. Even a later successful
construction produces review-pending evidence only and closes no task by
itself.
