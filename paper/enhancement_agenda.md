# Enhancement Agenda — From Music Paper to General Dual-Manifold Diffusion

**Target:** ICML 2027 (deadline expected late Jan 2027; not yet announced — confirm when posted; slip target: NeurIPS 2027).
**Scope decisions:** case studies = symbolic music (primary) + handwriting (IAM-OnDB) + tabular (negative control); large cluster available; listening study deferred honestly, replaced by an audio demo page.
**Working window:** ~27 weeks (Jul 15, 2026 → late Jan 2027), incl. 3 buffer weeks.

---

## 1. The reframed paper

**New thesis (general, falsifiable).** In joint generation of coupled discrete–continuous data, when the continuous stream carries *temporal* structure, the temporal parameterization of the denoiser's continuous pathway is the decisive design choice: closed-form continuous-time (CFC) units succeed where grid FFNs, time-conditioned FFNs, gated FFNs, and generic ODE solvers fail — **and the advantage vanishes on unordered (tabular) data.** The predicted dissociation is what elevates the claim from a music observation to a general principle.

**Structure of the revised paper.**

1. General formulation (domain-agnostic): state (D, C); bifurcated forward process; factorized joint ELBO; explicitly separated *practical* weighted surrogate objective (resolves the ELBO/focal tension, W10); Gumbel-Softmax coupling (adopted); CFC temporal block with fully specified Δt and h(0) semantics, including irregular Δt.
2. A careful definition of "continuous time" distinguishing **data-time** (our axis: the sequence is samples of a continuous-time signal) from **diffusion-time** (CTMC/flow-matching sense, e.g., Campbell et al. 2024). This turns the biggest related-work threat (W9) into a sharpened positioning: multimodal discrete–continuous flows are continuous in *generation* time; none models the continuous stream as a *data-time* signal.
3. Case Study A — symbolic piano performance (stringent, high-dimensional, expressive).
4. Case Study B — handwriting (discrete characters/pen-lifts + continuous trajectories; naturally irregular Δt).
5. Case Study C — tabular negative control (head-to-head with TabDDPM/CoDi/TabDiff; prediction: CFC ≈ FFN).
6. Analysis: what continuous-time dynamics buy (magnitude vs. structure), what remains open (autocorrelation), memorization checks.

**Name the model** (candidate: DMD — Dual-Manifold Diffusion; decide in Phase 5).

---

## 2. Phases, experiments, and deliverables

### Phase 0 — Specification & theory hardening (Weeks 1–2)

| ID | Item | Fixes |
|---|---|---|
| P0.1 | Write the general formulation section; scrub all music-specific language from Secs. 1–4. | W8 |
| P0.2 | Specify the CFC block exactly: what Δt is (data-time inter-step interval), what h(0) is, position-wise vs. recurrent application; add to paper + repo README. | W2, W10 |
| P0.3 | Restate objective: principled bound (Eq. 4–6) → then the *practical* surrogate (focal + γ), with an ablation slot for bound-faithful vs. surrogate training. | W10 |
| P0.4 | Schedule-alignment note: how the shared t calibrates mask-rate vs. SNR across streams (connect to TabDiff's learned schedules; small ablation later). | W10 |
| P0.5 | Hyperparameter registry: γ, focal α/ρ, τ annealing, β_t, DDIM steps, NODE solver/tolerance/NFE, optimizer, param-matching accounting. | W4, W10 |

### Phase 1 — Protect the core claim on music (Weeks 1–5) ⚠️ highest priority

| ID | Experiment | Fixes |
|---|---|---|
| E1.1 | **Calibrated-jitter baselines:** (a) quantized score + i.i.d. N(0, σ_H²) residuals; (b) AR(1) jitter matched to human σ *and* ρ₁. Add both rows to every timing table. | W1 |
| E1.2 | **Conditional timing analyses:** deviation vs. metrical position (downbeat lengthening), phrase position, chord asynchrony / melody lead, register. Report conditional W₁ for human / CFC / jitter / all backbones. | W1 |
| E1.3 | **Gated-FFN control** (GLU/highway, matched params) — is the CFC gain gating or continuous time? If CFC is applied recurrently: add **GRU control**. | W2 |
| E1.4 | **Resolution-transfer test:** train at s=4, sample/evaluate at s=8 and on beat-tracked *irregular* grids (variable Δt). Substantiates "interpolates between grid points." | W2 |
| E1.5 | Re-run the four original backbones at **5 seeds** with the finalized eval protocol (feeds Phase 4). | W4 |

**Gate G1 (end of Week 5).**
- If CFC > jitter on conditional metrics → proceed as planned (claims survive).
- If jitter ties CFC on all timing metrics → pivot the narrative: "matching rubato magnitude is trivial; *structure* is the open problem" — the paper becomes methodology + benchmark + dissociation, with conditional-structure metrics as the contribution. (Still publishable; arguably more interesting.) Everything downstream proceeds either way.

### Phase 2 — Fair baselines (Weeks 4–9)

| ID | Experiment | Fixes |
|---|---|---|
| E2.1 | AR baseline with **distributional head** (mixture-density / discretized-logistic) — the fair AR-vs-diffusion comparison. Retire the word "strong" for the deterministic one. | W3 |
| E2.2 | **SCHmUBERT-style all-discrete D3PM** (binned attributes) on our representation — the direct competitor for the "bins sacrifice nuance" claim. | W3, W7 |
| E2.3 | **VQ-VAE latent + diffusion baseline** — tests the *actual* latent quantization-gap hypothesis (joint codebook, not per-attribute bins). | W7 |
| E2.4 | **Calibration parity:** apply activation-rate calibration to all models or none; report both. | W10 |
| E2.5 | Engage performance-rendering line: run DExter (code available) on our splits if feasible; otherwise a careful positioning paragraph + metric alignment. | W3, W9 |

### Phase 3 — Generalization case studies (Weeks 6–14)

| ID | Experiment | Fixes |
|---|---|---|
| E3.1 | **Handwriting (IAM-OnDB):** discrete = characters + pen-lifts; continuous = pen offsets/velocities with real irregular Δt. Full backbone grid (grid/time-cond/gated/NODE/CFC), 5 seeds. Metrics: character accuracy/CER (structure), trajectory W₁ + velocity ACF (attributes: magnitude *and* structure). | W8 |
| E3.2 | **Tabular dissociation (Adult, Cardio, + 1 more):** same grid vs. TabDDPM/CoDi/TabDiff. **Pre-register the prediction: CFC ≈ FFN here.** Standard tabular metrics (marginal/W₁, correlation, ML-efficiency). | W8, W9 |
| E3.3 | Unified cross-domain metric protocol: every domain reports (i) discrete fidelity, (ii) continuous marginal distance, (iii) continuous *temporal-structure* distance (ACF/spectral). | W8, W4 |

### Phase 4 — Representation validity & statistics overhaul (Weeks 4–16, continuous track)

| ID | Item | Fixes |
|---|---|---|
| E4.1 | **Replace estimated beat grid with ASAP annotations** (beat/downbeat-annotated MAESTRO subset). Compare: does human ρ₁ rise above 0.12 on a true grid? (If yes, the old grid was destroying structure — report it.) Document the beat-grid method for the remainder. | W6 |
| E4.2 | Round-trip validation: performance → (score, residuals) → performance; report reconstruction error, half-grid wrap-around rate. | W6 |
| E4.3 | Define polyphony handling: ordering of the deviation series for ρ₁, chord-tone treatment; report data ACF vs. lag (not just lag-1) and vs. metrical position. | W6 |
| E4.4 | Document silent-position handling of C (mask the Gaussian loss to active events; ablate if time permits). | W6 |
| E4.5 | Quantization sweep redo: state retrain-vs-post-hoc, add variance + tests, scope the claim to per-attribute binning; E2.3 covers the latent case. | W7 |
| E4.6 | **Statistics:** 5 seeds on all headline tables; mean ± sd in *every* cell; bootstrap CIs over eval excerpts; paired tests where meaningful (state test, n, p); state eval-set size; **human-vs-human noise-floor row in every table**; velocity units fixed (MIDI [0,127] vs. [0,1] — one convention everywhere). | W4 |
| E4.7 | Memorization/novelty check: n-gram & excerpt overlap vs. MAESTRO train. | W10 |
| E4.8 | Report every promised metric or delete the promise: FMD, OA, groove, IOI-W₁, MusPy descriptors in an appendix table. | W5 |

### Phase 5 — Positioning, writing, artifacts (Weeks 12–18)

| ID | Item | Fixes |
|---|---|---|
| P5.1 | Related work rewrite: add Campbell et al. 2022 (CTMC discrete diffusion), Campbell et al. ICML 2024 (multimodal DFM), CDCD, discrete flow matching; performance-rendering line (DExter, ScorePerformer, VirtuosoNet, basis-function models); data-time vs. diffusion-time framing (§1 above). | W9 |
| P5.2 | **Verify or replace refs [3], [4]** (could not be located; likely placeholders) + full bibliography audit. | W9 |
| P5.3 | Rewrite §5.3/§6.8: listening study explicitly moved to future work; **build audio demo page** (all systems, identical synthesis) + handwriting sample gallery. | W5 |
| P5.4 | Code release: repo with configs, seeds, eval scripts, hyperparameter registry (P0.5); wall-clock table incl. CFC-vs-NODE cost. | W10 |
| P5.5 | Full restructure per §1; fix minors (Fig. 2 tick typo, doubled periods, "best in bold" consistency, h(0) definition, model name). | W4, W10 |

### Phase 6 — Red-team, finalize, submit (Weeks 18–27)

| ID | Item |
|---|---|
| P6.1 | Freeze experiments (Week 20); final stats pass. |
| P6.2 | **Internal red-team review:** re-review the full draft against the original referee report, weakness by weakness (I re-run the reviewer pass); external lab read. |
| P6.3 | Reproducibility checklist, impact statement, ICML formatting; confirm actual ICML 2027 deadline when announced. |
| P6.4 | Buffer (3 weeks) → submit. If G1 pivot happened, revisit title/claims here. |

---

## 3. Weakness-coverage matrix

| Review weakness | Covered by |
|---|---|
| W1 trivial jitter explanation | E1.1, E1.2, Gate G1 |
| W2 mechanism unidentified (gating confound, Δt, interpolation claim) | P0.2, E1.3, E1.4 |
| W3 AR strawman; no prior-system comparisons | E2.1, E2.2, E2.5 |
| W4 statistics (seeds, dispersion, tests, eval size, noise floor, units) | E1.5, E4.6, E3.3, P5.5 |
| W5 missing promised metrics; listening-study inconsistency | E4.8, P5.3 |
| W6 representation validity (beat grid, polyphony, silent positions, round-trip) | E4.1–E4.4 |
| W7 quantization test ≠ latent-VQ hypothesis | E2.3, E4.5 |
| W8 generality gap | P0.1, E3.1–E3.3 (the pivot itself) |
| W9 related-work gaps; refs [3]/[4] | P5.1, P5.2, §1 data-time framing |
| W10 reproducibility; ELBO/focal tension; calibration parity; memorization | P0.2–P0.5, E2.4, E4.7, P5.4 |

---

## 4. Division of labor (you + me)

**I can produce in these sessions:** the jitter-baseline and conditional-timing evaluation code (E1.1/E1.2 are pure post-processing on generated MIDI — no GPU needed); the gated-FFN and CFC-block reference implementations (E1.3/P0.2); the unified metrics package (E3.3, E4.6 bootstrap/tests); rewritten paper sections (P0.1, P5.1, P5.3, P5.5); the demo-page skeleton; and the red-team re-review (P6.2).

**Needs your lab:** all GPU training runs, MAESTRO/ASAP/IAM-OnDB data access and pipelines, cluster scheduling, code release under your names, and any decisions at Gate G1.

**Standing cadence suggestion:** weekly — you bring run results, we analyze together, I update tables/sections; Gate G1 review end of Week 5 (≈ Aug 19).

---

## 5. Risk register

| Risk | Mitigation |
|---|---|
| Jitter baseline ties CFC (G1) | Pre-planned narrative pivot (§Phase 1); conditional-structure metrics become the contribution. |
| CFC gain disappears vs. gated FFN | Report honestly; paper becomes "gating, not continuous time" — still a publishable finding with the dissociation design. |
| ASAP grid changes human ρ₁ a lot | That is itself a result (representation artifact); fold into E4.1 analysis. |
| IAM-OnDB pipeline slower than planned | Quick, Draw! as drop-in fallback (simpler format, same structure). |
| ICML 2027 deadline earlier than expected | Phase order is priority order; Phases 0–2 alone + tabular control make a submittable core. NeurIPS 2027 as slip. |
