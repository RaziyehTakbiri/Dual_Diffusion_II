# Project test-data prospective no-acquisition seal v1

## Registered state

The registered state is
`NO_TEST_DATA_ACQUIRED_USER_REPORTED_PROSPECTIVE_SEAL_ACTIVE`. This is a
prospective, procedural, noncryptographic user-report seal. It is not an
independently verified fact about any filesystem, cache, network, connector,
account, remote service, or physical storage medium.

The normalized visible user item 5 is preserved exactly, including the spelling
`de`:

> 5- What are the canonical test-data locations, or has test data not yet been acquired? No test has been acquired. For what purpose de we need it at all?

The answer portion is:

> No test has been acquired. For what purpose de we need it at all?

Only trailing transport whitespace or entity framing is unbound. Raw transport
bytes are not bound. The statement is user-reported, not cryptographically
authenticated, and not independently verified.

## Current scientific and custody boundary

This seal does not resolve the final test-secrecy field. `F172`, corresponding to
`/freeze_predicate/test_data_unopened_before_freeze`, remains `null`. The current
projection remains 166 unresolved pre-execution fields plus six deferred
post-execution fields, for 172 effective unresolved fields total, with 12 open
blockers. Global state remains `DRAFT_NOT_EXECUTABLE`.

Canonical test-data locations, object hashes, and byte counts are unknown and
are represented by empty rosters. This package performed no test-data scan,
acquisition, opening, network access, or connector contact. It makes no global
absence claim and no filesystem-, cache-, network-, account-, or
remote-service-absence claim. It does not attest any pre-existing local or
external state.

The following immutable governance inputs are byte-bound and reopened by the
validator:

| Role | Path | Bytes | SHA-256 |
|---|---|---:|---|
| execution preregistration | `research/fixtures/manuscript_v3_execution_preregistration_v1.json` | 39,771 | `edd572fc8d8c1b72ad3bc947c4427b79095d45b4d9f44371c5806066d71b0706` |
| pre-execution closure v2 | `research/fixtures/manuscript_v3_execution_preregistration_preexecution_closure_v2.json` | 24,571 | `11329efc97d844f5a39223f170e8c4d5ea5341756ed6f89d9e40bbf4e0c529db` |

The closure record self-digest remains
`a393df8432e8ffd1b01368879290e090474ce34ab5b67edb102e3400b6cecae4`.
Immediately before seal construction, the mutable completion tracker had SHA-256
`a7351bdad5d067856bacc673c128cd025e0fcd44870e7d33fdb7f8b2eca4e91c`
and 31,794 bytes; the mutable evidence ledger had SHA-256
`3a3ba08b8f4c0710e3d38f52132ac8df6ed537ba9a944110be51a859cfd02acb`
and 33,723 bytes. These are historical provenance receipts only. They are not
live custody requirements and the validator does not open either mutable file.
The trackers may consume the frozen seal one-way afterward without creating a
hash cycle or invalidating it. This additive seal changes neither immutable input
and closes zero fields and zero blockers.

## Prospective protected scope

For this seal, **test data** means scientific held-out PhysioNet or Retail
material and outcome-bearing derivatives from those held-out partitions. It does
not mean unit-test fixtures, synthetic hostile-test records, or files created
inside isolated pytest temporary directories. Those software-test materials
cannot establish or change the scientific test-data custody state.

The protected future scope comprises the held-out PhysioNet and Retail test
partitions and all outcome-bearing contents derived from them, including labels,
targets, event values, predictions, per-example losses, aggregate metrics,
diagnostics, and decision statistics. Development processes, development
workers, model-selection routes, and tuning routes may not receive those
partitions or outcomes before the final sealed freeze permits the separately
specified access.

Before any external source contact, authentication, download, acquisition, or
opening, a separate acquisition/snapshot/split/escrow protocol must be frozen,
content-addressed, reviewed, and specifically authorized. That later protocol
must bind the canonical source and version, applicable license and governance
approvals, acquisition identity and custody, snapshot hashes and byte counts, a
deterministic split algorithm and all split inputs, group/leakage constraints,
escrow identities and access controls, an append-only access-log schema, and
terminal violation handling.

After an authorized acquisition begins, the snapshot must be fixed and the
deterministic partition assignment completed under the frozen route before any
development exposure. The held-out partitions and outcome-bearing derivatives
must then enter escrow. Every contact, attempted access, granted access, denial,
and authorized final opening must receive a durable access-log entry. This seal
does not create that operational protocol, authorize contact, or authorize data
access.

Any protected-data contact before the separate protocol is frozen and authorized,
any held-out content or outcome exposure before the permitted final opening, or
any unlogged access attempt enters
`PROSPECTIVE_TEST_DATA_SEAL_VIOLATION_TERMINAL`. A violation cannot be repaired by
deleting evidence, redrawing a split, reacquiring data, or retrying the route. It
blocks evidence admission and claim promotion until a separately authorized
independent disposition defines an honest terminal outcome.

## Authority and trust boundary

This package authorizes no acquisition, source contact, authentication, network
or connector use, scan, test-data opening, deterministic split execution, escrow
operation, runtime approval, entropy draw, training, rank, production,
scientific execution, claim promotion, submission, or retry. It does not inspect
or import scientific project code.

## Publication and anonymity boundary

This exact seal package and its custody are internal evidence only:
`internal_evidence_only=true`. Inclusion in an anonymous submission or public
release is forbidden:
`anonymous_or_public_submission_inclusion_permitted=false`. A separately created
and reviewed publication-safe derivative is required:
`publication_safe_derivative_required=true`.

The raw normalized visible-user question and answer, the answer alone, exact
conversation provenance, internal source/package paths, raw and record hashes,
byte and line counts, and historical tracker provenance are excluded from every
public derivative. A derivative may state only a sanitized scientific custody
conclusion supported by a fresh anonymity audit; it may not reproduce or permit
reconstruction of the excluded raw provenance.

The validator reopens only the six exact governance/package files named by its
closed manifest and performs honest-host procedural checks. It is not a security
sandbox and does not resist an actor able to alter the validator, process memory,
Python runtime, or bound records in concert. Hostile tests write only synthetic
copies inside isolated pytest temporary directories; those copies are neither
canonical evidence nor operational data.
