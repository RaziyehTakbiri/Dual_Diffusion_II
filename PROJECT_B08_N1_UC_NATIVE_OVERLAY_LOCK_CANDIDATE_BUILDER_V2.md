# B08 N1 UC-native overlay/F152-lock candidate-003 builder V2

**Source disposition:**
`PASS_UC_NATIVE_CANDIDATE_003_BUILDER_AND_HASH_FIRST_LAUNCHER_V2_ZERO_DELTA`  
**Execution disposition:** default-off preflight only  
**Candidate state:** absent and unspent  
**Construction authority:** not issued  
**Exact eligible project delta:** zero

## 1. Scope and narrow supersession

V2 retains the fixed candidate-003 target, flat append-only Unity Catalog
protocol, isolated wheel-only construction, dependency and installed-payload
closure, bounded child-process supervision, failure evidence, and
success-receipt ambiguity rules accepted for V1.

V2 changes only the source-identity and source-presentation route needed for
future Databricks execution. The operator-supplied V1 preflight is preserved in
the [V1 Databricks HOLD record](PROJECT_B08_N1_UC_NATIVE_OVERLAY_LOCK_CANDIDATE_003_V1_DATABRICKS_PREFLIGHT_HOLD.md).
It proved that the observed Databricks source-folder view did not support V1's
live `git config --local` gate even after the reviewed source had been pushed and
pulled.

The exact [V1 contract](PROJECT_B08_N1_UC_NATIVE_OVERLAY_LOCK_CANDIDATE_BUILDER_V1.md)
and [V1 review](PROJECT_B08_N1_UC_NATIVE_OVERLAY_LOCK_CANDIDATE_BUILDER_V1_INDEPENDENT_REVIEW.md)
remain unchanged historical records. V2 supersedes only their future
live-Git/runtime-mode/exact-terminal-LF route and associated next-action
instructions. No historical V1 finding is converted into a project closure.

`README.md` is one of the 304 exact build-input files in the reviewed snapshot,
so its V1 candidate-003 references are deliberately preserved byte-for-byte in
this freeze. Those references are historical and their operator route is
superseded by section 10 of this V2 contract; they must not be used as current
instructions.

The builder creates, at most, one review-pending and data-free dependency
overlay/F152-lock candidate. It does not install into the Databricks base
environment, edit the canonical repository lock, access study/test data, invoke
Spark or the Databricks REST API, run scientific computation, or close F151,
F152, B08, Wave 2, a Formal Test, a result, a blocker, or a timetable task.

## 2. Exact accepted V2 source

| Object | Bytes | SHA-256 |
|---|---:|---|
| `databricks/notebooks/b08_n1_uc_native_overlay_lock_candidate.py` | 278,717 | `7c7edb28f459618b1f35538e444b9cf40e70026b02fd0919ded9a20097f9014d` |
| launcher tracked raw bytes, `databricks/notebooks/b08_n1_uc_native_overlay_lock_candidate_launcher.py` | 9,693 | `d47dec6532bd660bbb03c336a9b1b19081d3f4b012a94fb462b87025865aa1a3` |
| launcher canonical identity payload | 9,692 | `7035ee3fdee6fb6b50005798f8c178a140ee1d3727471d8a58ef160f66f57afb` |
| `tests/unit/test_b08_n1_uc_native_overlay_lock_candidate.py` | 167,998 | `373928da75645e1ecb81e14867218d546dfb933663a29da1b317ab0e953067e3` |
| `tests/unit/test_b08_n1_uc_native_overlay_lock_candidate_launcher.py` | 12,120 | `1a20e4d14abbdd8f0c998933ebcb03267a1631847026c0f3ab9f661ee287299a` |
| `requirements/b08-n1-candidate-003-project-source-snapshot-v1.json` | 726 | `1e9ee7f36286333e7f8936acf61068597c7ea23338b663aad7cabd441c794ebe` |

The canonical launcher identity removes exactly one optional terminal LF from
the tracked source payload. The tracked 9,693-byte payload therefore has a
9,692-byte canonical identity. A materialized launcher with or without that one
LF has the same accepted canonical identity only if every other byte is exact.
Runtime presentation mode is not used as launcher or builder identity; the
canonical source mode is `0644`.

The builder itself remains exact-byte bound. No terminal-byte normalization is
permitted for the builder.

## 3. Reviewed project-source snapshot

The hard-pinned snapshot selects exactly:

- `README.md`;
- `pyproject.toml`; and
- the recursively sorted 302 Python files under `src/heterodiff/`.

Its reviewed aggregate is:

| Property | Exact value |
|---|---|
| Project-source file count | 304 |
| Project-source total bytes | 18,924,848 |
| Project-source manifest SHA-256 | `0e2decc9d0c6dbb4ff6b41dec4ee78b6139ea2aa8a419880e3e06ff4f8716021` |
| Offline-reviewed Git commit declaration | `c13b3ac0d8585b6af65f3aac6bfff16872ce9f55` |
| Offline-reviewed commit/source epoch | `1788447596` |
| Canonical staged source mode | `0644` |

The commit and epoch are an offline review declaration, not runtime Git
attestation. The snapshot explicitly records:

- `runtime_git_metadata_required=false`;
- `live_git_checkout_identity_claimed=false`; and
- `whole_repository_cleanliness_claimed=false`.

The snapshot file is a separately pinned provenance anchor. The builder and
launcher are separately bound execution sources and are not smuggled into the
304-file build-input aggregate.

## 4. V2 source-identity proof

The active V2 route does not call the Git CLI to establish runtime source
identity. Instead it:

1. opens the pinned snapshot and selected sources through physical no-follow
   paths;
2. requires the snapshot's exact 726-byte canonical ASCII JSON representation
   and SHA-256;
3. reconstructs the exact ordered 304-file manifest, file count, aggregate
   bytes, and domain-separated manifest digest;
4. verifies the exact builder bytes and canonical launcher identity;
5. emits a domain-separated V2 source-identity record and V2 review package;
6. repeats the same proof immediately before intent;
7. compares that proof with the default preflight result;
8. writes the durable intent only after that equality check; and
9. repeats the complete source proof after intent and before any network or
   build command.

The copied build tree is created only from the bound 304-file manifest and each
copied payload is rechecked against its source record. Any selected-source,
builder, launcher, snapshot, count, size, order, or digest change fails closed.

This proves equality to the offline-reviewed selected content snapshot. It does
not prove a live Git `HEAD`, live index, whole-worktree cleanliness, unselected
file state, repository hosting state, or remote provenance. Files outside the
selected 304-file build-input set and separately bound execution/evidence files
are outside this source-identity claim.

## 5. Fixed target and append-only namespace

The only selected managed-storage parent remains:

`/Volumes/development/team_eds_supplychain/b08_runtime_output`

The fixed candidate identifier remains `b08-n1-overlay-candidate-003`. Its
virtual prefix and all 132 reserved flat leaf names must be absent at preflight:

- one attempt-intent object;
- 128 ordinal payload-chunk names;
- one payload manifest;
- one construction-success receipt; and
- one construction-failure receipt.

The intent is the first durable candidate object. Used chunks are contiguous
from ordinal zero and precede the manifest. A success receipt is written last
and is the only success commit marker. Every managed leaf uses exclusive create,
complete close, and two fresh exact size/SHA-256 readbacks. Custody does not
depend on `fsync`, `chmod`, device/inode, timestamps, rename, deletion, repair,
or a candidate-directory identity.

Immediately before success publication, the builder rebinds every expected
present object and requires every expected absent reserved object to remain
absent. If success-receipt creation may have begun or a success object becomes
visible, the result is terminally ambiguous and a contradictory failure receipt
is forbidden.

## 6. Hash-first and authorization boundary

The builder must be entered through the exact reviewed launcher. The launcher:

1. reads the builder once through no-follow descriptors;
2. verifies the operator-supplied exact builder SHA-256;
3. computes its own canonical launcher identity;
4. supplies the exact V2 launch-evidence shape; and
5. compiles and executes the same in-memory builder bytes it hashed.

The launch evidence is procedural operator attestation. The launcher cannot
cryptographically self-attest its own executing cells.

Construction requires the hash-first evidence plus all four independently
deliberate builder gates:

1. `EXECUTION_MODE=CONSTRUCT_ONE_UC_NATIVE_REVIEW_PENDING_CANDIDATE_003`;
2. `NETWORK_AND_BUILD_AUTHORIZED=True`;
3. `ONE_SHOT_ACKNOWLEDGEMENT=AUTHORIZE_ONE_DATA_FREE_N1_UC_NATIVE_NETWORK_BUILD_CANDIDATE_003`; and
4. `REVIEW_PACKAGE_AUTHORIZATION=AUTHORIZE_REVIEWED_CANDIDATE_003_PACKAGE_SHA256_<independently-reviewed-package-sha256>`.

The locally reproduced default-off Gitless path and launcher-to-builder path
both passed and emitted review-package SHA-256
`5404dd580fac351e888d40836a399d5490396f35df576013eb1a78ecd20d9b23`.
That local digest is evidence for source review only. It is not a construction
authorization token. A Databricks default-off preflight must independently
reproduce the package, and its complete output must be reviewed before any
future token may be issued.

No standing or reusable authorization exists.

## 7. Isolated dependency construction retained from V1

Only after an exact authorized intent commit, the builder may:

1. create a transient staging root and pip-free isolated virtual environment;
2. bind the host `pip==25.0.1` installation and declared payload closure;
3. download wheel artifacts only from the fixed HTTPS PyPI and PyTorch CPU
   indexes, without URL credentials;
4. retain and hash-lock bootstrap and build-tool wheels;
5. build `heterodiff==0.1.0` from the copied source-only tree;
6. resolve a wheel-only transitive set for `numpy==2.4.6`, `scipy==1.17.1`,
   `threadpoolctl==3.6.0`, `torch==2.12.1+cpu`, and `heterodiff==0.1.0`;
7. create and verify an exact `--require-hashes` F152 lock candidate;
8. install only into a separate overlay and verify distribution, metadata,
   RECORD, entrypoint, ownership, and installed-payload closure; and
9. create a deterministic stored ZIP64 archive and publish bounded 256 MiB
   ordinal chunks followed by a content-bound manifest.

Archive verification and chunk planning use the same pinned no-follow file
description with full-hash bookends. The base Databricks Python environment is
never an installation target.

Downloaded tools run as bounded child processes in a replacement environment
with staging-local home, cache, configuration, and temporary roots. They are
not OS-sandboxed. The builder therefore does not claim that third-party code
cannot read unrelated files, create effects outside staging, or contact an
endpoint beyond the configured package indexes.

## 8. Failure and terminal-state semantics

Each network/build child has a 30-minute timeout, 16 MiB bound per output stream,
process-group termination, bounded reaping, and reader-thread cleanup. Failure
records retain bounded sanitized output tails, captured-byte counts and hashes,
bytes observed before termination, capture-completeness flags, exact step/code,
and bounded internal detail.

After intent, a normal failure may publish one failure receipt only after intent
custody is reverified and success remains freshly absent. Any namespace with a
committed or possibly committed intent, payload, manifest, or terminal receipt
is spent or ambiguous and requires independent review. It must not be repaired,
deleted, or reused.

## 9. Verification and nonclaims

The exact focused builder/launcher suite passed **194/194**. The broad B08
selection passed **695/695**. Two independent hostile audits reported P0/P1/P2
**0/0/0**. The final local Gitless default-off preflight and the full
launcher-to-builder default-off path both passed their intended source and
review-package checks.

This source acceptance proves no:

- Databricks candidate construction;
- live Git checkout identity or whole-repository cleanliness;
- dependency availability at a future time;
- atomic snapshot, cache coherence, immutability, or historical object lineage;
- physical durability or capacity reservation;
- F151 production-environment digest;
- canonical F152 lock value;
- effective whole-runtime satisfaction;
- study/test-data readiness;
- calibration, training, inference, result, or scientific claim; or
- release or submission readiness.

Candidate-003 remains absent and unspent. Construction remains unauthorized.

## 10. Exact next default-off Databricks steps

1. Commit and push the exact reviewed V2 builder, launcher, tests, and pinned
   snapshot, then pull those exact bytes into the Databricks Git folder.
   Commit/push/pull is transport and review custody; runtime `.git` visibility is
   not required or claimed.
2. Attach the same dedicated DBR 17.3 x86_64 CPU cluster with the already
   verified deterministic environment. Do not attach or inspect study/test data.
3. Open only
   `databricks/notebooks/b08_n1_uc_native_overlay_lock_candidate_launcher.py`.
   Do not run the builder directly.
4. Use **Run all** once with launcher input left at its default
   `NOT_AUTHORIZED`. It must return
   `HOLD_REVIEWED_BUILDER_SHA256_REQUIRED` and `builder_executed=false`.
5. Enter exact builder SHA-256
   `7c7edb28f459618b1f35538e444b9cf40e70026b02fd0919ded9a20097f9014d`
   in the launcher's builder-hash widget and use **Run all** once more.
6. Leave all four builder construction inputs at their defaults:
   `PREFLIGHT_ONLY`, network/build `false`, one-shot acknowledgement
   `NOT_AUTHORIZED`, and review-package authorization `NOT_AUTHORIZED`.
7. The output must remain
   `HOLD_PREFLIGHT_INPUTS_OR_AUTHORITY_INCOMPLETE` solely because the
   construction gates are intentionally absent. It must report no preflight
   errors, exact runtime and environment, exact source-snapshot identity,
   hash-first launch evidence, an absent virtual prefix and all 132 reserved
   leaves absent, and review-package SHA-256
   `5404dd580fac351e888d40836a399d5490396f35df576013eb1a78ecd20d9b23`.
8. Return the complete JSON for independent review. Do not enable any
   construction gate and do not authorize network/build.

Only a later, separately reviewed authorization can consider one construction
attempt. Even a successful candidate construction would remain review-pending
and would not itself close a project task or field.

## 11. Project-state effect

This V2 source acceptance closes no operational timetable task.

- Marked tasks: **62 checked / 101 open / 163 total**
- Fields: **24 open / 148 closed**
- Blockers: **7 OPEN / 5 CLOSED**
- Formal Tests 28/29/30: **OPEN / OPEN / PENDING**
- Result slots: **0/4**
- F151/F152: **OPEN and null**
- B08: **OPEN**
- Wave 2: **OPEN**

The exact project-state delta is zero.
