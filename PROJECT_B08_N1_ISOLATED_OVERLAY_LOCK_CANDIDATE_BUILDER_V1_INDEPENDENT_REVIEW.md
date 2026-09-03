# Independent hostile review: B08 N1 isolated overlay/lock candidate builder V1

## Review disposition

**`PASS_N1_ISOLATED_OVERLAY_LOCK_CANDIDATE_BUILDER_V1_ZERO_DELTA`.** The
exact frozen Databricks notebook and focused test file below are accepted as a
narrowly bounded, data-free builder for one review-pending native overlay and
F152-lock candidate.

- P0: 0
- P1: 0
- P2: 0
- Exact eligible project, field, blocker, result, and timetable delta: **zero**
- B08 and Wave 2 remain `OPEN`.
- F151 and F152 remain `OPEN` and null.
- F153 retains only its previously accepted prospective-policy status.

This review does not execute the notebook and grants no standing or reusable
Databricks, network, dependency-resolution, installation, runtime-capture,
data, calibration, training, inference, scientific-execution, field-closure,
blocker-closure, B08-closure, or tracker authority.

## Exact frozen bytes reviewed

| File | Bytes | SHA-256 |
|---|---:|---|
| `databricks/notebooks/b08_n1_isolated_overlay_lock_candidate.py` | 128,477 | `0f340a8a7cd8c789709a152e407443a2f104181b9ea006b852b5751ef4c8ecbe` |
| `tests/unit/test_b08_n1_isolated_overlay_lock_candidate.py` | 84,211 | `ae1162f60786bb1414576afa4ec7fb2d967e9cd33d1110ff671d3edaa2fd8b2f` |

All findings and conclusions in this review apply only to these exact bytes.
Every earlier builder revision and hash is superseded for this purpose.

## Exact predecessor and endpoint bindings

The notebook fails closed unless it observes the separately accepted V2 target
under these exact bindings:

| Binding | Exact value |
|---|---|
| Profile path | `requirements/b08-databricks-aws-dbr17.3-x86_64-cpu-py312.native-runtime-profile-v2.template.json` |
| Profile schema | `heterodiff-b08-databricks-native-runtime-profile-v2` |
| Profile ID | `b08-databricks-aws-native-dbr17.3-ubuntu24.04.4-linux-x86_64-cpu-py312-v2` |
| Profile record-digest domain | `heterodiff/b08/databricks-native-runtime-profile/v2\0` |
| Profile canonical file SHA-256 | `4058d9e236733698a0a97022156cfbedd4af308b541883c2cc687d8b9a7840f6` |
| Profile domain-separated semantic SHA-256 | `d5994e8158737b2d1cbd369b347698e131256639b93e5a33ac1ba7ee49c098c3` |
| V2 independent-review path | `PROJECT_B08_NATIVE_DATABRICKS_RUNTIME_TARGET_SUCCESSOR_V2_INDEPENDENT_REVIEW.md` |
| V2 independent-review SHA-256 | `0d75872dc984fbbaf671875407b082dfb447bc007e55572158ed23383c2df450` |

The two accepted package-index endpoints are immutable source constants rather
than operator input:

- `https://pypi.org/simple`; and
- `https://download.pytorch.org/whl/cpu`.

Credentials and alternative indexes are not accepted. Any endpoint or mirror
change requires new notebook bytes and a new independent review.

## Default path and one-shot gates

Direct execution with defaults returns a structured hold with
`construction_authorized=false`. It reports every write, subprocess-backed
package operation, network/contact, Spark, Databricks REST, study/test-data,
calibration, training, and inference safety flag as false.

The tracked notebook receives operator input through one text widget and three
bounded dropdowns. Construction can become eligible only when all of the
following are simultaneously exact:

1. the destination names a previously absent child below
   `/Volumes/<catalog>/<schema>/<volume>/...`;
2. execution mode is `CONSTRUCT_ONE_REVIEW_PENDING_CANDIDATE`;
3. network/build authorization is `true`; and
4. the acknowledgement is
   `AUTHORIZE_ONE_DATA_FREE_N1_NETWORK_BUILD_WITH_NO_BASE_INSTALL`.

The canonical repository F152 lock must remain absent. Existing `/Volumes`
ancestors must remain physical directories with the preflighted device/inode
and mode bindings. The destination root is created exclusively and cannot be
reused. The attempt is spent when its durable intent is committed, before the
first Git, network, virtual-environment, package, build, or publish subprocess
or operation.

An explicit repository-root override remains authoritative. Otherwise the
notebook checks the executed notebook's `__file__` ancestry and then current-
working-directory ancestry. The unrelated-working-directory route was tested
and remained structured and read-only.

## Exact source and Git provenance

Before intent, the notebook hashes the selected source bytes and the builder
notebook without invoking Git. After durable intent and before any network or
build phase, Git is invoked through a fixed `/usr/bin:/bin` path and a stripped
environment. System/global configuration, prompts, lazy fetch, optional locks,
hooks, fsmonitor, recursive submodules, and replacement objects are disabled.
Local include, filter, external diff/textconv, worktree-config, fsmonitor, hook,
and submodule-update execution surfaces are rejected.

The selected source path set is exactly:

- `pyproject.toml`;
- `README.md`;
- every regular `src/heterodiff/**/*.py` source; and
- the construction notebook as a separately bound provenance object.

The bound set must equal both the Git index set and the exact `HEAD` tree set.
Each worktree file's SHA-256, size, canonical executable/non-executable mode,
and direct Git blob SHA-1 must match the corresponding `HEAD` blob and mode.
Git status must then be empty. This rejects ignored or untracked Python source,
ignored or untracked builder bytes, sparse/missing selected source, staged or
worktree substitutions, mode changes, and Git replacement-object substitution.
The verified provenance summary is bound into both the candidate manifest and
the construction receipt.

The Git revision is deliberately null in the pre-network intent and marked for
post-intent verification. The later manifest/receipt bind the verified revision
and commit epoch together with the pre-intent source manifest and exact builder
hash. Source bytes are rehashed after copying into the private staging tree.

## Durable custody, no-clobber publication, and terminal semantics

The notebook commits canonical `attempt-intent.json` exclusively, fsyncs and
reopens it, and retains an `O_DIRECTORY`/`O_NOFOLLOW` descriptor to the exact
attempt-root inode. Before every post-intent subprocess and every build or
publish boundary it reopens and rehashes the intent through that descriptor,
verifies the retained device/inode, and requires the declared path still to
resolve to the same root before normal work proceeds. Child processes use
`close_fds=True`.

After creation, the retained directory device/inode is the custody authority;
the mutable pathname is only a locator. Simultaneous pathname/root/leaf
authority cannot be honestly established across separate userspace calls. The
notebook therefore explicitly forbids external concurrent root mutation and
marks final declared-path-to-retained-root binding as unproven. Candidate
acceptance must later rebind the declared path, retained root, intent, manifest,
and receipt. A hostile rename/replacement before a tool step fails before the
subprocess or phase flags. If external replacement occurs during final receipt
publication, the receipt remains bound to the retained inode and the candidate
remains review-pending rather than being falsely accepted at the replacement
path.

All durable leaves are created with `O_EXCL` and `O_NOFOLLOW`, written fully,
fsynced, directory-fsynced, reopened, and reverified for device/inode, SHA-256,
size, and safe mode. Publication operates through retained/openat descriptors
and never overwrites an existing object. Source file modes are restricted to
safe non-group/world-writable values, applied with `fchmod` so the umask cannot
silently alter them, and included in the durable published-file manifest.
Independent probing reproduced exact `0755` preservation for an executable
overlay script.

Partial publication is terminal and preserves already written evidence. A
failure receipt is no-clobber and records truthful phase telemetry. Success is
committed only after artifact publication and transient-staging cleanup. Any
exception or interrupt after success-receipt publication begins is treated as
terminal receipt ambiguity and suppresses a contradictory failure receipt.
Descriptor-close, initial-binding, directory-fsync, preexisting-leaf,
post-write interrupt, leaf-swap, and retained-root replacement paths were all
reviewed or exercised fail-closed.

## Isolated build, wheel, lock, and overlay audit

The builder does not install into or import from the mutable Databricks base
environment. It creates a private temporary virtual environment with
`system_site_packages=False`, records the bundled `ensurepip` wheel bindings,
strips ambient pip/user configuration, and binds every later Python/pip call to
the isolated interpreter. Exact `pip==25.0.1`, `setuptools==74.0.0`, and
`wheel==0.45.1` artifacts are first downloaded as wheels, inspected, locked by
hash, installed only into that virtual environment, and then version-verified.

The project wheel is built without dependency resolution or build isolation
from the copied, Git-provenance-verified source. Runtime resolution accepts
wheels only. Every wheel directory rejects nonregular objects, non-wheel
objects, source distributions, and duplicate normalized distributions.

Each wheel is inspected for safe and unique archive paths, exactly one
`METADATA`, `WHEEL`, and `RECORD`, complete member coverage, SHA-256 hashes,
sizes, and embedded identity. The candidate lock contains an exact normalized
name/version and SHA-256 artifact hash for every resolved wheel, including the
project wheel and the complete transitive resolver output.

Overlay installation uses only the local wheelhouse with `--no-index`,
`--require-hashes`, `--only-binary=:all:`, `--ignore-installed`,
`--no-compile`, and an isolated prefix. Installed identities must equal the
lock exactly. Every installed payload object must be a regular, `RECORD`-
declared file with its declared hash and size. Console-script paths are
accepted only after lexical normalization proves they remain inside the
overlay. Escapes and duplicate ownership fail closed. Separate payload and
ownership manifests are hashed; the payload manifest includes file modes, and
durable publication preserves and rebinds those modes.

The review-pending manifest binds the durable intent, retained root identity,
V2 profile and review, exact Git/source/builder provenance, official indexes,
`ensurepip`, isolated build tools, project wheel, F152-lock candidate, every
wheel artifact, overlay payload/ownership, and command journal. The success
receipt is not staged and is the final durable leaf.

## Focused and hostile verification

The exact frozen focused suite passed from the repository root:

```text
49 passed
```

The same exact focused suite passed from an unrelated `/private/tmp` working
directory:

```text
49 passed
```

The V1 profile, V2 profile, and N1 builder suites passed together:

```text
96 passed
```

The broader B08/Databricks regression selection passed:

```text
414 passed
```

The 49-case focused matrix covers default HOLD/no-operation behavior, widget
immutability, unrelated-CWD discovery, structured preflight failure, overlay
containment and ownership, durable intent-before-tool enforcement, root and
intent fsync, retained-root/path replacement, success/failure receipt races and
interrupts, one-shot non-reuse, partial no-clobber publication, exact executable
mode preservation, tampered intent rejection, truthful telemetry, hardened Git
configuration, exact tracked-source acceptance, ignored-source rejection, Git
replacement-object rejection, ignored-builder rejection, descriptor cleanup,
structured pre-intent failures and interrupts, terminal-receipt ambiguity, V2
and builder binding, wheel-only/hash-lock guards, and final receipt ordering.

Both files parse as Python ASTs, contain no duplicate literal dictionary keys,
and pass `pyflakes`. The reviewed paths contain no trailing whitespace.
Independent probes in addition to the suite confirmed:

- a `0755` staging executable remains `0755` durably and is mode-bound in the
  published-file manifest;
- ignored Python source is rejected as
  `BOUND_SOURCE_DIFFERS_FROM_GIT_INDEX_PATH_SET` before network begins; and
- an injected pre-intent `OSError` becomes
  `PRE_INTENT_CONSTRUCTION_FAILED`, with no destination and every durable/network
  flag still false.

## Zero-delta authority and limitations

The notebook is a candidate constructor, not a production runtime capture or a
scientific route. It does not call Spark or Databricks REST APIs, access study
or test data, import project/scientific modules into the controlling process,
calibrate, train, infer, inspect scientific results, modify the base runtime,
write the canonical repository lock, or edit the README, evidence ledger,
timetable, or tracker.

Even a successful receipt is explicitly
`CANDIDATE_CONSTRUCTED_REVIEW_REQUIRED_DO_NOT_INSTALL`. It does not establish:

- declared-path-to-retained-root binding at later review time;
- F152 independent acceptance or canonical-lock closure;
- F151 production-runtime manifest closure;
- F153 effective whole-runtime or driver/worker equivalence;
- scientific-execution readiness; or
- any blocker, B08, Wave-2, timetable, field, result, or manuscript transition.

No package-index contact, dependency resolution, candidate construction, or
Databricks execution occurred during this source review. Actual `/Volumes`
filesystem capability and the resolved artifact set remain operational facts
for the separately authorized attempt and later candidate review.

## Narrow next eligible action

The current local package must first be committed, pushed, and pulled into the
matching Databricks checkout so the notebook, selected source, V2 package, and
review records are exact tracked `HEAD` bytes. An uncommitted or untracked
checkout will fail the reviewed provenance gate after consuming the attempt.

After that transfer, the sole newly eligible operational action is a separately
and explicitly authorized **single execution of the exact frozen notebook** to
construct one data-free, review-pending V2-bound isolated overlay/F152-lock
candidate at one previously absent durable `/Volumes/...` destination.

That authority must bind at least:

- notebook SHA-256
  `0f340a8a7cd8c789709a152e407443a2f104181b9ea006b852b5751ef4c8ecbe`;
- this accepted builder package and its exact predecessor hashes;
- one exact new `/Volumes/...` destination;
- the two fixed official index endpoints; and
- the three exact construction widget-gate values above.

The authority is consumed when durable intent is committed, even if a later
phase fails. A failed, partial, or ambiguous attempt must not be retried or
reused under the same authority or destination. The resulting candidate must
receive a separate independent review that rebinds its declared path, retained
root, intent, receipt, lock, artifacts, installed payload, ownership, modes,
and provenance before any canonical lock write, production-runtime overlay
installation, F151/F152/F153 transition, scientific execution, B08/Wave-2
closure, or tracker change is considered.

## Final finding

No critical, major, or minor default-path, authorization, provenance,
replacement-object, isolation, custody, telemetry, mode-preservation,
wheel-only, hash-lock, overlay-closure, no-clobber, structured-failure, or
authority-boundary defect remains in the exact frozen bytes. They may be
retained as the zero-delta builder V1 package and used only for the narrow
one-shot candidate-construction step described above.
