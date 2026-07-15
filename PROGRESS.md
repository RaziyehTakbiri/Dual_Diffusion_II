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
| 2026-07-15 | **Operating mode change:** Raziyeh delegates decision authority; Claude picks best actions optimizing for ICML-level manuscript; only irreversible/budget-heavy calls escalated | Standing instruction |
| 2026-07-15 | **Spec v0.2 decided (Option A):** tempo curve = generated per-step channel C^step=log(δ/δ̄) [R14]; Δ-feedback sampling [R15]; s=4 kept, s=12 = appendix ablation [R16]; Δ-feedback de-risked via block-expressivity probe before full training | Aims the ladder at the strongest structure (ρ₁≈0.64); structurally defeats W1 jitter objection; publishable mechanism; negligible compute |
| 2026-07-15 | **Central empirical reframing:** rubato's temporal structure lives in the beat-level TEMPO CURVE (ρ₁≈0.64, style-dependent), NOT in grid residuals (ρ₁≈−0.06 uniformly = quantization artifact on any sixteenth grid). The manuscript's open problem ("no model captures rubato structure, human ρ₁≈0.12") was measuring the wrong quantity. | New target metrics: tempo-curve ACF, chord asynchrony, residual σ (stratified). Spec v0.2 question raised: should the model GENERATE the tempo curve (log-Δ as a third continuous channel)? → Raziyeh to decide |

## Run log (Databricks)
| Date | Run/Experiment | Config/seeds | Metrics file in `results/` | Notes |
|---|---|---|---|---|
| 2026-07-15 | **E4.1b score-aligned micro-timing** (run locally by Claude; stdlib MIDI reader cross-validated vs pretty_midi: 0.019% note-count diff; synthetic ground-truth tests 4/4) | 1036/1067 aligned (31 skips = ASAP's documented unaligned perfs), 16 s | `score_align_asap.{csv,json}` | **Note-level micro-timing IS structured: ρ₁=0.39±0.19 (all), 0.24±0.17 (duple-only)** vs −0.06 on grid residuals — the structure was real, the grid instrument destroyed it. σ=49 ms (43 duple); 28% of notes non-duple (triplets/ornaments — the artifact source, quantified). Asynchrony σ=27 ms (score-exact chords). Unbiased (median 0.00 ms); match rate 92%. Per-composer duple ρ₁ uniformly positive (0.18–0.28); σ scales Bach 25→Ravel 72 ms. Caveats: beat annotations derived from performances (on-beat deviations partly absorbed); greedy matching noise attenuates ρ (estimates conservative). |
| 2026-07-15 | E4.1 human-ACF study, **ASAP grid**, 1067 perfs / 3.59M notes | grid=asap, s=4, paired map | `human_acf_asap.{csv,json}` | σ=43.2±31.5 ms (WORSE than fixed!), ρ₁=−0.055±0.150 — **uniformly negative across all composers** → measurement artifact: subdivision–rhythm mismatch (triplets/ornaments/runs land between sixteenth cells; collisions blow up for ornamental composers: Liszt 4.2%, Ravel 5.4%). Asynchrony 14.8 ms behaves like true signal (Bach 9.7 → Ravel 21.8, musically sensible gradient). |
| 2026-07-15 | **E4.1b tempo-curve study (beat annotations only — no grid)** | 1067 perfs, all beats | `tempo_curve_asap.{csv,json}` | **THE REAL STRUCTURE: tempo-curve ρ₁=0.64±0.22**, slow decay (ρ₈=0.36); style-dependent exactly as musicology predicts (Bach 0.37 < Chopin 0.53 < Liszt 0.67) while residual-channel ρ₁ is uniformly ≈−0.06 (artifact). Median period CV 0.26. Macro-rubato structure lives at the BEAT level, not in grid residuals. |
| 2026-07-15 | E4.3 human-ACF study, **fixed grid**, full MAESTRO v3 | grid=fixed, s=4, 1276 pieces / 7.04M notes, 0 skipped | `human_acf_fixed.{csv,json}` | σ=35.9±18.5 ms (median 33.8; 76% of pieces in 25–45 ms ≈ δ/√12 saturation band → residuals dominated by ALIASED TEMPO DRIFT, not note-level rubato). ρ₁=0.074±0.147 (median 0.085; 25% of pieces negative) — manuscript's "σ≈20 ms, ρ₁≈0.12" does NOT reproduce; old targets were estimator-dependent. corr(σ,ρ₁)=0.19 (drift inflates both). **Clean signal: within-chord asynchrony σ=18.6±4.8 ms** — grid-robust, matches melody-lead literature. Round-trip on real data: onset err ≤1e-5 ms, keep 99.7% (min 90.1%), wraps 0. |

## Session log
| Date | Done | Next |
|---|---|---|
| 2026-07-15 | Paper read & reviewed (see `reviews/`); agenda agreed; project folder + tracker created | R: drop codebase, generated samples, held-out set into folder. Claude: E1.1/E1.2 metrics core |
| 2026-07-15 (later) | From-scratch rebuild decided. MODEL_SPEC v0.1 written (10 tagged revisions R1–R13). Repo scaffolded; milestone M1 done: B0–B5 temporal blocks + param matching + CPU test suite (syntax-checked; param-match tolerances verified analytically at d=128 and d=512 — all rungs ≤0.4%). PyPI unreachable in Claude's sandbox, so pytest execution is on R. | R: review Spec §10 checklist + run `pytest tests/`. Claude: M2 (representation + round-trip validator + human ACF study) |
| 2026-07-15 (tex) | Original manuscript .tex received → `paper/original_manuscript.tex` (752 lines, Elsevier MLWA class). Confirms W10: γ, τ, optimizer, schedules appear only symbolically — no numeric hyperparameters anywhere. ASAP tooling added: verified TSV parser, `asap_map.py` generator, paired-comparison filter in `human_acf`; suite now 11/11. | — |
| 2026-07-15 (M2) | Spec v0.1 **approved** (all §10 items); M1 tests green on R's machine. **M2 built and 10/10 ground-truth tests pass in Claude's sandbox** (numpy available there): representation encode/decode (exact round-trip), fixed-grid estimator (two-stage: IOI comb with signed-cosine score + unwrap/regression — first version had a real harmonic-locking bug, caught by the tests), chord grouping, ACF, metrical profile, `build_music` dataset builder, `human_acf` study script. E4.1 preview on synthetic drifting-tempo data: true-grid measurement exact (σ 14.9/15.0, ρ₁ 0.59/0.60); legacy fixed grid inflates σ 2.4× — the manuscript's human ρ₁≈0.12 is now formally suspect. | R: run human_acf + build_music on MAESTRO (fixed grid) and drop outputs into `results/`; secure ASAP. Claude: M3 (forward processes + objective) |

---

**M4 status (2026-07-15, done):** `dmd/models/denoiser.py` (DiT trunk: token
per grid step, adaLN-Zero, ladder in the FFN slot, dual heads, Gumbel/ST/
detached/none coupling modes) + `tests/test_denoiser.py` (coupling-gradient
proof, Δ-propagation dissociation, whole-model param matching) +
`notebooks/03_m4_checks` incl. the [R15] Δ-feedback de-risk probe (block
expressivity on synthetic AR(1) tempo curves; decides whether Δ-feedback is
core mechanism or ablation). Torch tests await R's cluster. E4.1b tools:
`midi_lite.py` (stdlib MIDI reader, cross-validated), `score_align.py`
(tests 4/4, full-corpus run complete).

## Next actions
1. **Raziyeh (top priority — critical path, E4.1):** ASAP recipe (no MAESTRO
   mapping needed; the repo contains all performance MIDIs + annotations):
   a. Get https://github.com/fosfrancesco/asap-dataset onto Databricks
      (git clone or zip download; ~no audio needed; CC BY-NC-SA, cite
      Foscarin et al. 2020).
   b. In a notebook: `from dmd.data.asap_map import main;
      main(["--asap_root", "<asap>", "--out", "<out>/asap_map.csv"])`
      (expect ≈1067 pairs).
   c. Rerun `01_m2_data_audit` with `MIDI_GLOB = "<asap>/**/*.mid*"`,
      `GRID = "asap"`, `ANNOTATION_MAP = "<out>/asap_map.csv"`.
   d. Rerun once more with `GRID = "fixed"` and the SAME map (the map now
      also filters the file set → paired comparison on identical pieces).
   e. Drop all four output files into `results/`.
   Parser is now VERIFIED against the ASAP README format (compound labels
   `db,4/4`, `bR` beats included; unit-tested). Note: subdivision = beat/4
   everywhere, incl. compound meters (documented simplification).
2. **Raziyeh:** confirm whether the full run also executed the dataset-build
   cell (`SMOKE = False` → `maestro_fixed_{train,validation,test}.npz` +
   `maestro_fixed_audit.csv` on Databricks). If yes, drop the audit CSV into
   `results/`; the .npz stay on Databricks for M5 training.
3. **Raziyeh (Databricks, ML runtime, ~5 min):** run `03_m4_checks` (it
   supersedes 02 — runs the full suite M1–M4 as its gate, then the Δ-feedback
   probe). Paste the probe table + read-out cell output into chat or drop
   into `results/`. This is the only thing blocking on your side.
4. **Claude (next session):** decide [R15] core-vs-ablation from the probe;
   M5 training harness (TorchDistributor + MLflow, γ grad-matching at init,
   config-diff enforcement) + M6 sampler (DDIM + calibrated unmasking +
   Δ-feedback loop) + v0.2 data loader (log-Δ channel from the existing
   ASAP npz). Then the first real training smoke run.

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
