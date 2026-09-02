# A1 R1 replacement-seed draw: post-draw registration v1

Status: **R1_A1_SEED_REGISTRY_FROZEN_NOT_EXECUTABLE**  
Global state: **DRAFT_NOT_EXECUTABLE**  
Registration mode: **additive post-draw custody record; no rerun and no scientific execution**

## 1. What this milestone records

The preregistered one-shot replacement-seed draw completed successfully. The
accepted replacement is **4052249444591756**, with accepted allowed-set rank
**4052249444591748**. It replaces exposed ordinal zero only. The resulting
ordered registry is:

```text
[4052249444591756, 3253, 5003, 7411, 10007, 13007, 16001, 20011]
```

This registration records custody and the deterministic mapping result. It did
not rerun the draw, contact entropy, execute rank code, train a model, run an
experiment, integrate the registry into a runner, or promote a scientific
claim. The one attempt is spent and no retry, redraw, top-up, candidate
screening, or outcome-based seed substitution is permitted.

The only current transition is:

```text
R1_A1_SEED_DRAW_AUTHORIZED_NOT_YET_CONSUMED
    -> R1_A1_SEED_REGISTRY_FROZEN_NOT_EXECUTABLE
```

It is not a transition to R1 execution, qualification, claim support, or
submission readiness.

## 2. Exact frozen mapping

The draw used the preregistered exact mapping:

- safe integer universe `U = 9007199254740992` (`2^53`);
- excluded original registry
  `E = [1729, 3253, 5003, 7411, 10007, 13007, 16001, 20011]`;
- allowed count `M = 9007199254740984` (`U - 8`);
- 256-bit entropy space `2^256 =
  115792089237316195423570985008687907853269984665640564039457584007913129639936`;
- acceptance limit `L = 2^256 - 64 =
  115792089237316195423570985008687907853269984665640564039457584007913129639872`;
- acceptance predicate `X < L`;
- accepted rank `X mod M = 4052249444591748`; and
- ascending-exclusion unranking result `4052249444591756`.

The exact entropy integer and raw 32-byte entropy hex are deliberately not
copied into this note or the machine registration. They remain only in the
owner-only raw draw record. For custody comparison, the SHA-256 fingerprint of
the exact entropy bytes is
`e0d75d1d1dc42748910d56d031205a431e2d619491b69eea2ae0ce4c9eaf2982`.
That fingerprint was computed after the draw and was not an entropy source,
selection input, metric, threshold, or candidate-screening signal.

Independent verification reopens the raw internal draw record, checks `X < L`,
recomputes `X mod M`, independently un-ranks the allowed set, and checks the
registered seed. It never prints or duplicates the raw entropy.

## 3. Exact custody chain

The successful chain is frozen by both raw-file SHA-256 and record self-digest:

| Record | Raw SHA-256 | Record self-digest | Mode |
|---|---|---|---|
| Attempt marker | `fa9047433d62620d145fda0a9f56aabf4296003356d9c3b4336b455d1e4de76b` | `ec5984402ee5f9dbde658713bfa43d4026e32851b8a7dff53ef703a7ac1d47d5` | `0600` |
| Seed-draw record | `63cff401182cf6502cd51d9d732eaccb0bec4c63ddbb4ff308b0d968a56dbd0f` | `51702215c41e7832e12685cde8e8a1674c106956afb872d2e428a181be6c912b` | `0600` |
| Replacement registry | `d2854c9b1bbc7fb668d5741c3544b4b47adef340bcf58e74db33ba461f9b378b` | `2be16cc37b6e046c95538679b05e334b0f299e08eed5c1ac67be1a5077f18f05` | `0600` |
| Success receipt | `89705733ba5c26967981223fd760198be9844f5c38c7e793821bdda82aa37056` | `d4f36bdf4a6fd6c1a363b80a98f25efbda5ec5faddcd04fe1dc330be4b67df65` | `0600` |

The attempt marker is a nonsymlink regular file. The terminal directory is a
nonsymlink `0700` directory containing exactly three nonsymlink `0600` regular
files: `seed-draw-record.json`, `replacement-seed-registry.json`, and
`success-receipt.json`. The pending directory and failure receipt are absent.
All absence gates use `lstat` no-entry semantics: a broken symlink counts as a
present and invalid entry, never as absence.
The status auditor reopens the chain as `ATTEMPT_SPENT_TERMINAL_SUCCESS`.

The pre-draw human freeze, machine freeze, draw module, and hostile test remain
byte-for-byte unchanged at their final approved hashes. The machine
registration also projects and reopens every one of the pre-draw sidecar's 24
closed-world predecessor rows. All seven historical seed/source modules remain
unchanged and custody-only.

## 4. Registry and downstream projection

Seed `1729` remains development-exposed across every method, lane, and budget,
with a budget wildcard where a budget is not applicable. It is never restored
to confirmatory use. The replacement occupies ordinal zero everywhere; the
remaining seven ordinals are preserved exactly. Numeric re-sorting, partial
lane substitution, post-draw grid pruning, and using different replacements in
different lanes are forbidden.

The frozen registry deterministically projects to:

- 24 exact-population coordinates (`3 x 8`);
- 48 primary sampled coordinates (`2 x 3 x 8`);
- 72 sampled control coordinates (`3 x 3 x 8`);
- 120 complete sampled coordinates; and
- 144 coordinates when the exact-population coordinates are included.

These are registered future-grid counts, not executed coordinates or results.

## 5. State preservation and nonclaims

This registration changes no claim row, theorem, preregistration, CP76 snapshot,
D1 artifact, historical implementation, production order, or prior freeze. All
11 checked production roots remain absent, as do the formal runtime-identity
manifest and the draw's pending directory. There is no readiness transition.

In particular, this milestone does **not** assert or authorize any of the
following:

- retry, redraw, top-up, seed screening, or candidate replacement;
- a second entropy contact;
- registry integration, source amendment, runner integration, or a runtime
  capsule;
- rank, training, confirmatory, or production execution;
- checkpoint, metric, threshold, success-rule, or overflow-policy selection;
- a scientific result, R1 or R2 qualification, C17 proof, claim promotion, or
  submission readiness.

D1 remains prior observed development knowledge and is not production evidence.
The new seed was generated outcome-independently; neither D1 bytes, metrics,
hashes, timestamps, runtime/process metadata, nor the user's decision text or
hash entered the mapping.

## 6. Required next gate

Before any R1 runner or production execution, a separate additive and versioned
registry-integration/source-amendment preregistration is required. It must:

1. preserve the seven historical source files byte-for-byte;
2. introduce a new registry-aware adapter or successor source rather than edit
   a historical file in place;
3. bind the successful registry and enforce ordinal-zero substitution across
   every method, lane, and budget;
4. bind a formal runtime-identity manifest and a closed execution capsule;
5. freeze the exact launch plan, phase-consumption and result-receipt contracts;
   and
6. pass a fresh zero-execution hostile audit before any rank, training, or
   production process can start.

This post-draw registration does not create that adapter or capsule and does not
authorize that next milestone's execution.

## 7. Publication and trust boundary

This human note, its machine sidecar, its hostile test, the attempt marker, and
the entire raw terminal directory are internal custody artifacts, not anonymous
submission artifacts. The raw draw record contains the entropy hex. None of
these raw files may be included in an anonymous submission or public release.
In-place sanitization is forbidden. Any future public use requires a separate
publication-safe derivative, a frozen include/exclude roster, and a fresh
anonymity audit; the derivative path is currently null.

The custody checks are a procedural honest-host/workspace boundary, not a
security sandbox against an actor controlling same-user process memory, module
globals, or registered files. No such hostile-process tamper-resistance claim is
made.

## 8. Machine authority

The canonical machine registration is
`research/fixtures/manuscript_v3_a1_r1_replacement_seed_draw_postdraw_registration_v1.json`.
It is the authoritative closed-world record. It self-digests under the domain
`heterodiff-manuscript-v3-a1-r1-replacement-seed-draw-postdraw-registration-v1`
and binds the final bytes of this human note and the hostile test without a
digest cycle.
