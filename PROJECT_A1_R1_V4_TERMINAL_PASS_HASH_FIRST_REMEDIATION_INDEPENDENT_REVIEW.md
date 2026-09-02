# Independent review — A1 R1 V4 terminal-PASS hash-first remediation

Decision: `GO_HASH_FIRST_CHAIN_REMEDIATION_CURRENT_CUSTODY_HOLD`

Finding counts: `P0=0`, `P1=0`, `P2=0` within the registered remediation
scope. The present custody `HOLD` is an intentional inherited-gate result, not
an unresolved review finding.

## Reviewed immutable candidate

| Role | Bytes | SHA-256 |
|---|---:|---|
| Human remediation record | 4,346 | `b3c17dab8b9c2140c901386fdfa817f1f47aa7528c73ffc7ff42879e351be6ae` |
| Hash-first wrapper | 16,612 | `70662c1b2c567bc8802c79f48b73b2804f2f02c5c5d2ea3f504de36776cf1d74` |
| Hostile tests | 10,058 | `04b711bc635d05a4e7f86b2c0354bc1a513b417a5580ebcbd455884a9e523f03` |
| General validator trust-boundary audit | 4,971 | `23bea75dd9fd3cbfe4a44fb896ef7a5c583178583540d6dc1fd5f4efdd024023` |

All four files were independently reopened as regular mode-`0644`, link-count
one, LF-terminated files without CR bytes. Candidate bytes remained unchanged
through both reviews.

## Independent security recomputation

Two read-only reviewers independently confirmed that the wrapper:

1. component-opens and captures all three validators before the first compile;
2. requires regular mode-`0644`, link-count-one custody and exact sizes/hashes;
3. compiles only the captured V4, V3, and V2 buffers into exact `ModuleType`
   objects under non-`__main__` names;
4. replaces V3's V2 pathname loader and V4's V3 pathname loader before any
   public V4 validation call, binding both to the captured root;
5. restores absent, explicit-`None`, and arbitrary-object `sys.modules` entries
   on successful and exceptional compilation; and
6. recaptures and compares all validator identities after validation.

The inherited validator pins independently match:

- V4: 69,164 bytes,
  `573ac885e449a0203d4c0b78dfa833fb4269c1fc94aeb2289c9dd8e507460fb0`;
- V3: 44,262 bytes,
  `2ae995d7609778f9201e3a90a2861c74898dfdc357b3f0b6f75b46bc68ce78bd`;
- V2: 62,047 bytes,
  `ce59c0d855d22eea01e0091110ab6e928d071fe57ba1416f6e0ccab0e5bcf671`.

The accepted historical validators were not edited. Direct inherited V4/V3
use remains unsupported as a revalidation trust entrypoint.

## Current canonical outcome

The canonical workspace run returns JSON status `HOLD`, state
`HASH_FIRST_CHAIN_INTEGRITY_PASS_CURRENT_CUSTODY_HOLD`, and process exit code
`2`. It reports `current_v3_custody_pass=false`,
`historical_registration_revalidated=false`, and null historical-PASS/current-
custody payloads. Its exact four-path focused-cache roster has digest
`e2266e13638e78a326bd74c0e1376b47f1699c6bef892024959d6f3ce322dbdc`.

Reviewers verified that the four existing cache paths were neither removed nor
bypassed. The historical registration digest
`9d69a41faa8f4a52c21c81ef9009d0eff0315e5d7e7d5ae3ff39cc135e4451bb`
continues to identify an immutable earlier receipt; it is not represented as a
fresh present-tense custody PASS.

## Tests and broader boundary

The final focused hostile suite passes `15/15` with bytecode and pytest caches
disabled. The final accepted overnight union plus this suite passes
`1,095/1,095`. Coverage includes each pre-capture source substitution,
post-capture substitution, forged captured mappings, modes, hard links, leaf
and ancestor symlinks, root mismatch, loader replacement, fail-closed HOLD
exit, exact pins, and module-registry restoration.

The separate trust-boundary audit accurately narrows 26 legacy validators to
stable-parent/honest-host filesystem semantics and identifies four frozen
loaders as unsupported for direct long-lived embedding with a pre-existing
explicit-`None` module entry. Those limitations are disclosed rather than
silently claimed fixed; the new wrapper itself meets the stronger behavior.

## Effect boundary

The wrapper has no writer, process, network, entropy, clock, data,
runtime-approval, operational-receipt, or scientific route. Review and tests
changed no accepted predecessor, historical receipt, timetable checkbox,
field, blocker, Formal Test, result, authority, attempt, runtime, scientific
state, or claim. Registration is evidence maintenance under the already
started hostile integration/runtime-custody review workstream only.
