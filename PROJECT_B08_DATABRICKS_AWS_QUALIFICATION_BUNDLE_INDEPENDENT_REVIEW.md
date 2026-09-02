# Independent hostile review: B08 Databricks AWS qualification bundle

**Current review boundary:** enum and deterministic-capture compatibility
successor accepted

## Review disposition

**GO for the bounded, data-free qualification-bundle purpose, with no open
findings.**  This is not a GO for calibration, a Databricks run, field closure,
blocker closure, or timetable closure.

- P0: 0
- P1: 0
- P2: 0
- Exact eligible project delta: **zero** (`field_delta=0`, `blocker_delta=0`,
  `timetable_delta=0`, B08 remains `OPEN`, Formal Tests 28/29 remain `OPEN`,
  and Formal Test 30 remains `PENDING`).

## Frozen bytes reviewed

| File | Bytes | SHA-256 |
|---|---:|---|
| `PROJECT_B08_DATABRICKS_AWS_QUALIFICATION_BUNDLE.md` | 26,458 | `a94e4ae80ece430bf1986cf23c777d87b76af943721224e3dc1b3fd8b7335fe7` |
| `src/heterodiff/experiments/b08_databricks_aws_qualification.py` | 24,825 | `632bb5dd078cd91b9c7e4148e5d284d499f91f4ee5697df52a73e279f3c78e1f` |
| `research/diagnostics/b08_databricks_aws_qualification_capture_v1.py` | 39,892 | `ce16f4c6c797f64b2f101c54ffc0338824e9e7ebf91fca276ca2d50260c8be4d` |
| `research/fixtures/manuscript_v3_b08_databricks_aws_qualification_template_v1.json` | 3,834 | `d5a31b69ee3a4aa586bc040c49d12d05e13fc11d66b81f1ef3a05db4958470ca` |
| `research/fixtures/manuscript_v3_b08_databricks_aws_admin_storage_reservation_template_v1.json` | 1,175 | `f8a910f8c3d8c9458b7c68de18adcefc439fa2975f8fa83957ad2af1755ec8cf` |
| `tests/unit/test_b08_databricks_aws_qualification.py` | 8,568 | `8a76dfd44c6542748b1911dceee49f03fb1b412de337b892aece78b470caaf60` |
| `tests/unit/test_b08_databricks_aws_qualification_capture_v1.py` | 10,141 | `8f06738fcfdc4f58132dbd781d6eb205a569b6741c161a466412184887da05b7` |
| `research/diagnostics/manuscript_v3_b08_databricks_aws_qualification_bundle_v1.py` | 9,257 | `82b0b4e274c8b62153dca502a252386b372bb5d720c9133ef7a147059cf92981` |
| `tests/unit/test_manuscript_v3_b08_databricks_aws_qualification_bundle_v1.py` | 2,940 | `3c3d5fc3c1b573cb0d1bc50c447917400904c22171f1af01934fa61a1e2b0dbe` |

The qualification-template canonical semantic digest independently reproduced
as `771b150637bce72480164ed5ef168e9d426a58277962161b6962ed9d02520239`.

## Reproduction receipt

- Focused core, capture, and package-validator tests: **51 passed**.
- Broad B08 compatibility suite: **130 passed**.
- Package validator from the project root: **PASS**.
- Package validator from `/private/tmp` with absolute interpreter/script paths:
  **PASS**.
- Both validator invocations returned
  `PASS_B08_DATABRICKS_AWS_QUALIFICATION_BUNDLE_HOLD_NO_CLOSURE` and the same
  zero-delta state (`62 checked / 101 open / 163 total`).
- Bytecode emission and pytest cache creation were suppressed.

## Independent semantic audit

The bundle is aligned with the project's B08 boundary: it constructs and
checks a contract and empty HOLD templates; it neither claims external
qualification nor authorizes execution.  Its Databricks assumptions are
appropriately explicit: AWS classic compute, dedicated access, fixed topology,
on-demand CPU nodes, Photon disabled, pinned runtime, and immutable custom
container identity.  Single-node (`worker_count=0`) and multiworker evidence
are distinguished without pretending that driver-only structural capture
proves worker compliance.

The storage arithmetic is exact: 1,099,511,627,776 destination bytes plus
34,359,738,368 auxiliary bytes equals 1,133,871,366,144 combined bytes, with
at least 4,096 inodes.  The contract also correctly requires exclusivity,
disjoint accounting, non-sparse allocation, quota and durability evidence,
and prevents a Unity Catalog Volume or S3 object prefix from being treated as
proof of physical reservation.

The capture helper is standard-library-only, performs no network, Spark, REST,
subprocess, randomness, or secret-store operation, uses no-clobber private
`0600` output, and labels its result as structural evidence requiring later
normalization and external review.  Hostile checks confirmed that camelCase
secret/private-identity keys (including `clientSecret`, `apiToken`,
`privateKey`, and `accessKey`) now fail closed and that `/Workspace` paths are
rejected.  `/tmp` is expressly limited to transient staging with custody
checks and cannot satisfy capacity or durability evidence.  These repairs
close the two P1 defects found against the pre-freeze candidate.

The enum-compatibility successor accepts Databricks' current
`DATA_SECURITY_MODE_DEDICATED` value and maps it to the established
`DEDICATED` receipt representation. Independently generated predecessor
receipts using `SINGLE_USER` and `DEDICATED` remain valid. Every other official
security-mode value tested failed closed; explicit `SHARED` and
`USER_ISOLATION` cases also failed closed; and snake/camel-case private-identity
keys remained rejected when the current enum was supplied. The change
introduces no network, Spark, data, calibration, closure, or tracker authority.

The successor also repairs a capture-completeness mismatch exposed by the
real preflight: the helper's allowlist now includes `BLIS_NUM_THREADS`,
`PYTHONDONTWRITEBYTECODE`, `PYTHONNOUSERSITE`, and `PYTHONSAFEPATH`. A
cross-module regression requires every deterministic control in the governing
qualification core to be capturable and verifies the exact values. This adds
receipt visibility only; it does not install, infer, or approve any control.

## Final findings table

| Priority | Open | Final result |
|---|---:|---|
| P0 | 0 | No critical correctness, safety, or closure-boundary defect found. |
| P1 | 0 | The pre-freeze secret-key and `/Workspace` custody defects remain closed. |
| P2 | 0 | The sole validator custody-hardening finding is remediated and independently reproduced. |

The remediated validator walks from a directory descriptor, uses no-follow
descriptor opens, requires a regular single-link file that is neither group-
nor world-writable, bounds the read to the descriptor-reported size, and
checks device, inode, size, and modification identity after reading.  In a
fresh isolated capsule, changing the byte-correct pure-core candidate to mode
`0666` now failed closed with `ValidationError` before semantic validation.
The focused suite contains the corresponding regression.

## Closure decision

No field, B08 blocker, formal-test route, timetable checkbox, calibration, or
production obligation is eligible for closure from this package.  The only
eligible action is to retain the bundle as a reviewed, data-free qualification
contract and use it later to collect separately governed evidence.
