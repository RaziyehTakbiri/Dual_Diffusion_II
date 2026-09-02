# E-A1-D1 trained-checkpoint development-evidence registration

**Evidence ID:** `E-A1-D1`  
**Evidence class:** `NONCONFIRMATORY_DEVELOPMENT_EVIDENCE`  
**Registration mode:** `ADDITIVE_LEDGER_SIDECAR`  
**Source lane:** `A1-D1-TRAINED-CHECKPOINT-DIAGNOSTIC-V1`  
**Source outcome:** `COMPLETE_FINITE_KNOWN_LAW_DIAGNOSTIC`  
**Scope:** `TRAINED_DEVELOPMENT_CHECKPOINT_DIAGNOSTIC_ONLY`  
**Disposition:** **PASS WITH EXPLICIT SCOPE LIMITS**  
**Model-quality decision:** `NOT_MADE`

## 1. Purpose and status meaning

This additive record registers the completed finite-A1 trained-checkpoint
diagnostic as development evidence. It does not rewrite the historical claim
ledger, execution preregistration, CP76 readiness snapshot, manuscript prose,
or either the V2 checkpoint artifact or D1 result artifact.

Here, **PASS WITH EXPLICIT SCOPE LIMITS** means only that the frozen one-shot
diagnostic completed, its custody and completeness checks passed, and its
prespecified numerical-coherence checks passed. It is not a favorable
model-quality decision. The learned-quality quantities had no acceptance
threshold, and none is introduced after observing the result.

This record is not a confirmatory result. It does not qualify `R1-A1` or
`R2-HYBRID`, close or prove `C17`, promote a C-row or manuscript claim,
authorize confirmatory or production execution, select a checkpoint, or make
the manuscript ready for submission.

## 2. Bound source evidence

The registered result is the exact two-file D1 output rooted at
`artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1`, together with
its adjacent consumed-attempt marker.

| Artifact | Raw SHA-256 | Record/self SHA-256 |
|---|---|---|
| `diagnostic-record.json` | `4b983cd0dcb0e068bfd6d8c47d726e2f02ecb6cf5e17b4f77022d1e10f8c7b10` | `68434890dbd3157b70e700d6a649000dbc9ee60e297b9196af46e312beba07e6` |
| `success-receipt.json` | `eabecf04bfe0831fa14d60126c541774aaf25c58283ebb999dc3de2403e9cada` | `54167cf673861b93db3dd6cd354f9e08796bef59ef19b08ca4b03e59c4a62105` |
| adjacent attempt marker | `acfc404eca9ed711279087861518b7e9b32dfdb5fec4aaba318b50e7b4854e14` | `4d9bdd188be51385d08c4a7540905096ce1f4f856ee313a524542f51684bbeb6` |

The result also binds the machine freeze
`11d341f65bde47caffcf3c946919c3c0c83254684fb58d0ad643b1874fb3a973`,
human freeze
`59f00d83aba2545ec80b4778cfa181b0a5a0be043bddfb42aef212aaf7533e6d`,
orchestration source
`7cf3a5785f6bb3576357fe8c9bd867955660c2ff2486ca0710c1398e32b1cb0e`,
and pre-execution hostile test
`fda8bafabcb8737035d0b342fd5639a6618900d0a958bd0dbbf0adb827ac0d25`.
The prior hostile test is a frozen pre-execution input; this registration's
separate focused test is the post-run validator and does not launch D1.

The source checkpoint remains the optimizer-produced V2 checkpoint with raw
checkpoint SHA-256
`e414fc880a04df2a868855c195666ce400ca3f975278900aaa450032b6c66e7c`.
The D1 evidence binds the V2 outer receipt raw SHA-256
`7c730742f38c0ad1dbfd023ee65851328f3655769ae58d23e6cdca8bbb11b885`,
inner SUCCESS-ledger SHA-256
`df4c5770f10350e4f0a0267842de775731349de67cc282cec1e6bbddfc7bc6cc`,
final-parameter SHA-256
`d0bf29778dd866f5cd752f76be39df05d8dc2d6a89476070b77dd25326530388`,
and classifier SHA-256
`5f35eddd4354b2ecf77abb9e01b46fbedf17bb917727827478a9bbc11cd3f14e`.

## 3. Registered coverage and values

The completed record covers all 33 reporting times over all 20 finite states
and all 21 canonical observations; all 21 path-reference preflights; all 21
aggregate path evaluations; and all 21 family supplements. The reference-set
SHA-256 is
`000000831290fe27cd1f49fb1b180fea33e39e47ad0e0d62d38eab274c39dbd5`.
The birth, death, and replacement partitions contain exactly 30, 30, and 60
active edges. The continuous component `KC` is
`NOT_APPLICABLE_NO_CONTINUOUS_COORDINATES`, not a numeric zero.

The registered path summaries are:

| Quantity | Value |
|---|---:|
| observation-weighted path KL (nats) | `0.006581007621322472` |
| observation-law conditional mean path KL among retained outcomes (nats) | `0.003631773437855018` |
| overflow path KL | `0.09711382901483998` |
| observation-weighted endpoint TV (dimensionless) | `0.023690985304278375` |
| overflow endpoint TV (dimensionless) | `0.11814236369841445` |
| overflow maximum intermediate TV (dimensionless) | `0.18287473808256435` |
| overflow observation mass | `0.03154866637521339` |
| overflow normalized path score | `0.17036802470127654` |
| weighted initializer component `K0` | `0.00279485108355441` |
| weighted birth component `K+` | `0.0024939882142367` |
| weighted death component `K-` | `0.0011921553561048588` |
| weighted replacement component `KR` | `0.00010001296742650317` |
| maximum family/aggregate cross-check difference | `6.938893903907228e-18` |

These values are copied by exact JSON pointer and decimal value into the
machine sidecar. The adaptive binary64 primary/refined agreement is a
diagnostic, not an interval enclosure or theorem proof.
All path-KL and component values are in nats; total-variation values are
dimensionless. The retained mean is weighted by the observation law
conditional on a retained outcome, not an unweighted average over observation
labels.

## 4. Mandatory visible limitations

Overflow is the weakest reported observation regime. Its path KL is
`0.09711382901483998`, endpoint TV is `0.11814236369841445`, and conditional-
initial TV is `0.11726381207950134`; its maximum intermediate TV is
`0.18287473808256435`, observation mass is `0.03154866637521339`, and
normalized path score is `0.17036802470127654`. These values may not be
replaced by the more favorable retained-observation summaries.

The normalization residual has physical-weighted RMSE
`0.02547407630692731` and maximum `0.15100529268222873`; the semigroup residual
has physical-weighted RMSE `0.011197231762216917` and maximum
`0.15721987873877863`. The maximum absolute residual-potential error
`1.140606604491632` is retained explicitly. These were report-only learned-
quality quantities, not frozen pass/fail gates. The registration therefore
makes no model-quality pass decision.

The subject is finite and all-atomic. It exercises no continuous-coordinate
energy, no occurrence-attached continuous mark fibers, and no real-domain
data. It contains no rigorous numerical enclosure, simultaneous-coverage
proof, production checkpoint, production-order admission, or scientific-
result eligibility. The diagnostic performed no training, fine-tuning, or
checkpoint selection.

The source evaluator's `production_bound=true` field means only that the
evaluator was tied to canonical SUCCESS-ledger custody. It is not production
authorization, production-checkpoint status, scientific eligibility, or a
claim-bearing result.

## 5. Claim, execution, and readiness preservation

This is an evidence-register sidecar, not a legacy claim-ledger-row mutation.
The bound historical claim ledger remains unchanged: `C17` remains
`THEOREM-TARGET`; `R1-A1` and `R2-HYBRID` remain `NOT RUN` with empty result
cells; and no claim row or result slot changes.

The execution preregistration remains `DRAFT_NOT_EXECUTABLE`, with
confirmatory execution unauthorized. CP76 remains an immutable historical
snapshot with readiness `NOT_READY`, submission readiness false, and no
readiness transition or supersession. This registration does not alter the
production workflow or manuscript prose.

The bound machine preregistration still contains exactly 174 unresolved null
values and 12 unresolved blockers. Ten blockers apply at
`CONFIRMATORY_EXECUTION`; two apply at
`CLAIM_PROMOTION_AND_SUBMISSION_NOT_CONFIRMATORY_EXECUTION`. Required
pre-execution nulls remain blocking. Every current freeze-predicate condition
remains false or unresolved as recorded in the machine sidecar; none of those
nulls, blockers, artifacts, or freeze conditions is closed by E-A1-D1.
Null post-execution proof, methods/statistics, and reproduction audit plans do
not block confirmatory execution, but they continue to block claim promotion
and submission.

CP76 historically recorded eight missing direct-support files. Since that
snapshot, `novelty_audit_matrix.md` and `execution_preregistration.md` have
appeared. The six paths still absent are:

- `manuscript_v3/configuration_reference_code_audit.md`;
- `manuscript_v3/reversible_hybrid_reference_code_audit.md`;
- `manuscript_v3/reverse_energy_objective_code_audit.md`;
- `manuscript_v3/association_observation_code_audit.md`;
- `manuscript_v3/association_preconditioner_code_audit.md`; and
- `manuscript_v3/configuration_energy_code_audit.md`.

This live file-presence delta is non-authoritative and does not rewrite CP76.
The substantive `novelty-independently-assessed` and
`execution-preregistered` criteria remain `BLOCKED`, overall readiness remains
`NOT_READY`, and there is no readiness transition.

## 6. Publication and anonymity boundary

This internal evidence registration is not a submission artifact. It is not
approved for inclusion in an anonymous submission or public release, and the
raw V2 artifact is not approved for either inclusion route. Raw V2 contains
local filesystem-path, process, timestamp, and detailed runtime metadata.

Those immutable custody artifacts must not be sanitized in place. A separate
publication-safe derivative is required, but its path is currently `null`.
The submission include/exclude roster is not frozen, and a fresh publication
and anonymity audit remains required before any anonymous or public artifact
is assembled.

## 7. Review boundary and next scientific step

No externally appointed reviewer panel is required to register this bounded,
nonpromotional development evidence. The focused post-run test independently
reopens the published bytes, recomputes the raw and self digests, projects the
registered values, and rejects claim, readiness, production, and scope
laundering. No transient review is represented as a durable independent-review
artifact.

A later claim or result-slot transition still requires its separately frozen
confirmatory design and the proof, methods/statistics, and reproducibility
review artifacts required by the manuscript execution preregistration. This
registration cannot serve as that transition.

D1 is now prior observed development knowledge. It may not be used to select a
future `R1-A1` primary metric, acceptance threshold, checkpoint, seed count, or
overflow policy, and overflow may not be excluded. Any future R1 freeze must
cite the D1 diagnostic-record raw SHA-256
`4b983cd0dcb0e068bfd6d8c47d726e2f02ecb6cf5e17b4f77022d1e10f8c7b10`
and declare controls against post-D1 outcome-driven design.

Accordingly, E-A1-D1 is not eligible for a confirmatory decision and was not
used for metric, threshold, checkpoint, seed-count, or overflow-policy
selection.
