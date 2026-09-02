# Finite-A1 trained development-checkpoint diagnostic freeze V1

**Lane:** `A1-D1-TRAINED-CHECKPOINT-DIAGNOSTIC-V1`  
**State:** `FROZEN_DIAGNOSTIC_EXECUTION_AUTHORIZED`  
**Scope:** `TRAINED_DEVELOPMENT_CHECKPOINT_DIAGNOSTIC_ONLY`  
**Only successful outcome:** `COMPLETE_FINITE_KNOWN_LAW_DIAGNOSTIC`  
**Training authorized:** no  
**Confirmatory or production execution authorized:** no  
**Scientific-result or manuscript-claim effect:** none

## 1. Purpose and boundary

This freeze authorizes one read-only diagnostic execution against the genuine
optimizer-produced finite-A1 V2 development checkpoint. It closes the next
engineering step after checkpoint creation: reopen the exact V2 custody,
construct its certificate-bound classifier from the retained capsule, evaluate
all frozen non-path and path quantities, and issue one atomic diagnostic record
only if every custody, completeness, and numerical-coherence check passes.

The diagnostic is not a training run, checkpoint-selection run, production
campaign, confirmatory experiment, or manuscript result. No outcome from this
lane can qualify `R1-A1` or `R2-HYBRID`, close `C17`, authorize production,
change a preregistered result slot, promote a claim, or establish scientific
eligibility. The word `production_bound` in the pre-existing evaluator API
means only that the callable is tied to canonical SUCCESS-ledger custody; it
does not grant production or scientific status in this lane.

There is exactly one diagnostic execution and no retry, resume, alternate
checkpoint, substitute runtime, reduced observation set, or post-result
threshold change. A failure or interruption yields no complete diagnostic and
does not authorize another attempt.

Before the worker process starts, the runner must durably create the adjacent
marker
`artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1.attempt.json`
with state `ATTEMPT_CONSUMED_NONRETRYABLE`. Its exclusive creation is the
irreversible attempt boundary. The marker contains no diagnostic totals. It
remains in place after interruption, failure, or success, and any pre-existing
marker makes another launch a refusal. A successful diagnostic record and
receipt must bind both the marker's raw and self digests.

## 2. Immutable V2 checkpoint custody

The sole input is the completed V2 lane
`A1-DEV-GUIDED-1729-N32768-V2` at
`artifacts/manuscript_v3_a1_development_checkpoint_v2`. The diagnostic must
reopen, validate, and preserve the following identities before evaluation,
between the major evaluation phases, and before publication of any output:

| Identity | Frozen value |
|---|---|
| outer success-receipt raw SHA-256 | `7c730742f38c0ad1dbfd023ee65851328f3655769ae58d23e6cdca8bbb11b885` |
| outer success-receipt self SHA-256 | `154d64d654a4f175f07e323524782f90af29dbbb5f81c053ce0105a67dbfe747` |
| inner SUCCESS-ledger self SHA-256 | `df4c5770f10350e4f0a0267842de775731349de67cc282cec1e6bbddfc7bc6cc` |
| campaign SHA-256 | `5bdf07f03e5f6ebb0340c6a55a3f9af45a89ee2010232650faa8cab54dc98508` |
| run-key SHA-256 | `dc7484372d3f8a633755450bda9d70f0ed182005dba052a0fa86747ae0fe4f70` |
| checkpoint-file SHA-256 | `e414fc880a04df2a868855c195666ce400ca3f975278900aaa450032b6c66e7c` |
| final-parameter SHA-256 | `d0bf29778dd866f5cd752f76be39df05d8dc2d6a89476070b77dd25326530388` |
| feature SHA-256 | `f73a1a793aae93001d7537ddfdd44955d33bdc14ba37dbc397e056d67111d37d` |
| classifier SHA-256 | `5f35eddd4354b2ecf77abb9e01b46fbedf17bb917727827478a9bbc11cd3f14e` |
| continuous-certificate SHA-256 | `008a0df7c67600932257991ddf5b69fa77fb9056b90f45ec280f45629ad89926` |
| execution-runtime SHA-256 | `032a7e48bccd0efbd79606621daf0825885b76ea83118ab2d75ac8aa4d905ea0` |
| capsule source-manifest SHA-256 | `1ead8f21969b1ebf31d98fca846efc21edbf9dee95a8e4c7be8e19bf9b16dfb1` |
| training-configuration SHA-256 | `eda69c9d2a57c62ce4805da1d3cad9606619ef703eda5d6a45fb1b602022f968` |
| training preflight SHA-256 | `b8fd9ccf80ddd2993c3d546f9cb28583d93d82af66e69b09d2f9cd339e41ef3b` |

The exact checkpoint path is
`artifacts/manuscript_v3_a1_development_checkpoint_v2/capsule/artifacts/a1_campaign_v4/dc7484372d3f8a633755450bda9d70f0ed182005dba052a0fa86747ae0fe4f70.pt`.
The inner ledger is the sibling `ledger.json`. Its raw SHA-256 is
`2edf370e99fbd9755abcdd715be8a6ee0be7b23aae9e3ee2fa20184cee46e879`.

All optimizer, final-snapshot, certificate, classifier, run, campaign, and
receipt identities must agree through the existing SUCCESS-ledger verifier.
The bound evaluator must expose the final parameter, inner success receipt,
classifier, and campaign identities above. Any missing, changed, malformed,
or merely caller-supplied identity is a refusal. The V2 directory and every
file beneath it are read-only inputs; this lane may not create, edit, rename,
move, replace, or delete anything there.

## 3. Capsule-only implementation and runtime

Every scientific or checkpoint API must be imported from the immutable V2
capsule at
`artifacts/manuscript_v3_a1_development_checkpoint_v2/capsule/src`.
The live repository `src` tree must not be importable by the diagnostic
process, and the capsule must not be patched. The new orchestration program
lives outside `src` at
`research/diagnostics/finite_association_trained_checkpoint_diagnostic.py`;
it may only compose, validate, and serialize the retained capsule APIs.

The interpreter is exactly `.venv-m1/bin/python` in safe-path mode. The
runtime remains native arm64 CPython 3.11.5 with NumPy 2.4.6, SciPy 1.17.1,
CPU-only PyTorch 2.12.1, and threadpoolctl 3.6.0. Accelerators are hidden,
deterministic PyTorch algorithms are enabled, `PYTHONHASHSEED=0`, bytecode
writes are disabled, and every discovered numerical pool plus PyTorch
intra-op and inter-op execution uses one thread. The retained checkpoint
execution-runtime SHA-256 is
`032a7e48bccd0efbd79606621daf0825885b76ea83118ab2d75ac8aa4d905ea0`.

The independently reconstructed path-runtime record must have SHA-256
`4992cb102180bb6e6bf76a70280a19a6ca0952b5148c662c331ebafcbb504cda`.
The exact execution entry point will be the hash-bound orchestration program
under this environment; no training entry point or optimizer permit may be
called.

## 4. Frozen finite subject

The capsule must freshly reconstruct the target-runtime finite-A1 fixture and
obtain all of the following exact identities:

| Subject identity | Frozen value |
|---|---|
| production fixture SHA-256 | `0121b487728b40356de6707a33ba4881100c3d1b587259b19723463a60cecdcc` |
| ordered path-content SHA-256 | `ba9de201cdf249d9c2adeb07202075e20765e0bab637ce79668fde245b19f67f` |
| edge-family partition SHA-256 | `bc54ccc360803bc1673508a540a59ba48c24d58b8a316b0c3674632542cefc6f` |
| active birth/death/replacement edge counts | `(30, 30, 60)` |

The subject contains 20 capped three-type count states and 21 canonical
observations, with overflow fixed at index 20. The reporting grid is exactly
`t_j=j/32`, `j=0,...,32`. All 33 times, all 20 states, all 21 observations,
and all positive aggregate generator edges are mandatory. The historical
local-compatibility fixture and path tokens are inadmissible.

## 5. Frozen evidence-binder sequence

The single attempt must perform the following ordered sequence without using
cached diagnostic results:

1. verify that the diagnostic output root is absent and reopen the exact V2
   outer receipt, ledger, checkpoint, and capsule source custody;
2. use the capsule SUCCESS-ledger verifier to load and revalidate the exact
   fitted checkpoint, then derive the certificate-bound classifier through
   the capsule's fitted-checkpoint evaluator binding;
3. freshly reconstruct the fixture, path content, family partition, and
   target path runtime and match every frozen identity;
4. evaluate the complete 33-knot non-path grid;
5. construct the complete ordered 21-observation path-reference preflight,
   require it to pass, and retain its reference-set digest;
6. evaluate the candidate aggregate path law for all 21 observations using
   that exact preflight;
7. independently compute the all-21 family supplement for `K0`, `K+`, `K-`,
   and `KR`, while recording `KC` as explicitly not applicable;
8. reopen V2 custody and the bound implementation/freeze/test bytes, validate
   every internal and cross-record identity, and only then atomically publish
   one result artifact.

The checkpoint and evaluator integrity callbacks must surround every
classifier-use phase. A precomputed reference set, cached classifier grid,
live-tree fixture, partial observation record, or hand-constructed evidence
container is inadmissible.

## 6. Complete 33-knot non-path evaluation

The non-path record must be the capsule's complete
`FiniteAssociationNonPathEvaluation` over the exact `33 x 20 x 21` grids. It
must bind the frozen final parameter, classifier, inner success receipt, and
campaign identities and must report every existing mandatory group:

- masked excess BCE on train, validation, joint/time/pair interpolation,
  latent-three, anchor-three, both-three, overflow, and balanced OOD strata;
- centered log-information RMSE and maximum error;
- residual RMSE, maximum error, correction scale, and oracle range;
- birth, death, and replacement edge log-rate diagnostics;
- conditional-initial total variation;
- Brier, excess Brier, ten-bin reliability ECE, and maximum reliability gap;
  and
- terminal, generator-row-sum, normalization, semigroup, and edit-cycle
  coherence diagnostics.

All arrays and reported scalars must be finite, internally consistent, and
cover the full frozen grid. Terminal guide/target log-density error must be at
most `1e-12`, maximum terminal residual at most `1e-10`, generator row-sum
residual at most `1e-10`, and scalar edit-cycle residual at most `1e-10`.
Other learned-quality quantities are report-only: no favorable performance
threshold may be invented, and an unfavorable finite value is not grounds to
select another checkpoint or suppress the diagnostic.

## 7. Complete 21-observation aggregate path evaluation

Before a candidate path is evaluated, all 21 canonical reusable reference
records must be freshly built and content-bound in observation order
`0,...,20`. The preflight must use the exact fixture/path/runtime identities,
the frozen primary and refined solver settings, and independent numerical
calls. For every reference:

- oracle-self path KL is at most `1e-10` nat;
- primary/refined unconditional path-KL change is at most `1e-8` nat;
- primary and refined unconditional denominators are each strictly greater
  than `1e-12` nat; and
- exact-target occupancy maximum absolute error is at most `1e-8`.

The candidate aggregate path evaluation must then cover all 21 observations
with one common parameter/classifier/receipt/campaign/reference-set custody.
For every observation, primary/refined path-KL change and primary/refined
endpoint total variation must each be at most `1e-8`, and target occupancy
error must be at most `1e-8`. All path KL, normalized path scores, initial,
intermediate, and endpoint quantities and all retained, overflow, ambiguous,
and observation-weighted summaries must be finite and internally consistent.
No subset of favorable observations can stand in for the complete record.

## 8. All-21 family supplement

For each observation, the supplement uses the same exact target-conditioned
initial law and exact target occupation as the aggregate calculation. Every
positive aggregate generator edge must be classified exactly once by the
frozen `(30, 30, 60)` birth/death/replacement partition. It records, in order:

- `K0_NORMALIZED_INITIALIZER`;
- `KC_CONTINUOUS_COORDINATES`, with applicability and target measure both
  `NOT_APPLICABLE_NO_CONTINUOUS_COORDINATES`, numeric values absent, and no
  contribution to the total;
- `K_PLUS_BIRTH`;
- `K_MINUS_DEATH`; and
- `K_R_REPLACEMENT`.

`K0`, `K+`, `K-`, and `KR` must each have primary and refined finite,
nonnegative values. Every per-component primary/refined absolute difference
must be at most `1e-8`. For both numerical lanes, the four applicable
components must sum to the corresponding independently computed aggregate
path KL within `1e-8` nat. The reported dynamic subtotal must equal
`K+ + K- + KR`, and the total must equal `K0 + K+ + K- + KR`, each within
`1e-8` nat. The supplement must also match the aggregate record's initial,
dynamic, and total terms separately within `1e-8` nat. Opposing family errors
may not cancel in a total-only comparison: every family gate is applied
separately.

Adaptive primary/refined agreement is a floating-point diagnostic, not an
interval proof. Consequently all interval-enclosure, simultaneous-coverage,
rigorous-error-enclosure, and theorem-proof fields remain false.

## 9. Atomic result and disposition

The sole output root is
`artifacts/manuscript_v3_a1_trained_checkpoint_diagnostic_v1` and must be
absent at attempt start. No bytes may appear there until all checks above have
passed. Work is performed in a fresh private staging directory; on success,
exactly `diagnostic-record.json` and `success-receipt.json` are fsynced and
the directory is atomically installed at the frozen root. No copy of the
implementation, hostile test, machine freeze, or human freeze is retained in
the output directory. Instead, the two published records collectively bind
the SHA-256 digests of those four frozen inputs. A failure removes only that
attempt's private staging directory and issues no diagnostic artifact.
Pre-existing or partially installed output is a refusal, not resumable state.

Only when every required check passes may the record state be
`COMPLETE_FINITE_KNOWN_LAW_DIAGNOSTIC`, with scope exactly
`TRAINED_DEVELOPMENT_CHECKPOINT_DIAGNOSTIC_ONLY`. Otherwise no complete state
may be issued. Success still leaves all of the following false:

- production-order admissibility and production authorization;
- confirmatory execution and confirmatory-result status;
- `R1-A1` and `R2-HYBRID` qualification;
- `C17` closure or theorem completion;
- scientific-result eligibility; and
- manuscript claim promotion.

The retained V1 failure and V2 development artifacts remain untouched. This
diagnostic neither consumes nor creates an optimizer authorization and cannot
train, fine-tune, select, overwrite, or relabel a checkpoint.

## 10. Final implementation binding

The orchestration source and hostile test paths were frozen after their final
audited bytes were established:

- `research/diagnostics/finite_association_trained_checkpoint_diagnostic.py`,
  SHA-256 `7cf3a5785f6bb3576357fe8c9bd867955660c2ff2486ca0710c1398e32b1cb0e`;
- `tests/unit/test_finite_association_trained_checkpoint_diagnostic.py`,
  SHA-256 `fda8bafabcb8737035d0b342fd5639a6618900d0a958bd0dbbf0adb827ac0d25`.

Those final bindings were completed before execution authorization. They
authorize only the single diagnostic lane defined here and no training or
broader scientific transition.
