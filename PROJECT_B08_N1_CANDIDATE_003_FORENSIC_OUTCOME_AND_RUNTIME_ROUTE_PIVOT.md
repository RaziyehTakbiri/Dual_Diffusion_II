# B08 N1 candidate-003 forensic outcome and runtime-route pivot

**Recorded:** 2026-09-04  
**Decision:** `CANDIDATE_003_PERMANENTLY_SPENT_UNRESOLVED_CUSTODY_ROUTE_RETIRED`  
**Tracked delta:** zero

## Evidence basis

This record summarizes the operator-supplied semantic JSON from the completed
read-only candidate-003 forensic run. The raw output file was not supplied, its
bytes are not hashed here, operator identity is not externally authenticated,
and execution time is not externally attested. The supplied semantic text also
does not cryptographically bind the exact remote notebook bytes or executed
source identity.

The reported run establishes the following narrow facts:

- both required path-visible snapshots completed and were equal;
- the 132-name reserved namespace contained exactly two regular control files,
  with 130 reserved names absent and the virtual candidate prefix absent;
- `b08-n1-overlay-candidate-003.attempt-intent.json` was 15,973 bytes, had
  SHA-256 `ea8441151c07aef1a6fdf3320ff54d61237d3812b0c679cc0c2954a8db416015`,
  and passed all validation, including internal record SHA-256
  `f9832c8b78a802254891b2d6f117c6c54f958a729bbac44f7bc1fcb5979f224f`;
- `b08-n1-overlay-candidate-003.construction-failure-receipt.json` was 17,862
  bytes with SHA-256
  `c0118dae41980dc2fbbf820992b9698c63f268d1c59e4789da4d718acaa18d3c`;
- the validator reported no failure-receipt validation error other than
  `FAILURE_COMMAND_JOURNAL_ARGV_BINDING_MISMATCH`.

The forensic run reports no mutation, subprocess or package operation, direct
external network access, Spark/REST access, study/test-data access, calibration,
training, or inference. It did not inspect or report the canonical F152 lock.
Separately, current accepted project evidence contains no overlay payload,
success receipt, review-pending lock, or canonical F152 lock.

## Interpretation boundary

The mismatch does **not** establish that an unsafe command ran or that the
receipt is corrupt. A plausible provisional P2 portability hypothesis is that
the builder constructs replacements from resolved
`sys.executable` and `sys.prefix` paths while sanitizing the lexical command
arguments, so a symlinked Databricks interpreter can be recorded as
`<HOST_PREFIX>/bin/python` while the forensic validator accepts only
`<HOST_PYTHON>`. Existing tests did not exercise that overlap.

That explanation remains an inference. The semantic output does not expose the
offending journal entry, argument, or command step, so exact causality is not
claimed. The earlier source review's P0/P1/P2 `0/0/0` verdict remains historical
for its exact reviewed bytes; this post-run evidence adds a prospective
portability concern rather than rewriting that frozen review. Fail-closed safety
held, but classifier completeness was not demonstrated.

## Final disposition

Candidate 003 is `PERMANENTLY_SPENT_UNRESOLVED`. Preserve its namespace and all
historical records unchanged. Do not rerun, reuse, repair, rename, replace, or
delete Candidate 003. Candidate 004 is not authorized or planned. No additional
remote causal forensics will be pursued unless an external audit or compliance
obligation specifically requires exact attribution.

The completed forensic run satisfies and prospectively supersedes the earlier
tracker instruction to run the V1 forensic notebook once. It does not validate
the failure receipt, create a dependency lock, or close F151, F152, B08, Wave 2,
or a scientific task.

## Prospective Databricks route

Before any scientific outcome was accessed, the user adopted this project
management pivot. It changes no model, metric, threshold, seed, result, or
scientific decision.

The B08 custom-container/ECR and runtime-overlay append-only one-shot custody
routes are retired for future project work. They are classified as superseded,
not completed. The active B08 reproducibility route is conventional and
project-scoped:

1. Capture a sanitized execution-runtime manifest covering the Databricks
   Runtime/Spark version, Python, OS/architecture, node type, core/device model,
   CPU/GPU and memory, driver/worker topology, relevant deterministic variables,
   installed distributions, and import origins.
2. Check in a fully resolved hash-pinned project dependency lock, bind the exact
   content-addressed source-manifest and built project-wheel digests, then
   verify the installed environment with exact-version/import-origin checks and
   `pip check`, after
   installation in a fresh or restarted notebook interpreter.
3. Run the relevant unit and integration suites plus one tiny data-free or
   synthetic whole-method smoke test on the selected runtime.
4. Before confirmatory work, freeze prospective wall-time, accelerator,
   peak-memory, model-evaluation, tuning, final-run, total-compute, and durable
   output ceilings, then verify documented Unity Catalog quota or accountable
   administrative capacity assurance, projected-output bounds, and local-scratch
   fail-fast checks against those ceilings.

Docker/ECR, a custom container, an image-pull instance profile, bitwise identity
of Databricks-managed internals, disabled auto-termination, Unity Catalog
B08 runtime-overlay append-only candidate namespaces, B08 one-shot runtime
custody protocols, and further Candidate 003 failure forensics are not closure
requirements absent a specific external obligation. This does not alter the
separate Gate-C preregistration and scientific-custody tasks in the timetable.

F153 remains closed only for its existing CPU-only, single-threaded,
CUDA-hidden policy. Any later GPU or multithreaded scientific route must
explicitly supersede or reopen F153 before execution.

## Project state after this decision

- Marked tasks: **62 checked / 101 open / 163 total**
- Fields: **24 open / 148 closed** (`PRE` 23/143; `POST` 1/5)
- Blockers: **7 open / 5 closed**
- Gate A: **5/8**
- Formal Tests 28/29/30: **`OPEN` / `OPEN` / `PENDING`**
- Results: **0/4**
- F151/F152: **OPEN and null**
- B08 and Wave 2: **OPEN**
