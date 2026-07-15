# Model Specification — Dual-Manifold Diffusion (DMD)

**Version 0.1 — draft for Raziyeh's review.** Every deliberate revision vs. the submitted manuscript is tagged **[R#]** with its rationale and the review weakness it fixes. Code implements this document and nothing else; when we change the math, we change this file first.

---

## 1. General problem

A data point is a coupled pair x₀ = (D₀, C₀) on a product space:

- **Discrete stream** D₀ ∈ V^N — a length-N sequence over vocabulary V (one-hot representation D₀ ∈ {0,1}^{N×|V|}), with an extra absorbing symbol `[MASK]` used only by the forward process.
- **Continuous stream** C₀ ∈ R^{N×K} — K real attributes attached to each sequence element.
- **Time map** Δ ∈ R₊^N — the *data-time* interval attached to each step (Δᵢ = physical time between element i−1 and i). **[R1]** Δ is now an explicit part of the data specification, not an implementation detail. This is what makes "continuous time" well-defined and testable (fixes W2's underspecification; enables irregular grids and the resolution-transfer experiment E1.4).

An **activity mask** M ∈ {0,1}^N marks elements whose continuous attributes are defined (e.g., sounding notes). **[R2]** Attributes at inactive positions are *undefined*, not zero (fixes W6/E4.4 ambiguity).

Goal: learn p(D₀, C₀) without collapsing either geometry (Hamming vs. Euclidean).

## 2. Music instantiation (Case Study A)

Flattened grid: N = T·P with T = 256 grid steps, P = 88 pitches; V = {off, on}; K = 2 (velocity v, micro-timing r).

- **Grid [R3]:** beat/downbeat positions from **ASAP annotations** where available; fallback: documented dynamic beat tracking. The grid step δᵢ is *local* (varies with tempo), so Δ is genuinely irregular. Replaces the manuscript's unspecified constant-tempo estimate (fixes W6/E4.1). The old fixed-δ grid is kept as a config option for backward comparison.
- Onset residual rᵢ = oᵢ − ôᵢ ∈ (−δᵢ/2, δᵢ/2], normalized as rᵢ/δᵢ ∈ (−½, ½]. **[R4]** Normalizing by the local grid step makes the channel tempo-invariant; raw milliseconds are recovered for metrics. Report half-grid wrap-around rate (E4.2).
- Velocity: MIDI [0,127] → v = velocity/127 ∈ [0,1]. **One convention everywhere; all reported W₁ in stated units** (fixes the W4 units inconsistency).
- Polyphony: for autocorrelation metrics, the deviation series is ordered by onset time with *chord groups* (|o_i − o_j| < 30 ms) handled two ways, both reported: (a) chord-mean series (tempo/phrasing structure), (b) within-chord asynchrony series (melody-lead structure). **[R5]** (fixes W6/E4.3).

## 3. Forward processes (shared diffusion index t = 1…T_d)

Discrete (absorbing D3PM): q(Dₜ|Dₜ₋₁) masks each token independently w.p. βₜ; closed-form marginal keeps a token unmasked at t w.p. ᾱᵗᴰ = Π(1−βₛ).

Continuous (VP): q(Cₜ|C₀) = N(√ᾱₜ C₀, (1−ᾱₜ)I) with cosine ᾱₜ. **Diffusion runs on all N positions; supervision does not (see §4).**

**Schedule alignment [R6]:** choose the mask schedule so both streams lose information at commensurate rates: set 1−ᾱᵗᴰ (mask probability) = 1−√ᾱₜ (default), with `schedule.alignment ∈ {sqrt_alpha, linear, independent}` as a config axis and a small ablation (P0.4; addresses the shared-t calibration question a reviewer would ask, cf. TabDiff's learned schedules).

Joint corruption factorizes given x₀ (manuscript Eq. 3, unchanged).

## 4. Objective

**Exact bound (for the paper's theory section):** manuscript Eqs. (4)–(6) are kept verbatim; both posterior and model factorize, per-step KL splits additively.

**Practical surrogate (what we train) [R7]:**

L = L_D + γ·L_C, with

- L_D: cross-entropy over *masked* positions with focal modulation (α_y, ρ) — stated *explicitly as a reweighted surrogate of* the D3PM term, not as the bound (resolves the W10 ELBO/focal tension; `loss.discrete ∈ {elbo_ce, focal}` so the bound-faithful variant is an ablation, not a rewrite).
- L_C = ‖M ⊙ (ε − ε_θ(Cₜ, D̃₀, Δ, t))‖² / max(ΣM, 1). **[R8]** The continuous loss is masked to active events; inactive positions carry pure noise through the network but contribute no gradient (fixes W6/E4.4; ablation flag `loss.supervise_silent` to quantify the old behavior).
- γ set so the two gradient norms match at init (recorded, not hand-tuned) **[R9]** — removes a magic number (W10).

## 5. Reverse process and coupling (unchanged in substance)

pθ(xₜ₋₁|xₜ) = pθ(Dₜ₋₁|xₜ) · pθ(Cₜ₋₁|xₜ, D̃₀), with Gumbel-Softmax bridge D̃₀ = softmax((l + g)/τ), τ annealed τ₀→τ_min (cosine), both logged. Coupling remains an adopted design (CoDi-style); ablation `coupling ∈ {gumbel, straight_through, detached, none}` gives the no-coupling control the review asked for implicitly (W10/E2.4-adjacent).

## 6. Temporal backbone — the block ladder **[R10]** (heart of the paper; fixes W2)

Shared trunk: a 12-layer transformer (attention + block) on N-position embeddings; diffusion-time embedding via FiLM/adaLN everywhere (identical across variants). Only the **block** differs, and the ladder isolates one factor per rung:

| Rung | Block | Adds | Question it answers |
|---|---|---|---|
| B0 | `ffn` — position-wise MLP | — | manuscript's Grid FFN |
| B1 | `ffn_timecond` — MLP with Δ,position features appended | time *input* | is a time signal enough? (manuscript control) |
| B2 | `gated_ffn` — GLU-style gate, no recurrence, no Δt | gating | **is the CFC gain just gating?** (new, required by W2) |
| B3 | `gru` — bidirectional GRU scan | recurrence | is it just sequential mixing? (new, required by W2) |
| B4 | `cfc` — bidirectional CFC scan (below) | closed-form continuous-time gate on Δt | the claim |
| B5 | `node` — Neural-ODE block (torchdiffeq, dopri5, tol/NFE logged) | solver-based continuous time | closed form vs. generic solver (manuscript control) |

**CFC block (exact) [R11].** Along the musical-time axis (per pitch lane for music; per point for handwriting), a bidirectional scan. Update at step i, with uᵢ = [xᵢ, hᵢ₋₁]:

  wᵢ = σ(−softplus(f(uᵢ)) · Δᵢ)   (decay gate; softplus ⇒ rate > 0)
  hᵢ = wᵢ ⊙ g(uᵢ) + (1 − wᵢ) ⊙ ĥ(uᵢ)

with f, g, ĥ small linear maps, h₀ learned. Forward and backward scans concatenated then projected (denoiser is non-causal). Two documented deviations from manuscript Eq. (8): the frozen h(0) becomes the recurrent carry hᵢ₋₁ inside uᵢ, and a third network ĥ replaces the raw initial state — this matches Hasani et al.'s CfC more faithfully; limits: Δᵢ→∞ ⇒ hᵢ→ĥ(uᵢ) (input-driven), Δᵢ→0 ⇒ hᵢ→½(g+ĥ)(uᵢ). Δ enters *only* here — so B4 vs. B3 isolates the continuous-time gate given recurrence, and B4 vs. B2 isolates it given gating.

**Parameter matching [R12]:** widths solved numerically per rung to equalize total trainable parameters within ±1% (utility in `dmd/utils/params.py`; matched counts logged to MLflow — makes the "matched capacity" claim auditable, W4/W10).

## 7. Sampling

DDIM (η=0, S steps, logged) for C conditioned on D̃₀; confidence-ordered iterative unmasking for D. **Calibration parity [R13]:** activation-rate calibration is a sampler flag applied uniformly to *every* model (including baselines) or to none; both settings reported (fixes W10/E2.4).

## 8. Domain adapters

- **Handwriting (IAM-OnDB):** N = stroke points; V = {char id × pen-state}; K = 2 (Δx, Δy, normalized); Δ = recorded inter-sample times (natively irregular). Same trunk, same ladder.
- **Tabular (negative control):** N = number of columns, no data-time ⇒ Δ undefined ⇒ CFC's gate has no time input and the scan order is arbitrary: the *architecture itself* predicts no CFC advantage. Pre-registered prediction for E3.2.

## 9. Spec ↔ agenda map

R1/R11 → W2, E1.3–E1.4 · R2/R8 → W6, E4.4 · R3–R5 → W6, E4.1–E4.3 · R6 → P0.4 · R7/R9 → W10 · R10/R12 → W2/W4 · R13 → W10, E2.4 · §8 → W8, E3.1–E3.2.

## 10. Sign-off checklist (Raziyeh)

1. Approve R3 (ASAP-annotated grid as default representation)?
2. Approve R8 (masked continuous loss) as the new default, old behavior as ablation?
3. Approve R11 (recurrent bidirectional CFC with ĥ network) — this *replaces* manuscript Eq. (8)?
4. Approve the B0–B5 ladder as the headline ablation table of the revised paper?
5. T_d (diffusion steps), S (DDIM steps), and trunk size: keep 1000/50/12×512 as defaults?
