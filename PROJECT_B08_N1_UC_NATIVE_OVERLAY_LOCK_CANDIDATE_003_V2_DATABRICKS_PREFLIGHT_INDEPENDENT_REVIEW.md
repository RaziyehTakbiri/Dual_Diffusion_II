# Independent hostile review: candidate-003 V2 Databricks default-off preflight

## Review disposition

**`PASS_DATABRICKS_V2_DEFAULT_OFF_PREFLIGHT_REVIEW_PACKAGE_REPRODUCED_CANDIDATE_003_UNSPENT_AS_OBSERVED`.**

- P0: 0
- P1: 0
- P2: 0
- Candidate-003: absent and unspent as observed
- Construction authority: not issued
- Exact tracked project delta: zero

The operator-supplied V2 output is accepted as the expected, error-free
default-off Databricks preflight. Its HOLD is intentional because only the four
construction gates were left unset.

## Independent binding audit

The review independently recomputed or compared the supplied bindings with the
accepted local package:

| Binding | Independently verified value |
|---|---|
| Builder | 278,717 bytes; `7c7edb28f459618b1f35538e444b9cf40e70026b02fd0919ded9a20097f9014d` |
| Launcher canonical identity | 9,692 bytes; `7035ee3fdee6fb6b50005798f8c178a140ee1d3727471d8a58ef160f66f57afb` |
| Launcher tracked raw bytes | 9,693 bytes; `d47dec6532bd660bbb03c336a9b1b19081d3f4b012a94fb462b87025865aa1a3` |
| Snapshot anchor | 726 bytes; `1e9ee7f36286333e7f8936acf61068597c7ea23338b663aad7cabd441c794ebe` |
| Selected-source projection | 304 files; 18,924,848 bytes; `0e2decc9d0c6dbb4ff6b41dec4ee78b6139ea2aa8a419880e3e06ff4f8716021` |
| Source-identity record | `9716f23666953d87b8a02d0d4c18fe85bdb83597dd5a6e390551e9e413f36eec` |
| Native profile | raw `4058d9e236733698a0a97022156cfbedd4af308b541883c2cc687d8b9a7840f6`; semantic `d5994e8158737b2d1cbd369b347698e131256639b93e5a33ac1ba7ee49c098c3` |
| Native-target review | 8,456 bytes; `0d75872dc984fbbaf671875407b082dfb447bc007e55572158ed23383c2df450` |
| UC probe review | 5,735 bytes; `7612dbe3c4072c0ab2847bb17d99d6a5aa66ccfff80734f0d961baec57229a59` |
| UC probe outcome | 5,120 bytes; `f96160da93789d4749b3ce005182a0f57a49a5bc4408296d46ca4fd7fc71bcd7` |
| Review-package record | `5404dd580fac351e888d40836a399d5490396f35df576013eb1a78ecd20d9b23` |

The raw launcher differs from its canonical identity by exactly one terminal LF,
which is the sole permitted launcher normalization. Runtime presentation mode
is not used as source identity. The builder and selected-source content remain
exact-byte bound.

## Preflight semantics

The supplied output reports:

- `errors = []`;
- exact source identity;
- exact hash-first execution evidence;
- a complete non-null review package;
- exact runtime within the declared wheel-selection ABI scope;
- exact deterministic environment;
- valid native profile;
- absent candidate-003 virtual prefix;
- all 132 reserved leaves absent;
- absent canonical F152 lock; and
- no write, network, package, build, installation, Spark, REST, data, or
  scientific action.

The required-input list contains exactly the intentionally absent execution
mode, network/build authority, one-shot acknowledgement, and package-bound
authorization token. Therefore the observed
`HOLD_PREFLIGHT_INPUTS_OR_AUTHORITY_INCOMPLETE` decision is a successful
default-off safety result, not a runtime-profile or source failure.

The null `authorized_review_package_sha256` is likewise correct in a run that
did not supply the authorization token.

## Verification

The exact focused builder/launcher suite was rerun and passed:

```text
194 passed
```

The focused test run did not modify the reviewed builder, launcher, snapshot,
or selected-source projection. No Databricks construction was executed by this
review.

## Custody limitations and nonclaims

The chat-supplied JSON is semantic evidence, not a separately downloaded raw
output object. This review therefore does not invent a raw-output hash,
authenticated operator identity, or attested execution time.

Candidate absence and the 132-leaf roster are sequential path-visible
observations. This review does not claim an atomic snapshot, cache coherence,
future object-store stability, historical lineage, or universal immutability.

The runtime claim remains limited to wheel-selection ABI fields. The unobserved
native-target fields prevent a whole-profile, F151, or effective F153 claim.
The preflight also does not prove future dependency availability, F152
transitive/artifact closure, capacity, calibration, data admission, a Formal
Test, a result, or scientific readiness.

The supplied output does not separately prove that the preliminary launcher
run with no expected builder hash was performed. That omission does not defeat
the exact final hash-first execution evidence, but no separate preliminary-run
claim is made here.

## Project-state effect

The additive V2 Databricks preflight-execution checkpoint is complete, but no
operational checklist item closes.

- Marked tasks: **62 checked / 101 open / 163 total**
- Fields: **24 open / 148 closed**
- Blockers: **7 OPEN / 5 CLOSED**
- Formal Tests 28/29/30: **OPEN / OPEN / PENDING**
- Result slots: **0/4**
- F151/F152: **OPEN and null**
- B08 and Wave 2: **OPEN**

The next boundary is a separate exact-package-bound one-shot construction
authorization. This review establishes eligibility for that decision but does
not grant it.
