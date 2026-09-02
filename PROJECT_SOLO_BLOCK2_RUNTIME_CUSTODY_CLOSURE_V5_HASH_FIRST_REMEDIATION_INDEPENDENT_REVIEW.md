# Solo Block 2 V5 hash-first remediation: independent review receipt

**Review date:** 2026-09-01  
**Reviewer lane:** `/root/overnight_integrity_audit`  
**Reviewer role:** independent read-only hostile security review, separate from
the remediation author  
**Verdict:** `GO_HASH_FIRST_VALIDATION_REMEDIATION_ONLY`  
**P0/P1/P2 findings in remediation scope:** `0/0/0`

## 1. Scope and amendment effect

This receipt accepts only the additive, offline, hash-first validation envelope
for the already accepted Solo Block 2 V5 package. It is external to the
envelope and its validator pins. It mutates no accepted V1--V5 byte and grants
no package lock, authority, preflight, independent operational GO, row
authority, attempt, contact, network, data, runtime, or scientific permission.

The earlier V5 independent receipt remains evidence for the exact stopped V5
package and its observed zero-effect state. This receipt narrows and supersedes
only that receipt's implication that direct execution of the inherited V5/V4
validator chain is a safe hostile-custody trust entrypoint. Direct execution of
those inherited validators remains unsupported. The additive hash-first
envelope is now the sole supported validation entrypoint for the accepted V5
chain.

## 2. Exact remediation artifacts

All three files were exact regular files with mode `0644`, link count `1`, one
terminal LF, and no CR bytes.

| Path | Bytes | SHA-256 |
|---|---:|---|
| `PROJECT_SOLO_BLOCK2_RUNTIME_CUSTODY_CLOSURE_V5_HASH_FIRST_REMEDIATION.md` | 3,381 | `5bf023209a2cced2564836fc88708e9153164daf2fff19df3728abab93b8eae1` |
| `research/diagnostics/manuscript_v3_solo_block2_runtime_custody_closure_v5_hash_first.py` | 10,845 | `47ea305da1efdc18a03b216a51744a969ef3abe9fdc10a4f4a9df5b0f492520c` |
| `tests/unit/test_manuscript_v3_solo_block2_runtime_custody_closure_v5_hash_first.py` | 6,120 | `fe3a7b3bfa284865c9442fadbfebbc581260209819596dc45df61ffe2519a1fd` |

The envelope independently bound these exact inherited validators before any
compile operation:

| Validator | Bytes | SHA-256 |
|---|---:|---|
| V5 | 23,872 | `4699e3073ec19b3f82320b70f29d4b9a63169622a9ed042a30262c3fe7d01c96` |
| V4 | 20,334 | `bc32e4775a6ea1ac557bafc66a27411f5cddfeb79e4daa0bd4dfc09e89af7a44` |
| V3 | 36,357 | `53fb7a3afb8f0cf798e9d0cd0970fe370f5e2c0a7ed72bef0ce5c9f414de1153` |

## 3. Security review

The reviewer confirmed that all three validator sources are opened without
following symlinks and verified for exact byte length, SHA-256, regular-file
type, mode `0644`, and single-link custody before any source is compiled.
`_compile_chain` independently rechecks the exact captured type, roster, raw
length, raw digest, mode, and link count. Only captured buffers are compiled,
always under non-`__main__` names. The V4-to-V3 and V5-to-V4 disk loaders are
then replaced with the already captured namespaces.

After exact V5 validation, all three validators are reopened and their device,
inode, UID, GID, mode, link count, size, raw digest, modification time, and
change time must match the pre-execution capture. Therefore a hostile path
replacement cannot change the bytes executed and cannot survive the final
identity gate.

The hostile suite covered all three pre-compile drift positions, post-capture
path substitution, a forged captured mapping, a marker-writing payload that
would falsely return `PASS` and restore canonical path bytes, unsafe mode, and
unsafe hard-link custody. Every hostile payload was rejected and every marker
remained absent.

## 4. Qualification results

With bytecode generation disabled and the pytest cache provider disabled:

- the focused remediation suite passed `10/10`;
- the wrapper returned `PASS` from the project root;
- the wrapper returned `PASS` from `/private/tmp` as an unrelated working
  directory;
- three validators were compiled from captured, preverified bytes only;
- two inherited disk loaders were replaced; and
- network actions, operational receipts, and activated budget were all `0`.

The reviewer found no production-executor import or invocation and no network,
contact, subprocess, entropy, clock, science, runtime-custody write, receipt,
or budget effect. Test mutations were confined to disposable temporary paths.

The live V4 root remained exact and empty at device `16777234`, inode
`67067435`, UID `501`, GID `20`, mode `0700`, link count `2`, roster `[]`.

## 5. Registration boundary

This review closes the V5 hash-before-execution remediation only. It changes no
field, blocker, Formal Test, result, scientific count, operational count, or
original Solo Block 2 task. All seven original Solo Block 2 operational tasks
remain open, and V5 remains on network and activation hold pending a fresh,
separately reviewed authority chain.

The unrelated, already disclosed two-macrostep parent-source authentication
limitation remains P2 and outside this remediation's bounded verdict.
