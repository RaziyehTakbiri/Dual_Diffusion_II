# Independent review: B12 Gate-B0 integration implementation candidate v1

**Review date:** 2026-09-01  
**Decision:** `GO_EXACT_GATE_B0_IMPLEMENTATION_CHECKBOX_REGISTRATION_ONLY`  
**Findings:** P0 = 0; P1 = 0; P2 = 0  
**Authorized registration:** `Runtime identity, runner, capsule, ledger, and recomputation implementations exist.`  
**All other deltas:** zero

## Exact reviewed bytes

This review binds the following seven exact candidate artifacts. Any byte
change invalidates this acceptance and requires a fresh independent review.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `PROJECT_B12_GATE_B0_INTEGRATION_IMPLEMENTATION_CANDIDATE.md` | 7,383 | `023cb2b9c54212af11eca1c218bd6f67ac49277897d03eeab41dd40802799a7c` |
| `src/heterodiff/evaluation/b12_integration_stack.py` | 87,584 | `61ccbc749d0922f2e0aadb63c800952f0b8c5575bd5d884e3e574833cada3b59` |
| `src/heterodiff/evaluation/b12_independent_component_recomputation.py` | 16,684 | `8b2b9de7c1d64f79cb5517894201f6410338fc9ba8323aca34f55a99fcbd1055` |
| `tests/unit/test_b12_integration_stack.py` | 34,479 | `417139b0fcda9ed280647f6bf7d39ff0eb34ac5fe3fed8660702ce1812c00bf5` |
| `tests/unit/test_manuscript_v3_b12_gate_b0_integration_implementation_candidate_v1.py` | 7,972 | `5e928cd5fca422db0643ea9aadf6a810ddbe242796a7280c2f450dc6e67a5453` |
| `research/diagnostics/manuscript_v3_b12_gate_b0_integration_implementation_candidate_v1.py` | 31,423 | `e3706baf2912bce6fd37e1b076fcf67fa8faa0c45d3499906b40cb80c9250ed7` |
| `research/fixtures/manuscript_v3_b12_gate_b0_integration_implementation_candidate_v1.json` | 9,824 | `63c6c7f045b9d0577157938c1368552955619d511c4e25b25a39ba5d52a6a95d` |

The canonical machine record carries the independently reproduced semantic
record SHA-256
`d61a7465f71057bad7c39fd88f2c9cef14e169caab80b7a9319d60c557817e1c`.

## Review result

The exact five implementation surfaces named by the existing Gate-B0 task are
present and focused-tested:

- a strict future caller-supplied `RuntimeIdentityBinding` seam;
- an integrated runner with the exact corrected 22-adapter binding and exact
  50-row residual roster;
- an atomic exact-roster component/evidence capsule;
- a durable paired INTENT/OUTCOME ledger; and
- a genuinely separate integration-level recomputation module that does not
  import the primary integration module.

The capsule physically includes the exact canonical `component-bindings.json`.
The manifest names and hashes that payload, and the accepted `CapsuleReceipt`
includes its digest in the ordered payload roster. Its closed-world claim is
truthfully limited to the component/evidence directory roster; it claims
neither standalone executability nor transitive source/dependency closure.

The deterministic exercise mints no ACCEPT receipt under any of the exact 50
real residual IDs. It exposes 50 exact runner-subject-bound slots, all with
`receipt=None` and `OPEN_RECEIPT_ABSENT`. Local minting for every real residual
ID is rejected. The future production constructor requires a runtime identity,
the complete exact real roster, exact accepted receipt types and subjects, and
rejects nonproduction authentication markers as case-insensitive embedded
substrings.

The adapter manifest is the corrected exact 22-row B06-derived snapshot. The
legacy B12-v2 mismatch at zero-based ordinals 12 through 19 is explicitly
rejected. Canonical path checks reject double separators, `/./` aliases, and
trailing separators. Capsule and ledger custody checks also reject tampering,
extra or partial files, mode changes, hard links, symlinks, ordinal gaps, and
cross-pair substitutions.

## Prior P1 and exact closure

The first hostile audit found one P1: the production authentication guard
tokenized reviewer and method identifiers and therefore accepted concatenated
markers such as `LOCALAUTH`, `SYNTHETICREVIEWER`, `OFFLINEAUTH`, and
`testprincipal`. A complete exact 50-real-residual hostile bundle using
`LOCALAUTH` and `OFFLINEAUTH` could reach the production-bound pending-review
state.

That defect is closed in these exact bytes. The guard now uppercases each exact
identifier and rejects every forbidden marker wherever it occurs as an
embedded substring. The focused hostile test reconstructs all 50 real
ACCEPT-shaped receipts on the exact runtime-bound runner subject with
`LOCALAUTH` and `OFFLINEAUTH` and requires
`build_integrated_runner_receipt` to reject the bundle. Additional mixed-case
and embedded-marker probes also fail closed. Re-review found no replacement
bypass.

The standalone validator additionally avoids preloaded or tampered project
module caches. It stable-reads all bound project dependencies into controlled
temporary package/module namespaces, checks each captured execution buffer
against the fixed expected byte count and SHA-256 immediately before
`compile`/`exec`, and reconstructs semantics from those captured bytes. The
package test preloads an exact-`ModuleType` primary spoof with the accepted
`__file__`, poisons its surfaces, sets the independent module cache and parent
attribute to explicit `None`, and still requires identical semantics and a
validator PASS.

## Verification evidence

- Focused integration plus sealed package suites: **52/52 PASS**.
- Relevant combined compatibility selection: **367/367 PASS**.
- Standalone validator from the project root: **PASS**, record
  `d61a7465f71057bad7c39fd88f2c9cef14e169caab80b7a9319d60c557817e1c`.
- Standalone validator from unrelated working directory `/private/tmp`:
  **PASS**, with the identical record.
- Final hostile disposition: **P0/P1/P2 = 0/0/0**.

## Exact registration authorization and nonclosure

Independent acceptance authorizes formal registration of exactly one existing
Gate-B0 timetable checkbox:

> Runtime identity, runner, capsule, ledger, and recomputation implementations exist.

No other timetable checkbox is authorized. This review does not itself edit
the timetable, tracker, evidence ledger, candidate, or any predecessor. It
authorizes no Gate-B0 completion and no B02, B03, B08, B09, B10, B11, or B12
closure.

Field delta, blocker delta, Formal-Test delta, result delta,
runtime-selection delta, authority delta, data/contact delta, and science delta
are all exactly zero. Formal Tests 28 and 29 remain OPEN, Formal Test 30 remains
PENDING, all 50 real residual receipts remain absent in the exercise, no
production runtime is selected, no data is accessed, and no scientific
execution or result claim occurs.
