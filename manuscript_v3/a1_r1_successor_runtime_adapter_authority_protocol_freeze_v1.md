# A1 R1 successor runtime, adapter, authority, and typed-custody protocol freeze v1

## 1. Outcome and exact scope

This is an additive, internal, zero execution milestone. It freezes canonical
record schemas, source and coordinate custody, a future child bootstrap
specification, an acyclic precreation transition, and fail-closed protocol
boundaries. It does not create an executable capsule, approve a runtime, activate
an authority, issue a permit, consume a coordinate, launch a worker, run rank,
train a model, run a scientific experiment, or promote any result or claim.

The exact state is
`R1_A1_SUCCESSOR_RUNTIME_ADMISSION_ADAPTER_AUTHORITY_AND_TYPED_CUSTODY_PROTOCOL_FROZEN_ZERO_EXECUTION_ACTIVATION_DEFERRED_NOT_EXECUTABLE`.
The global project state remains `DRAFT_NOT_EXECUTABLE`.
In plain language, this package is not executable.

The historical claim ledger, execution preregistration, CP76 records, frozen
source-coordinate registration, post-draw seed registry, D1 records, historical
source modules, and all experiment artifacts remain byte-for-byte untouched.

## 2. What is frozen

The machine record catalogs exactly 22 distinct canonical schemas, each with one
semantic terminal digest field. They cover successor runtime candidate, review,
and approval wrappers; a materialized source-capsule content manifest; successor
plan and activation records; phase authorization; distinct rank
request/completion/admission; distinct coordinate
permit/request/completion/consumption; phase-aggregate admission; the
PRIMARY_METRICS request/completion/admission barrier; the child bootstrap; the
precreation-attempt marker; prerequisite evidence; and source-capsule admission.

This catalog deliberately reuses only the existing external runtime-manifest
schema `heterodiff-a1-production-runtime-identity-manifest-v1`. It does not reuse
the legacy approval receipt or its historical paths, and it does not invent a
successor runtime-manifest producer. Runtime wrapper parsing and cross-link
checks are schema-only: runtime-chain semantics, runtime stability, and runtime
admission are not qualified.

The source-capsule content plan is closed over 47 local package source files
(45 preactivation source rows plus two deferred local runtime sources), three
nonpackage inputs, and three child-visible protocol files. The child-visible
protocol files are the contracts module, the adapter module, and a non-code
bootstrap JSON record. The parent authority is excluded from the child's import
path. The historical planned adapter under the workspace source tree remains
permanently absent. Nothing was materialized by this milestone.

The bootstrap is exact: `.venv-m1/bin/python` with `-P -B -S -X utf8`, a complete
replacement environment allowlist, no inherited `PYTHONHOME` or `PYTHONPATH`, no
`.pth` processing, and the future capsule protocol directory followed by capsule
source and the exact runtime-approved site-packages. Every imported file and
`__file__` identity must be hash-verified before a later child could be admitted.
The adapter exposes only inert parser-level projections and has no launch,
legacy-object construction, authority import, ledger write, or execution route.

## 3. Registry and coordinate custody

The seed registry remains, in ordinal order,
`[4052249444591756, 3253, 5003, 7411, 10007, 13007, 16001, 20011]`.
The replacement remains ordinal 0 across every lane; numeric resorting, partial
substitution, and grid pruning are forbidden. Seed 1729 remains disclosed prior
development exposure and is absent from every execution-admissible coordinate.

The frozen coordinate identities are exact 24, primary 48, controls 72,
complete sampled 120, execution-phase schedule 144, and aggregate identity 144.
The two 144-order notions remain distinct: the execution schedule is exact then
primary then controls, while the aggregate identity is exact then the
seed-budget-interleaved complete sampled order. The five-event order is
RANK, EXACT, PRIMARY, PRIMARY_METRICS, CONTROLS.

## 4. Event-ledger protocol, not an activated ledger

The future global event order is frozen without issuing any event:

- RANK uses ordinals 0 through 3.
- EXACT authorization is 4; 24 four-record coordinate lifecycles are followed
  by aggregate admission 101.
- PRIMARY authorization is 102; 48 four-record coordinate lifecycles are
  followed by aggregate admission 295.
- PRIMARY_METRICS uses ordinals 296 through 299.
- CONTROLS authorization is 300; 72 four-record coordinate lifecycles are
  followed by aggregate admission 589. The next unused ordinal would be 590.

For a coordinate at phase-local ordinal `i`, the event ordinal is
`coordinate_phase_base + 4*i + offset`, with offsets 1, 2, 3, and 4 for permit,
request, completion, and consumption. Coordinate zero follows the phase
authorization; each later permit follows the immediately preceding validated
consumption; each aggregate follows the final ordered consumption. CONTROLS must
bind its 72 members, prior PRIMARY-48 custody, complete-sampled-120 identity, and
the PRIMARY_METRICS barrier.

These are required future invariants, not achieved replay prevention. The
sequential transcript validator, authority ledger, nonce spent set, and replay
protection are not activated. The transcript entry points are explicit
fail-closed stubs so a later change cannot accidentally enable obsolete partial
logic.

## 5. Acyclic precreation transition

The current live branch requires the precreation marker and every successor
custody root to be absent. A later writer must first lstat the full frozen future
custody-path roster and exclusively create the exact marker while those paths
are pristine. The marker binds a campaign nonce plus this registration's raw and
self digests, the frozen predecessor snapshot, registry, source, schedule,
bootstrap, schema-catalog, code, test, and path-roster identities. It binds a
domain-separated static precreation-plan commitment, not the final plan hash.

Only after that marker may a later milestone materialize and admit a capsule,
capture and approve a runtime at the versioned successor namespace, load closed
prerequisite evidence, and construct the final plan. The final plan must bind the
marker raw and record digests, the static commitment, capsule admission, runtime
manifest and approval, prerequisite evidence, and the audited package hashes;
activation comes last. This order avoids a marker-plan cycle.

The marker's Boolean fields and terminal label do not by themselves prove
exclusive creation or historical pristineness. Campaign-nonce generation,
independence, custody, and one-shot issuance are deferred to the later audited
writer milestone. After an exact marker appears, this immutable registration is
verified through the bound supersession branch: its old absence statements are
historical pre-marker facts, never restated as current live absence.

## 6. Live loaders and current refusal state

The source-capsule admission loader is read-only and closed-world. A future
successful load requires exactly the frozen files and directories, regular files
only, root/directories mode 0700, files mode 0600, link count one, no symlinks,
hard links, bytecode, missing entries, extra files, or extra directories, stable
ancestor/file/directory identities across the audit, all raw hashes, all five
overlays, the registry semantic identity, and the six deferred dynamic local
edges. The loader cannot succeed now because no marker or capsule exists.

The prerequisite-evidence loader reopens the authoritative current baseline and
refuses it: 172 unresolved null values remain, consisting of 166 preexecution and
six deferred postexecution nulls; all 12 blockers remain open, with 10
confirmatory-execution blockers and two claim-promotion/submission blockers.
The freeze predicate is false, and the test-data-unopened value remains null in
the current preregistration. No prerequisite-evidence object is issued.

Loader-only Python types and private helper names are procedural honest-process
controls, not an adversarial security or sandbox boundary. A same-process actor
who mutates module globals, invokes Python-private helpers, alters process memory,
or changes registered files is outside the guarantee. Any later activation must
reopen the live files and receipts; it may never trust an object type, a Boolean,
or a supplied digest alone.

## 7. D1 and development-evidence boundary

D1 remains prior observed development knowledge. It is not R1 execution input,
production evidence, a production checkpoint, a threshold/metric/success-rule
selector, or a basis for excluding overflow. The exact D1/V2 execution-output
lineage quarantine is derived recursively from the complete registered checkpoint
custody and the complete canonical D1 attempt, diagnostic, success, and V2
success records. It includes
campaign, checkpoint, classifier, fixture, parameter, path, run-key, reference,
inner/outer receipt, diagnostic, and output-derived identities, with an exact
count, role labels, and domain-separated roster digest in the machine sidecar.
The full-record rule intentionally over-quarantines governance hashes inside
those records. A future
completion or output-evidence carrier matching any quarantined digest must fail.
The only exception is an exact governance hash in its explicitly named
prerequisite-disclosure field; no such exception applies to a completion or
output-evidence carrier.

Both exact and sampled member completions remain provisional until a typed,
parent-reopened loader/revalidator receipt and full phase-aggregate admission are
available. A Boolean claim of member revalidation never confers final evidence
eligibility. The current D1/event-ledger enforcement helpers do not activate
transcript admission.

## 8. Explicit nonclaims and next gate

No runtime bundle or approval exists. No source capsule is materialized or
execution-admitted. No successor plan, activation, phase authorization, permit,
request, completion, consumption, aggregate admission, metrics admission, result,
or receipt is issued. Plan/activation parsing and cross-record hash carrying are
not plan or activation semantics. Runtime semantics, authority integration,
adapter integration, binder integration, replay prevention, typed consumption,
rank, training, production, scientific eligibility, R1, R2, C17, claim promotion,
and submission readiness all remain false.

The next proper milestone must close the executable preregistration blockers;
define and audit nonce/marker one-shot custody; materialize and independently
admit the content-addressed capsule; validate the external-schema runtime
candidate and approved manifests by reopening their capture envelopes and
semantic identities at the new namespace; load prerequisite evidence; implement
the sole-writer authority ledger and exact sequential transcript validators; and
bind every live loader result into a final plan before any activation. That later
milestone must remain zero execution until a separately audited activation is
complete.

## 9. Publication and trust boundary

This registration and all five companion code/test/sidecar files are internal
custody artifacts, not anonymous-submission or public-release artifacts. Raw
predecessor, D1, runtime, path, and source custody must not be included in a
submission. No in-place sanitization is permitted. Any publication use requires
a new publication-safe derivative, an explicit include/exclude roster, and a
fresh anonymity audit; no derivative path or roster is frozen here.

The guarantees are procedural and assume an honest host and unmodified registered
bytes. They are not a sandbox and do not resist a same-user actor who deliberately
changes process memory, module globals, filesystem state, or audit inputs.
