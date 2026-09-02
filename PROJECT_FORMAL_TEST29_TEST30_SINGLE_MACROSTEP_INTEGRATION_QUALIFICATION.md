# Formal Tests 29–30 synthetic single-macrostep integration precursor

**Reported:** 2026-08-31  
**Global project state:** `DRAFT_NOT_EXECUTABLE`  
**Narrow predicate:** `SYNTHETIC_SUPPLIED_INPUT_SINGLE_MACROSTEP_LEFT_JUMP_RIGHT_INTEGRATION_VALIDATED`  
**Formal Test 28:** **OPEN**  
**Formal Test 29:** **OPEN**  
**Formal Test 30:** **PENDING**

## Decision

This additive internal package qualifies one deterministic, caller-supplied,
single-macrostep composition of the already stopped Test-29 and Test-30
precursors.  It starts from the exact two-occurrence synthetic state exposed by
the Test-30 precursor, applies a stochastic-Heun half-step using supplied
physical Brownian increments at CP23-shaped tag-4 addresses, applies exactly
one finite-acyclic Test-29 birth, death, or replacement edit using one supplied
uint64 word at a CP24-shaped tag-6 address, and applies a second Heun half-step
using supplied physical increments at tag-5 addresses for the post-edit live
lineage.

The low four word bits are exhausted over all sixteen cases.  This covers all
three edit families, both source choices where a source is required, both
bounded normal-word cells for destination-bearing routes, and terminal
cardinalities one, two, and three.  Every case consumes one central addressed
word, preserves the exact Test-29 fresh/retired-lineage result, uses disjoint
left/central/right address identities, and terminates after a statically
bounded amount of work.

This is a component qualification only.  It does **not** close any formal test,
project field, blocker, or result slot.

## Authority boundary

The exact conversation-visible authority used for this bounded local work is:

> Okay, sounds good. What I want you to do is to set aside a significant portion of work to do such that you are busy for around 8 hours, because I am going to sleep, and dont want my absence to make you idle.

Only trailing transport whitespace or its HTML-space representation is
excluded.  This text authorizes continued bounded local project work.  It does
not authorize browsing, external contact, data acquisition, entropy, a live
random stream, scientific execution, training, claim promotion, submission,
runtime approval, or tracker mutation.

## Exact component boundary

The component implements only this supplied-input sequence:

1. Bootstrap the Test-30 synthetic occurrences `(1, A, 0.75)` and
   `(2, B, -0.4)`.  This state is a deterministic fixture and is **not** an
   admitted Test-28 initializer.
2. Preflight the complete left tag-4 increment roster for initial serials 1
   and 2.  Each value is a physical half-step increment `delta W`, not a
   standardized normal variate and not evidence of a Brownian law.
3. Apply the Test-30 additive-OU stochastic-Heun formula for duration `h/2`
   with frozen macrostep width `h = 0.25`.
4. Consume one supplied Test-29 word at exact CP24-compatible address
   `key=(29030,6)`, `counter=(0,0,0,0)`.  The frozen rank-one route law has
   masses birth `1/2`, replacement `1/4`, and death `1/4`.
5. For birth or replacement, construct the new coordinate using the selected
   finite normal-quantile-cell midpoint representative.  This is explicitly
   not a continuous Gaussian sample.  Death creates no coordinate.
6. Require the coordinate roster to match the Test-29 terminal lineage
   exactly.  Preflight the full right tag-5 roster for that lineage, then apply
   the same Heun half-step formula for duration `h/2`.

The frozen qualifier runs low-word values 0 through 15.  Its exact aggregate
receipt is:

- route families: birth 8, replacement 4, death 4;
- terminal cardinalities: one in 4 cases, two in 4 cases, three in 8 cases;
- selected source serials: serial 1 in 4 cases and serial 2 in 4 cases;
- bounded normal cells: cell 0 in 6 destination cases and cell 1 in 6;
- sixteen distinct canonical input digests and sixteen distinct case-report
  digests;
- one left/jump/right composition, unique addresses, and exact Test-29 lineage
  in every case.

The qualifier digest is
`ccf2639c539d312463209bd165cc288df1ba77518f1d31aa7e616df18b66455f`.
It commits every qualification scope, policy, count, case input digest, case
report digest, positive flag, negative flag, project delta, and pass field.
Each case-report digest likewise commits every material identity, state,
lineage, count, scope, failure-policy, positive, negative, and pass field.
Digest recomputation alone is not treated as semantic validation.  The public
case validator requires the exact supplied input and the admitted Test-29 and
Test-30 parent APIs, reruns a nonrecursive internal execution core, and
strictly compares every result field, including the input and report digests,
route/source/created/cell relations, all coordinates, counts, and flags.  The
public frozen-qualification validator reruns all sixteen ordered canonical
inputs through that same core, rebuilds the aggregate, and strictly compares
every aggregate field and both ordered case-digest tuples.  The public run
functions execute once and then use those reconstruction validators; neither
internal core calls a public run or validator.  Thus a stale digest and a
semantically altered result with a freshly recomputed digest both fail closed.

## Frozen parent custody

The read-only validator hard-pins every file of both independently audited
parent packages before it executes any parent or composite source.  It then
executes exactly the already stable-read, hash-verified source bytes in fresh
in-memory modules.  It does not reopen a source path for execution, use an
importlib path loader, or use cached bytecode.

The public composite source does not authenticate arbitrary parent module
objects.  Its module boundary checks only exact module type, schema equality,
and the presence of required symbols.  All no-effect and exact-parent claims in
this package apply only to the validator-admitted, hard-pinned parent bytes
listed below.  An arbitrary caller-supplied module may be effectful and is
outside the qualification.

The stopped Test-29 five-file parent is pinned by these raw SHA-256 values:

- source: `308a16090128871c9a79cdaff265d3b6633e18b062a605b257f3173198d8a089`;
- human: `4dfc775e04708d800ab7cbbb2241e0399e11f1f5edccac41da15ae186c067c05`;
- machine: `79fb7722a9007d18d0fe6f0c7f00026b37170930b87686e910d472b28e54b2b9`;
- validator: `b962f9b9fcc957e1a25590d341f4fc0b9889fd041757d9c623b36d4fca300905`;
- hostile test: `6f9fc2576958992c5688123228128f2f56cecc47b4e8bc2de3b238e510d1662d`.

Its machine self-digest is
`6c443bf95161371536b6f3f395a4a2328c70d0f83d4e254f54e699e31e07797d`.
Its independently audited narrow predicate is
`FINITE_ACYCLIC_TEST29_ROUTE_CELL_LINEAGE_COMPLETION_QUALIFIED`; full Formal
Test 29 remains open.

The stopped Test-30 five-file parent is pinned by these raw SHA-256 values:

- source: `373ef98c3605e0c0211da8dbc8782f2517cd5976026980e4fcd24435670839e0`;
- human: `7a6978be9d7f453adebb2d7ea1464523b7b43df8027138d18c744a2add0140d4`;
- machine: `03b6ff21dedc065a3385f403f7631ee89023bd9572d5793405fa2d8492cb7cb5`;
- validator: `7319bc6de7ec32b65aed81af64d027f639b0b9c91fe3534b853fe42c8429758b`;
- hostile test: `7d0b18f0d1470e6cacc44918e078b6122b5822cb7080e544507c5c0e8b19efef`.

Its machine self-digest is
`f70ccc081c029939b8b150a00c5ad776bd58a4081c37af5b1d2fccb4be698fbe`.
Its independently audited narrow predicate is
`SYNTHETIC_EXPLICIT_INPUT_TEST30_COUPLING_PRECURSOR_VALIDATED`; full Formal
Test 30 remains pending.

The method-specification snapshot is pinned at
`58bdfd689caa1698a07e415074e98bd3a80e9d69467d9ddec8f8471aba36c34d`
for the left-Heun / midpoint jump / right-Heun ordering only.

## Fail-closed behavior

The exact finite central parent selection runs first because its selected edit
determines the terminal lineage and therefore the required right-increment
roster.  Under the validator-admitted pure parent, this selection has no
external effect.  Before any Heun/path arithmetic, result return, or
source-owned effect, the source revalidates both complete increment rosters and
rejects wrong parent module types or schemas, missing required parent symbols,
noncanonical or object-mutated integer/float/string/tuple fields, booleans or
subclasses, nonfinite or nonpositive widths, wrong run or step identifiers,
wrong central-word types or reconstructed CP24 addresses, wrong raw-word
types, missing/extra/reordered/duplicated increment rows, wrong or
noncanonical CP23 domains/tags/keys/counters, wrong occurrence rosters, address
reuse, and lineage/coordinate-roster disagreement.  It has no retry, fallback,
tolerance substitution, partial result, filesystem write, subprocess, network,
or entropy surface under those admitted parents.

The validator separately rejects noncanonical machine bytes, a wrong machine
self-digest, symlinks, hard links, executable modes, ancestor changes,
mid-read changes, unsafe relative paths, source or parent drift, publication or
authority expansion, nonclosure-flag promotion, and coherent re-binding of any
hard-pinned input.  Hostile tests also demonstrate that an alternate source
path and cached bytecode cannot be executed after verified bytes have been
accepted.  Coherent-drift and effectful-preexecution hostiles cover the
composite source, the specification, and all ten files of the two parent
packages.  Separate hostile cases alter a coordinate, route, family, source
index/serial, created serial, normal cell, or input digest, recompute the case
digest, and verify rejection against the supplied input.  Other hostiles
reverse or replace ordered qualification case input/report hashes, recompute
the aggregate digest, and verify rejection by the canonical sixteen-case
rerun.

## Exact nonclosures

The following remain false or absent:

- Test-28 initializer distribution, admission, tag-3 coordination, and live
  source;
- live CP23 or CP24 stream consumption;
- any word-to-Gaussian or Brownian marginal, independence, or coupling law;
- a continuous Gaussian destination draw;
- waiting-clock simulation, proposal acceptance, thinning, rejection, or the
  full jump-substep law, including zero or multiple edits;
- a general Strang path, arbitrary configuration, learned/native drift,
  step-halving study, production endpoint law, or independent scientific
  recomputation;
- runtime or runner custody, scientific result, evidence admission, claim
  promotion, submission, field/blocker closure, or tracker edit.

Consequently Formal Test 28 remains **OPEN**, Formal Test 29 remains **OPEN**,
and Formal Test 30 remains **PENDING**, even if every package test passes.

## Publication and anonymity boundary

This package is internal evidence only.  Anonymous or public inclusion is not
permitted.  Any publication use requires a separately prepared,
publication-safe derivative and a fresh anonymity audit.  That derivative
must omit the visible authority text, conversation provenance, internal paths,
hashes, validation commands, test receipts, and custody details.  Only
sanitized method content and the honest unresolved-status boundary may be
carried forward.

## Registration rule

After an independent read-only audit reports no P0, P1, or P2 finding, a later
authorized tracker integration may register only the named narrow predicate as
a new component control.  This package itself edits no tracker and changes no
existing scientific field, blocker, formal-test state, or result.
