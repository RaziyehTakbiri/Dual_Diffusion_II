# Formal Tests 29–30 two-macrostep parent-custody remediation

Status: `FINAL_ADDITIVE_HASH_FIRST_PARENT_SOURCE_CUSTODY_ENVELOPE`

## Finding and disposition

The accepted two-macrostep development precursor remains byte-for-byte
unchanged. Its public API deliberately accepts caller-supplied module objects
and checks their exact type, schemas, and required symbols, but it cannot
authenticate a coherently rebound parent implementation. The original
independent review therefore retained P2-01 and correctly reported
`parent_custody_authenticated=False`.

This additive remediation establishes
`research/diagnostics/formal_test29_test30_two_macrostep_parent_custody_hash_first_v1.py`
as the sole supported reusable qualification entrypoint. It authenticates the
candidate and all three parent source files before importing or executing any
project source. The original candidate result remains truthful and unchanged:
its internal `parent_custody_authenticated` field stays false because the
candidate API itself remains generic. The surrounding envelope separately
records that its exact parent-source custody gate passed.

## Exact source pins

| Role | Bytes | SHA-256 |
|---|---:|---|
| Two-macrostep candidate | 59,285 | `d1c3013aa0f4e7b31e19cef98d4aa5edf7991c5b8634dbfe091f8053b1808176` |
| Single-macrostep parent | 61,434 | `e2f57ede06cb432f8507eb32eead7a77fbfc8d8d44cc7725a941182e7aedd0c7` |
| Test-29 parent | 52,186 | `308a16090128871c9a79cdaff265d3b6633e18b062a605b257f3173198d8a089` |
| Test-30 parent | 42,349 | `373ef98c3605e0c0211da8dbc8782f2517cd5976026980e4fcd24435670839e0` |

Before the first compile, the envelope component-opens and captures all four
sources without following symlinks, requires regular mode-`0644` single-link
custody, and verifies exact length and SHA-256. It rechecks the complete
captured roster, exact captured object type, path, length, raw digest, mode,
and link count immediately before compilation. Only captured buffers are
compiled into exact `ModuleType` objects under non-`__main__` names.

After the exact 1,024-case qualification, the envelope reopens every source and
requires unchanged device, inode, UID, GID, mode, link count, size, raw digest,
modification time, and change time. Initial drift, post-capture substitution,
forged captured mappings, self-restoring schema-compatible payloads, unsafe
modes, and hard links therefore fail closed without executing hostile bytes.

## Preserved qualification and boundary

The envelope requires the accepted predicate
`SYNTHETIC_SUPPLIED_INPUT_TWO_MACROSTEP_ROLLING_LINEAGE_PATH_VALIDATED`, all
1,024 ordered low-word pairs and distinct input/report digests, and aggregate
report SHA-256
`2a278585373d017b3b60bed28dcbc0ab3830f72c0512891658fc2ab54c666d53`.

This is source-custody hardening for the already bounded, supplied-input
development predicate only. It adds no entropy, clock, filesystem output,
network, process, data, protected input, runtime receipt, or scientific
execution. It closes no field, blocker, Formal Test, result, or timetable
task, and does not establish a production path, live CP23/CP24 source,
continuous Gaussian law, arbitrary-length Strang integration, or step-halving
result.
