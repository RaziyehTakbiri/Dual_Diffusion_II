# B08 N1 UC-native overlay/F152-lock candidate-003 builder V1

**Source disposition:**
`PASS_UC_NATIVE_CANDIDATE_003_BUILDER_AND_HASH_FIRST_LAUNCHER_ZERO_DELTA`

**Execution disposition:** default-off preflight only; candidate-003 has not run

**Eligible project delta:** zero

## 1. Purpose and boundary

The successful probe-001 execution established the narrow Unity Catalog Volume
behavior needed by a replacement writer: exclusive creation, non-overwriting
collision, exactly one winner in a synchronized two-process race, and repeated
content-bound readback. It did not make the earlier POSIX-oriented candidate
builder safe. This successor implements a flat, append-only protocol that uses
only the storage behavior actually observed by that probe.

The builder creates one review-pending, data-free dependency overlay and F152
lock candidate. It does not install into the Databricks base environment, edit
the canonical repository lock, access study/test data, invoke Spark or the
Databricks REST API, run calibration/training/inference, or close a field,
blocker, Formal Test, B08, or Wave 2.

## 2. Exact accepted source

| Object | Bytes | SHA-256 |
|---|---:|---|
| `databricks/notebooks/b08_n1_uc_native_overlay_lock_candidate.py` | 268,155 | `0c787b14f44cb6b6adedbefb5a6793f2dce270130184a885e816e69f16681d08` |
| `databricks/notebooks/b08_n1_uc_native_overlay_lock_candidate_launcher.py` | 9,041 | `b974380f2af950a77571eaf0d34317d2858c170458cc6d791cf0794f64366616` |
| `tests/unit/test_b08_n1_uc_native_overlay_lock_candidate.py` | 154,847 | `23e375c738aa0deb3000a8b3deb6a5131afaa35aee2d52ec2833c5eaa06dba1b` |
| `tests/unit/test_b08_n1_uc_native_overlay_lock_candidate_launcher.py` | 11,363 | `bcbcfe907790782ddfe7d1120146836ca79ef020d714b8d80dad46eefa21f132` |

The current project-source manifest contains 304 files: `README.md`,
`pyproject.toml`, and all 302 Python files below `src/heterodiff/`. Its local
pre-commit semantic digest is
`0e2decc9d0c6dbb4ff6b41dec4ee78b6139ea2aa8a419880e3e06ff4f8716021`.
The builder and launcher are bound separately, producing 306 provenance-bound
paths in total. This manifest digest is not a substitute for the later exact
Git revision and review-package digest.

## 3. Fixed target and namespace

The only selected managed-storage parent is:

`/Volumes/development/team_eds_supplychain/b08_runtime_output`

The fixed candidate identifier is `b08-n1-overlay-candidate-003`. The apparent
path ending in that identifier is a virtual prefix only and must remain absent;
the builder creates no candidate directory. It reserves exactly 132 flat leaf
names in the existing parent:

- one attempt-intent control object;
- 128 ordinal payload-chunk names;
- one payload manifest;
- one construction-success receipt; and
- one construction-failure receipt.

Every reserved leaf and the virtual prefix must be absent at preflight. The
intent is written first. Used chunks are contiguous from ordinal zero, followed
by the manifest. A success receipt is written last and is the only success
commit marker. All unused chunk names, the failure receipt, and the success
receipt must be freshly observed absent immediately before that final commit.

Each managed leaf is written with one exclusive create, a complete close, and
two fresh exact size/SHA-256 readbacks. Managed-storage acceptance never relies
on `fsync`, `chmod`, device/inode, timestamps, rename, deletion, repair, or a
directory identity.

## 4. Hash-first and authorization boundary

The builder must not be run directly. The accepted launcher reads the tracked
builder once through no-follow descriptors, verifies the operator-supplied
builder SHA-256, compiles those same in-memory bytes, and executes them. The
active launcher's own identity remains an operator-held procedural trust anchor;
it cannot cryptographically self-attest its executing cells.

The builder defaults to preflight and requires all of these independent gates
for construction:

1. hash-first launch evidence for the exact accepted builder bytes;
2. `CONSTRUCT_ONE_UC_NATIVE_REVIEW_PENDING_CANDIDATE_003`;
3. explicit network/build authority set to `true`;
4. `AUTHORIZE_ONE_DATA_FREE_N1_UC_NATIVE_NETWORK_BUILD_CANDIDATE_003`; and
5. `AUTHORIZE_REVIEWED_CANDIDATE_003_PACKAGE_SHA256_<digest>`, where the digest
   must equal the exact review package emitted by a clean default preflight and
   accepted in a later independent review.

No standing or reusable authorization exists. The present source review does
not issue gate 5 and therefore does not authorize construction.

## 5. Pre-intent Git and source proof

Before any irreversible intent create, preflight and construction independently
verify that every selected source path, the builder, and the launcher:

- is a regular physical file with a bounded, content-addressed record;
- appears exactly once at stage zero in the Git index;
- appears at the same mode and blob identity in the selected `HEAD` tree; and
- has worktree bytes and mode matching both the index and `HEAD`.

The exact Git revision, commit epoch, and verified source-provenance projection
are included in the review package and attempt intent. Construction repeats the
same proof before intent, compares it with preflight, writes the intent, and
then repeats it after intent before any network or build command. A change
fails closed.

The current local checkout intentionally fails this gate because the builder,
launcher, and 117 Python source files below `src/heterodiff/data/` and
`src/heterodiff/artifacts/` are not yet committed. The focused tests are also
untracked and must be committed as reviewed evidence, although they are not
members of the construction source manifest. The `.gitignore` successor keeps
global `data/` and `artifacts/` products ignored while explicitly exposing only
these Python package-source files. All 117 files must be committed and pushed
before the Databricks preflight can produce a review package.

## 6. Isolated dependency construction

After an exact authorized intent commit, the builder:

1. creates a local transient staging root and a pip-free isolated virtual
   environment;
2. binds the host `pip==25.0.1` installation and complete declared payload;
3. downloads only exact wheel artifacts from the fixed HTTPS PyPI and PyTorch
   CPU indexes, with no URL credentials;
4. retains and hash-locks bootstrap/build-tool wheels before installing them
   only into the private environment;
5. builds the project wheel from a copied, content-bound source-only tree;
6. resolves a complete wheel-only transitive runtime set for `numpy==2.4.6`,
   `scipy==1.17.1`, `threadpoolctl==3.6.0`, `torch==2.12.1+cpu`, and
   `heterodiff==0.1.0`;
7. creates an exact `--require-hashes` F152 lock candidate and verifies the
   wheel/metadata/RECORD/name/version/tag/ownership closures;
8. installs only into a separate overlay, then verifies every installed
   distribution and RECORD-owned payload; and
9. creates a deterministic, uncompressed archive and publishes it as bounded
   256 MiB ordinal chunks plus a content-bound payload manifest.

The archive is held through one no-follow, single-link file descriptor. Its
initial and final full hashes bookend both member verification and chunk
planning through duplicated references to the same open description. Archive
paths, counts, sizes, central-directory bounds, compression modes, and exact
member identities are checked before publication.

Child processes receive a replacement/allowlisted environment with deterministic
controls, staging-local `HOME` and XDG/cache/temp roots, disabled user/config
inputs, and no inherited proxy or credential environment. Downloaded tooling is
not OS-sandboxed, so unrelated-file access, effects outside staging, and exact
third-party network-endpoint confinement are not claimed.

## 7. Failure and terminal-state semantics

Every network/build child has a 30-minute bound, a 16 MiB bound per output
stream, process-group termination, bounded reaping, and reader-thread cleanup.
Failures preserve exact step/code and a separately bounded, sanitized 4 KiB
internal detail, together with bounded sanitized output tails, captured-byte
counts and SHA-256 values, bytes observed before termination, and capture
completeness flags. Exact index URLs, runtime paths, and basic URL credentials
are redacted from persisted text.

After a committed intent, a normal failure may publish one failure receipt only
after re-verifying intent custody and freshly observing the success receipt
absent. If a success-receipt create may have begun—or a success leaf is visible
after failure—the outcome is terminally ambiguous and no contradictory failure
receipt is permitted. All spent or ambiguous namespaces require independent
forensics and must never be repaired or reused.

## 8. Verification and nonclaims

The exact focused builder/launcher suite passed `184/184`. The broad B08 family
selection passed `685/685`. Two independent hostile audits found P0/P1/P2
`0/0/0`. Python AST parsing, duplicate literal-dictionary-key inspection,
`pyflakes`, embedded-probe compilation, direct-call arity inspection, and
`git diff --check` were clean.

This source acceptance proves no successful candidate construction, dependency
availability at a future time, atomic snapshot, cache coherence, immutability,
historical object lineage, universal atomicity, physical durability, capacity
reservation, F151 production environment, canonical F152 value, effective
whole-runtime satisfaction, scientific readiness, or result.

## 9. Next eligible action

Commit and push the complete source set, pull that exact commit into the
Databricks Git folder, attach the same dedicated DBR 17.3 x86_64 CPU cluster,
and open only the accepted hash-first launcher. Use **Run all** once with the
launcher's default `NOT_AUTHORIZED` value. This materializes its widget and must
return `HOLD_REVIEWED_BUILDER_SHA256_REQUIRED` without executing the builder.
Then enter the exact builder SHA-256 from section 2 and use **Run all** once
more. Leave all four builder construction inputs at their defaults when they
appear. Return the complete default-off preflight JSON for independent review.

Do not authorize construction until that output proves the exact runtime,
environment, absent 132-leaf namespace, clean Git binding, hash-first evidence,
and non-null review-package digest.
