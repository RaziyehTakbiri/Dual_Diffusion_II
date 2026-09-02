# A1 R1 V4 terminal-PASS hash-first validation remediation

Status: `HASH_FIRST_CHAIN_INTEGRITY_PASS_CURRENT_CUSTODY_HOLD`

## Finding and disposition

The accepted historical V4 terminal-PASS receipt and its V3/V2 predecessors
remain byte-for-byte unchanged. During the 2026-09-01 overnight trust audit, a
new validation-entrypoint defect was found: the V4 validator authenticated the
V3 pathname, then separately reread and executed V3; V3 repeated that pattern
for V2. A same-path substitution between those reads could therefore execute
bytes that were not the bytes whose hash passed. Current validator bytes were
exact and no hostile substitution or unauthorized action occurred.

The additive read-only envelope
`research/diagnostics/finite_association_r1_v4_terminal_pass_hash_first_v1.py`
is now the sole supported revalidation entrypoint for this V4→V3→V2 chain.
Direct use of the three inherited validators as a trust entrypoint is
unsupported. No historical file is altered or re-signed.

## Exact pre-execution pins

Before the first compile, the envelope component-opens all three validators
without following symlinks, requires regular mode-`0644` single-link custody,
captures their complete bytes and file identities, and verifies:

| Role | Bytes | SHA-256 |
|---|---:|---|
| V4 terminal-PASS validator | 69,164 | `573ac885e449a0203d4c0b78dfa833fb4269c1fc94aeb2289c9dd8e507460fb0` |
| V3 terminal-failure validator | 44,262 | `2ae995d7609778f9201e3a90a2861c74898dfdc357b3f0b6f75b46bc68ce78bd` |
| V2 terminal-failure validator | 62,047 | `ce59c0d855d22eea01e0091110ab6e928d071fe57ba1416f6e0ccab0e5bcf671` |

Only captured buffers are compiled into exact `ModuleType` objects under
non-`__main__` names. The envelope replaces V3's inherited V2 pathname loader
with the captured V2 module and V4's inherited V3 pathname loader with the
captured, already-patched V3 module. Requested roots are bound to the captured
root, all temporary `sys.modules` slots are restored on success and exception,
and all three validator identities must be unchanged after validation.

## Current custody HOLD is preserved

Hash-first chain integrity passes, but the inherited V3 custody policy
correctly refuses the present workspace because four focused bytecode-cache
files now exist:

- `research/production/__pycache__/finite_association_r1_activation_preparation_rehearsal_authority_v3.cpython-39.pyc`
- `research/production/__pycache__/finite_association_r1_activation_preparation_rehearsal_contracts_v3.cpython-39.pyc`
- `research/production/__pycache__/finite_association_r1_activation_preparation_rehearsal_runtime_v3.cpython-39.pyc`
- `tests/unit/__pycache__/test_manuscript_v3_a1_r1_activation_preparation_v3_live_host_environment_rehearsal_freeze_v1.cpython-39-pytest-7.1.2.pyc`

The ordered hold-roster digest is
`e2266e13638e78a326bd74c0e1376b47f1699c6bef892024959d6f3ce322dbdc`.
Those existing files were not deleted, moved, ignored, or whitelisted. The
wrapper therefore reports `HOLD`, `current_v3_custody_pass=false`, and
`historical_registration_revalidated=false`; it does not synthesize a current
PASS. Its command-line entrypoint exits nonzero on HOLD so a caller cannot
mistake the structured hold record for a successful validation gate.
Historical registration record
`9d69a41faa8f4a52c21c81ef9009d0eff0315e5d7e7d5ae3ff39cc135e4451bb`
continues to identify the immutable prior record, not a fresh custody result.

## Boundary and qualification

The envelope has no writer, subprocess, resolver, socket, entropy, data,
runtime-approval, or scientific route. It creates no operational receipt,
changes no attempt state, and edits no tracker during validation. The focused
15-test hostile suite covers all three pre-capture substitutions, post-capture
path substitution, forged captured mappings, unsafe modes, hard links, leaf
and ancestor symlinks, root-bound loader replacement, fail-closed HOLD exit
status, exact pin inventory, and `sys.modules` restoration—including explicit
`None` entries—on successful and exceptional compile paths. Tests run with
bytecode and pytest caches disabled.

This remediation changes no timetable checkbox, field, blocker, Formal Test,
result, authority, runtime, scientific state, or claim. It secures the
revalidation entrypoint while preserving the current custody HOLD honestly.
