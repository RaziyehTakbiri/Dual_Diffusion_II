# Accepted-validator trust-boundary audit — 2026-09-01

Status: `VALIDATOR_TRUST_SURFACES_AUDITED_BOUNDARIES_NARROWED`

## Scope and result

The overnight audit inspected all 33 Python validators referenced by the
evidence ledger before this audit. It reviewed source-execution order,
filesystem path custody, working-directory dependence, dynamic imports,
`sys.modules` restoration, and network, subprocess, entropy, clock, and write
surfaces. This was static and read-only except for disposable hostile-test
copies; it did not invoke any production executor or operational authority.

Nine validators dynamically execute project source. Eight verify the exact
buffer that is subsequently compiled before execution. The sole P1 exception
was the historical R1 V4→V3→V2 chain, whose V4 and V3 validators authenticated
a path and then reread that path for execution. That path is remediated by the
additive hash-first envelope documented in
`PROJECT_A1_R1_V4_TERMINAL_PASS_HASH_FIRST_REMEDIATION.md`. The inherited
validators remain byte-stable and are no longer supported as direct trust
entrypoints.

No validator in the audit imported or invoked a production network,
subprocess, RNG/entropy, clock, or filesystem-writer route during validation.
No default direct-script working-directory dependency or unsafe pathname-based
project import was found.

## Legacy filesystem-custody boundary

Twenty-six of the 33 pre-audit ledger-referenced validators use ordinary
pathname reads or partial `lstat`/open checks rather than a fully
component-anchored `openat`/`O_NOFOLLOW` chain with complete ancestor and
post-read identity verification. Their exact byte hashes still protect the
content they compare, and validators that compile a captured, prehashed buffer
do not execute a later pathname reread. They do not, however, establish a
malicious-concurrent-host or self-restoring-ancestor guarantee.

Accordingly, unless a package names a later hash-first wrapper as its sole
supported entrypoint, “read-only validator” and “hostile tests” mean exact-byte
semantic validation under a stable-parent, honest-host assumption. “Hostile”
describes malformed or adversarial input fixtures; it does not claim resistance
to a concurrently malicious filesystem or host administrator. The three
hash-first envelopes for Solo Block 2 V5, the two-macrostep parent chain, and
the historical R1 V4→V3→V2 chain have their stronger custody guarantees stated
separately and narrowly.

This support boundary is a documentation and invocation constraint. It does
not alter any accepted package byte, promote a legacy validator to a hostile-
host security control, or invalidate an immutable historical receipt.

## Explicit-`None` module-registry boundary

Four accepted legacy validators use `sys.modules.get(name)` and therefore
conflate an absent entry with a pre-existing entry whose value is explicitly
`None`:

- `research/diagnostics/manuscript_v3_cks_count_normalized_event_reference_implementation_v1.py`
- `research/diagnostics/manuscript_v3_formal_test29_finite_acyclic_route_qualification_v1.py`
- `research/diagnostics/manuscript_v3_formal_test30_synthetic_coupled_path_qualification_v1.py`
- `research/diagnostics/manuscript_v3_formal_test29_test30_single_macrostep_integration_v1.py`

Their normal isolated-process path restores an absent slot and their existing
accepted outputs are unchanged. Direct embedding in a long-lived interpreter
with an explicit-`None` value already installed at the validator's synthetic
module name is unsupported because cleanup would remove that sentinel. A
future successor must use a distinct missing-object sentinel and prove exact
restoration of absent, explicit-`None`, and arbitrary-object entries on both
success and exception. The new hash-first wrappers already use that stronger
sentinel pattern.

This is a process-local hygiene limitation, not a filesystem, network,
operational, scientific, or result-integrity finding for the accepted isolated
runs. The four frozen validator files are not edited here.

## Current R1 custody state

The new R1 hash-first envelope proves the three validator pins and loader
substitution before execution, but the inherited V3 custody predicate currently
finds four focused bytecode-cache paths. Those paths are preserved. Therefore
the supported envelope reports
`HASH_FIRST_CHAIN_INTEGRITY_PASS_CURRENT_CUSTODY_HOLD`, not a fresh V4 PASS.
The historical terminal-PASS record remains an immutable historical receipt;
present-tense exact custody and historical revalidation are not claimed.

## Project-state effect

This audit and its support-boundary clarification close no timetable checkbox,
field, blocker, Formal Test, result, authority, operational task, runtime,
scientific state, or claim. All accepted historical files remain byte-stable.
The ledger may cite this audit to make the supported trust boundaries
discoverable; that citation is evidence maintenance only.
