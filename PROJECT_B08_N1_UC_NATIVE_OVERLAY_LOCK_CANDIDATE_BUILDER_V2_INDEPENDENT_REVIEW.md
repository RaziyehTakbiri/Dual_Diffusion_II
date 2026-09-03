# Independent hostile review: B08 N1 UC-native candidate-003 builder V2

## Review disposition

**`PASS_UC_NATIVE_CANDIDATE_003_BUILDER_AND_HASH_FIRST_LAUNCHER_V2_ZERO_DELTA`.**

The exact V2 builder, canonicalized hash-first launcher, tests, and reviewed
content snapshot bound below are accepted for one default-off, data-free
Databricks preflight. They are not accepted for construction.

- P0: 0
- P1: 0
- P2: 0
- Exact eligible project, field, blocker, result, and timetable delta: **zero**
- Candidate-003: **absent and unspent**
- Construction authority: **not issued**
- F151, F152, B08, and Wave 2: **OPEN**

## Exact bytes reviewed

| File or identity object | Bytes | SHA-256 |
|---|---:|---|
| `databricks/notebooks/b08_n1_uc_native_overlay_lock_candidate.py` | 278,717 | `7c7edb28f459618b1f35538e444b9cf40e70026b02fd0919ded9a20097f9014d` |
| launcher tracked raw bytes | 9,693 | `d47dec6532bd660bbb03c336a9b1b19081d3f4b012a94fb462b87025865aa1a3` |
| launcher canonical identity payload | 9,692 | `7035ee3fdee6fb6b50005798f8c178a140ee1d3727471d8a58ef160f66f57afb` |
| `tests/unit/test_b08_n1_uc_native_overlay_lock_candidate.py` | 167,998 | `373928da75645e1ecb81e14867218d546dfb933663a29da1b317ab0e953067e3` |
| `tests/unit/test_b08_n1_uc_native_overlay_lock_candidate_launcher.py` | 12,120 | `1a20e4d14abbdd8f0c998933ebcb03267a1631847026c0f3ab9f661ee287299a` |
| `requirements/b08-n1-candidate-003-project-source-snapshot-v1.json` | 726 | `1e9ee7f36286333e7f8936acf61068597c7ea23338b663aad7cabd441c794ebe` |

The launcher canonical identity removes exactly one optional terminal LF and no
other byte. The builder remains exact-byte bound. Runtime presentation mode is
excluded from execution-source identity and the canonical mode is `0644`.

All findings in this review apply only to these exact objects and identity
rules.

## Triggering V1 evidence

The exact [V1 Databricks preflight HOLD](PROJECT_B08_N1_UC_NATIVE_OVERLAY_LOCK_CANDIDATE_003_V1_DATABRICKS_PREFLIGHT_HOLD.md)
records:

- decision `HOLD_PREFLIGHT_INPUTS_OR_AUTHORITY_INCOMPLETE`;
- sole error `BOUND_SOURCE_GIT_PREFLIGHT_FAILED`;
- inner code `TOOL_STEP_FAILED`;
- detail `git_local_config_safety:returncode=128`; and
- standard error
  `fatal: --local can only be used inside a git repository\n`.

Runtime, deterministic environment, destination absence, and the hash-first
builder binding otherwise passed. V1 made no write, network, package, build, or
scientific operation, and candidate-003 remained unspent.

The runtime launcher presentation was 9,040 bytes,
`8986a7d7b3065f6b82fa6b47d839af4a79b690a2f04d1f81baa9b7fa3e40cd94`,
mode `0755`, compared with the 9,041-byte reviewed V1 launcher
`b974380f2af950a77571eaf0d34317d2858c170458cc6d791cf0794f64366616`,
mode `0644`. The only byte difference was the omitted terminal LF.

## V2 source-identity assessment

V2 correctly removes live Git metadata from the runtime trust boundary. It
binds a canonical 726-byte snapshot whose selected-source projection is:

- 304 files;
- 18,924,848 aggregate bytes;
- manifest SHA-256
  `0e2decc9d0c6dbb4ff6b41dec4ee78b6139ea2aa8a419880e3e06ff4f8716021`;
- offline-reviewed commit declaration
  `c13b3ac0d8585b6af65f3aac6bfff16872ce9f55`; and
- source epoch `1788447596`.

The commit declaration is explicitly offline review context, not a runtime Git
attestation. V2 expressly claims neither live checkout identity nor
whole-repository cleanliness.

The active source proof reopens and verifies the snapshot, complete selected
source manifest, exact builder, and canonical launcher at default preflight,
again before intent, and again after intent before network/build. The build tree
copies only manifest-bound sources and checks every copied payload. Exact
content/count/size/order/digest changes fail closed.

The normalization boundary is narrow and appropriate for the observed
Databricks transformation:

- the builder permits no byte normalization;
- the launcher permits only one optional terminal LF;
- source runtime mode is presentation-only and canonicalized to `0644`; and
- selected build-input content is otherwise exact.

The source identity therefore proves equality to the offline-reviewed selected
content without making an unavailable live Git claim.

## Hash-first and authority assessment

The V2 launcher hashes the exact builder payload, verifies the operator-supplied
reviewed digest, compiles those same in-memory bytes, and emits an exact V2
launch-evidence record containing the canonical launcher identity. A normal
direct builder run lacks this caller-supplied evidence and is not a supported
construction entry point; the evidence is a procedural gate rather than a
cryptographic proof of the active launcher cells.

The builder remains default-off. Construction requires the exact launch
evidence plus execution mode, network/build authority, one-shot
acknowledgement, and an independently reviewed review-package authorization
token. The local Gitless default-off and launcher-to-builder paths reproduced
review-package SHA-256
`5404dd580fac351e888d40836a399d5490396f35df576013eb1a78ecd20d9b23`.
That value is not issued here as construction authority. The actual Databricks
default-off output must first reproduce it and receive separate review.

## Storage, construction, and terminal-state assessment

V2 retains the accepted V1 material protections:

- fixed existing Unity Catalog Volume parent and candidate-003 identifier;
- exact flat 132-leaf namespace with every leaf initially absent;
- exclusive create, complete close, and two fresh content-bound readbacks;
- intent first, contiguous chunks, manifest after chunks, and success receipt
  last;
- full expected-present and expected-absent namespace closure immediately
  before success;
- no custody dependence on POSIX `fsync`, mode, device/inode, timestamps,
  rename, deletion, repair, or candidate-directory identity;
- isolated pip-free environment and no base-runtime installation target;
- retained, wheel-only, exact-hash dependency and build-tool closure;
- exact generated-lock, wheel, metadata, RECORD, entrypoint, installed-payload,
  archive-member, and archive/chunk verification;
- same-descriptor archive hash bookends and bounded chunk planning;
- bounded subprocess output, timeout, termination, reaping, and failure
  diagnostics; and
- suppression of contradictory failure receipts whenever success publication
  may have begun or become visible.

The writer remains correctly limited to probe-001's observed create,
non-overwrite, race, and repeated-readback behavior. It does not claim atomic
snapshots, cache coherence, immutability, physical durability, universal
atomicity, historical lineage, or future FUSE stability.

Downloaded third-party tools are not OS-sandboxed. Their unrelated-file access,
effects outside staging, and exact endpoint confinement remain explicit
nonproofs.

## Verification

The exact focused builder/launcher suite passed:

```text
194 passed
```

The broad B08 family selection passed:

```text
695 passed
```

Two independent hostile audits reported:

```text
P0: 0
P1: 0
P2: 0
```

The final source hashes were stable for the accepted run. Coverage included the
Gitless content-snapshot path, exact snapshot/file/count/size/digest mutations,
launcher terminal-LF and mode presentation, normal direct-builder default hold,
hash-first evidence, default-off authority, pre-intent and post-intent source
rechecks, append-only namespace closure, collision and terminal ambiguity,
wheel/overlay/archive provenance, bounded process failure evidence, and the
local launcher-to-builder review-package path.

No Databricks candidate construction was executed by this source review.

## Historical preservation and nonclaims

The exact [V1 contract](PROJECT_B08_N1_UC_NATIVE_OVERLAY_LOCK_CANDIDATE_BUILDER_V1.md)
and [V1 independent review](PROJECT_B08_N1_UC_NATIVE_OVERLAY_LOCK_CANDIDATE_BUILDER_V1_INDEPENDENT_REVIEW.md)
remain unchanged historical evidence. V2 supersedes only V1's future live-Git,
runtime-mode, exact-terminal-LF, and associated next-action route.

The V1 references still visible in `README.md` are likewise historical. The
README is intentionally byte-preserved because it is a member of the reviewed
304-file build snapshot; the exact V2 action below is the controlling current
route.

This review does not:

- issue candidate-003 construction authority;
- authenticate a live Git checkout, index, remote, or whole-repository state;
- create F151 or F152;
- prove future dependency availability, production runtime satisfaction,
  capacity, or physical storage reservation;
- access or admit study/test data;
- run calibration, training, inference, or a Formal Test;
- fill a result slot;
- support a scientific claim; or
- authorize release or submission.

## Exact next default-off Databricks action

1. Deliver the exact reviewed V2 builder, launcher, tests, and snapshot through
   commit/push/pull. This is content transport; runtime Git metadata is not a
   prerequisite.
2. Attach the same dedicated DBR 17.3 x86_64 CPU cluster with the exact
   deterministic environment.
3. Open only the reviewed hash-first launcher and use **Run all** with the
   default `NOT_AUTHORIZED` value. Require
   `HOLD_REVIEWED_BUILDER_SHA256_REQUIRED` and `builder_executed=false`.
4. Enter builder SHA-256
   `7c7edb28f459618b1f35538e444b9cf40e70026b02fd0919ded9a20097f9014d`
   and use **Run all** again.
5. Leave execution mode at `PREFLIGHT_ONLY`, network/build authority `false`,
   acknowledgement `NOT_AUTHORIZED`, and review-package authorization
   `NOT_AUTHORIZED`.
6. Require an error-free default-off preflight with exact runtime/environment,
   exact reviewed source-snapshot identity, exact hash-first evidence, all 132
   reserved leaves and the virtual prefix absent, and review-package SHA-256
   `5404dd580fac351e888d40836a399d5490396f35df576013eb1a78ecd20d9b23`.
7. Return the complete JSON for independent review. Do not authorize
   construction or network/build.

## Project-state effect

No operational timetable task is marked complete.

- Marked tasks: **62 checked / 101 open / 163 total**
- Fields: **24 open / 148 closed**
- Blockers: **7 OPEN / 5 CLOSED**
- Formal Tests 28/29/30: **OPEN / OPEN / PENDING**
- Result slots: **0/4**
- F151/F152: **OPEN and null**
- B08: **OPEN**
- Wave 2: **OPEN**

The exact project-state delta is zero.
