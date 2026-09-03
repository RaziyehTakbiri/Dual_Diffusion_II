# B08 N1 Unity Catalog Volume write-capability probe independent review

**Disposition:** `PASS_SOURCE_SAFE_FOR_ONE_EXACT_AUTHORIZED_PROBE_RUN`

**P0 / P1 / P2 findings:** `0 / 0 / 0`

**Eligible project delta:** zero

## 1. Reviewed boundary

This review accepts only the exact source bytes listed below for one bounded,
data-free capability probe on the already selected dedicated DBR 17.3 x86_64
cluster. It does not accept or authorize an N1 overlay construction, package
resolution, direct external network contact, canonical-lock publication, study/test-data
access, calibration, training, inference, or scientific interpretation.

| Reviewed object | Bytes | SHA-256 |
|---|---:|---|
| `PROJECT_B08_N1_CANDIDATE_002_OBJECT_SNAPSHOT_FORENSICS_V2_OUTCOME.md` | 5,318 | `d487130f4fa8397e9e94cc5f6ec6714c85ed6179ec4e6c18a2d079425e59ec7a` |
| `databricks/notebooks/b08_n1_uc_volume_write_capability_probe.py` | 35,681 | `849fdad4c73d3123e584b5020184dfac25acbd66860576726fbd73ca4aa15ded` |
| `tests/unit/test_b08_n1_uc_volume_write_capability_probe.py` | 26,657 | `9177f20e77d8d42b519d203561853e40b6ebfcb8e03546abac680c0042b76c1e` |

The forensic outcome records the operator-supplied classification
`STABLY_COMPLETE_EXPECTED_INTENT_VISIBLE` for the permanently spent
candidate-002 path. The probe does not open, list, mutate, or derive its own
paths from candidate-002 or any future candidate-003 construction path.

## 2. Exact probe contract

The notebook hard-codes the existing parent

`/Volumes/development/team_eds_supplychain/b08_runtime_output`

and exactly two initially absent retained leaves:

- `b08-n1-uc-volume-write-capability-probe-001-primary.bin`
- `b08-n1-uc-volume-write-capability-probe-001-race.bin`

It creates no directory. Its three default-off Databricks dropdown gates must
have the following exact values before the one run can proceed:

| Widget | Exact run value |
|---|---|
| `b08_n1_uc_volume_probe_mode` | `RUN_ONE_BOUNDED_UC_VOLUME_WRITE_CAPABILITY_PROBE` |
| `b08_n1_uc_volume_probe_write_authorized` | `true` |
| `b08_n1_uc_volume_probe_acknowledgement` | `AUTHORIZE_ONE_DATA_FREE_UC_VOLUME_WRITE_CAPABILITY_PROBE_001` |

The fixed 4,096-byte payload identities are:

| Role | SHA-256 |
|---|---|
| `PRIMARY` | `26b7e40be0bcf3e6667020b3acf6e07faa17585b21b2936305dd6c9ad3860b15` |
| `COLLISION` | `b23f99e1f653e62fa5bc14cc528a9ec3b6d11be482b2ee51b519d1d6ad8c5466` |
| `RACE_A` | `6896d9ea3f73a4434f5832bc65714e7d066f177373f36f34dc8a6f735daa41b1` |
| `RACE_B` | `725bcd6c66d02acf6ebeab9c92410e010ea22e336876256aaf05a211f4ce1902` |

The notebook permits at most four exclusive-create calls and at most 12,288
payload bytes even under a broken race outcome. A PASS requires exactly four
create calls, exact primary create/write/readback, a same-path collision that
does not write, and a synchronized two-process race with exactly one creator
and one collider. It then obtains repeated exact size-and-SHA-256 readback
through freshly opened descriptors. Both leaves are deliberately retained as
probe evidence; once any attempt begins, their names are spent.

## 3. Hostile-review conclusions

The final source closes the review findings concerning:

- truthful reporting of managed Unity Catalog metadata and payload I/O;
- whole-protocol child cleanup, bounded process reaping, and explicit
  cluster-termination-required handling when quiescence cannot be confirmed;
- role-swapped race coverage and rejection of malformed or duplicate child
  reports;
- structured handling of Unity Catalog visibility errors at preflight;
- rejection of the false-PASS case where `FileExistsError` is raised during a
  write rather than by the exclusive open; and
- counting payload bytes as completed by the notebook only after the payload
  file and parent descriptors close successfully, without claiming `fsync` or
  physical-storage durability.

The focused probe suite passes `38/38` from both the repository root and an
unrelated working directory. The combined probe, candidate-002 V2/V1 forensic,
and N1 builder suite passes `136/136`. Static analysis and repository whitespace
validation are clean. The injected write-time-`EEXIST` regression is executed
and rejected as an error rather than misclassified as the intended collision.

## 4. Run disposition and stop rules

On first import, run the notebook once with all three default-off values. That
read-only preflight materializes the widgets and should return
`HOLD_UC_VOLUME_PROBE_AUTHORITY_INCOMPLETE` while writing no payload. Proceed
only if it reports both hard-coded leaves absent and no preflight error. The
exact reviewed source is then safe for one authorized probe run. If either leaf
already exists, stop: do not delete, rename, repair, reuse, or improvise a new
path. If the notebook reports that cluster termination is required before
forensics, terminate that cluster and stop before inspecting the retained
leaves. Preserve and return the complete JSON result for review.

A PASS is empirical evidence about this exact Unity Catalog Volume path and
runtime behavior. It does not make the existing POSIX-oriented N1 builder safe
to rerun. A separately implemented and independently reviewed Unity Catalog
Volume-native successor writer is still required before any candidate-003
construction can be considered.

## 5. Project-state effect

This is source acceptance for a bounded diagnostic only. No timetable checkbox,
field, blocker, Formal Test, result, runtime, capacity, or scientific predicate
closes. The marked-task view remains `62 complete / 101 open / 163 total`;
fields remain `24 open / 148 closed`; blockers remain `7 open / 5 closed`;
Formal Tests remain `OPEN / OPEN / PENDING`. F151, F152, B08, and Wave 2 remain
open.
