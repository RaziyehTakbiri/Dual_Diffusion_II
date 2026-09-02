# R1-A1 outcome-independent replacement-seed draw freeze V1

**Freeze:** `A1-R1-REPLACEMENT-SEED-DRAW-FREEZE-V1`  
**Milestone:** `R1_A1_SEED_DRAW_AUTHORIZED_NOT_YET_CONSUMED`  
**Global manuscript state:** `DRAFT_NOT_EXECUTABLE`  
**Entropy contacted:** no  
**Seed drawn:** no  
**Rank, training, or production execution:** none

## 1. Purpose and exact authorization

This additive pre-draw freeze authorizes one future operating-system-backed draw
to replace the development-exposed seed `1729` while preserving an eight-seed
paired design. It does not draw the replacement in this milestone. The attempt
marker, pending directory, terminal output directory, entropy, replacement
seed, and replacement registry are all absent at freeze time.

The normalized recommendation was exactly:

> One material statistical choice prevents an executable R1 freeze: should we preserve eight paired seeds by generating a new outcome-independent replacement for 1729—recommended—or proceed with seven clean seeds?

Its UTF-8 SHA-256 is
`c15926195485cf8f6245fc57aca0c6951d408a7f33844551e596db061caacbb2`.
The normalized assent was exactly:

> Please move forward with your recommended option above.

Its UTF-8 SHA-256 is
`0a8ee5fc5192bd9e2a6c11150e01b26418896eba08eb01af23eb6a210359e301`.
UI formatting and trailing whitespace were normalized away; the Unicode text
shown above was preserved and encoded as UTF-8. Together these texts resolve
the branch as `ONE_REPLACEMENT_KEEP_EIGHT`. They are authorization evidence,
not selection inputs, not entropy, and not inputs to the seed mapping.

## 2. Why seed 1729 is excluded

D1 observed the coordinate `seed=1729`, `method=guided`, and accepted-example
budget `32768`. The exposure disposition is conservatively seed-wide:
`PILOT_NONCONFIRMATORY_EXPOSED` across all methods, lanes, and budgets, with a
budget wildcard where a budget is not applicable. The enumerated primary
coordinate is not an exhaustive exposure boundary.

The exclusion is driven only by the fact of prior development exposure. D1 metrics,
metric directions, checkpoint bytes, hashes, timestamps, process or
host metadata, and runtime metadata are not selection inputs. D1 cannot define
the success rule, metric, threshold, checkpoint, confirmatory seed count, or
overflow policy. D1 remains development evidence and is not admissible as an
R1 execution input or production evidence.

## 3. Exact unbiased mapping

The safe JSON-integer universe is

```text
U = 2^53 = 9007199254740992
```

The eight excluded historical seeds are

```text
E = (1729, 3253, 5003, 7411, 10007, 13007, 16001, 20011)
```

There are

```text
M = U - 8 = 9007199254740984
```

allowed seeds. After the durable attempt marker exists, the implementation
calls `secrets.token_bytes(32)` exactly once and interprets those bytes as an
unsigned big-endian 256-bit integer `X`. Since `2^256 mod M = 64`, the exact
acceptance limit is

```text
L = 2^256 - 64
```

If `X >= L`, rejection burns the attempt and produces terminal failure with no
replacement registry. There is no redraw, top-up, second entropy call, or
seven-seed fallback. If `X < L`, the allowed-set rank is `j = X mod M`.

The rank is deterministically unranked in ascending integer order. Begin with
`candidate=j`; for each excluded seed in ascending `E`, increment the candidate
once when `candidate >= excluded`. The accepted candidate is therefore uniform
on `[0,2^53) \\ E` under a uniform 256-bit source, without modulo bias.

On success the registry is exactly

```text
(replacement, 3253, 5003, 7411, 10007, 13007, 16001, 20011)
```

The replacement occupies ordinal zero. The seven nonzero ordinals are not
sorted around it or otherwise changed. The registry remains length eight and
contains eight unique safe integers.

The downstream projection is frozen before the replacement is known: exact
population has `3 x 8 = 24` coordinates; primary has `2 x 3 x 8 = 48`;
controls have `3 x 3 x 8 = 72`; the complete sampled campaign has `120`; and
the named all-including-exact total is `144`. Ordinal-zero substitution applies
across every method, lane, and budget. Numeric resorting, post-draw grid
pruning, and partial-lane substitution are forbidden.

## 4. One-attempt custody and failure semantics

The paths reserved for the future draw are:

- marker:
  `artifacts/manuscript_v3_a1_r1_replacement_seed_draw_v1.attempt.json`;
- private terminal construction directory:
  `artifacts/.manuscript_v3_a1_r1_replacement_seed_draw_v1.pending`; and
- terminal output directory:
  `artifacts/manuscript_v3_a1_r1_replacement_seed_draw_v1`.

The `artifacts` parent must be a real, nonsymlink directory resolving inside
the workspace. The marker is durable before entropy: it is created as a new
regular file with `O_EXCL` and `O_NOFOLLOW`, file-fsynced, parent-directory
fsynced, and reopened byte for byte. A preexisting marker, pending entry,
terminal entry, symlink, concurrent launch, or protected production root fails
closed before entropy.

All eleven closure-V2 production roots and the formal runtime-identity manifest
are dynamic absence gates. One shared check runs before the marker, immediately
before terminal publication, immediately after publication, during the deep
terminal audit, and on every status audit. Appearance at any boundary burns or
invalidates the attempt and cannot be accepted as success.

Once the marker is durable, the attempt is permanently consumed whether the
entropy call succeeds, rejects in the 64-value tail, returns malformed bytes,
raises, or the process is interrupted. There is no retry and no recovery that
contacts entropy or selects again. A marker with no terminal directory is
`ATTEMPT_SPENT_TERMINAL_ABSENT_OR_PENDING_NO_RETRY`; any retained pending bytes
are forensic-only. Resolving such a failure requires a new audited additive
decision, never re-execution of this one-shot protocol.

Terminal records are built with exclusive nonsymlink files in the private
directory. Every file and directory is fsynced. All frozen inputs are reopened
before publication. Publication uses an atomic no-clobber kernel directory
rename, so a raced target is never replaced. The published type, exact
closed-world inventory, canonical self-digests, entropy-to-seed calculation,
registry, and receipt hash chain are deeply reopened; all frozen inputs are
revalidated again before the caller returns. A drift burns the attempt and
cannot yield an accepted `SUCCESS` through the auditor.

The terminal auditor does not reuse the production mapping helper. It
independently applies `divmod` and a bounded binary search over the safe seed
universe, so a shared unranking defect cannot validate its own result.

The attempt marker and terminal files are owner-only (`0600`, with no group or
other permission bits). Pending and published terminal directories are
owner-only (`0700`, with no group or other permission bits). The pending and
terminal paths may contain raw entropy and are internal custody material.

The contract says no candidate is printed by execution, status, or audit. Status and freeze
audit touch zero entropy. Live execution is not an importable API and accepts no
supplied workspace root, entropy callback, seed suggestion, metric, or
candidate. It is available only as direct-file `__main__` from the exact
canonical workspace, with the bound CPython 3.11 environment and isolated,
no-site, no-bytecode, safe-path flags. The exact future command is:

```text
.venv-m1/bin/python -I -S -B research/diagnostics/finite_association_r1_replacement_seed_draw.py --execute-one-shot
```

The working directory must exactly equal the machine sidecar's bound
`custody_protocol.canonical_workspace_root`; this human note does not repeat
that internal local path.
Imported execution, alternate-root execution, a noncanonical interpreter or
argument vector, missing `-I -S -B` isolation, and ordinary import/runpy
attempts that monkeypatch entropy refuse before the marker and before entropy.
Synthetic-byte publication helpers are test-private and restricted to temporary
noncanonical workspaces. There is no readable capability key. Every high-level
canonical-root writer rechecks
direct-file `__main__` identity, canonical globals/file/cwd, `sys.argv`, the
full real-interpreter `sys.orig_argv` vector, `sys.executable`, its resolved
interpreter path
`/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11`, and all
four runtime flags before writing. It also independently reopens the native
Darwin process vector through libc `_NSGetArgc` and `_NSGetArgv`, decodes each
entry as strict UTF-8, and requires the exact six-entry vector consisting of
the framework Python application path, `-I`, `-S`, `-B`, the relative module
path, and `--execute-one-shot`. Mutable Python `sys.argv` and `sys.orig_argv`
are not authority by themselves. A `runpy` context with forged Python vectors,
including one launched under `-I -S -B -c`, cannot match the frozen native
process vector and cannot contact entropy or write custody state.

This is a procedural honest-host/process boundary, not a security sandbox. The
native Darwin vector is read independently of Python's mutable copies, but it is
not claimed immutable against an actor who can mutate this process's memory.
The package likewise makes no resistance claim against a same-user actor who
rewrites module globals or replaces and consistently re-registers bound files.
Its refusal claims cover ordinary import, runpy, and Python-vector-only
injection under the recorded environment; they do not claim protection from a
hostile actor already controlling the live process or workspace custody.

## 5. Future terminal records

An accepted draw will atomically publish exactly:

1. `seed-draw-record.json`, including the lowercase 32-byte entropy hex and the
   independently recomputable rank and candidate;
2. `replacement-seed-registry.json`, binding ordinal-zero substitution and the
   immutable eight-seed registry; and
3. `success-receipt.json`, binding marker, draw, and registry raw and semantic
   digests.

An entropy-tail rejection will publish the draw record and
`failure-receipt.json`. An entropy-source exception or invalid-length return
will publish only `failure-receipt.json`, because no valid 256-bit draw exists.
No separate entropy receipt is required. Every failure state is
`INCOMPLETE_NO_REDRAW`.

Even after a successful future draw, the strongest state will be only
`R1_A1_SEED_REGISTRY_FROZEN_NOT_EXECUTABLE`. The draw cannot create a runtime
manifest, source capsule, runner binding, production plan, coordinate permit,
power review, preexecution freeze receipt, rank result, training result, R1 or
R2 result, C17 proof, claim promotion, or submission readiness.

## 6. Bound scientific and custody baselines

The freeze directly reopens and hash-binds the manuscript claim ledger, human
and machine preregistration, scientific-route test, historical CP76 manifest
and readiness test, A1 Specification 62, all four closure-V2 files, the D1
diagnostic record, the E-A1-D1 machine registration, and the macOS-arm64
environment lock. The closure-V2 and D1 semantic self-digests are also bound.

In particular:

- closure-V2 machine raw/self SHA-256:
  `11329efc97d844f5a39223f170e8c4d5ea5341756ed6f89d9e40bbf4e0c529db` /
  `a393df8432e8ffd1b01368879290e090474ce34ab5b67edb102e3400b6cecae4`;
- D1 diagnostic raw/self SHA-256:
  `4b983cd0dcb0e068bfd6d8c47d726e2f02ecb6cf5e17b4f77022d1e10f8c7b10` /
  `68434890dbd3157b70e700d6a649000dbc9ee60e297b9196af46e312beba07e6`;
- E-A1-D1 registration raw/self SHA-256:
  `b52685e2b61a30c5781f0e75138eaae6410063fa2312a447eeed7a4d1902cac0` /
  `d1c52907ba0bbb6b17cb2cb4e930d983623f39c161ad8a116afa43dccbbfa1b9`;
  and
- environment lock raw SHA-256:
  `ba373a4f7ef687e55d6f0a5cbc1f14eaf9db03ab1cf001cc8d6009e85adbbc5d`.

These are static custody inputs. Their bytes and metadata never enter the
mapping.

## 7. Historical seven-source implementation boundary

The historical seven modules hard-code the original seed registry and remain
immutable, custody-only evidence:

| Role | Historical file | Raw SHA-256 |
|---|---|---|
| residual data | `src/heterodiff/experiments/finite_association_residual_data.py` | `30c5d002c2e88238b840b3685f614d9ad42eda48782d655fabc859d6f4f82ac3` |
| residual training | `src/heterodiff/experiments/finite_association_residual_training_torch.py` | `44876731d31705c8c815cd586bf2b03b0490777db6a13ad8679e5199b794f115` |
| exact population | `src/heterodiff/experiments/finite_association_exact_population_torch.py` | `699c609807d5f68a1f36a76eeac5b36b06fa6eef52e6e74cf318acb0faf194c9` |
| sampled isolated runner | `src/heterodiff/experiments/finite_association_isolated_runner.py` | `13e0d042e9bb509e11c4ffc9d2381565f2a939def7a0add38380bfedce63240f` |
| exact isolated runner | `src/heterodiff/experiments/finite_association_exact_population_isolated_runner.py` | `e9ab2ee47d0ccc8ff615187405c948bb5927ffc95ff08607e42e4ed095d662ef` |
| test-only execution order | `src/heterodiff/experiments/finite_association_execution_order.py` | `e31753485aad2d5dc57ab0c5dfa80697ac4a11ab7937c62b4c8875d3038c0185` |
| production order | `src/heterodiff/experiments/finite_association_production_order.py` | `be2b4134672fc2895242d8cbb68d8c540345574f1b31ed8b04a50b88793235e1` |

This package neither patches nor imports those modules and does not monkeypatch
their seeds. A later registry-aware R1 source capsule must be new, additive,
versioned, and explicitly bind the successful registry digest through every
plan, permit, request, consumption record, receipt, and result. The present
freeze does not implement or authorize that future capsule. Historical sources
remain immutable through draw publication and afterward so the receipt stays
auditable. A separate audited post-draw registry-integration/source-amendment
preregistration milestone must preserve the old grid/source bytes, add a
versioned registry-aware adapter or successor source, and bind it before runner
integration is separately authorized. No R1 runner or production execution may
precede those later gates.

## 8. State and publication preservation

There is no rank execution, no training execution, no experiment execution,
no formal runtime manifest, no production plan, no production-order admission,
and no protected production root. R1 and R2 remain `NOT RUN`; C17 remains a
theorem target; the claim ledger, preregistration, CP76 snapshot, result slots,
and manuscript claims are unchanged. The twelve preregistration blockers
remain open. This seed-draw decision does not itself close a scientific or
execution blocker.

All eleven production roots checked by closure V2 remain required absent: the
production-order root, three rank-gate files, exact campaign, sampled campaign,
two primary-metric roots, candidate-decision root, independent-audit root, and
publication-decision root. The formal runtime identity manifest
`requirements/m1-reference-macos-arm64-py311.runtime-identity.json` also
remains absent. This draw cannot create or transition any of them.

This internal freeze, machine sidecar, orchestration source, and hostile test
are not a submission artifact. Raw inclusion in an anonymous submission or
public release is forbidden. In-place sanitization is forbidden. A separate
publication-safe derivative and a fresh anonymity audit are required; no
include/exclude roster is frozen here.

The same exclusion applies to every future raw custody path: the attempt
marker; pending and terminal directories; the raw entropy-bearing draw record;
the replacement registry; and success or failure receipt. Neither pending nor
published custody bytes may enter an anonymous submission or public release.

## 9. Exact new-file boundary

This milestone adds only:

- `manuscript_v3/a1_r1_replacement_seed_draw_freeze_v1.md`;
- `research/fixtures/manuscript_v3_a1_r1_replacement_seed_draw_freeze_v1.json`;
- `research/diagnostics/finite_association_r1_replacement_seed_draw.py`; and
- `tests/unit/test_manuscript_v3_a1_r1_replacement_seed_draw_freeze_v1.py`.

The machine sidecar canonically binds the final exact bytes of the human
freeze, orchestration module, and hostile test, and self-digests its own
canonical record without a hash cycle. No existing file is amended by this
milestone.
