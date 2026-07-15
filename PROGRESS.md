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
| E4.2 | Round-trip representation validation | Claude code / R runs | ▶ | Validator done; every `build_music` run emits an audit CSV. Awaiting first MAESTRO run |
| E4.3 | Polyphony/ACF definitions + data ACF study | Claude code / R runs | ▶ | `human_acf.py` done: chord-mean vs within-chord asynchrony split [R5], ACF lags 1–8, metrical profile. Awaiting first MAESTRO run |
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

## Run log (Databricks)
| Date | Run/Experiment | Config/seeds | Metrics file in `results/` | Notes |
|---|---|---|---|---|
| — | — | — | — | — |

## Session log
| Date | Done | Next |
|---|---|---|
| 2026-07-15 | Paper read & reviewed (see `reviews/`); agenda agreed; project folder + tracker created | R: drop codebase, generated samples, held-out set into folder. Claude: E1.1/E1.2 metrics core |
| 2026-07-15 (later) | From-scratch rebuild decided. MODEL_SPEC v0.1 written (10 tagged revisions R1–R13). Repo scaffolded; milestone M1 done: B0–B5 temporal blocks + param matching + CPU test suite (syntax-checked; param-match tolerances verified analytically at d=128 and d=512 — all rungs ≤0.4%). PyPI unreachable in Claude's sandbox, so pytest execution is on R. | R: review Spec §10 checklist + run `pytest tests/`. Claude: M2 (representation + round-trip validator + human ACF study) |
| 2026-07-15 (M2) | Spec v0.1 **approved** (all §10 items); M1 tests green on R's machine. **M2 built and 10/10 ground-truth tests pass in Claude's sandbox** (numpy available there): representation encode/decode (exact round-trip), fixed-grid estimator (two-stage: IOI comb with signed-cosine score + unwrap/regression — first version had a real harmonic-locking bug, caught by the tests), chord grouping, ACF, metrical profile, `build_music` dataset builder, `human_acf` study script. E4.1 preview on synthetic drifting-tempo data: true-grid measurement exact (σ 14.9/15.0, ρ₁ 0.59/0.60); legacy fixed grid inflates σ 2.4× — the manuscript's human ρ₁≈0.12 is now formally suspect. | R: run human_acf + build_music on MAESTRO (fixed grid) and drop outputs into `results/`; secure ASAP. Claude: M3 (forward processes + objective) |

---

## Next actions
1. **Raziyeh (Databricks notebook, CPU, ~minutes):** import
   `code/notebooks/01_m2_data_audit.py` (Databricks source format — renders as
   a notebook on import) **or** `01_m2_data_audit.ipynb` (identical Jupyter
   twin, auto-generated by `notebooks/_to_ipynb.py`) into Databricks,
   set `CODE_DIR` / `MIDI_GLOB` / `MAESTRO_CSV` in the config cell,
   run with `SMOKE = True`, then `SMOKE = False`. It runs the 10 ground-truth
   tests, the human-ACF study (E4.3), and the dataset build + audit (E4.2).
   Download the 3 listed output files into `results/` here. These are the
   paper's new ground-truth human numbers (fixed grid).
2. **Raziyeh:** secure ASAP annotations → rerun the notebook with
   `GRID = "asap"` + `ANNOTATION_MAP`; the fixed-vs-ASAP delta is the E4.1
   result. Verify `beats_from_annotation_txt` against real ASAP files (parser
   marked VERIFY in code).
3. **Claude (next session):** M3 — forward processes (absorbing + VP, schedule
   alignment [R6]) and the masked objective [R7–R9], with CPU statistical
   tests (marginal laws, ELBO term sanity), plus driver notebook
   `02_m3_checks.py` in the same pattern.

**Standing convention (2026-07-15):** Raziyeh runs everything through Databricks
*notebooks*, never a terminal. Every runnable module keeps a `main(argv)`
function; each milestone ships a driver notebook in `code/notebooks/`
(Databricks source format). Multi-GPU training will use TorchDistributor.
