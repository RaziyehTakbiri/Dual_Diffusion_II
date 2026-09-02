# B11 pre-outcome audit-plan freeze

**Reported date:** 2026-09-01  
**State:** `B11_PREOUTCOME_AUDIT_PLANS_FROZEN_REPORTS_NOT_CREATED`  
**Global state:** `DRAFT_NOT_EXECUTABLE`  
**Package kind:** `ADDITIVE_OFFLINE_POSTEXECUTION_PLAN_FIELD_CLOSURE`  
**Control predicate:** `PREOUTCOME_PROOF_CODE_METHODS_STATISTICS_CLEAN_ROOM_AUDIT_PLANS_FROZEN`

## 1. Exact scope and authority boundary

This package freezes three ordinary audit plans before any outcome is known. It
closes exactly these three post-execution plan fields:

| Field | JSON pointer | Frozen plan |
|---|---|---|
| `F168` | `/ethics_release_and_review_plan/proof_and_code_audit_plan` | `PROOF_AND_CODE_AUDIT_PLAN_V1` |
| `F170` | `/ethics_release_and_review_plan/methods_and_statistics_audit_plan` | `METHODS_AND_STATISTICS_AUDIT_PLAN_V1` |
| `F171` | `/ethics_release_and_review_plan/clean_room_reproduction_audit_plan` | `CLEAN_ROOM_REPRODUCTION_AUDIT_PLAN_V1` |

The responsible process is owned by the already registered role `Owner C —
Data, governance, and reproduction coordinator`. The future audit-executor and
clean-room-executor roles and selection criteria are defined here, but no
person, institution, account, external identity, competence declaration,
conflict-of-interest disclosure, or appointment is selected or authenticated.

This is one integrated B11 package because the three plans share one custody,
role-separation, severity, finding-preservation, and terminal-disposition
contract. It is not three precursor layers. It reduces the tracked field count
by three. It does not close B11, create a report, or execute any audit.

The package is static and offline. It performs no network or connector use,
source contact, data access, entropy, subprocess launch, environment build,
runtime capture, clean-room run, training, scientific execution, result
inspection, claim promotion, submission, tracker edit, or evidence-ledger edit.
It supplies no authority for any later one of those acts.

## 2. Exact predecessor and count boundary

The machine record binds the immutable execution preregistration, the accepted
four-file F104 formula-freeze package, its independent `GO` review, and the
anti-drift policy. The accepted F104 successor state is the sole count baseline:

- pre-execution: 145 open / 21 closed;
- post-execution: 6 open / 0 closed;
- total: 151 open / 21 closed;
- all 12 blockers open;
- Formal Tests 28 and 29 `OPEN`, Formal Test 30 `PENDING`; and
- R1--R4 unexecuted with 0/4 result slots filled.

This additive package changes only the three named post-execution fields. After
independent acceptance, the eligible projection is:

- pre-execution: 145 open / 21 closed, unchanged;
- post-execution: 3 open / 3 closed;
- total: 148 open / 24 closed;
- open post-execution fields exactly `F164`, `F165`, and `F169`; and
- all blocker, Formal-Test, result, runtime, operational, data, authority,
  scientific, claim, and submission states unchanged.

In particular, `F169`,
`/ethics_release_and_review_plan/proof_and_code_audit_artifact_path`, remains
`OPEN` with value `null`. No realized proof/code audit artifact or path exists.
B11 remains `OPEN` because no audit has run and no report, finding disposition,
or clean-room reproduction exists.

## 3. Shared owner-role and independence process

The exact shared process is:

1. `OWNER_C_DATA_GOVERNANCE_AND_REPRODUCTION_COORDINATOR` admits the future
   immutable input manifest, assigns a qualified audit-executor role, preserves
   findings, and records the terminal disposition. Owner C may coordinate but
   may not override a terminal failure or act as the sole auditor.
2. `INDEPENDENT_AUDIT_EXECUTOR_NOT_ANY_AUTHOR_OR_IMPLEMENTER_OF_SUBJECT`
   performs the proof/code or methods/statistics audit. No author or implementer
   of any audited subject artifact may fill this role, even if that person was
   not the sole author and did not implement the specific code under review. A
   subject author or implementer may answer questions but may not audit,
   self-accept a finding, or accept the final report.
3. `CLEAN_ROOM_EXECUTOR_NOT_ANY_AUTHOR_OR_IMPLEMENTER_OF_SUBJECT_AND_SEPARATE_FROM_SUBJECT_WORKSPACE`
   performs the later reproduction from only an admitted input manifest. The
   clean-room executor is subject to the same no-author/no-implementer rule and
   must additionally remain separate from the subject workspace. It may not
   discover or import an unlisted dependency.
4. Every auditor is read-only with respect to frozen subject artifacts. Known
   authorship or implementation overlap, known input or subject mutation, or a
   known forbidden rerun or redesign is a substantive defect and returns
   `FAIL`. Missing or unverified separation, custody, competence,
   conflict-of-interest, or other readiness evidence returns
   `INCOMPLETE_FAIL_CLOSED` only when no known substantive defect exists.
5. Findings are never deleted. Any P0 or P1 finding fails. P2 findings
   may coexist with pass only when fully disclosed, bounded, and shown not to
   change the audited predicate, scientific claim, or reproducibility result.
   An unbounded or undisclosed P2 fails.
6. An audit finding may narrow a claim or stop submission. It may not authorize
   a confirmatory rerun, seed replacement, result-dependent redesign, threshold
   change, domain swap, compute top-up, or deletion of a failed attempt.

Before either executor role is admitted, the future assignment/admission record
must contain exactly the executor identity, a declaration that the executor is
not any author or implementer of the audited subject, a declared subject-matter
competence record, a complete conflict-of-interest disclosure, Owner C's
recorded review and acceptance of that disclosure, and Owner C's recorded
assignment acceptance. Known authorship/implementation overlap returns
`FAIL`. Missing or unverified competence,
disclosure, separation, or Owner C acceptance returns
`INCOMPLETE_FAIL_CLOSED` only when no known defect exists. These are selection
criteria only; this package creates none of those records and appoints nobody.

Actual auditor and executor identities, competence declarations,
conflict-of-interest disclosures or acceptances, appointments, reports,
signatures, paths, and runs are all absent and remain future gated receipts.

## 4. F168 — proof and code audit plan

`PROOF_AND_CODE_AUDIT_PLAN_V1` requires the future immutable input manifest to
contain, in order:

1. the final theorem statement, assumption roster, and claim boundary;
2. the proof package, obligation roster, lemmas, counterexamples, and boundary
   cases;
3. the final proof-to-code symbol crosswalk;
4. the exact source and configuration manifest for every audited executable
   quantity;
5. the exact tests, expected predicates, and independent recomputation recipe;
6. all earlier proof/code findings and their preserved dispositions; and
7. the claim-ledger entries whose support depends on the audited proof.

The future executor must complete these ordered phases:

1. admit exact input custody and reject missing, extra, aliased, reordered, or
   mutable inputs;
2. match every public theorem statement to its exact assumptions and scope;
3. verify proof-obligation completeness and nonoverlap, including initializer,
   continuous, discrete-edge, cap, reference, and numerical terms;
4. check every proof symbol and executable quantity in both crosswalk
   directions, with no orphan proof symbol or unclaimed code symbol;
5. verify executable boundary cases, negative controls, and counterexamples;
6. reconcile every finding with the claim ledger without changing frozen
   scientific inputs or outcomes; and
7. produce an immutable terminal report and complete finding register.

The required future evidence classes are a custody receipt, coverage matrix,
two-direction symbol crosswalk result, boundary-case result roster, complete
finding register, claim-impact disposition, and terminal report digest. No such
evidence is created here. Completion is impossible unless every required input,
phase, and output is exact and hash-bound, role separation holds, all findings
are preserved, no P0 or P1 remains, every P2 is bounded and
disclosed, and the report records no forbidden rerun or redesign.

## 5. F170 — methods and statistics audit plan

`METHODS_AND_STATISTICS_AUDIT_PLAN_V1` requires the future immutable input
manifest to contain, in order:

1. the final frozen preregistration and machine companion;
2. the accepted field, blocker, Formal-Test, gate, and result-transition ledger;
3. exact domain, split, method, baseline, checkpoint, seed, and run manifests;
4. raw predictions or samples, per-run logs, checkpoints, and terminal statuses;
5. metric, estimand, margin, multiplicity, interval, power, and constraint
   specifications;
6. primary and secondary metric tables and independent recomputation recipes;
7. every failure, exclusion, deviation, abort, and attempted rerun record; and
8. planned and realized compute receipts plus the claim ledger.

The future executor must complete these ordered phases:

1. admit exact input custody and the complete scheduled-attempt roster;
2. compare every realized method, domain, split, seed, and checkpoint choice to
   the pre-outcome freeze;
3. verify the estimand, pairing, natural-group hierarchy, missingness, and
   failure treatment;
4. independently recompute primary metrics, multiplicity, intervals, margins,
   and every pass/fail predicate;
5. reconcile power, sample-size, stopping, and seed-registry compliance;
6. reconcile failures, exclusions, deviations, aborts, and retry prohibitions;
7. reconcile planned and realized compute, including failed attempts;
8. check every promoted or withheld claim against the exact terminal evidence;
   and
9. produce an immutable terminal report and complete finding register.

The required future evidence classes are a custody receipt, roster-completeness
receipt, preregistration-deviation matrix, independent numerical recomputation,
failure/exclusion/deviation register, compute reconciliation, claim-impact
disposition, complete finding register, and terminal report digest. No result,
metric value, run record, or report is present in this package. The same exact
shared completion and no-rerun rules apply.

## 6. F171 — clean-room reproduction audit plan

`CLEAN_ROOM_REPRODUCTION_AUDIT_PLAN_V1` requires the future immutable input
manifest to contain, in order:

1. the frozen source tree or commit archive;
2. environment, container, lockfile, toolchain, and hardware requirement
   digests;
3. the complete clean-room input-manifest schema and admitted instance;
4. authorized data-acquisition, license, schema, preprocessing, and split
   manifests plus the lawfully supplied data capsule;
5. method, baseline, checkpoint, seed, schedule, and compute manifests;
6. exact invocation specifications and expected artifact schemas;
7. original artifact, result, failure, and compute receipts for comparison; and
8. the frozen comparison tolerances and terminal predicates.

The future executor must complete these ordered phases:

1. admit exact input custody and prove separation from the subject workspace;
2. construct the declared environment using only admitted inputs and separately
   authorized operations;
3. admit the lawfully supplied data capsule without discovering or substituting
   any source;
4. execute only the frozen schedule, preserving every attempt and failure;
5. reproduce the required artifact inventory and independently recompute the
   terminal predicates;
6. compare every required output under the frozen exact or numeric tolerance;
7. reconcile all deviations, environmental differences, failures, and compute;
   and
8. produce an immutable terminal report and complete finding register.

The required future evidence classes are a workspace-separation receipt,
input-admission receipt, environment reconstruction receipt, complete attempt
roster, reproduced artifact inventory, exact/tolerance comparison matrix,
failure/deviation and compute reconciliation, complete finding register, and
terminal report digest. This package creates none of them. A future clean-room
run requires its own authority and gates; this plan is not that authority.

## 7. Fail-closed terminal rule

The validator exposes one pure helper over caller-supplied synthetic completion
evidence. `PASS` requires all required inputs, the exact roster, role separation,
all ordered phases, all outputs, the full finding register, and an actual report;
zero P0 findings and zero P1 findings; zero unbounded or undisclosed P2 findings;
an admitted executor who is no author or implementer of the subject; an accepted
competence and conflict-of-interest record; and no subject mutation or
forbidden rerun/redesign. Any known substantive
defect returns `FAIL` even when readiness evidence is also missing. Only a state
with no known substantive defect but missing readiness evidence returns
`INCOMPLETE_FAIL_CLOSED`. The helper reads no file and performs no audit.

The current package necessarily evaluates as not executed because all actual
assignment, input-instance, report, artifact-path, run, and result fields are
null or false. A frozen plan is not a completed audit.

## 8. Package and qualification boundary

The package contains exactly:

- `PROJECT_B11_PREOUTCOME_AUDIT_PLAN_FREEZE.md`;
- `research/fixtures/manuscript_v3_b11_preoutcome_audit_plan_freeze_v1.json`;
- `research/diagnostics/manuscript_v3_b11_preoutcome_audit_plan_freeze_v1.py`;
  and
- `tests/unit/test_manuscript_v3_b11_preoutcome_audit_plan_freeze_v1.py`.

The validator performs stable no-follow reads of exact single-link `0644`
files, checks ancestor and descriptor/path stability, rejects noncanonical or
duplicate-key JSON, recomputes predecessor semantic digests when present, and
reconstructs the entire expected machine record. Hostile tests mutate only
temporary replicas and cover exact-byte custody, links, modes, path escapes,
noncanonical and duplicate JSON, plan order and cardinality, field roster and
counts, F169/B11 false promotion, actual-report forgery, known authorship or
implementation overlap, known input/subject mutation, missing or unverified
readiness, and
forbidden effect surfaces.

The package is not independently accepted merely because its own validator and
tests pass. An independent reviewer must re-open the exact four files, recompute
their hashes and semantic digest, inspect the plan semantics and effect surface,
and issue a separate review receipt before any tracker or ledger registration.

## 9. Evidence-ready registration text

> Upon independent acceptance, register only this delta: F168
> (`/ethics_release_and_review_plan/proof_and_code_audit_plan`), F170
> (`/ethics_release_and_review_plan/methods_and_statistics_audit_plan`), and
> F171 (`/ethics_release_and_review_plan/clean_room_reproduction_audit_plan`)
> are closed by the exact pre-outcome plans `PROOF_AND_CODE_AUDIT_PLAN_V1`,
> `METHODS_AND_STATISTICS_AUDIT_PLAN_V1`, and
> `CLEAN_ROOM_REPRODUCTION_AUDIT_PLAN_V1`. Pre-execution counts remain 145 open
> / 21 closed; post-execution counts move from 6 open / 0 closed to 3 open / 3
> closed; total counts move from 151 open / 21 closed to 148 open / 24 closed.
> F169 remains OPEN/null and B11 and all 12 blockers remain OPEN. Formal Tests
> 28 and 29 remain OPEN, Formal Test 30 remains PENDING, R1--R4 remain
> unexecuted, and 0/4 results are filled. No auditor or clean-room executor
> identity or appointment, subject-matter competence declaration,
> conflict-of-interest disclosure or Owner C acceptance receipt, audit input
> instance, artifact/report/path, clean-room run, network, data,
> entropy, subprocess, runtime, scientific result, claim, submission, tracker
> edit, or evidence-ledger edit is supplied by this package.
