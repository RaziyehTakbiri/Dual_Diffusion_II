# B12 Gate-B0 integration implementation candidate v1

**State:** `IMPLEMENTATION_SURFACES_COMPLETE_REGISTRATION_PENDING_INDEPENDENT_REVIEW`  
**Sole proposed timetable closure:** `Runtime identity, runner, capsule, ledger, and recomputation implementations exist.`  
**Applied timetable delta:** zero  
**Field, blocker, Formal-Test, result, runtime-selection, or science delta:** zero

## 1. Candidate boundary

This successor candidate implements and qualifies the five surfaces named by
the exact Gate-B0 timetable task. It proposes that one implementation-only
checkbox for independent review. It does not edit the timetable or evidence
ledger and does not itself apply the proposed checkmark.

The proposal is deliberately narrow. It does not propose closure of Gate B0,
B08, B12, any other timetable task, any F-field, any blocker, Formal Test
28--30, or any result slot. It selects no production runtime, authenticates no
authority, contacts no source, accesses no dataset, consumes no scientific
entropy, trains no model, performs no inference, and executes no science.

## 2. Exact implementation surfaces

### Runtime identity

`RuntimeIdentityBinding` is a strict future caller-supplied production-runtime
identity seam. It accepts only its exact built-in class and exact ten-field
mapping, requires five nonzero component digests, enforces generation and
predecessor coherence, verifies a domain-separated binding digest, and rejects
missing, extra, zero, stale, wrong-type, subclass, and duck inputs. No actual
B08 runtime identity is instantiated or selected by this package.

### Runner

`IntegratedRunnerReceiptV3` binds one capsule receipt, the corrected exact
22-adapter manifest, a complete paired ledger, recomputation evidence, an
optional future runtime identity, and the accepted exact 50-residual roster.
The deterministic exercise path represents every real residual as an exact
subject-bound `ResidualPredicateSlot` with `receipt=None` and state
`OPEN_RECEIPT_ABSENT`. It never creates acceptance-shaped evidence under a real
residual ID. The local predicate helper rejects all 50 real IDs.

The future production builder requires a caller-supplied runtime identity and
all 50 accepted-contract receipt objects in exact order and on the exact whole
runner subject. It rejects partial rosters, wrong subjects, wrong concrete
types, and reviewer/method identifiers marked local, synthetic, fixture, test,
mock, demo, offline, or qualification. Even a structurally complete future
bundle remains `PENDING_INDEPENDENT_REVIEW`; this implementation does not close
B12.

### Capsule

`ClosedWorldCapsulePlan`, `write_closed_world_capsule`, and
`validate_closed_world_capsule` implement an atomic, no-follow, exact-roster
component/evidence capsule. Its exact canonical `component-bindings.json` is a
physical `0600` payload, named and hashed in the manifest, included in the
accepted `CapsuleReceipt.ordered_file_sha256s`, and cross-checked against all
four Formal-Test-29/30 component source payloads.

"Closed world" means only that the capsule directory contains exactly every
component/evidence payload named by its manifest plus the manifest and
finalization record. It does not mean standalone executability and does not
claim a transitive source or dependency closure.

### Durable ledger

The ledger surface creates an exact `0700` local ledger and persists canonical
`0600` event files through no-clobber pending-file creation, full writes,
`fsync`, hard-link publication, pending-file unlink, and directory `fsync`.
Replay requires contiguous 20-digit ordinals, exact previous-event chaining,
strict INTENT/OUTCOME alternation, and exact operation/request pair matching.
Partial post-INTENT crash state is explicitly replayable but cannot be treated
as a complete pair. Extra files, gaps, tampering, symlinks, hard links, wrong
modes, and cross-operation outcomes fail closed.

### Separate recomputation

The primary integration source builds an exact four-component binding document
and deterministic Formal-Test-29/30 supplied-input output. The separate
`b12_independent_component_recomputation.py` module does not import the primary
integration module. It independently parses the canonical binding document,
reopens and hashes every bound source through stable no-follow descriptors,
checks the exact component schemas and entry points, reruns the bounded
qualifications, and independently serializes the result. Candidate and
independent bytes must match exactly. This is an independent integration-level
orchestration/serialization path, not an independent scientific reimplementation
of the four existing components.

## 3. Corrected adapter binding

The integration consumes
`b12_two_domain_adapter_stack.ADAPTER_ROSTER_SNAPSHOT` directly. The roster is
the exact current B06-derived 22-row order. It rejects the accepted B12-v2
legacy mismatch at exactly zero-based ordinals 12 through 19. The adapter
receipts used by the deterministic exercise remain synthetic-interface-only;
external algorithms, the four-plus-four author extensions, real data adapters,
and domain-scale qualification remain open.

## 4. Custody and canonicality

All content digests are lowercase SHA-256 with explicit domains for semantic
subjects. Local custody reads use stable descriptors, no-follow traversal,
regular-file, mode, single-link, bounded-size, and before/after identity checks.
Claimed project-relative paths must equal their `PurePosixPath.as_posix()`
representation; `a//b`, `a/./b`, trailing slash, absolute, and parent-escape
aliases fail. Claimed canonical absolute roots must also retain their exact
textual `Path` representation and resolve to themselves.

## 5. Registration proposal and prohibited deltas

Pending independent exact-byte review, this package proposes exactly one
timetable change:

- mark `Runtime identity, runner, capsule, ledger, and recomputation implementations exist.` complete.

It proposes and applies none of the following:

- no Gate-B0, B02, B03, B08, B09, B10, B11, or B12 closure;
- no F-field value or closure, including F139--F144, F147, F150, F151, or F172;
- no Formal-Test-28, Formal-Test-29, or Formal-Test-30 state change;
- no result-slot or manuscript-claim promotion;
- no runtime identity selection, hardware/capacity claim, data action, contact,
  authority, training, inference, or scientific execution; and
- no tracker or evidence-ledger edit by this candidate.

## 6. Qualification

The focused integration suite contains 44 passing cases. It covers partial
writes, crash/replay, tampering, paths and aliases, links and modes, exact
types, ducks and subclasses, subjects and cross-bindings, capsule self-
containment, the corrected 22-row adapter boundary, the exact 50-row OPEN
residual boundary, runtime identity hostility, and nonclosure. The separate
package suite contains eight hash-first/canonicality/nonclaim tests. The
relevant combined compatibility selection contains 367 passing cases.

The standalone validator reopens the exact candidate and predecessor bytes,
checks canonical duplicate-free machine JSON and its semantic self-digest,
reconstructs the deterministic component/capsule/adapter/ledger/recomputation/
runner semantics, and emits one stable record SHA-256. Independent review of
the sealed bytes is required before the sole proposed timetable registration
may be applied.
