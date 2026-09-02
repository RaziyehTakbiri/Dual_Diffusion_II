# Solo Block 2 V5 hash-first validation remediation

Status: `FINAL_ADDITIVE_HASH_FIRST_VALIDATION_ENVELOPE_NETWORK_AND_OPERATIONAL_HOLD`

## Finding and disposition

The accepted V5 package remains byte-for-byte unchanged and remains an offline,
operationally unauthorized construction. A later overnight integrity audit
identified one unsafe trust-entrypoint property in its validator chain: the V5
validator evaluated the V4 validator before checking V4's raw hash, and the V4
validator likewise evaluated V3 before checking V3's raw hash. Current V3, V4,
and V5 bytes were exact and safe, the V4 custody root remained empty, and no
unauthorized action occurred. Nevertheless, direct use of the inherited V5 or
V4 validators is now on validation hold.

This additive remediation establishes
`research/diagnostics/manuscript_v3_solo_block2_runtime_custody_closure_v5_hash_first.py`
as the sole supported validation entrypoint for the accepted V5 chain. It does
not alter or re-sign any accepted V1--V5 package byte.

## Hash-first contract

Before compiling any validator, the envelope opens all three validators without
following symlinks, requires regular mode-`0644` single-link custody, captures
their complete identity metadata, and verifies the following exact byte pins:

| Validator | Bytes | SHA-256 |
|---|---:|---|
| V5 | 23,872 | `4699e3073ec19b3f82320b70f29d4b9a63169622a9ed042a30262c3fe7d01c96` |
| V4 | 20,334 | `bc32e4775a6ea1ac557bafc66a27411f5cddfeb79e4daa0bd4dfc09e89af7a44` |
| V3 | 36,357 | `53fb7a3afb8f0cf798e9d0cd0970fe370f5e2c0a7ed72bef0ce5c9f414de1153` |

Only the captured bytes are compiled, always under non-`__main__` names. The
envelope replaces V4's inherited V3 disk loader with the already captured V3
namespace, replaces V5's inherited V4 disk loader with the already captured V4
namespace, runs the exact V5 validation, and then reopens all three files and
requires their complete identities to be unchanged. A changed V3, V4, or V5
validator is refused before any validator byte is compiled. Path substitution
after capture cannot change the bytes compiled by the envelope.

## Operational boundary

The V5 executor intentionally contains future receipt, resolver, socket, TLS,
and request surfaces. They are procedural activation surfaces guarded by exact
direct-script, interpreter, environment, fixed-root, package, authority,
budget, chronology, and custody conditions; Python naming is not a security
boundary. This remediation does not invoke or authorize any of those surfaces.

The envelope imports no production executor and performs no registrar,
preflight, attempt, resolver, socket, TLS, HTTP, contact, data, or scientific
operation. It creates no operational receipt and activates no budget. The V4
root remains exact and empty. The original seven Solo Block 2 operational tasks,
all scientific fields, and all result counters remain unchanged.

## Qualification

Qualification is offline, bytecode-cache-disabled, and pytest-cache-disabled.
Hostile temporary-copy tests replace each of V3, V4, and V5 with top-level
marker-writing payloads and require rejection with every marker absent. A
post-capture substitution test proves that only captured bytes are compiled.
Mode and hard-link mutations are refused. The wrapper must pass from both the
project root and an unrelated working directory without changing the live V4
root.
