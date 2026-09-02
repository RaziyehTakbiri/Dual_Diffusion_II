# CP75 external production-schema review checklist and claim matrix

Status: READY_FOR_EXTERNAL_REVIEW. No external review, authority, acceptance, production execution, gate, blocker, evidence, or closure is claimed.

## Frozen subject

- Subject record SHA-256: 97430f3996bec07a60f708eb94b0841fe30dd8770ee417b2d1f8a3f435f93314
- Scope/nonclaim SHA-256: fcd0840b23a7bd5ecf81511af3dfa7a4c9d230eaaa3217be074d69876cdeaa51
- Acceptance target: NONEXECUTABLE_CANDIDATE_DESCRIPTOR_FOR_CP75_DEVELOPMENT_AND_PRODUCTION_EXECUTABLE_SCHEMA_REVIEW
- Candidate descriptor acceptance is reviewable only for CP75 development.
- Production executable-schema acceptance is ineligible for this exact subject.
- The exact six production open items remain: primary-threshold-comparison-operator, primary-threshold-comparison-direction, primary-threshold-value-law, primary-selected-count-justification, primary-32-slot-decision-function, decision-timestamp-authority.

## Reviewer roles and exact criterion coverage

- protocol-and-provenance-reviewer: subject-byte-custody, cp65-lineage-and-alias-custody, scope-authority-and-nonclaim-boundary, artifact-inventory-preservation, lifecycle-branch-exhaustiveness, crash-cut-and-durability-closure, publication-manifest-and-direct-dag-closure, digest-preimage-and-24-crossbinding-closure, power-threshold-and-decision-executability
- runtime-and-durability-reviewer: subject-byte-custody, scope-authority-and-nonclaim-boundary, artifact-inventory-preservation, lifecycle-branch-exhaustiveness, crash-cut-and-durability-closure, publication-manifest-and-direct-dag-closure, output-envelope-framing-and-cardinality, raw-stable-stderr-rng-and-recomputation-semantics, resource-failure-retention-and-independent-validation, power-threshold-and-decision-executability
- statistical-power-and-decision-reviewer: subject-byte-custody, scope-authority-and-nonclaim-boundary, output-envelope-framing-and-cardinality, digest-preimage-and-24-crossbinding-closure, power-threshold-and-decision-executability
- independent-recomputation-reviewer: subject-byte-custody, cp65-lineage-and-alias-custody, scope-authority-and-nonclaim-boundary, artifact-inventory-preservation, output-envelope-framing-and-cardinality, digest-preimage-and-24-crossbinding-closure, raw-stable-stderr-rng-and-recomputation-semantics, resource-failure-retention-and-independent-validation, power-threshold-and-decision-executability

Every role must bind a distinct externally governed identity and key. Signature mathematics alone is never identity or authority.

## Claim matrix

| # | Criterion | Candidate blocking | Production blocking | Local pre-review state |
|---:|---|:---:|:---:|---|
| 1 | subject-byte-custody | yes | yes | UNREVIEWED |
| 2 | cp65-lineage-and-alias-custody | yes | yes | UNREVIEWED |
| 3 | scope-authority-and-nonclaim-boundary | yes | yes | UNREVIEWED |
| 4 | artifact-inventory-preservation | yes | yes | UNREVIEWED |
| 5 | lifecycle-branch-exhaustiveness | yes | yes | UNREVIEWED |
| 6 | crash-cut-and-durability-closure | yes | yes | UNREVIEWED |
| 7 | publication-manifest-and-direct-dag-closure | yes | yes | UNREVIEWED |
| 8 | output-envelope-framing-and-cardinality | yes | yes | UNREVIEWED |
| 9 | digest-preimage-and-24-crossbinding-closure | yes | yes | UNREVIEWED |
| 10 | raw-stable-stderr-rng-and-recomputation-semantics | yes | yes | UNREVIEWED |
| 11 | resource-failure-retention-and-independent-validation | yes | yes | UNREVIEWED |
| 12 | power-threshold-and-decision-executability | no | yes | PRODUCTION_NONPASS_REQUIRED |

## Criterion questions

### 1. subject-byte-custody

<!-- CP75-CRITERION:subject-byte-custody:QUESTION-BEGIN -->
Do the supplied final v25 and CP74 source, test, embedded record, byte-count, line-count, receipt, and SHA-256 pins match the frozen review subject exactly?
<!-- CP75-CRITERION:subject-byte-custody:QUESTION-END -->

Acceptance rule: exact byte and digest equality for every named subject component and embedded record pointer

### 2. cp65-lineage-and-alias-custody

<!-- CP75-CRITERION:cp65-lineage-and-alias-custody:QUESTION-BEGIN -->
Does the subject preserve the CP65 artifact-order, schema-record-order, referenced-output-order, gate-evidence DAG alias, and typed-graph hash-reference lineage without claiming CP75 revalidation of the full typed graph?
<!-- CP75-CRITERION:cp65-lineage-and-alias-custody:QUESTION-END -->

Acceptance rule: all three CP65 order hashes, the 20/44 gate view, two aliases, and hash-only 456/708 typed-graph boundary must match

### 3. scope-authority-and-nonclaim-boundary

<!-- CP75-CRITERION:scope-authority-and-nonclaim-boundary:QUESTION-BEGIN -->
Are the candidate-only, nonexecutable, unresolved-decision, unaccepted, unauthoritative, nonevidentiary, nongate, nonblocker, nonexecution, and OPEN scope boundaries complete and immutable under subject change?
<!-- CP75-CRITERION:scope-authority-and-nonclaim-boundary:QUESTION-END -->

Acceptance rule: all fixed nonclaims and six open items must be acknowledged; any subject mutation supersedes this request

### 4. artifact-inventory-preservation

<!-- CP75-CRITERION:artifact-inventory-preservation:QUESTION-BEGIN -->
Are all 64 CP65 artifact descriptors preserved and are their eleven branch occurrence expressions and conditional occurrence rules closed without optional or open-ended production claims?
<!-- CP75-CRITERION:artifact-inventory-preservation:QUESTION-END -->

Acceptance rule: all 64 descriptors and every 64-by-11 occurrence cell must match the candidate definition

### 5. lifecycle-branch-exhaustiveness

<!-- CP75-CRITERION:lifecycle-branch-exhaustiveness:QUESTION-BEGIN -->
Are the eleven lifecycle branches mutually exclusive, collectively exhaustive, and consistent with their required, forbidden, durable-prefix, terminal, and recovery artifacts?
<!-- CP75-CRITERION:lifecycle-branch-exhaustiveness:QUESTION-END -->

Acceptance rule: all eleven branch rows must be disjoint, exhaustive, and dependency-compatible

### 6. crash-cut-and-durability-closure

<!-- CP75-CRITERION:crash-cut-and-durability-closure:QUESTION-BEGIN -->
Are all six named crash cuts complete at-cut durable closures with exact forbidden and recovery semantics, including the preallocated empty acquisition journal and post-STARTED recovery boundary?
<!-- CP75-CRITERION:crash-cut-and-durability-closure:QUESTION-END -->

Acceptance rule: all six at-cut vectors and recovery-only effects must match the frozen truth table

### 7. publication-manifest-and-direct-dag-closure

<!-- CP75-CRITERION:publication-manifest-and-direct-dag-closure:QUESTION-BEGIN -->
Are SHA-manifest and COMMITTED exceptions, the exact gate-evidence direct DAG, conditional predecessors, downward closure, and acyclic publication order preserved?
<!-- CP75-CRITERION:publication-manifest-and-direct-dag-closure:QUESTION-END -->

Acceptance rule: manifest and COMMITTED exception vectors plus the direct DAG must match exactly

### 8. output-envelope-framing-and-cardinality

<!-- CP75-CRITERION:output-envelope-framing-and-cardinality:QUESTION-BEGIN -->
Are all fifteen output envelopes, complete-instance cardinalities, heterogeneous unit counts, final-file framing rules, and abnormal whole-final-shard prefix rules exact?
<!-- CP75-CRITERION:output-envelope-framing-and-cardinality:QUESTION-END -->

Acceptance rule: all fifteen envelopes and the 201 final instances and 196617 units must match exactly

### 9. digest-preimage-and-24-crossbinding-closure

<!-- CP75-CRITERION:digest-preimage-and-24-crossbinding-closure:QUESTION-BEGIN -->
Are every record, ordered, body, plain-file digest preimage and all twenty-four crossbindings closed, acyclic, and bound to exact carriers and predecessor pointers?
<!-- CP75-CRITERION:digest-preimage-and-24-crossbinding-closure:QUESTION-END -->

Acceptance rule: all executable digest formulas and twenty-four crossbindings must match exactly

### 10. raw-stable-stderr-rng-and-recomputation-semantics

<!-- CP75-CRITERION:raw-stable-stderr-rng-and-recomputation-semantics:QUESTION-BEGIN -->
Are the raw-to-stable, stderr, Philox state, CP69 interchange, CP71 recomputation, diagnostic, primary, decision, and ledger candidate semantics exact while production bodies remain unobserved?
<!-- CP75-CRITERION:raw-stable-stderr-rng-and-recomputation-semantics:QUESTION-END -->

Acceptance rule: all candidate nested schemas and exact projections must match without a production observation claim

### 11. resource-failure-retention-and-independent-validation

<!-- CP75-CRITERION:resource-failure-retention-and-independent-validation:QUESTION-BEGIN -->
Are parser and issued-record resource bounds, stable error precedence, atomic failure, sealing, concurrency, successful-return nonretention, and source-independent reconstruction adequate and nonauthoritative?
<!-- CP75-CRITERION:resource-failure-retention-and-independent-validation:QUESTION-END -->

Acceptance rule: all bounded-parser, sealing, error, concurrency, and nonretention claims must survive hostile reconstruction

### 12. power-threshold-and-decision-executability

<!-- CP75-CRITERION:power-threshold-and-decision-executability:QUESTION-BEGIN -->
Are threshold operator, direction, value law, selected-count justification, the thirty-two-slot decision function, and timestamp authority externally resolved sufficiently for production executability?
<!-- CP75-CRITERION:power-threshold-and-decision-executability:QUESTION-END -->

Acceptance rule: current CP74 must not receive production ACCEPT; external power and decision semantics remain unresolved

## Two-axis response rules

Criterion dispositions are PASS, DEFER, FAIL, or ABSTAIN. Per axis, FAIL derives REJECT; otherwise DEFER derives DEFER; otherwise ABSTAIN derives ABSTAIN; otherwise all applicable blocking criteria PASS derive scoped ACCEPT.

For the current subject, protocol/provenance and runtime/durability reviewers record criterion 12 as ABSTAIN; statistical/power and independent/recomputation reviewers record it as DEFER. Candidate acceptance still requires criteria 1 through 11 PASS. Production ACCEPT is forbidden.

Unexpected findings are permitted and must use bounded unique identifiers. Conditions are DEFER, never acceptance.

### Exact axis derivation precedence

- if-any-applicable-blocking-result-FAIL-then-axis-disposition-REJECT
- else-if-any-applicable-blocking-result-DEFER-then-axis-disposition-DEFER
- else-if-any-applicable-blocking-result-ABSTAIN-then-axis-disposition-ABSTAIN
- else-all-applicable-blocking-results-PASS-then-candidate-axis-ACCEPT_FOR_CP75_DEVELOPMENT_ONLY-or-production-axis-ACCEPT
- WITHDRAW-is-a-separate-empty-result-response-branch-and-both-axes-WITHDRAW

### Exact current-subject criterion 12 role branches

- protocol-and-provenance-reviewer: ABSTAIN; finding_ids=empty;required_change_ids-contribution=empty;comment_sha256=nonzero-reason-digest;acknowledged_subject_open_item_ids=exact-six
- runtime-and-durability-reviewer: ABSTAIN; finding_ids=empty;required_change_ids-contribution=empty;comment_sha256=nonzero-reason-digest;acknowledged_subject_open_item_ids=exact-six
- statistical-power-and-decision-reviewer: DEFER; finding_ids=exact-six-known-open-item-ids;required_change_ids=exact-six-known-open-item-ids;comment_sha256=nonzero-reason-digest;acknowledged_subject_open_item_ids=exact-six
- independent-recomputation-reviewer: DEFER; finding_ids=exact-six-known-open-item-ids;required_change_ids=exact-six-known-open-item-ids;comment_sha256=nonzero-reason-digest;acknowledged_subject_open_item_ids=exact-six

### Exact criterion-result branches

- PASS=>finding_ids-exact-empty;comment_sha256-exact-nonzero-lowercase-64hex
- DEFER=>finding_ids-nonempty-bounded-unique-identifiers;comment_sha256-exact-nonzero-lowercase-64hex
- FAIL=>finding_ids-nonempty-bounded-unique-identifiers;comment_sha256-exact-nonzero-lowercase-64hex
- ABSTAIN=>finding_ids-exact-empty;required-change-contribution-exact-empty;comment_sha256-exact-nonzero-reason-lowercase-64hex
- every-row-has-exact-five-keys-and-row_sha256-is-zero-carrier-domain-digest

### Exact response and relation branches

- substantive-ordinary=>all-exact-response-fields-nonnull-except-supersedes_response_sha256-and-withdraws_response_sha256-both-null
- substantive-replacement=>all-exact-response-fields-nonnull-except-withdraws_response_sha256-null;supersedes_response_sha256-lowercase-64hex
- withdrawal=>both-axis-dispositions-WITHDRAW;ordered-criterion-results-and-their-digest-vector-and-open-findings-and-required-changes-and-acknowledged-open-items-and-review-method-ids-exact-empty;withdraws_response_sha256-lowercase-64hex;supersedes_response_sha256-null
- nonwithdrawal=>withdraws_response_sha256-null
- template-only-unissued=>all-reviewer-identity-key-authority-report-result-decision-time-signature-and-response-digest-fields-null;never-an-issued-response

### Exact finding, change, and report bindings

- open_finding_ids=stable-ordered-unique-union-of-row-finding_ids-in-criterion-order-and-row-order
- required_change_ids=bounded-unique-subset-of-open_finding_ids-and-thus-resolved-by-full-review-report-pointer
- substantive-response-full_review_report_sha256=nonzero-lowercase-64hex-pointer-only;packet-and-one-response-validator-do-not-verify-report-bytes
- unexpected-finding-identifiers-are-nonempty-lowercase-ascii-[a-z0-9][a-z0-9._:-]{0,127}-unique-and-not-closed-to-an-allowlist
- every-nonwithdrawal-response-acknowledges-exact-six-subject-open-item-ids-in-subject-order

### Exact public-key and interval grammar

- SHA256(cp65-test28-independent-reviewer-public-key-identity-v1\0+canonical(reviewer_role,reviewer_identity_sha256,signature_scheme_id,authority_id,modulus_hex,public_exponent))
- SHA256(cp75-test28-production-schema-acceptance-reviewer-public-key-document-v1\0+canonical(exact-public-key-document-with-document_sha256-set-to-64-zero-hex))
- response.reviewer_public_key_document_sha256=plain-SHA256-of-exact-supplied-canonical-public-key-document-bytes;the-internal-document_sha256-zero-carrier-digest-is-validated-separately;response.reviewer_role=public-key.reviewer_role;response.reviewer_identity_sha256=public-key.reviewer_identity_sha256;response.reviewer_organization_sha256=public-key.reviewer_organization_sha256;response.signature_scheme_id=public-key.signature_scheme_id;response.authority_id=public-key.authority_id;response.reviewer_public_key_identity_sha256=public-key.key_identity_sha256
- modulus_hex=exact-768-lowercase-hex-characters;decoded-length=384;integer-bit_length=3072;high-bit-set;odd;gcd(modulus,65537)=1;public_exponent=65537;signature_scheme_id=exact-fixed-profile
- exact-UTC-YYYY-MM-DDTHH:MM:SSZ;key-valid_from<key-valid_until;response-valid_from<=signed_at<response-valid_until;response-interval-contained-in-key-interval;coherence-only-no-clock-or-trusted-time-validity-claim
- Mathematical validity never implies identity, trust, appointment, authority, current-time validity, or acceptance.

## External return requirements

A substantive response must bind the exact request, manifest, subject, checklist, contract vectors, review context, reviewer identity and organization, public-key document, authority appointment, conflict-of-interest and independence attestations, revocation status, method/toolchain, full report, criterion rows, both dispositions, validity interval, and signature.

The supplied-response validator checks exact bytes and RSA-PSS mathematics for one response only. It does not check external attachment bytes, trust, authority, current time, revocation, supersession, withdrawal targets, conflicts, aggregation, or acceptance.

## Non-effect

Even a future externally accepted nonexecutable candidate descriptor authorizes only construction of a separate development qualification. It does not freeze a production schema, satisfy CP65 gates 15 through 17, close a blocker, authorize execution, accept evidence, or close Formal Test 28.
