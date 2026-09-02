# Independent review — B08 Wave-2 local-capacity preflight terminal no-go

**Reviewed:** 2026-09-02  
**Disposition:** `GO_BOUNDED_B08_WAVE2_LOCAL_CAPACITY_TERMINAL_NO_GO`  
**Field closures authorized:** none  
**B08 closure authorized:** no  
**Timetable closure authorized:** none  
**Findings:** P0 `0`; P1 `0`; P2 `0`

## 1. Decision

I independently accept the package only as a truthful, read-only, zero-delta
capacity refusal. The exact captured free-space operand is far below the
already-frozen Test-28 combined storage floor, no byte was reserved, and none
of the four compound B08 requirements is supplied. The package therefore
supports `B08_REMAINS_OPEN_EXTERNAL_CAPACITY_REQUIRED` and nothing stronger.

This `GO` does **not** mean that Wave 2, B08, the Gate-A capacity item, or the
timetable task `Hardware, Test-28 storage, and compute capacity are reserved.`
is complete. It accepts the bounded no-go and the decision not to attempt an
unsafe local allocation. F150--F152, F154--F157, F159--F160, and F162 remain
open and null. The previously accepted closures F153, F158, and F161 are
unchanged.

## 2. Exact candidate custody

I reviewed the following five candidate files. Immediately before this review
was written, every file was a regular `0644`, single-link file with the exact
size and raw SHA-256 digest below.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `PROJECT_B08_WAVE2_CAPACITY_PREFLIGHT_NO_GO.md` | 6,453 | `e6d7c4ab79482e0718d8dfcb08437f764b31e36e015383acba2ae6d4b4c4e6d6` |
| `src/heterodiff/experiments/b08_wave2_capacity_preflight.py` | 10,641 | `687ac4fd46f41cf17caa93c2bf744c044b0568dab406349a04bc79e28689e6fd` |
| `research/fixtures/manuscript_v3_b08_wave2_capacity_preflight_v1.json` | 4,833 | `e32a096137f56174939a8457e1877f71b5765f627a4d682bb077210dd6c6a917` |
| `research/diagnostics/manuscript_v3_b08_wave2_capacity_preflight_v1.py` | 5,631 | `13a577874fede7636351cf374e290d85abf464d38b5c4a4391f736cfaa5c2145` |
| `tests/unit/test_b08_wave2_capacity_preflight.py` | 4,692 | `a3a93ddd5d36fd54d17542ddfcf32d3c4dcf7ab6d624c94b1c5cddd1755d30b8` |

The machine record is ASCII canonical JSON with exactly one terminal LF and no
duplicate keys or non-finite values. Its semantic projection recomputes to
record digest
`a8247bea6a3d6c96ddad583f6f35e740347d4ba0c7b4ed4cacd53274d1ed792c`.

## 3. Independent predecessor and arithmetic recomputation

All three predecessor bindings were reread directly and matched both size and
raw digest:

| Role | Bytes | SHA-256 |
|---|---:|---|
| Accepted B08 partial-freeze machine | 20,982 | `f141e12624f10a13aab61fc034914e3fea5d75bb5f4f49cc4dd723c4fe48eda6` |
| Current Test-28 capacity contract | 7,087,027 | `7faed3c5b07415fbc45fec02d026e36d465819a38e9187369bf0a42a91c29f68` |
| Accepted nonconfirmatory whole-method beta review | 11,076 | `e24f2e97a67048323170b44d6e537ab07c3a7a6692cf682bc3053c1165732765` |

The frozen CP64 contract independently confirms the three decisive byte
operands: 1,099,511,627,776 destination bytes, 34,359,738,368 auxiliary bytes,
and 1,133,871,366,144 combined bytes. It also retains the minimum 4,096-inode,
same-filesystem, exclusive, non-sparse, quota, no-double-count, and durability
requirements described by the human record. CP64 still records
`capacity_measured=false`, `capacity_receipt_present=false`, and
`production_resources_allocated=false`.

Independent integer arithmetic reproduced every claimed result:

| Check | Independent result |
|---|---:|
| `38,359,440 * 1,024` | 39,280,066,560 available bytes |
| `1,099,511,627,776 + 34,359,738,368` | 1,133,871,366,144 combined required bytes |
| `1,133,871,366,144 - 39,280,066,560` | 1,094,591,299,584-byte shortfall |
| reduced `available / combined` | `799155/23068672` |
| reserved bytes evidenced | 0 |

The synthetic receipt body independently recomputes to
`c7b35c476b938a24bd36945571eb681ff7e79ce24c1e5ebfed7424d9d462bd48`.
Independent regeneration of the 64-MiB zero stream produced
`3b6a07d0d404fab4e23b6d34bc6696a6a312dd92821332385e5af7c01c421351`;
independent regeneration of the stated 512-by-512 binary32 matrix product
produced
`c76266f28c6450c7287b439af602d1b5b72ea14f4feab8de04b4ad0c860e1773`.
Those checks confirm deterministic local arithmetic only; the recorded timings
are not promoted to calibration weights or ceilings.

As a corroborative review-time observation, the same filesystem later exposed
38,179,704 available 1,024-byte blocks, slightly fewer than the candidate's
point-in-time 38,359,440-block capture. Free space is volatile, and neither
snapshot is a reservation receipt. This does not weaken the zero-delta no-go:
both observations are far below the frozen combined floor, and the candidate
explicitly disclaims attestation and promotion.

## 4. Validation and compatibility results

I ran the candidate validator once from the project root and once from an
unrelated working directory. Both runs returned
`PASS_B08_WAVE2_LOCAL_CAPACITY_TERMINAL_NO_GO` with the same record digest,
ten-field residual roster, byte requirement, shortfall, and `B08_closed=false`.

The independently executed test surfaces were:

| Surface | Result |
|---|---:|
| Wave-2 focused tests | 13/13 passed |
| Accepted B08 partial-freeze compatibility tests | 66/66 passed |
| Accepted B08 predecessor validator | `PASS_THREE_FIELDS_ONLY_B08_REMAINS_OPEN` |

The focused suite covers canonical equality, exact arithmetic, the exact ten
residual fields, zero project delta, receipt self-digest, deterministic output
agreement, hostile record mutations, Boolean/integer alias rejection, and the
absence of a source effect surface. The candidate source imports no network,
subprocess, entropy, or filesystem-writing facility and performs no capture,
reservation, benchmark, data, training, inference, or scientific operation.

## 5. Closure-eligibility audit

The active ledger independently confirms that the ten residual fields are
open, B08 is open, and the hardware/capacity timetable checkbox is unchecked.
The candidate supplies none of the evidence needed to change that state:

1. no selected and accountable production hardware/runtime identity;
2. no complete observed production dependency manifest or production lock;
3. no F104 calibration weights on the selected frozen environment;
4. no qualified complete-run wall-time, accelerator-time, memory, persistent-
   byte, model-evaluation, scalar, or eight-axis ceilings;
5. no instantiated tuning or final allocation; and
6. no physical capacity reservation, quota, durability, or feasibility
   receipt.

Accordingly, the only eligible registration is the informational fact that the
local capacity attempt terminated safely with no-go. The exact project delta
is empty:

- no field closes;
- B08 does not close;
- no Formal Test closes;
- no result slot fills;
- no timetable checkbox closes; and
- no hardware, runtime, capacity, data, science, claim, release, or submission
  state is created.

## 6. Findings and required next input

No P0, P1, or P2 defect was found within the package's deliberately narrow
zero-delta claim. A real successor requires an accountable production
environment and reservation that satisfy the frozen capacity predicate and can
support the complete schedule. Alternatively, an explicitly authorized
pre-outcome scientific rescope would have to reopen and re-review every
affected budget, power, fairness, runtime, and Test-28 dependency. This package
authorizes neither path.
