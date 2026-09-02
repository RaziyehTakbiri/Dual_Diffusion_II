# B08 Wave-2 local-capacity preflight and terminal no-go candidate

**Reported:** 2026-09-02  
**Candidate state:** `B08_WAVE2_LOCAL_CAPACITY_PREFLIGHT_TERMINAL_NO_GO`  
**Scientific or confirmatory execution:** none  
**Proposed field, blocker, Formal-Test, or timetable delta:** zero

## 1. Outcome

The safe local part of Wave 2 has been exhausted. The accepted B08 partial
freeze still validates, and a fresh deterministic, data-free repeatability
exercise was completed on the current local CPU route. Neither item supplies
production capacity.

The current workspace filesystem reported 38,359,440 available 1,024-byte
blocks, or exactly 39,280,066,560 available bytes. The already-frozen Test-28
capacity predicate requires all of the following on one qualified storage
root:

- 1,099,511,627,776 physically reserved destination bytes;
- 34,359,738,368 separately reserved auxiliary bytes;
- 1,133,871,366,144 combined effective reserved bytes;
- at least 4,096 available inodes after reservation; and
- the frozen exclusivity, non-sparse-allocation, quota, durability, same-root,
  no-double-count, and filesystem-operation checks.

The observed free-space snapshot is only the exact fraction
`799155/23068672` (about 3.46%) of the combined byte floor. It is short by
1,094,591,299,584 bytes even before inode, quota, exclusivity, durability, and
runtime requirements are considered. Zero bytes were reserved. A free-space
snapshot is not a reservation receipt, and attempting to allocate more than a
terabyte on this nearly full local filesystem would be unsafe and impossible.

Therefore the current local host cannot truthfully satisfy the accepted B08
capacity predicate. The package does not select it as production hardware and
does not manufacture a reservation, runtime, ceiling, or weight receipt.

## 2. Fresh data-free work

The prior B08 package was revalidated without mutation:

- its validator returned `PASS_THREE_FIELDS_ONLY_B08_REMAINS_OPEN`; and
- all 66 focused tests passed.

A fresh CPU-only repeatability exercise used no domain data, seed, random
input, model checkpoint, learner, optimizer, external process, or network
access. Five explicit 64-MiB all-zero SHA-256 rows reproduced one output digest
within the run. Three explicit 512-by-512 binary32 matrix products reproduced
one output digest within the run. Timings are retained only as volatile host
observations. These exercises do not represent the ten F104 event classes,
domain-scale work, a selected production environment, or a calibration-weight
receipt, so no timing is promoted to an F104 weight or B08 ceiling.

## 3. Exact residual-field evidence requirements

All ten residual B08 fields remain open and null:

| Field | Evidence required before closure |
|---|---|
| F150 | A selected production-hardware identity bound to an accountable availability/reservation receipt. |
| F151 | A complete observed production software/runtime manifest, including every B12 primary, comparator, baseline, adapter, runner, and measurement dependency, with its canonical digest. |
| F152 | A production lock or container digest whose stated role matches the selected host; the current M1 lock expressly disclaims future production/large-training use. |
| F154 | A pre-test per-run wall-time ceiling supported by a qualified complete run unit on the selected frozen runtime. |
| F155 | A pre-test accelerator-hour ceiling supported by the selected route; exact zero is admissible only after a CPU-only production route is actually selected and qualified. |
| F156 | Pre-test peak device-memory, peak host-memory, and persistent-byte ceilings supported by complete-run qualification. |
| F157 | A frozen mapping from the complete B12 run unit to exact model-evaluation accounting and its per-run ceiling. F143/F147 are now frozen, but that mapping and complete run unit remain absent. |
| F159 | The exact tuning allocation instantiated from accepted candidate grids, F104 weights, scalar and hard-axis ceilings, and reserved capacity. |
| F160 | The exact final-training and confirmatory-inference allocation instantiated from the complete schedule, F104 weights, scalar and hard-axis ceilings, and reserved capacity. |
| F162 | The total scalar and eight-axis ceiling across every scheduled and charged attempt, plus a reservation/resource receipt proving feasibility. |

## 4. Exact B08 closure predicate

B08 remains an all-or-nothing blocker. It cannot close until one coherent
production package supplies:

1. `HARDWARE_AND_RUNTIME_IDENTITY`;
2. `CALIBRATION_WEIGHTS` for every domain/event cell, measured once on that
   frozen environment before test access;
3. `SCALAR_AND_HARD_AXIS_CEILING_VALUES`, including wall time, accelerator
   time, peak device memory, peak host memory, model evaluations, persistent
   bytes, failure count, and parameter count; and
4. `CAPACITY_RESERVATION_RECEIPT` satisfying the frozen storage and availability
   predicate.

The current evidence satisfies none of those four compound requirements. In
particular, the accepted whole-method beta is nonconfirmatory and explicitly
not a complete arbitrary-length production path, while the eight local author
extensions do not supply the upstream production runtimes or real adapters.

## 5. Authority and safety boundary

No dependency was installed or downloaded. No infrastructure was purchased or
reserved. No person or service was contacted. No data was accessed. No
scientific seed, training, inference, result, claim, release, or submission was
created. No tracker or evidence-ledger item is edited by this package.

The exact achieved project closure is therefore empty. The accepted prior
closures F153, F158, and F161 remain valid; F150--F152, F154--F157,
F159--F160, F162, B08, the Gate-A hardware/capacity item, and the timetable task
`Hardware, Test-28 storage, and compute capacity are reserved.` remain open.

## 6. Irreducible next input

Progress now requires a real resource decision, not more local arithmetic. A
future successor must provide either:

- an accountable production environment and reservation with at least the
  frozen storage floor and enough compute for the complete B06 schedule; or
- an explicitly authorized pre-outcome rescope that changes the scientific
  schedule and then reopens every affected preregistered budget, power,
  fairness, runtime, and Test-28 dependency for review.

Neither alternative is selected by this no-go candidate.
