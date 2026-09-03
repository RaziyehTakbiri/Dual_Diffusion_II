# B08 N1 UC-native candidate-003 V1 Databricks preflight HOLD

**Reported:** 2026-09-03  
**Observed notebook decision:** `HOLD_PREFLIGHT_INPUTS_OR_AUTHORITY_INCOMPLETE`  
**Candidate state:** absent and unspent  
**Construction authorized or executed:** no  
**Field, blocker, Formal-Test, result, or timetable delta:** zero

## 1. Evidence boundary

This record is a semantic transcription of the complete operator-supplied
default-off Databricks preflight JSON. The chat transport did not provide a
separately downloadable raw-output object, so this record does not claim a raw
output byte hash, externally authenticated operator identity, or externally
attested execution time.

The run exercised the exact V1 builder through its hash-first launcher. It was a
preflight, not a construction attempt. It performed the bounded Unity Catalog
namespace visibility checks needed by preflight, but it wrote no object, made no
direct external network contact, performed no package resolution, build, or
installation, and did not consume candidate-003.

## 2. V1 bytes and observed Databricks materialization

The builder executed by the launcher was exactly the independently reviewed V1
builder:

| Object | Bytes | SHA-256 | Mode |
|---|---:|---|---|
| Reviewed and executed V1 builder | 268,155 | `0c787b14f44cb6b6adedbefb5a6793f2dce270130184a885e816e69f16681d08` | runtime presentation not used for this comparison |
| Locally reviewed V1 launcher | 9,041 | `b974380f2af950a77571eaf0d34317d2858c170458cc6d791cf0794f64366616` | `0644` |
| Databricks-materialized V1 launcher | 9,040 | `8986a7d7b3065f6b82fa6b47d839af4a79b690a2f04d1f81baa9b7fa3e40cd94` | `0755` |

Offline comparison established that the 9,040-byte Databricks launcher payload
is the reviewed 9,041-byte launcher with exactly its single terminal LF omitted.
No other launcher-byte difference is accepted by this record. The observed
mode and terminal-LF transformation are Databricks source-notebook presentation
facts, not evidence that arbitrary source drift is harmless.

The launcher verified and executed the exact 268,155-byte builder from the same
in-memory payload. The hash-first boundary therefore passed; the HOLD occurred
later.

## 3. Exact preflight failure

The supplied output reported:

- `decision = HOLD_PREFLIGHT_INPUTS_OR_AUTHORITY_INCOMPLETE`;
- `errors = ["BOUND_SOURCE_GIT_PREFLIGHT_FAILED"]`;
- `source_git_preflight.error_code = TOOL_STEP_FAILED`;
- `source_git_preflight.error_detail =
  git_local_config_safety:returncode=128`; and
- command standard error exactly
  `fatal: --local can only be used inside a git repository\n`.

The failure occurred when V1 invoked `git config --local` as the first part of
its live Git `HEAD`/index/worktree proof. The observed Databricks source-folder
view exposed the required files but did not expose that execution location to
the Git CLI as a local repository. Consequently V1 could not complete its
commit-dependent source proof and could not emit a usable non-null review
package.

This is an incompatibility between the V1 runtime Git-metadata gate and the
observed Databricks execution view. It is not evidence that the reviewed builder
bytes were corrupt, that the selected project-source bytes were wrong, or that
the Unity Catalog namespace was spent.

## 4. Preconditions that did pass

The same supplied output established all of the following within its bounded
preflight scope:

- the DBR 17.3 x86_64 CPU runtime profile was exact;
- all 15 deterministic environment values were exact;
- the canonical F152 repository lock remained absent;
- the virtual candidate-003 prefix was absent;
- all 132 reserved candidate-003 leaf names were absent;
- the hash-first launcher executed the exact reviewed builder bytes; and
- construction remained unauthorized.

These facts do not create F151, F152, a production runtime, a capacity
reservation, or scientific readiness. They do establish that the V1 HOLD was
not caused by the runtime profile, deterministic environment, destination
collision, or builder-byte mismatch.

## 5. Safety and custody result

The supplied preflight reported no:

- managed candidate object write;
- base-runtime installation;
- package resolution, download, build, or installation;
- direct external network or contact operation;
- Spark or Databricks REST operation;
- study/test-data access;
- calibration, training, inference, or result inspection; or
- scientific or release decision.

Candidate-003 therefore remains absent and unspent. No attempt intent, payload
chunk, payload manifest, success receipt, or failure receipt was created. This
HOLD must not be classified as a terminal candidate no-go or as a consumed
attempt.

## 6. Historical preservation and V2 supersession

The exact [V1 contract](PROJECT_B08_N1_UC_NATIVE_OVERLAY_LOCK_CANDIDATE_BUILDER_V1.md)
and [V1 independent review](PROJECT_B08_N1_UC_NATIVE_OVERLAY_LOCK_CANDIDATE_BUILDER_V1_INDEPENDENT_REVIEW.md)
remain valid historical evidence for the bytes and source-review scope they
bind. They are preserved unchanged.

The [V2 successor contract](PROJECT_B08_N1_UC_NATIVE_OVERLAY_LOCK_CANDIDATE_BUILDER_V2.md)
and [V2 independent review](PROJECT_B08_N1_UC_NATIVE_OVERLAY_LOCK_CANDIDATE_BUILDER_V2_INDEPENDENT_REVIEW.md)
supersede only these V1 requirements for future execution:

1. live runtime Git `HEAD`/index/worktree verification;
2. treating runtime source-file mode as identity;
3. requiring the runtime launcher to retain the locally stored terminal LF; and
4. the V1 next-action instructions that expected commit/push/pull alone to make
   Git metadata visible to the Databricks runtime.

Commit/push/pull remains the source-delivery mechanism. It is not reinterpreted
as proof that the Databricks execution view exposes a usable `.git` repository.
All other historical V1 evidence and all separately accepted storage,
dependency, failure, and authorization boundaries remain preserved.

## 7. Project-state effect

This evidence registration closes no operational timetable task.

- Marked tasks: **62 checked / 101 open / 163 total**
- Fields: **24 open / 148 closed**
- Blockers: **7 OPEN / 5 CLOSED**
- Formal Test 28: **OPEN**
- Formal Test 29: **OPEN**
- Formal Test 30: **PENDING**
- Result slots: **0/4**
- F151: **OPEN and null**
- F152: **OPEN and null**
- B08: **OPEN**
- Wave 2: **OPEN**

The exact project-state delta is zero.

## 8. Next boundary

Do not rerun or authorize the V1 builder. Future preflight work must use only
the exact V2 hash-first launcher and V2 builder bound by their independent
review. The next permitted operation remains default-off and data-free; it does
not authorize candidate construction.
