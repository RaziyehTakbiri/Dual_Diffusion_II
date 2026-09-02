# PhysioNet patient-disjoint split design and synthetic qualification

**Package state:** `PHYSIONET_PATIENT_DISJOINT_SPLIT_DESIGN_FROZEN_AND_SYNTHETICALLY_QUALIFIED_NO_DATA_ACCESS`  
**Project state:** `DRAFT_NOT_EXECUTABLE`  
**Reported date:** `2026-08-30`  
**Real PhysioNet data or source accessed:** no  
**Real split performed or feasibility observed:** no

## 1. Scope and renewed authority

The normalized visible renewed-scope instruction is:

> Sounds great. Go ahead and finish them in parallel. Mark all the completed tasks as the end.

It is 92 UTF-8 bytes and has SHA-256
`465aa47a0714b7914e33b6b6772afbfad3a56959cb6eb9f10b8e98f39c0f8d38`.
Only the visible text is bound. Raw transport bytes, trailing transport
framing, the conversation envelope, account identity, timestamp, and
cryptographic user authentication are not bound.

The instruction is interpreted as the explicit scope review required for one
locally bounded PhysioNet patient-group ordering/split-design package. It does
not authorize dataset or documentation browsing, source/license/governance or
approval contact, authentication, acquisition, data opening, a real split,
escrow, entropy, runtime or scientific execution, tracker mutation, or claim
promotion. A later one-way tracker update may occur only after exact independent
review; this package performs none.

The additive quartet is:

- `PROJECT_PHYSIONET_PATIENT_DISJOINT_SPLIT_DESIGN.md`;
- `research/fixtures/manuscript_v3_physionet_patient_disjoint_split_design_v1.json`;
- `research/diagnostics/manuscript_v3_physionet_patient_disjoint_split_design_v1.py`;
- `tests/unit/test_manuscript_v3_physionet_patient_disjoint_split_design_v1.py`.

No existing preregistration, closure, seal, static-selection, precontact,
Retail, power, tracker, runtime, authority, source, or result byte is modified.

During the preceding read-only design audit, the existing local PhysioNet raw,
adapter, and inventory source files were inspected as text. They were not
imported or executed and are not official-source, schema, dataset, or contact
evidence. Their current bytes are not added as live authority here; the bound
precontact candidate already carries explicitly historical snapshot receipts.

## 2. Exact effect and non-effect

After exact validation this quartet may support only the project-control
predicate
`PHYSIONET_PATIENT_DISJOINT_SPLIT_DESIGN_AND_SYNTHETIC_QUALIFICATION_VALIDATED`.
It closes zero unresolved fields, zero blockers, zero formal tests, and zero
result slots. In particular, B02, B07, F058, F061, and the populated-precontact
instance remain open.

The package resolves only the candidate's local missing specification for a
literal PhysioNet patient ordering/hash rule, canonical patient-ID bytes, and a
hash-collision tie break. It does not supply:

- a real split manifest or the F058 path;
- a power justification for 70/15/15 or the F061 value;
- a complete approval-contact roster or any official response;
- real escrow principals, keys, ACL acceptance, or opening authority;
- source version, archive, license, governance, schema, or timezone facts; or
- population, admission, contact, data-access, or scientific authority.

This is a standalone B02/F058/F061 design artifact under the renewed scope
review, not a third populated-precontact instance and not an amendment of the
frozen four-row candidate.

## 3. Conditional normalized-manifest contract

The pure splitter accepts only a finite in-memory list of exact mappings with
the two keys `record_ordinal` and `patient_id`.

- `record_ordinal` is a strict integer, never a Boolean, and the complete set is
  exactly `0..R-1` regardless of input-list order.
- `patient_id` is a nonempty ASCII-decimal string of at most 64 characters,
  denotes a strictly positive integer, and must already equal its minimal
  decimal representation. Leading signs, whitespace, non-ASCII digits, leading
  zeroes, zero, and aliases are refused.
- Multiple records may share one exact patient identifier; all such records
  remain in the same split. At least five distinct patients are required.
- Extra or missing keys, labels, targets, outcomes, treatment indicators,
  predictions, losses, test indicators, floats, aliases, and malformed values
  invalidate the whole manifest. No row is quarantined or repaired.

This representation is an agent-selected conditional interface. `RecordID` is
an inherited local interface token, not a verified official-source fact. It
does not claim that a future official archive has been parsed into it. A future
raw parser must bind every snapshot record to this projection without omission
and must establish through an admitted schema receipt that its patient identity
is the exact source `RecordID` under the frozen minimal-decimal rule. A mismatch
is domain no-go, not permission to change the rule.

## 4. Exact patient ordering

The canonical patient bytes are the ASCII bytes of the already-minimal positive
decimal `patient_id`. Their maximum length is 64 bytes.

The literal hash domain is the 37-byte ASCII string
`heterodiff/physionet-patient-order/v1` followed by one NUL byte. For patient
bytes `P`, the exact preimage is:

```text
ASCII("heterodiff/physionet-patient-order/v1") || 0x00 ||
uint16_be(len(P)) || P
```

The ordering digest is SHA-256 of that preimage. Patients are ordered by the
lexicographic pair `(digest_bytes, patient_bytes)`. The second component is the
frozen total tie break even if distinct patients collide under SHA-256. No
seed, entropy, secret, platform hash, locale, file order, or outcome enters the
ordering.

## 5. Hamilton allocation and assignment

Unique patients, not records or measurement rows, are the allocation units.
The candidate proportions are exactly 70/100 TRAIN, 15/100 VALIDATION, and
15/100 TEST. For `N` unique patients, each initial count is
`floor(N * numerator / 100)`. Remaining patients are assigned by descending
integer remainder, with fixed tie priority TRAIN, VALIDATION, TEST. All three
counts must be positive, which is guaranteed only after the explicit minimum
of five distinct patients is met.

The first TRAIN-count ordered patients enter TRAIN, the next VALIDATION-count
patients enter VALIDATION, and all remaining patients enter TEST. Every record
inherits its patient's split. Output patient assignments are ordered by
canonical patient bytes; record assignments are ordered by `record_ordinal`.

Success requires:

1. every input record ordinal appears exactly once in the output;
2. every canonical patient appears exactly once in the patient assignment;
3. every record for a patient has the same split;
4. patient counts equal the exact Hamilton allocation;
5. record and patient unions are complete and split sets are pairwise disjoint;
6. all three splits are nonempty; and
7. input-list permutations produce identical canonical output.

The rule is deterministic and patient-disjoint, but 70/15/15 remains a
candidate allocation. Synthetic correctness is not power justification.

## 6. Failure and anti-selection contract

Malformed manifests use `INVALID_NORMALIZED_MANIFEST`. Fewer than five unique
patients uses `INSUFFICIENT_PATIENT_GROUPS`. An internal preservation or
disjointness failure uses `INTERNAL_ALL_RECORD_PRESERVATION_FAILURE` or
`INTERNAL_PATIENT_DISJOINTNESS_FAILURE` and fails closed.

There is no fallback ordering, alternate proportion, seed redraw, patient or
record exclusion, duplicate deletion, retry, top-up, patient migration,
resplitting, favorable selection, or post-observation amendment. A future real
manifest that cannot satisfy this frozen conditional rule is terminal domain
no-go for this rule and requires an expressly authorized new pre-outcome route;
it is not repaired after held-out facts are observed.

## 7. Pure output and privacy boundary

On success the implementation returns a canonical in-memory mapping containing:

- the algorithm and outcome identifiers;
- domain-separated SHA-256 commitments to the normalized input and assignment;
- record and patient totals;
- exact patient and record counts per split;
- every patient assignment with its ordering digest; and
- every record assignment.

The function opens, contacts, persists, publishes, or executes nothing. The
patient identifiers and assignment carriers are internal private-manifest
material and are not publication safe. This quartet contains no real patient
identifier, record, timestamp, source response, credential, key, account,
approval, protected outcome, scientific result, or local absolute path. A
separately reviewed safe derivative is required for public or anonymous use.

## 8. Synthetic qualification and custody

Synthetic tests must cover constructive allocations, repeated records per
patient, Hamilton remainder/tie cases, input permutation invariance, injected
hash collisions and the canonical-byte tie break, all-row preservation,
patient disjointness, minimum patient count, malformed ordinals and IDs,
leading-zero aliases, extra outcome/label/test fields, strict type identity,
canonical output digests, and every zero-effect/nonclaim boundary.

The validator reopens the exact preregistration and closure, the complete seal,
static-selection, precontact-candidate, Retail-design, and power-route
quartets. Bindings are one-way. Mutable trackers are not inputs and this
quartet contains no tracker digest or reverse dependency.

Ordinary software qualification may launch the Python/pytest interpreter and
use in-memory synthetic fixtures. It is not a scientific or operational split.
Qualification must disable Python bytecode and pytest cache metadata. The
package validator is read-only and neither package source exposes a network,
subprocess, entropy, runtime, data, or file-writer route.

Qualification results are owner-observed tool output. No raw command, stdout,
or cache pre/post receipt is registered as a workspace artifact, and no
independent test execution is claimed by this quartet itself.

## 9. Definition of done

This quartet is complete only when all four files are canonical and mutually
bound without a cycle, every immutable predecessor reopens exactly, the pure
algorithm and closed machine record validate, hostile synthetic tests pass from
the workspace and an unrelated working directory with bytecode and pytest cache
disabled, and no focused bytecode cache exists.

Completion validates only
`PHYSIONET_PATIENT_DISJOINT_SPLIT_DESIGN_AND_SYNTHETIC_QUALIFICATION_VALIDATED`.
The original populated-precontact checkbox, independent admission, fresh
administrative authority, contact, approvals, later data-access instance,
fresh data authority, acquisition, split, escrow, all 172 fields, all 12
blockers, and every scientific gate remain open and unauthorized.
