# Independent review — B12 whole-method nonconfirmatory runner

## Decision

**NO-GO for both proposed timetable registrations.**

Final finding counts are **P0/P1/P2 = 0/1/0**.

The exact candidate is mechanically reproducible and truthfully preserves its
nonconfirmatory boundary, but its evidence does not establish the data-flow
integration asserted by either proposed checkbox.  The initializer and sampler
are executed in the same core document as the bounded path, but the selected
initializer configuration is not supplied to, transformed into, or bound by
the path.  This is a material P1 evidence-to-claim mismatch.

Accordingly, this review authorizes an exact timetable checkbox delta of
**zero**:

- `Produce whole-method beta: initializer, continuous path, jump/edit law, and sampler integrated.` — **not authorized**;
- `End-to-end method is feature-complete.` — **not authorized**.

No candidate file was edited during this review.  No tracker, evidence ledger,
blocker record, field, Formal-Test state, result slot, runtime state, data
state, training state, scientific state, or authority state was edited.

## Exact reviewed successor

| Role | Path | Bytes | Raw SHA-256 |
|---|---|---:|---|
| Human candidate | `PROJECT_B12_WHOLE_METHOD_NONCONFIRMATORY_RUNNER.md` | 9,575 | `60a084e03c93f731968394b734a181da62f450835fbba03b887fdf126f152eed` |
| Primary runner | `src/heterodiff/evaluation/b12_whole_method_nonconfirmatory_runner.py` | 40,451 | `c1c5c44584af43631def5f13e862a6a486f9622dfa970e476a915d4ff488509d` |
| Separate recomputation | `src/heterodiff/evaluation/b12_whole_method_nonconfirmatory_recomputation.py` | 25,993 | `edca70eaa2e4090f9ee224e1be55c7f587b24eba310033b6317c6049c7c545c5` |
| External author-extension predecessor | `src/heterodiff/evaluation/b12_external_author_extension_components.py` | 56,988 | `859d719c1782a9964cd7219af29faeac696f1bd1d8029efa8f176dc8b4f93807` |
| Canonical machine record | `research/fixtures/manuscript_v3_b12_whole_method_nonconfirmatory_runner_v1.json` | 9,789 | `a5debbc0db537993191c1554529fdf52e34ace80a92cb24a3555889a11f0490b` |
| Hash-first validator | `research/diagnostics/manuscript_v3_b12_whole_method_nonconfirmatory_runner_v1.py` | 20,434 | `b095842d4d5ebc77b4f5088e0a3d4542f1a55d15d1d8f729ccfcd0b4ba0a6722` |
| Focused hostile tests | `tests/unit/test_b12_whole_method_nonconfirmatory_runner.py` | 15,841 | `1319b3c420fc1bf2a083d9627c5da7896027f317f6479ab70d1461af4bc158d1` |

The machine self-record is
`451ef6059fea8cb2f98128c388056bcd82739645a97dfdd56021055744cb04af`.
The stable public receipt is
`677aedeac9fe02a3bac9a14316c2c1f1a0047d6839e9c7492063d344b5e93220`.
The primary and separate recomputation core-output digests are byte-equal at
`dabe8dc257e88055c7e1439f48d04b80d5d7a7d289d81e7b27fb1a53e67a0d52`.

## Independent reproduction

The standalone validator passed from the project root with decision
`PASS_CANDIDATE_PENDING_INDEPENDENT_REVIEW` and the exact stable receipt above.
An unrelated physical copy of the package also passed using the copied
validator and copied sources.

The exact test totals were:

- focused whole-method hostile suite: **23/23 passed**;
- bounded relevant compatibility suite: **234/234 passed**;
- total distinct focused plus compatibility tests: **257/257 passed**.

The compatibility roster covered the external author extensions, corrected
two-domain adapter stack, integration stack, Test-29 route oracle, two-step
Test-29/Test-30 path, two-domain production CKS projection, and the frozen
F139--F144/F147 training/checkpoint seam.

Additional copied-capsule probes confirmed fail-closed behavior for changed
human-record bytes, a leaf symlink, an intermediate `src` directory symlink,
and a hardlinked bound file.  The focused suite also confirmed exact supplied
input typing, digest tampering refusal, duplicate/noncanonical JSON refusal,
missing external implementation-record refusal, noncanonical-root refusal,
offline imports, primary-versus-recomputation source separation, and resistance
to preloaded target-module cache spoofing.

These results establish exact-byte reproducibility and a sound bounded
nonconfirmatory receipt.  They do not cure the semantic integration gap below.

## P1-01 — initializer output is not connected to the path

The timetable task requires the initializer, sampler, continuous path, and
jump/edit law to be **integrated**.  The candidate executes each component, but
the required initializer-to-path edge is absent:

1. `_core_output` independently places `_initializer_summary(supplied)` and
   `_path_summary(supplied)` into sibling fields.
2. `_initializer_summary` computes a selected configuration with SHA-256
   `c9450132be2800eddc7e8e36547c49e8b7839e1e282e32f0736b453267b92b06`.
3. `_path_summary` receives only the frozen wrapper object and uses only its two
   path words to call `build_frozen_two_macrostep_path_input`; it receives no
   initializer result, selected configuration, or initializer custody digest.
4. In the reconstructed core, every occurrence of the selected configuration
   digest is confined to the `initializer_and_sampler` subtree.  It does not
   occur in the path input, initial state, step reports, or path digest.
5. The underlying two-macrostep result explicitly sets
   `test28_initializer_admissible=False`; the whole-method runner requires that
   value to remain false before accepting the path.

Thus the receipt proves joint execution and common packaging, not whole-method
data-flow integration.  An initializer can select one configuration while the
path continues from its separately frozen synthetic initial occurrences.  The
claim in the human candidate that the initializer and sampler are connected to
the path is not supported by the executable semantics.

This is P1 because it directly defeats the core meaning of the first proposed
checkbox and necessarily propagates to the stronger feature-complete checkbox.

## Separate checkbox decisions

### Solo Block 7 whole-method beta — not eligible

The bounded two-step exercise genuinely integrates continuous left/right Heun
applications with replacement and death jumps, rolling lineage, and boundary
state continuity.  It also genuinely executes the fixed-budget initializer and
sampler.  A two-step bounded fixture can be sufficient for a beta milestone;
real data, upstream execution, and all 50 operational residual receipts need
not be present merely to demonstrate a beta.

However, the selected initializer configuration never initializes the path.
Because the checkbox expressly requires the initializer and sampler to be
integrated with the continuous and jump/edit path, co-location in one receipt
is insufficient.  The Solo Block 7 checkbox remains open.

### Gate-B0 end-to-end feature-complete — not eligible

The same missing initializer-to-path edge already prevents an end-to-end
feature-complete finding.  In addition, the candidate explicitly records that
the general arbitrary-length Strang path is outside the bounded two-step
exercise.  Gate B0 states that no new method layer or feature may be added
after the block; a runner that only accepts this exact two-step fixture cannot
support that freeze boundary as the general method runner.

The two upstream CSDI/EditPP packages and their native outputs were not
executed.  That fact does not by itself invalidate a local beta, and this
review does not require real or confirmatory execution to close a code-only
milestone.  It does mean the pending-slot author-extension interfaces cannot
be used as evidence that upstream runtime behavior works end to end.

All 50 real residual receipts also remain open.  Their continued absence does
not by itself defeat a narrowly defined code beta, but it forbids any inference
of B12, production, Formal-Test, runtime, scientific, or result closure.  The
roster includes still-unrealized production adapters, domain-scale runtime,
runner/recomputation, upstream-extension, immutable-ledger, and integrated
training/checkpoint obligations; this candidate does not convert those
operational gaps into feature-completeness evidence.

## Exact remediation required for a successor

For the Solo Block 7 beta checkbox, a successor must:

1. define a deterministic, typed transformation from the sampler's exact
   selected configuration into the path's initial state;
2. pass that transformed state into the continuous/jump path rather than
   independently constructing the frozen Test-30 initial occurrences;
3. bind the selected configuration digest, transformation policy, resulting
   initial-state digest, and path input/report digest in one recomputable
   custody chain;
4. make the separate implementation independently recompute that same edge;
5. replace the current `test28_initializer_admissible=False` boundary with a
   truthful positive admissibility result only after validating the actual
   initializer output; and
6. add hostile tests proving that substitution, omission, or alteration of the
   selected initializer configuration either changes the path and receipt
   deterministically or fails closed.

For the Gate-B0 feature-complete checkbox, the successor must additionally
provide and test the general method path surface needed after feature freeze,
including arbitrary caller-supplied valid step counts rather than only the
exact two-step fixture, while preserving lineage, address uniqueness,
continuous/jump ordering, and fail-closed typing across zero-, one-, two-, and
greater-than-two-step boundaries.  Any upstream interfaces cited as evidence
must expose a real callable integration boundary; permanently empty pending
slots are honest nonclaims, not end-to-end runtime evidence.

A successor may remain offline, synthetic, and nonconfirmatory.  It need not
close B12, execute science, contact data, or mint production receipts.  It must,
however, demonstrate the missing method data flow and, for Gate B0, the general
feature surface that the freeze statement presupposes.

## Unchanged project state

This NO-GO review applies exactly these deltas:

- timetable checkbox delta: **0**;
- field delta: **0**;
- blocker delta: **0**;
- Formal-Test delta: **0**;
- result delta: **0**;
- B12 delta: **0**;
- science/data/training/runtime/authority delta: **0**;
- tracker edit: **none**;
- evidence-ledger edit: **none**.

Formal Tests 28 and 29 remain `OPEN`; Formal Test 30 remains `PENDING`.  The 50
real residual receipt slots remain `OPEN_RECEIPT_ABSENT`.  No result, claim,
release, production receipt, or scientific conclusion follows from this
candidate or review.
