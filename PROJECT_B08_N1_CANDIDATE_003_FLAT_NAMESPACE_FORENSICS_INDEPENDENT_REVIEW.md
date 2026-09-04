# Independent review: B08 N1 candidate-003 flat-namespace forensics V1

## Review disposition

**`PASS_CANDIDATE_003_FLAT_NAMESPACE_FORENSICS_V1_ZERO_DELTA`.** The exact
notebook, tests, and terminal no-go record bound below are accepted for one
bounded, data-free, read-only run against the exact spent candidate-003 flat
namespace in the fixed Unity Catalog Volume parent.

- P0: 0
- P1: 0
- P2: 0
- Exact project-state and completion-timetable delta: **zero**
- Candidate-003 construction/retry/reuse remains prohibited.
- Candidate-004 is not authorized.

## Exact bytes reviewed

| File | Bytes | SHA-256 |
|---|---:|---|
| `databricks/notebooks/b08_n1_candidate_003_flat_namespace_forensics_v1.py` | 93,302 | `c0ee94d4b09c6ebaffbf686e488bae4a114d6a412e7b528c453a3e3a27f69fb2` |
| `tests/unit/test_b08_n1_candidate_003_flat_namespace_forensics_v1.py` | 109,375 | `530cb3b40b3460bd3bed8a7ed5cf3054128d93a0acecafc5451369618d17e6d5` |
| `PROJECT_B08_N1_CANDIDATE_003_TERMINAL_NO_GO.md` | 6,207 | `524e35dfe0dcb82cc28fdf5aecf41aa923914a4c0c836877c6a1780550279d32` |

The forensic validator embeds the SHA-256 identity of the exact historical
278,717-byte candidate-003 V2 builder:
`7c7edb28f459618b1f35538e444b9cf40e70026b02fd0919ded9a20097f9014d`.
The focused tests independently reconstruct the expected intent from that
local builder. These bindings support narrow receipt validation; they do not
authenticate the origin of any remotely visible object.

## Fixed target and observation boundary

The notebook has no widget, argument, environment, or alternate-path override.
Its only target is the fixed parent

`/Volumes/development/team_eds_supplychain/b08_runtime_output`

and the exact flat candidate ID `b08-n1-overlay-candidate-003`. It contains the
builder-derived ordered roster of exactly 132 reserved leaf names. It does not
enumerate the parent directory or inspect unrelated Volume objects.

The notebook performs two independent observations. Each opens a fresh parent
descriptor with read-only, directory, no-follow, and close-on-exec controls;
checks every exact reserved name relative to that descriptor; and closes every
descriptor on normal and injected failure paths. Control-leaf descriptors add
nonblocking access. Only the exact intent and construction-failure-receipt
names are eligible for payload reads. All other reserved objects are
metadata-only observations, and any nonregular object, unexpected state,
unread present control, or snapshot disagreement yields a HOLD.

Each control payload accepted for classification is capped at 1 MiB and uses
descriptor-relative, no-follow, read-only access. For a leaf whose visible and
opened sizes are at or below that limit, the loop may read one cumulative
overflow-sentinel byte beyond 1 MiB; such an observation is rejected rather
than accepted. Successful classification requires two completed canonical
projections with exact equality. This is sequential path-visible evidence, not
an atomic snapshot, historical object identity, lineage, freshness, cache
coherence, physical durability, immutability, or future-stability proof.

## Narrow semantic validation

The expected intent is reconstructed from the frozen V2 builder and bound at
15,973 bytes, raw SHA-256
`ea8441151c07aef1a6fdf3320ff54d61237d3812b0c679cc0c2954a8db416015`,
and internal record SHA-256
`f9832c8b78a802254891b2d6f117c6c54f958a729bbac44f7bc1fcb5979f224f`.
The review-package digest is exactly
`5404dd580fac351e888d40836a399d5490396f35df576013eb1a78ecd20d9b23`.

The failure-receipt validator enforces a narrow, builder-consistent schema and
transition envelope; it does not prove exhaustive concrete reachability or
authorship. Critical comparisons use recursive exact JSON types, preventing
Boolean/integer and integer/float coercion. Confirmed and last-confirmed
bindings must match exactly. Safety and nonproof declarations must be exact,
and opaque exception/diagnostic text is retained only through bounded hashes or
tightly checked identifiers.

For subprocess diagnostics, completed non-timeout captures require exact
captured/observed equality. A timeout may differ by at most one 65,536-byte
reader chunk. The quiescent `TOOL_OUTPUT_READER_FAILED` and
`TOOL_OUTPUT_STREAM_BYTE_LIMIT_EXCEEDED` branches require, independently for
both streams, `0 <= observed - captured <= 65,536`; the overflow-named stream
additionally requires exactly 16 MiB captured and an observed excess of one to
65,536 bytes. The broader nonproof boundaries for reader-nonquiescence and
supervisor failure remain conservative.

Bootstrap-wheel reachability checks bind the central-directory floor to
`47 * entry_count + 79` and the local-area/offset floor to
`31 * embedded_payload_file_count + 82`. The latter includes one nonempty
compressed byte for each required `METADATA`, `RECORD`, and `WHEEL` control.
Within any failure receipt it accepts, the validator exactly and boundedly
checks the portable pip-identity/payload-closure summaries and the bootstrap
wheel/derived-bootstrap-lock fields that are actually present. It does not
prove a complete dependency lock, project/runtime artifact closure, an
installed overlay, or construction success.

## Safety and telemetry findings

The positive static call-surface allowlist covers every current call form and
contains no write, delete, rename, chmod, chown, subprocess, network, Spark,
Databricks REST, package-operation, study/test-data, calibration, training,
inference, or construction surface.

The I/O ledger is conservative under exceptions: a successful parent open is
counted before its following `fstat`; a nonempty read is counted immediately
after `os.read` and before buffer extension. Injected `fstat`, zero-read, and
post-read `MemoryError` tests confirm that the public safety report cannot
understate potentially completed managed-storage access.

Every public output explicitly denies construction, candidate reuse, and
candidate-004 authority and exposes the managed-storage safety ledger. The
review disposition additionally grants no canonical-lock publication,
F151/F152 closure, B08/Wave-2 closure, Formal-Test execution, or scientific
authority.

## Verification

- Focused candidate-003 forensic suite: **153/153 passed**.
- Relevant six-suite chain covering the frozen builder, launcher, UC probe,
  candidate-002 V1/V2 forensics, and candidate-003 forensics: **421/421 passed**
  from the repository and **421/421 passed** from `/private/tmp` using absolute
  paths.
- Expanded chain including the legacy isolated-overlay builder: **483/483
  passed**.
- Independent diagnostic/ZIP boundary tests: **14/14 passed**.
- Independent one-scalar strict-type mutation sweep: **163 mutations, zero
  false passes**.
- Python AST parse: clean.
- Positive AST call-surface audit and frozen-byte assertions: clean.
- `git diff --check`: clean before record integration.
- Two independent hostile reviews converge on P0/P1/P2 **0/0/0** for the exact
  bytes above.

## Exact next action

Commit and push these exact bytes, then pull them into Databricks. Open and run
only

`databricks/notebooks/b08_n1_candidate_003_flat_namespace_forensics_v1.py`

exactly once on the existing dedicated DBR 17.3 x86_64 CPU cluster and return
the complete JSON. Do not set construction widgets, rerun the builder or
launcher, alter any candidate-003 object, or create candidate-004.

This review grants no network/build, Databricks REST mutation, package
installation, canonical-lock, F151/F152, data, calibration, training,
inference, scientific-result, blocker-closure, B08/Wave-2 closure, tracker, or
submission authority.
