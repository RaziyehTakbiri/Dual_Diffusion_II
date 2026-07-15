# Dual-Manifold Diffusion — Progress Tracker

**Target:** ICML 2027 (deadline TBA, expect late Jan 2027 — confirm when CFP posts; slip: NeurIPS 2027)
**Gate G1:** ≈ Aug 19, 2026 (jitter + gated-FFN controls decide claim survival)
**Roles:** Claude = math/proofs/code/writing · Raziyeh = Databricks GPU runs, data access, verification & sign-off
**Repo layout:** `paper/` manuscript & agenda · `code/` deliverable scripts · `results/` metrics exports from Databricks · `data/` samples & format specs · `reviews/` referee reports

**Status legend:** ☐ pending · ▶ in progress · ✔ done · ✖ blocked

---

## Status board

### Phase 0 — Specification & theory (Wk 1–2)
| ID | Item | Owner | Status | Notes |
|---|---|---|---|---|
| P0.1 | General (domain-agnostic) formulation section | Claude | ▶ | Spec §1–§5 drafted; paper prose pending |
| P0.2 | Exact CFC block spec (Δt, h(0), wiring) | Claude | ✔ | `paper/MODEL_SPEC.md` §6 [R11]; awaiting R sign-off |
| P0.3 | Bound vs. practical surrogate restatement | Claude | ✔ | Spec §4 [R7–R9] |
| P0.4 | Schedule-alignment note (shared t) | Claude | ✔ | Spec §3 [R6]; ablation axis in configs |
| P0.5 | Hyperparameter registry | Claude | ✔ | Lives in configs/ (single-read convention); grows with modules |

### Phase 1 — Core-claim protection, music (Wk 1–5) ⚠️ critical path
| ID | Item | Owner | Status | Notes |
|---|---|---|---|---|
| E1.1 | Calibrated-jitter baselines (iid + AR(1)) | Claude code / R runs | ☐ | No GPU needed; needs generated samples + held-out set |
| E1.2 | Conditional timing analyses | Claude code / R runs | ☐ | Same inputs as E1.1 |
| E1.3 | Gated-FFN (+GRU) control | Claude code / R trains | ▶ | Blocks implemented (`code/dmd/blocks/temporal.py`, B0–B5 ladder); training harness pending (M5) |
| E1.4 | Resolution-transfer test (s=4→8, irregular Δt) | Claude code / R trains | ☐ | |
| E1.5 | Re-run 4 backbones, 5 seeds, final protocol | R (Databricks) | ☐ | |
| G1 | **Decision gate** | Both | ☐ | Due ≈ Aug 19 |

### Phase 2 — Fair baselines (Wk 4–9)
| ID | Item | Owner | Status | Notes |
|---|---|---|---|---|
| E2.1 | Distributional-head AR (MDN/disc-logistic) | Claude code / R trains | ☐ | |
| E2.2 | SCHmUBERT-style all-discrete baseline | Claude code / R trains | ☐ | |
| E2.3 | VQ-VAE latent + diffusion baseline | Claude code / R trains | ☐ | |
| E2.4 | Calibration parity (all models or none) | Claude | ☐ | |
| E2.5 | DExter comparison / positioning | Claude | ☐ | |

### Phase 3 — Generalization (Wk 6–14)
| ID | Item | Owner | Status | Notes |
|---|---|---|---|---|
| E3.1 | Handwriting (IAM-OnDB) full grid, 5 seeds | Claude code / R trains | ☐ | R: check IAM-OnDB license/access |
| E3.2 | Tabular dissociation vs TabDDPM/CoDi/TabDiff | Claude code / R trains | ☐ | Prediction pre-registered: CFC ≈ FFN |
| E3.3 | Unified cross-domain metric protocol | Claude | ☐ | |

### Phase 4 — Representation & statistics (Wk 4–16)
| ID | Item | Owner | Status | Notes |
|---|---|---|---|---|
| E4.1 | ASAP beat-annotated grid; recompute human ρ₁ | Claude code / R runs | ▶ | Code ready (`--grid asap`); synthetic preview: drifting tempo on a fixed grid inflates σ 15→36 ms and distorts ρ₁ — manuscript's human numbers likely grid artifacts. Needs ASAP data |
| E4.2 | Round-trip representation validation | Claude code / R runs | ✔ | Validated on full MAESTRO: onset err ≤1e-5 ms, keep 99.7%, collisions 0.34% — representation is effectively lossless |
| E4.3 | Polyphony/ACF definitions + data ACF study | Claude code / R runs | ✔ (fixed-grid arm) | Full-corpus numbers in run log. Fixed-grid σ sits at the δ/√12 saturation → drift-aliased; ρ₁ heterogeneous (sd 0.15, 25% negative). ASAP arm (E4.1) now carries the structure story. NEW metric adopted for M7: within-chord asynchrony realism (18.6 ms human target, grid-robust) |
| E4.4 | Silent-position loss handling documented | Claude | ✔ | Resolved by design: masked L_C is the new default (Spec [R8]); legacy behavior kept as ablation flag |
| E4.5 | Quantization sweep redo (variance, scope) | R (Databricks) | ☐ | |
| E4.6 | Stats overhaul (5 seeds, CIs, tests, noise floors, units) | Claude code / R runs | ☐ | |
| E4.7 | Memorization/novelty check | Claude code / R runs | ☐ | |
| E4.8 | All promised metrics (FMD, OA, groove, IOI, MusPy) | Claude code / R runs | ☐ | |

### Phase 5 — Positioning & artifacts (Wk 12–18)
| ID | Item | Owner | Status | Notes |
|---|---|---|---|---|
| P5.1 | Related-work rewrite (data-time vs diffusion-time) | Claude | ☐ | |
| P5.2 | Fix refs [3],[4] + bibliography audit | Claude | ☐ | Flagged as unlocatable 2026-07-15 |
| P5.3 | §5.3/§6.8 rewrite + audio demo page | Claude | ☐ | |
| P5.4 | Code release prep + wall-clock table | Both | ☐ | |
| P5.5 | Full manuscript restructure + minors | Claude | ☐ | |

### Phase 6 — Red-team & submit (Wk 18–27)
| ID | Item | Owner | Status | Notes |
|---|---|---|---|---|
| P6.1 | Experiment freeze + final stats | Both | ☐ | Target Wk 20 |
| P6.2 | Internal red-team re-review | Claude | ☐ | |
| P6.3 | Checklist, disclosure, formatting | Both | ☐ | Check ICML AI-assistance policy |
| P6.4 | Submit | R | ☐ | |

---

## Decision log
| Date | Decision | Rationale |
|---|---|---|
| 2026-07-15 | Target ICML 2027; NeurIPS 2027 as slip | Scope needs ~6 months; ICLR 2027 (Sep 24) too tight |
| 2026-07-15 | Reframe as general dual-manifold method; music = case study | Fixes W8; dissociation prediction (CFC helps temporal, not tabular) makes claim falsifiable |
| 2026-07-15 | Case studies: music + handwriting (IAM-OnDB) + tabular control | Temporal fit + negative control; Quick,Draw! as fallback |
| 2026-07-15 | Listening study deferred honestly; audio demo page instead | ML-venue methods paper; fixes W5 |
| 2026-07-15 | Claude produces math/code/writing; Raziyeh runs on Databricks + verifies | This session |
| 2026-07-15 | **Pipeline rebuilt from scratch**; old codebase not used | Model & configs being revised anyway; spec-first workflow (`paper/MODEL_SPEC.md` is source of truth, code implements it) |
| 2026-07-15 | Headline ablation = B0–B5 ladder (ffn → +time input → +gating → +recurrence → CFC → ODE) | Each rung isolates one factor; kills the W2 gating/recurrence confounds by construction |
| 2026-07-15 | Masked continuous loss [R8], ASAP grid [R3], recurrent bidirectional CFC [R11] proposed as new defaults | Pending Raziyeh sign-off (Spec §10 checklist) |
| 2026-07-15 | **Manuscript's human timing targets (σ≈20 ms, ρ₁≈0.12) declared unreliable** — full-corpus fixed-grid measurement gives σ≈36 ms at the drift-aliasing saturation, ρ₁≈0.07 with huge cross-piece spread | All revised-paper timing targets will be re-derived: magnitude + structure from the ASAP grid (E4.1); within-chord asynchrony (σ≈18.6 ms) adopted as an additional grid-robust target metric |

## Run log (Databricks)
| Date | Run/Experiment | Config/seeds | Metrics file in `results/` | Notes |
|---|---|---|---|---|
| 2026-07-15 | E4.3 human-ACF study, **fixed grid**, full MAESTRO v3 | grid=fixed, s=4, 1276 pieces / 7.04M notes, 0 skipped | `human_acf_fixed.{csv,json}` | σ=35.9±18.5 ms (median 33.8; 76% of pieces in 25–45 ms ≈ δ/√12 saturation band → residuals dominated by ALIASED TEMPO DRIFT, not note-level rubato). ρ₁=0.074±0.147 (median 0.085; 25% of pieces negative) — manuscript's "σ≈20 ms, ρ₁≈0.12" does NOT reproduce; old targets were estimator-dependent. corr(σ,ρ₁)=0.19 (drift inflates both). **Clean signal: within-chord asynchrony σ=18.6±4.8 ms** — grid-robust, matches melody-lead literature. Round-trip on real data: onset err ≤1e-5 ms, keep 99.7% (min 90.1%), wraps 0. |

## Session log
| Date | Done | Next |
|---|---|---|
| 2026-07-15 | Paper read & reviewed (see `reviews/`); agenda agreed; project folder + tracker created | R: drop codebase, generated samples, held-out set into folder. Claude: E1.1/E1.2 metrics core |
| 2026-07-15 (later) | From-scratch rebuild decided. MODEL_SPEC v0.1 written (10 tagged revisions R1–R13). Repo scaffolded; milestone M1 done: B0–B5 temporal blocks + param matching + CPU test suite (syntax-checked; param-match tolerances verified analytically at d=128 and d=512 — all rungs ≤0.4%). PyPI unreachable in Claude's sandbox, so pytest execution is on R. | R: review Spec §10 checklist + run `pytest tests/`. Claude: M2 (representation + round-trip validator + human ACF study) |
| 2026-07-15 (M2) | Spec v0.1 **approved** (all §10 items); M1 tests green on R's machine. **M2 built and 10/10 ground-truth tests pass in Claude's sandbox** (numpy available there): representation encode/decode (exact round-trip), fixed-grid estimator (two-stage: IOI comb with signed-cosine score + unwrap/regression — first version had a real harmonic-locking bug, caught by the tests), chord grouping, ACF, metrical profile, `build_music` dataset builder, `human_acf` study script. E4.1 preview on synthetic drifting-tempo data: true-grid measurement exact (σ 14.9/15.0, ρ₁ 0.59/0.60); legacy fixed grid inflates σ 2.4× — the manuscript's human ρ₁≈0.12 is now formally suspect. | R: run human_acf + build_music on MAESTRO (fixed grid) and drop outputs into `results/`; secure ASAP. Claude: M3 (forward processes + objective) |

---

## Next actions
1. **Raziyeh (top priority — critical path):** secure ASAP annotations and
   rerun `01_m2_data_audit` with `GRID = "asap"` + `ANNOTATION_MAP`. The
   fixed-grid arm is done and shows drift aliasing; ONLY the ASAP grid can now
   give the paper's true human rubato magnitude + structure (E4.1). Verify
   `beats_from_annotation_txt` against a real ASAP file (marked VERIFY).
2. **Raziyeh:** confirm whether the full run also executed the dataset-build
   cell (`SMOKE = False` → `maestro_fixed_{train,validation,test}.npz` +
   `maestro_fixed_audit.csv` on Databricks). If yes, drop the audit CSV into
   `results/`; the .npz stay on Databricks for M5 training.
3. **Raziyeh (Databricks, ML runtime cluster, ~2 min):** run
   `02_m3_checks` notebook (.py or .ipynb) — executes the FULL test suite
   (M1+M2+M3) with torch. It's a gate, nothing to download; report any
   failure verbatim.
4. **Claude (next session):** M4 — denoiser trunk (transformer + adaLN
   diffusion-time conditioning, block ladder slot-in, structure/continuous
   heads, Gumbel-Softmax bridge) + tests, then M5 training harness
   (TorchDistributor + MLflow). Also: within-chord asynchrony metric goes
   into the M7 suite (adopted target: human 18.6 ms).

**M3 status (2026-07-15, done):** `dmd/diffusion/{schedules,forward,objective}.py`
+ `tests/test_diffusion.py` + `notebooks/02_m3_checks`. Schedule math verified
numerically in-sandbox (numpy mirror): β-chain reproduces marginal m_t to
<0.001; linear-schedule ELBO weight w_t = 1/t anchor exact; alignment
identities hold. Torch execution pending on R's side (sandbox has no torch).
Key design points: bound-faithful `elbo_ce` mode with derived absorbing-chain
weight (m_t−m_{t−1})/m_t [R7]; continuous loss masked to active events with
`supervise_silent` legacy ablation [R8]; γ via gradient-norm matching helper
[R9]; alignment axis {sqrt_alpha, alpha, linear} [R6].

**Standing convention (2026-07-15):** Raziyeh runs everything through Databricks
*notebooks*, never a terminal. Every runnable module keeps a `main(argv)`
function; each milestone ships a driver notebook in `code/notebooks/`
(Databricks source format). Multi-GPU training will use TorchDistributor.
