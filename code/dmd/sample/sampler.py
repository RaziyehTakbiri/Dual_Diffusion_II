"""Ancestral sampler: DDIM (continuous) + confidence-ordered unmasking
(discrete) + Δ-feedback [R15] (MODEL_SPEC §7, v0.2).

Reverse loop over a strided subset of t = T_d..1:
  1. model(D_t, C_t, Δ̂, t) -> logits, eps
  2. x0-estimates: Ĉ0 = (C_t - sqrt(1-ᾱ)·ε̂)/sqrt(ᾱ)
  3. **Δ-feedback**: Δ̂ <- stats-inverse of Ĉ0^step (clamped to a plausible
     tempo range), refreshed EVERY step - grid geometry is generated, not given
  4. discrete: unmask positions so the unmasked fraction tracks 1 - m_t;
     among masked cells, reveal the most confident; values sampled from the
     predicted x0 distribution (temperature 1). `calibrate=True` additionally
     tempers the on/off decision so the running activation rate tracks
     `target_rate` - the [R13] flag; parity across models is enforced by the
     experiment configs, never hardcoded.
  5. continuous: deterministic DDIM step (eta=0) toward t_next.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import torch
import torch.nn.functional as F

from dmd.data.loader import CorpusStats, step_channel_to_delta
from dmd.diffusion.schedules import ScheduleTables


@dataclass
class SampleResult:
    D: torch.Tensor        # (B, T, P) long {0,1}
    C_pitch: torch.Tensor  # (B, T, P, K) standardized scale
    C_step: torch.Tensor   # (B, T, 1)
    delta: torch.Tensor    # (B, T) seconds (from Δ-feedback inverse)


@torch.no_grad()
def generate(model, tables: ScheduleTables, stats: CorpusStats,
             B: int, T: int, P: int, K: int = 2,
             steps: int = 50, tau: float = 0.5,
             calibrate: bool = True, target_rate: float = 0.03,
             delta_feedback: bool = True, delta_uniform_s: float = 0.125,
             seed: int = 0, device: str = "cpu") -> SampleResult:
    g = torch.Generator(device="cpu").manual_seed(seed)
    dev = torch.device(device)
    MASK = 2

    D = torch.full((B, T, P), MASK, dtype=torch.long, device=dev)
    Cp = torch.randn(B, T, P, K, generator=g).to(dev)
    Cs = torch.randn(B, T, 1, generator=g).to(dev)
    delta = torch.full((B, T), delta_uniform_s, device=dev)

    ts = torch.linspace(tables.T_d, 1, steps).round().long().unique_consecutive()
    ab = tables.alpha_bar.to(dev)
    m = tables.m.to(dev)

    for k, t_cur in enumerate(ts):
        t_next = ts[k + 1] if k + 1 < len(ts) else torch.tensor(0)
        t_b = torch.full((B,), int(t_cur), dtype=torch.long, device=dev)
        out = model(D, Cp, Cs, delta, t_b, tau=tau, coupling="detached")

        a_cur = ab[int(t_cur)]
        a_next = ab[int(t_next)] if int(t_next) > 0 else torch.tensor(1.0, device=dev)

        # --- x0 estimates + DDIM (eta=0) for both continuous streams
        for X, eps in ((Cp, out.eps_pitch), (Cs, out.eps_step)):
            x0 = (X - (1 - a_cur).sqrt() * eps) / a_cur.sqrt().clamp_min(1e-4)
            x0.clamp_(-4.0, 4.0)
            X.copy_(a_next.sqrt() * x0 + (1 - a_next).sqrt() * eps)

        # --- Δ-feedback [R15]
        if delta_feedback:
            cs0 = (Cs - (1 - a_next).sqrt() * out.eps_step) / a_next.sqrt().clamp_min(1e-4)
            delta = step_channel_to_delta(cs0.squeeze(-1), stats).clamp(0.02, 2.0)

        # --- discrete unmasking toward unmasked fraction 1 - m[t_next]
        probs_on = F.softmax(out.logits, dim=-1)[..., 1]        # (B,T,P)
        if calibrate:
            # temper on-probability so revealed cells track the target rate
            probs_on = probs_on * (target_rate / probs_on.mean().clamp_min(1e-6))
            probs_on = probs_on.clamp(0.0, 1.0)
        still_masked = D.eq(MASK)
        n_masked = still_masked.sum(dim=(1, 2))                  # (B,)
        frac_next = float(m[int(t_next)]) if int(t_next) > 0 else 0.0
        target_masked = int(round(frac_next * T * P))
        for b in range(B):
            reveal = int(n_masked[b]) - target_masked
            if reveal <= 0:
                continue
            conf = torch.where(still_masked[b], (probs_on[b] - 0.5).abs(),
                               torch.tensor(-1.0, device=dev))
            idx = conf.flatten().topk(reveal).indices
            u = torch.rand(reveal, generator=g).to(dev)
            values = (u < probs_on[b].flatten()[idx]).long()
            D[b].view(-1)[idx] = values

    D[D.eq(MASK)] = 0  # safety: nothing should remain masked at t=0
    return SampleResult(D, Cp, Cs, delta)
