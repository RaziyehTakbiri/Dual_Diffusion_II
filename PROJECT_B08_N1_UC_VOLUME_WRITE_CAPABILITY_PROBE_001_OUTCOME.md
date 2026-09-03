# B08 N1 Unity Catalog Volume write-capability probe-001 outcome

**Recorded disposition:**
`PASS_UC_VOLUME_EXCLUSIVE_CREATE_AND_REPEATABLE_READBACK_CAPABILITY`

**Probe identifier:** `b08-n1-uc-volume-write-capability-probe-001`

**Attempt disposition:** spent; both retained leaves must be preserved

**Eligible project delta:** zero

## 1. Scope and provenance

This record is a semantic transcription of the operator-supplied JSON from the
one authorized, data-free probe of the exact Unity Catalog Volume parent

`/Volumes/development/team_eds_supplychain/b08_runtime_output`.

The supplied output does not include a raw-output byte artifact or its SHA-256,
an externally authenticated operator identity, an externally attested execution
time, or cryptographic proof of the Git revision and notebook bytes executed in
Databricks. The following local bindings identify the independently reviewed
materials in the repository; they are context, not remote-run attestation.

| Local repository object | Bytes | SHA-256 |
|---|---:|---|
| `databricks/notebooks/b08_n1_uc_volume_write_capability_probe.py` | 35,681 | `849fdad4c73d3123e584b5020184dfac25acbd66860576726fbd73ca4aa15ded` |
| `tests/unit/test_b08_n1_uc_volume_write_capability_probe.py` | 26,657 | `9177f20e77d8d42b519d203561853e40b6ebfcb8e03546abac680c0042b76c1e` |
| `PROJECT_B08_N1_UC_VOLUME_WRITE_CAPABILITY_PROBE_INDEPENDENT_REVIEW.md` | 5,735 | `7612dbe3c4072c0ab2847bb17d99d6a5aa66ccfff80734f0d961baec57229a59` |

The clean local repository context at transcription was commit
`e70f46ceedbbc7b6b702ee8bd9d90b80b53674aa`; this is contextual only.

## 2. Exact supplied observations

The attempt used exactly four exclusive-create calls against two fixed leaves.
Exactly two creates succeeded, and 8,192 payload bytes were confirmed complete.
The declared maximum possible payload under a broken race was 12,288 bytes.

### Primary create and collision

The retained primary leaf is

`/Volumes/development/team_eds_supplychain/b08_runtime_output/b08-n1-uc-volume-write-capability-probe-001-primary.bin`.

Its exact size is 4,096 bytes and its SHA-256 is
`26b7e40be0bcf3e6667020b3acf6e07faa17585b21b2936305dd6c9ad3860b15`.
The intentional second exclusive create returned `FILE_EXISTS_ERROR`. Fresh
readback before and after that collision produced the same size and digest, so
the collision did not overwrite the primary payload.

### Synchronized two-process race

The retained race leaf is

`/Volumes/development/team_eds_supplychain/b08_runtime_output/b08-n1-uc-volume-write-capability-probe-001-race.bin`.

`RACE_A` created the leaf with 4,096 bytes and SHA-256
`6896d9ea3f73a4434f5832bc65714e7d066f177373f36f34dc8a6f735daa41b1`.
`RACE_B` returned `COLLISION` without creating or writing. Two fresh readbacks
of the winning leaf independently returned the same name, size, and digest.

Both child processes exited with return code zero. Both were confirmed
quiescent, no termination was requested, and no cluster-termination-before-
forensics condition was raised.

## 3. Narrow capability established

For this exact selected runtime and Unity Catalog Volume parent, the supplied
result establishes the observed conjunction of:

- exclusive creation of a previously absent leaf;
- non-overwriting same-path collision behavior;
- exactly one successful creator in the synchronized two-process race; and
- repeated exact size-and-SHA-256 readback through fresh opens.

This empirical result clears only the bounded UC Volume storage-behavior
prerequisite for engineering a replacement writer. It does not clear the old
POSIX-oriented builder or authorize a candidate construction.

## 4. Preservation and nonclaims

Probe-001 and both exact leaves are permanently spent. Do not rerun, delete,
rename, repair, replace, or reuse either path.

The supplied result explicitly does not prove atomic snapshots, cache
coherence, future runtime or FUSE stability, historical object identity or
lineage, immutability, or universal atomicity. It also supplies no `fsync` or
physical-durability proof, capacity reservation, dependency lock, overlay,
manifest, production-runtime capture, successful construction, scientific
execution authority, or scientific result.

No calibration, training, or inference ran; no package resolution, build, or
installation ran; no Spark or Databricks REST call, direct external network
endpoint, or study/test-data path was accessed. Managed Unity Catalog storage
I/O was the exact capability under test.

## 5. Exact project state and next boundary

This successful capability probe closes no timetable checkbox or scientific
predicate. The marked-task view remains `62 complete / 101 open / 163 total`;
fields remain `24 open / 148 closed`; blockers remain `7 open / 5 closed`;
Formal Tests remain `OPEN / OPEN / PENDING`. F151, F152, B08, and Wave 2 remain
open. Candidate-002 remains a terminal no-go, and candidate-003 is not
authorized.

The next eligible work is local implementation, testing, and independent review
of a UC Volume-native successor writer. No further Databricks execution is
authorized by this outcome.
