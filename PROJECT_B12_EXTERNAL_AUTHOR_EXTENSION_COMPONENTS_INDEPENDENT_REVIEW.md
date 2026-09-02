# Independent review — B12 external author-extension components

## Decision

**GO — accept the exact eight offline author-extension component
implementations at `COMPONENT_IMPLEMENTATION_ONLY` scope.**

Final finding counts are **P0/P1/P2 = 0/0/0**.

This review accepts only the local, deterministic transformation and interface
surfaces for the four CSDI/PhysioNet and four EditPP/Retail author extensions.
It does not accept or imply upstream-package execution, upstream-native
functionality, real-data compatibility, domain-scale runtime qualification,
training, inference, generated configurations, production receipts,
scientific evidence, or full closure of any original B12 residual predicate.

No candidate file was edited during this review.  No project tracker or
evidence-ledger file was edited.  The timetable, field, blocker, Formal-Test,
result, science, data, runtime, and authority deltas are all exactly zero.

## Exact reviewed package

The accepted candidate is the following exact five-file successor:

| Role | Path | Bytes | Raw SHA-256 |
|---|---|---:|---|
| Human record | `PROJECT_B12_EXTERNAL_AUTHOR_EXTENSION_COMPONENTS.md` | 12,064 | `e6d841513c500e5b6c997bd76b34fb30aad55b30e02cd35ff52d4e0fc746d347` |
| Implementation source | `src/heterodiff/evaluation/b12_external_author_extension_components.py` | 56,988 | `859d719c1782a9964cd7219af29faeac696f1bd1d8029efa8f176dc8b4f93807` |
| Canonical machine record | `research/fixtures/manuscript_v3_b12_external_author_extension_components_v1.json` | 8,877 | `6a225e3c1536c78f629b069d5ba3b3ffc9d2714ff79645ed93db22a8e8f97a7f` |
| Hash-first validator | `research/diagnostics/manuscript_v3_b12_external_author_extension_components_v1.py` | 21,512 | `106e943a547037b9631b805b0ca20722b17faf6467307406ca9f41028585c92a` |
| Focused hostile tests | `tests/unit/test_b12_external_author_extension_components.py` | 26,524 | `159bd645f78e0ba2323b425b836b4e4b20750eb4730178e10102f38b57f2e94e` |

The validator reconstructed and matched canonical semantic record SHA-256
`fe6397184e01a0e2c807f049e4bab649b93b66899ecf758a52b1e05a6ae7f9bf`.
The machine record also pins 18 accepted predecessor artifacts covering B06,
F105, the corrected B12 adapter stack, and the F139--F144/F147 training and
checkpoint contract.

## Independent execution results

The review used the workspace Python 3.11.5 environment and pytest 9.1.1.
The exact standalone validator passed from the project root:

```text
PASS_B12_EXTERNAL_AUTHOR_EXTENSION_COMPONENTS_ONLY — exact eight implementation-only predicates; record fe6397184e01a0e2c807f049e4bab649b93b66899ecf758a52b1e05a6ae7f9bf
```

The exact copied-capsule test separately copied every candidate and predecessor
binding to an unrelated temporary root and reran that root's copied validator;
both the project-root and copied-root executions passed.

Test results were:

- focused hostile candidate suite: **23/23 passed**;
- relevant corrected-adapter, F105, and F139--F144/F147 compatibility suite:
  **104/104 passed**;
- total distinct focused plus compatibility tests: **127/127 passed**.

The copied-capsule pass is already one of the 23 focused tests and is not
double-counted in the total.

## Review of all eight implementations

The manifest contains exactly eight unique, source-bound implementation
records in this order:

1. `CSDI_AUTHOR_EXTENSION_1` — lossless occurrence channel for simultaneous
   duplicate rows;
2. `CSDI_AUTHOR_EXTENSION_2` — variable-cardinality event-multiset decoder;
3. `CSDI_AUTHOR_EXTENSION_3` — exact PhysioNet F105 event adapter;
4. `CSDI_AUTHOR_EXTENSION_4` — frozen partial-observation mask and 64-draw
   interface;
5. `EDITPP_AUTHOR_EXTENSION_1` — structured invoice, stock, description,
   quantity, price, and country heads;
6. `EDITPP_AUTHOR_EXTENSION_2` — simultaneous and duplicate occurrence-serial
   channel;
7. `EDITPP_AUTHOR_EXTENSION_3` — exact source-civil Retail F105 event adapter;
8. `EDITPP_AUTHOR_EXTENSION_4` — arbitrary-subset association mask and 64-draw
   interface.

Every record binds the exact original predicate and extension identity, B06
domain/configuration digest, F139--F147 executable-configuration digest,
concrete entry point, and reviewed implementation-source digest.  Every record
retains status
`IMPLEMENTED_OFFLINE_PURE_COMPONENT_PENDING_INDEPENDENT_REVIEW`, claim scope
`COMPONENT_IMPLEMENTATION_ONLY`, and four exact false flags for upstream-native
functionality, upstream execution, domain-scale runtime, and production
receipt.

The two adapters accept only exact F105 configurations in their frozen domain.
The PhysioNet path validates the exact 112-coordinate structure.  The Retail
path validates the exact 10-coordinate structure and projects the exact event
coordinates into ten named structured heads.  Both bind the accepted exact
64-dimensional context encoding, B06 configuration, F139--F147 executable
configuration, source digest, occurrence-complete channel, and adapter digest.

Duplicate equal events retain equal event digests but distinct serial-bound
occurrence digests.  The CSDI decoder round-trips zero-, one-, and multi-event
standalone contiguous occurrence tuples.  A contiguous prefix is correctly
documented as a separate valid standalone variable-cardinality multiset; it
cannot replace the occurrence roster inside its original parent adapter,
because the parent configuration and full event count remain bound.

Both conditioning builders accept empty, full, and noncontiguous subsets in a
strictly increasing exact serial tuple.  The observation mask is
occurrence-complete and binds the selected occurrence digests.  Selecting the
first versus second member of an equal duplicate pair changes the mask and
interface custody.  Each interface contains exactly 64 exact slots in ordinal
order `0..63`; every slot remains
`AWAITING_EXTERNAL_MODEL_OUTPUT_NO_OUTPUT_MINTED` with no generated
configuration digest.

## Hostile findings found and repaired before GO

### Repaired P1 — Retail head-to-occurrence coordinate association

The first sealed candidate checked a Retail head's occurrence serial and event
digest but did not compare its ten head coordinates with the ten coordinates
of that occurrence event.  The independent review constructed a head using a
different valid event's coordinates while retaining the first occurrence's
serial and event digest, then recomputed both the head and adapter digests.  The
first candidate accepted the internally redigested inconsistent adapter, whose
digest was
`787506c9f3ad0945b9ee3663efd9fe090696178f5d3a5ecf00576e7be1901be7`.

The successor now compares every Retail head coordinate to its bound
occurrence event coordinate.  Re-executing the identical fully redigested
attack fails with:

```text
Retail structured heads differ from their bound occurrence event
```

The focused suite contains a permanent fully redigested regression.  This
closes the P1 completely.

### Repaired P2 — copied-root parent-directory symlink custody

The next sealed validator used `O_NOFOLLOW` only for leaf files.  The review
constructed an otherwise unrelated capsule whose root `src` entry was a
directory symlink to the original project's `src`.  That validator followed
the intermediate symlink and incorrectly passed the capsule.

The final validator opens and retains one stable project-root directory
descriptor, canonicalizes every relative path, and walks every parent from the
root descriptor using `O_DIRECTORY|O_NOFOLLOW`.  It also verifies stable root,
parent, and leaf identities, requires bounded single-link regular `0644`
leaves, and uses `O_NOFOLLOW` for every leaf.

Re-executing the parent-symlink capsule attack now fails before source capture:

```text
FAIL — cannot safely open parent of src/heterodiff/evaluation/b12_external_author_extension_components.py: [Errno 20] Not a directory: 'src'
```

The focused suite permanently covers altered bytes, leaf symlinks,
intermediate-directory symlinks, and hardlinks.  This closes the P2 completely.

## Additional hostile probes

Independent probes confirmed that the final package fails closed for:

- wrong-domain and cross-adapter inputs;
- exact-type aliases, including `bool` as an integer, list-for-tuple inputs,
  and subclassed configurations;
- duplicate, unordered, negative, or out-of-range observation serials;
- malformed PhysioNet one-hot, mask, elapsed-time, and value blocks;
- malformed Retail optional-presence, source-civil, token, quantity, and price
  coordinates;
- occurrence removal inside a bound parent adapter, reordering, serial gaps,
  cross-occurrence substitutions, and redigested inconsistent Retail heads;
- changed B06, executable-training, context, occurrence, head, mask, adapter,
  interface, implementation-record, or self-digests;
- shortened, expanded, reordered, populated, or status-widened draw slots;
- integer aliases in boolean masks and boolean aliases in slot ordinals;
- malformed, uppercase, short, or zero source-digest inputs;
- claim widening to upstream-native behavior, runtime execution, production
  evidence, or closure;
- duplicate or noncanonical machine JSON keys;
- preloaded candidate-module cache spoofing; and
- copied-root byte tampering, leaf links, parent-directory links, hardlinks,
  and unstable file/root identity.

The source imports no filesystem, operating-system, network, HTTP, subprocess,
entropy, numerical-training, or upstream CSDI/EditPP module.  The validator
reopens and hash-checks all candidate and transitive predecessor sources before
compiling them into fresh module objects, so a preloaded forged candidate
module cannot determine its semantic reconstruction.

The valid nonzero `module_source_sha256` parameter remains explicitly a
caller-supplied binding at the pure component API boundary.  The authoritative
package validator does not trust a caller assertion: it hashes the reopened
implementation file and supplies that exact digest to semantic reconstruction.
Downstream integrators must likewise obtain the source digest from their own
captured bytes rather than treating an arbitrary caller value as external
authentication.

## Exact accepted scope and remaining obligations

This GO changes only the evidence status of the local implementation-absence
facet for the exact eight named residual predicates.  It does not satisfy the
full predicates.  In particular, all of the following remain absent or open:

- execution of pinned CSDI and EditPP packages and proof of their native
  behavior;
- upstream tensor/event-process input and output integration;
- real data, parsing, admission, split, escrow, governance, license, and
  privacy evidence;
- actual tuning, training, validation, checkpoint selection, conditional
  generation, or inference;
- domain-scale memory/time/no-truncation and B08 runtime qualification;
- authenticated runtime identity, immutable production ledger, and production
  receipts;
- scientific recomputation, results, claims, and release evidence;
- complete whole-method runtime integration and the remaining B12 residual
  receipts;
- Formal Tests 28--30; and
- B12 and every still-open blocker.

Accordingly, this independent receipt applies:

- timetable task delta: **0**;
- field delta: **0**;
- blocker delta: **0**;
- Formal-Test delta: **0**;
- result delta: **0**;
- science/data/training/runtime delta: **0**;
- tracker edit: **none**;
- evidence-ledger edit: **none**.

The accepted disposition is therefore narrow and exact: all eight offline
author-extension component implementations now exist and pass independent
hostile review, while every runtime, upstream, production, scientific, and
full-predicate obligation remains open.
