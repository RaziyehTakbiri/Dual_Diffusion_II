# Retail customer-disjoint temporal split design and synthetic qualification

**Package state:** `RETAIL_CUSTOMER_DISJOINT_TEMPORAL_SPLIT_DESIGN_FROZEN_AND_SYNTHETICALLY_QUALIFIED_NO_DATA_ACCESS`  
**Project state:** `DRAFT_NOT_EXECUTABLE`  
**Reported date:** `2026-08-30`  
**Real Retail data or source accessed:** no  
**Real split performed or feasibility observed:** no  

## 1. Exact scope and authority

The normalized visible authority text is:

> Alright, sounds good. Go ahead then.

Its UTF-8 length is 36 bytes and its SHA-256 is
`834e4a9458adde27cebea9341c11ef09e49dc04dbfb2d7b9a05ed9108a16413b`.
Trailing transport whitespace or an HTML-space entity, if any, is outside this
normalization. Raw transport bytes, the conversation envelope, account
identity, timestamps, and cryptographic user authentication are not bound.

The authority is interpreted narrowly as construction and synthetic
qualification of one exact Retail split-design rule. Filenames, schema,
normalized-manifest representation, algorithm details, error codes, and the
four-file implementation are agent-selected bounded details. It does not
authorize source, documentation, license, governance, approval, or access
contact; browsing; credentials; data acquisition or opening; a real split;
scientific execution; outcome inspection; tracker edits; or claim promotion.

The additive files are:

- `PROJECT_RETAIL_CUSTOMER_DISJOINT_TEMPORAL_SPLIT_DESIGN.md`;
- `research/fixtures/manuscript_v3_retail_customer_disjoint_temporal_split_design_v1.json`;
- `research/diagnostics/manuscript_v3_retail_customer_disjoint_temporal_split_design_v1.py`;
- `tests/unit/test_manuscript_v3_retail_customer_disjoint_temporal_split_design_v1.py`.

No existing preregistration, seal, static-selection package, precontact
candidate, tracker, manuscript, source, data, or result byte is changed.

## 2. Exact effect and non-effect

After independent validation, this quartet may support only the named project-
control predicate
`RETAIL_CUSTOMER_DISJOINT_TEMPORAL_SPLIT_DESIGN_AND_SYNTHETIC_QUALIFICATION_VALIDATED`.
It targets both exact Retail split-design seams: B03/F060 for the temporal
cutoff/window rule and B03/F061 for the 70/15/15 allocation proportions and
counts. It does not write or fill either F060 or F061 in the immutable
preregistration; both remain null and OPEN. The package closes zero of 172
unresolved fields, zero of 12 blockers, zero formal tests, and zero results.

The Solo Block 2 precontact candidate quartet remains byte-for-byte unchanged.
This package resolves only its local Retail-design seam. Its approval-contact
roster, power justification, real escrow identities and ACLs, external facts,
population, review, admission, and authority gaps all remain open. This is not
characterized as a third precontact micro-layer: it is a separately authorized
B03/F060/F061 Retail temporal-and-allocation design and synthetic-qualification
artifact.

## 3. Conditional normalized-manifest contract

The pure splitter never opens a raw dataset. Its sole input is a caller-supplied
finite list of exact dictionaries with exactly three fields:

- `row_ordinal`: a strict integer, with the set of ordinals exactly
  `0,1,...,R-1`;
- `customer_key_hex`: a nonempty lower-case, even-length hexadecimal encoding
  of opaque canonical customer-key bytes, at most 2048 hex characters; and
- `timestamp_utc_microseconds`: a strict signed 64-bit integer giving UTC
  microseconds since the Unix epoch.

The input list may arrive in any order. Byte-exact customer keys define natural
groups. A future raw-to-normalized parser and manifest custody receipt must
prove that this projection contains **every row** of one fixed immutable Retail
snapshot and binds the raw source fields to these carriers. That parser and
receipt do not exist here.

There is no eligible/ineligible post-snapshot filter. If even one snapshot row
has a missing, empty, malformed, ambiguous, out-of-range, or otherwise
unrepresentable customer key or timestamp, the whole manifest is invalid and
the domain is no-go. The row is not quarantined, censored, excluded, repaired,
or reassigned. Extra keys—including labels, outcomes, predictions, losses, or
test indicators—are rejected by the exact field roster and cannot influence
the algorithm.

## 4. Exact 70/15/15 Hamilton customer counts

Let `N` be the number of distinct byte-exact customers. The rule uses the
agent-selected rational proportions 70/100 training, 15/100 validation, and
15/100 test. It computes each floor quota with integer arithmetic:

`floor_s = floor(N * numerator_s / 100)`.

The remaining seats are assigned by descending integer remainder
`(N * numerator_s) mod 100`, with exact tie priority `TRAIN`, `VALIDATION`,
`TEST`. The three counts must sum to `N` and each must be positive. Therefore
`N >= 5` is required; smaller inputs fail closed. No random seed or entropy is
used.

This freezes a deterministic design choice. It is not a power justification,
does not close the power-review gate, and cannot be changed after observing a
real snapshot merely because the allocation is inconvenient.

## 5. Customer intervals and candidate boundaries

For each customer `c`, form the closed interval

`I_c = [minimum timestamp among c's rows, maximum timestamp among c's rows]`.

Let `T[0] < ... < T[M-1]` be all distinct observed row timestamps in exact
integer order. A boundary is represented by a gap between two adjacent values;
no floating-point midpoint is created. Enumerate every ordered pair of gap
indices `0 <= g1 < g2 <= M-2`.

For pair `(g1,g2)`, the exact windows are:

- TRAIN: `t <= T[g1]`;
- VALIDATION: `T[g1] < t <= T[g2]` (equivalently, because timestamps are
  discrete members of `T`, `T[g1+1] <= t <= T[g2]`); and
- TEST: `t > T[g2]` (equivalently `t >= T[g2+1]`).

A customer belongs to a window only if its **entire closed interval** lies in
that window. Any interval spanning either boundary makes that boundary pair
infeasible. All rows for a customer therefore move together.

## 6. Exact feasibility predicate and selection

A gap pair is feasible if and only if all of these hold:

1. every complete customer interval lies wholly in exactly one window;
2. every input row is assigned exactly once;
3. the three customer sets are pairwise disjoint and cover every customer;
4. their customer counts equal the exact Hamilton counts;
5. all three row and customer counts are positive;
6. `maximum TRAIN timestamp < minimum VALIDATION timestamp`; and
7. `maximum VALIDATION timestamp < minimum TEST timestamp`.

Feasible pairs are ordered lexicographically by the exact integer tuple
`(T[g1], T[g1+1], T[g2], T[g2+1])`. The first pair is selected. The rule uses
only customer-key equality and timestamps. It never reads or conditions on an
outcome, label, treatment, prediction, loss, metric, test statistic, or model
result.

If no feasible pair exists, the exact terminal code is
`NO_FEASIBLE_CUSTOMER_DISJOINT_TEMPORAL_BOUNDARY_PAIR`. There is no fallback,
new seed, boundary relaxation, alternate proportion, customer migration,
customer splitting, row exclusion, censoring, quarantine, retry, or post-result
repair. The Retail domain is not admitted under this rule.

## 7. Canonical pure output

On success, the pure implementation returns a canonical in-memory mapping with:

- algorithm and outcome identifiers;
- a domain-separated SHA-256 of the normalized input projection;
- row and customer totals;
- exact Hamilton customer counts;
- exact row counts;
- the four adjacent-timestamp boundary carriers;
- every customer assignment, sorted by decoded customer-key bytes;
- every row assignment, sorted by `row_ordinal`; and
- a domain-separated SHA-256 commitment to the assignment payload.

The output contains all input row ordinals exactly once. It does not open,
persist, contact, or publish anything. A future production runner, raw parser,
snapshot receipt, private manifest, and escrow route remain absent and
unauthorized. A real assignment would carry internal customer-key commitments
and is not publication-safe merely because it is normalized; it must remain in
the future private custody boundary.

## 8. Synthetic qualification

The hostile suite supplies only synthetic in-memory normalized rows. It covers:

- constructive feasible cases and exact boundaries/counts;
- repeated rows per customer and complete-customer grouping;
- overlapping/interleaved customer intervals with no feasible pair;
- equal timestamps at would-be boundaries;
- fewer than five customers;
- malformed, missing, extra, boolean-as-integer, overflow, duplicate-ordinal,
  empty-key, mixed-case-hex, and nonhex inputs;
- preservation of every row and customer;
- rejection rather than quarantine for every invalid row;
- permutation invariance of input-list order;
- label/outcome/test-indicator rejection and outcome independence;
- exact Hamilton remainders and tie priority;
- no-feasible terminal no-go with no alternate allocation;
- strict canonical machine/self/link/type validation;
- immutable predecessor custody; and
- absence of network, process, writer, entropy, data, or scientific routes in
  the read-only validator.

Passing synthetic tests proves only that the frozen pure rule behaves as
specified on synthetic manifests. It does not establish that a real Retail
snapshot satisfies the normalized-manifest contract or has a feasible boundary
pair.

Ordinary software qualification launches the Python/pytest interpreter and
writes pytest temporary replicas. That activity is not a scientific or
operational split subprocess and touches no source or data. Global workspace-
write absence is not claimed. The package-authored validator is read-only; the
hostile suite's writers are confined to pytest temporary replicas. Final runs
disable bytecode with `-B` and pytest cache metadata with
`-p no:cacheprovider`.

## 9. Custody and anonymity boundary

The validator reopens a fixed immutable predecessor roster: execution
preregistration and closure, the full prospective seal quartet, the full Solo
Block 2 static-selection quartet, and the full stable precontact-candidate
quartet. It validates exact bytes, modes, link counts, and relevant self-
digests. Mutable trackers and source files are not reverse-bound.

The package is internal research custody evidence, not a public or anonymous
supplement. It contains no real customer key, timestamp, row, URL response,
credential, account, key material, source receipt, protected outcome, local
absolute path, or scientific result. A future publication-safe derivative
requires separate review.

## 10. Definition of done

This Retail design package is complete only when the four additive files are
canonical and mutually bound without a cycle, all immutable predecessors reopen
exactly, the pure algorithm and every nonclaim validate, hostile tests pass in
temporary fixtures with bytecode and pytest cache disabled, and no focused
bytecode cache exists.

Completion validates only the named Retail design-and-synthetic-qualification
predicate. Real-data normalization, feasibility, split custody, power,
admission, escrow, external contact, data access, and science remain undone and
unauthorized.
