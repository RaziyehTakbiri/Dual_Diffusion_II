# Independent hostile review: B08 N1 UC-native candidate-003 builder V1

## Review disposition

**`PASS_UC_NATIVE_CANDIDATE_003_BUILDER_AND_HASH_FIRST_LAUNCHER_ZERO_DELTA`.**
The exact builder and launcher bound below are accepted for one default-off,
data-free preflight after they and the complete selected project source are
committed, pushed, and pulled into Databricks.

- P0: 0
- P1: 0
- P2: 0
- Exact eligible project, field, blocker, result, and timetable delta: **zero**
- F151, F152, B08, and Wave 2 remain `OPEN`.

This source review does not issue the commit-dependent review-package token and
does not authorize candidate-003 construction, network contact, package
resolution, build, install, runtime use, data access, calibration, training,
inference, science, or a tracker closure.

## Exact bytes reviewed

| File | Bytes | SHA-256 |
|---|---:|---|
| `databricks/notebooks/b08_n1_uc_native_overlay_lock_candidate.py` | 268,155 | `0c787b14f44cb6b6adedbefb5a6793f2dce270130184a885e816e69f16681d08` |
| `databricks/notebooks/b08_n1_uc_native_overlay_lock_candidate_launcher.py` | 9,041 | `b974380f2af950a77571eaf0d34317d2858c170458cc6d791cf0794f64366616` |
| `tests/unit/test_b08_n1_uc_native_overlay_lock_candidate.py` | 154,847 | `23e375c738aa0deb3000a8b3deb6a5131afaa35aee2d52ec2833c5eaa06dba1b` |
| `tests/unit/test_b08_n1_uc_native_overlay_lock_candidate_launcher.py` | 11,363 | `bcbcfe907790782ddfe7d1120146836ca79ef020d714b8d80dad46eefa21f132` |

All findings apply only to these exact bytes. The accepted probe-001 outcome is
separately fixed at 5,120 bytes and SHA-256
`f96160da93789d4749b3ce005182a0f57a49a5bc4408296d46ca4fd7fc71bcd7`.

## Hostile findings closed during review

Review was iterative and source bytes were re-frozen after every correction.
The accepted bytes close the material findings discovered during that process:

- Git `HEAD`/index/worktree proof now occurs before intent and is repeated after
  intent before network/build; the exact revision, commit epoch, and source
  projection bind the review package and durable intent.
- The package-source path set includes the previously globally ignored Python
  modules under `src/heterodiff/data/` and `src/heterodiff/artifacts/`; a dirty,
  incomplete, staged-only, or differently committed source set fails closed.
- Console-script RECORD paths may use the valid lexical `../../../bin/...`
  form only when their resolved targets remain within the exact overlay/prefix;
  wheel archive paths continue to reject traversal.
- Installed distributions are recognized only as direct `.dist-info` children
  of the exact overlay site-packages root; vendored nested metadata cannot spoof
  a top-level distribution.
- The generated F152 lock is locally revalidated for exact nonempty records,
  normalized names, versions, 64-lowerhex digests, and duplicates before use.
- Archive verification and payload planning use one pinned no-follow descriptor
  with bounded full-hash bookends; path replacement, mutation, truncation, and
  descriptor substitution regressions fail closed.
- Pre-success verification covers the complete reserved namespace: intent,
  contiguous used chunks, and manifest must match, while every unused chunk and
  both terminal receipts must have the required absence/presence state.
- Success-receipt publication ambiguity suppresses a contradictory failure
  receipt, including exceptions after a create call and path-visible success
  evidence observed by the outer handler.
- Failure telemetry preserves bounded sanitized stream evidence, exact
  step/code, internal failure category, and failure-receipt commit error code/
  detail. Post-`Popen` reader/supervisor failures terminate and reap the child,
  bounded-join all reader threads, and cannot bypass the durable command journal.

## Storage-protocol assessment

The writer is correctly narrowed to probe-001's observed capability. It uses a
fixed existing Volume parent and a fixed flat 132-leaf namespace, exclusive
create only, complete-close plus two fresh content-bound readbacks, intent-first
ordering, manifest-after-chunks ordering, and success-receipt-last ordering. It
does not reuse candidate-002's directory model or infer durability from POSIX
metadata that Unity Catalog object storage cannot establish.

The protocol explicitly retains the correct residual nonproofs: no atomic
snapshot, cache-coherence, historical-lineage, immutability, universal-atomicity,
or future-runtime/FUSE claim is made. Concurrency by an external writer is not
claimed absent. The fixed namespace, exclusive creates, content binding, full
pre-success projection, and terminal ambiguity rules are sufficient for this
one review-pending construction protocol under the observed probe behavior.

## Supply-chain and runtime assessment

The builder never targets the Databricks base environment. It uses a pip-free
private virtual environment, wheel-only fixed top-level requirements, exact
hash locks, retained build/runtime artifacts, strict wheel/RECORD/installed
payload closure, and a separate overlay. The deterministic archive and complete
source manifest bind the candidate material needed for later F151/F152 review.

The child environment is replacement-based and excludes inherited secrets and
proxies. Output and error records are bounded and sanitized. Third-party tools
are still not OS-sandboxed, so their unrelated-file effects and exact external
endpoint behavior remain explicitly outside the proof; that is an honest
residual limitation rather than an overclaim.

## Verification

The exact focused suite passed:

```text
184 passed
```

The broad B08 family selector passed:

```text
685 passed
```

The final stable hashes were checked before and after both runs. Tests cover
default-off behavior, launcher byte binding, pre-intent Git provenance,
review-package arity and content, complete namespace enumeration, every extra/
missing/reordered chunk case, hostile archive and path mutation, wheel and
installed-overlay identity, success/failure receipt ambiguity, subprocess
timeout/overflow/reader/supervisor cleanup, bounded sanitized diagnostics, and
exact failure-state preservation.

Two independent hostile audits reported no remaining concrete P0, P1, or P2
finding. Python AST parsing, duplicate literal-dictionary-key inspection,
`pyflakes`, embedded PIP-identity probe compilation, direct local-call arity
inspection, and `git diff --check` were clean.

## Required operational prerequisite

The repository is intentionally not yet eligible for a review-package token.
At review time, the builder, launcher, tests, and 117 intended Python modules in
`src/heterodiff/data/` and `src/heterodiff/artifacts/` were untracked, and the
`.gitignore` source exception was modified. The default local preflight correctly
returned `BOUND_SOURCE_DIFFERS_FROM_GIT_INDEX_PATH_SET`, emitted no review
package, wrote no file, and made no direct external network contact.

The operator must commit and push the complete current source, then pull that
exact commit into Databricks. Omitting any of the 117 modules is a hard stop,
because the built wheel would otherwise differ from the reviewed project source.

## Next eligible action

Open only the hash-first launcher and use **Run all** once with its default
`NOT_AUTHORIZED` value. This first run materializes the launcher widget and must
return `HOLD_REVIEWED_BUILDER_SHA256_REQUIRED` without executing the builder.
Enter builder SHA-256
`0c787b14f44cb6b6adedbefb5a6793f2dce270130184a885e816e69f16681d08`
in that widget and use **Run all** once more. Leave the builder's execution
mode, network/build authority, one-shot acknowledgement, and review-package
authorization at their defaults when those widgets appear. Return the complete
default-off preflight JSON for review.

A later construction may be considered only if that exact output has no errors,
shows the runtime/environment/profile exact, proves all 132 reserved leaves and
the virtual prefix absent, binds the committed Git revision and hash-first
launcher, and emits a non-null review package. Even a successful construction
would remain review-pending and would close no project task by itself.
