# Formal Tests 29–30 two-macrostep parent-custody remediation: independent review

**Review date:** 2026-09-01  
**Reviewer lane:** `/root/regression_inventory`  
**Reviewer role:** independent read-only source-custody and hostile-path review  
**Verdict:** `GO_HASH_FIRST_PARENT_CUSTODY_ENVELOPE_ONLY`  
**P0/P1/P2 findings in remediation scope:** `0/0/0`

## 1. Scope and P2 disposition

This receipt accepts only the additive hash-first parent-source custody
envelope for the already accepted two-macrostep development precursor. The
previous review's P2-01 is resolved for use through this exact wrapper. The
direct generic candidate API remains accurately unauthenticated and continues
to report `parent_custody_authenticated=False`; it is not an authoritative
reusable admission entrypoint.

The wrapper, rather than the generic API, separately returns
`envelope_parent_source_custody_authenticated=True` only after all four exact
source pins, the complete qualification, and post-execution identity checks
pass. This receipt is external to the wrapper and its pins.

## 2. Exact remediation artifacts

All three files were exact regular files with mode `0644` and link count `1`.

| Path | Bytes | SHA-256 |
|---|---:|---|
| `PROJECT_FORMAL_TEST29_TEST30_TWO_MACROSTEP_PARENT_CUSTODY_REMEDIATION.md` | 3,214 | `49510017a07db1731c7806db704cd041213f12fd4e639825121dcfd765447c0a` |
| `research/diagnostics/formal_test29_test30_two_macrostep_parent_custody_hash_first_v1.py` | 12,105 | `e71f145bc73b47a8d6a19329e05989523d0ca14d5726c4b02a8ec0e07f9a455e` |
| `tests/unit/test_formal_test29_test30_two_macrostep_parent_custody_hash_first_v1.py` | 7,266 | `843955aba3fb40a9911dfd82e2a0ff1b1eefeffc06125b4c08753770bf5221c3` |

The envelope independently pinned these accepted sources before any project
source was compiled:

| Role | Bytes | SHA-256 |
|---|---:|---|
| Two-macrostep candidate | 59,285 | `d1c3013aa0f4e7b31e19cef98d4aa5edf7991c5b8634dbfe091f8053b1808176` |
| Single-macrostep parent | 61,434 | `e2f57ede06cb432f8507eb32eead7a77fbfc8d8d44cc7725a941182e7aedd0c7` |
| Test-29 parent | 52,186 | `308a16090128871c9a79cdaff265d3b6633e18b062a605b257f3173198d8a089` |
| Test-30 parent | 42,349 | `373ef98c3605e0c0211da8dbc8782f2517cd5976026980e4fcd24435670839e0` |

## 3. Security review

The reviewer confirmed that the envelope completes componentwise no-follow
capture and exact length/digest plus regular mode-`0644` single-link custody
checks for the entire four-source roster before the first compile. Immediately
before compilation it independently rechecks the captured object type, path,
length, raw digest, declared digest, mode, link count, and complete roster.

Only captured buffers are compiled, under non-`__main__` exact `ModuleType`
names. The four temporary `sys.modules` slots are restored to their exact prior
presence and object values on successful and exceptional exits. After the
qualification, all four paths are reopened and required to retain identical
device, inode, UID, GID, mode, link count, size, digest, modification time, and
change time.

Hostile tests proved that:

- drift at each of the four precompile positions is rejected without executing
  its marker payload;
- post-capture path substitution cannot change the compiled module bytes;
- a forged captured mapping is rejected before compile;
- a schema-compatible, required-symbol-present, self-restoring parent payload
  never executes; and
- unsafe mode and hard-link custody are refused.

## 4. Qualification evidence

With bytecode generation disabled and the pytest cache provider disabled, the
independent focused suite passed `11/11`. Direct wrapped validation reproduced:

- all `1,024` ordered low-word pairs;
- `1,024` distinct input digests;
- `1,024` distinct report digests; and
- aggregate report SHA-256
  `2a278585373d017b3b60bed28dcbc0ab3830f72c0512891658fc2ab54c666d53`.

The owner-lane candidate-plus-parent regression passed `276/276`, and the
expanded accepted-package union including both overnight security envelopes
passed `1,080/1,080`.

## 5. Non-effect boundary

The wrapper result preserved formal-test, field, blocker, result-slot, and
tracker-edit counts at `0/0/0/0/0`. Review found no entropy, clock, network,
subprocess, filesystem output, data/protected-input, runtime-receipt, or
scientific-execution surface in the wrapper or exact executed sources.

This remediation closes only the wrapper-use source-custody gap. It closes no
timetable task, Formal Test, field, blocker, result, or scientific gate and
makes no production, arbitrary-length path, live-source, continuous-Gaussian,
or step-halving claim.
