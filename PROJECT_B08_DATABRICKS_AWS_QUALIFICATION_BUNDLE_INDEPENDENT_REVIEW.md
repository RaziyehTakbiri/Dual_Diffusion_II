# Independent hostile review: B08 Databricks AWS qualification bundle

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
| `PROJECT_B08_DATABRICKS_AWS_QUALIFICATION_BUNDLE.md` | 25,824 | `28b064a60e07e9179a4a870b97cf0ad8deb8503018555d486a36c8c941fc2dc4` |
| `src/heterodiff/experiments/b08_databricks_aws_qualification.py` | 24,825 | `632bb5dd078cd91b9c7e4148e5d284d499f91f4ee5697df52a73e279f3c78e1f` |
| `research/diagnostics/b08_databricks_aws_qualification_capture_v1.py` | 39,191 | `f1123e302f1f7731570d0649af45ed7fc881c7d4487beda29578a741d0b75642` |
| `research/fixtures/manuscript_v3_b08_databricks_aws_qualification_template_v1.json` | 3,834 | `d5a31b69ee3a4aa586bc040c49d12d05e13fc11d66b81f1ef3a05db4958470ca` |
| `research/fixtures/manuscript_v3_b08_databricks_aws_admin_storage_reservation_template_v1.json` | 1,175 | `f8a910f8c3d8c9458b7c68de18adcefc439fa2975f8fa83957ad2af1755ec8cf` |
| `tests/unit/test_b08_databricks_aws_qualification.py` | 8,568 | `8a76dfd44c6542748b1911dceee49f03fb1b412de337b892aece78b470caaf60` |
| `tests/unit/test_b08_databricks_aws_qualification_capture_v1.py` | 7,244 | `ee95a5dc522ab0ba3ee5ac25b3e8f23f8fd4a7cd0e374947df3f4196dad1ec9c` |
| `research/diagnostics/manuscript_v3_b08_databricks_aws_qualification_bundle_v1.py` | 9,256 | `b572a7dc992b4d00bbb664313cb1f13f2a0564e6a54f159dcb546ce3b062b7b3` |
| `tests/unit/test_manuscript_v3_b08_databricks_aws_qualification_bundle_v1.py` | 2,940 | `3c3d5fc3c1b573cb0d1bc50c447917400904c22171f1af01934fa61a1e2b0dbe` |

The qualification-template canonical semantic digest independently reproduced
as `771b150637bce72480164ed5ef168e9d426a58277962161b6962ed9d02520239`.

## Reproduction receipt

- Focused core, capture, and package-validator tests: **41 passed**.
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
