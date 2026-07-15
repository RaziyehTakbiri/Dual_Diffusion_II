"""Noise schedules for both streams (MODEL_SPEC §3, revision [R6]).

Continuous stream: cosine variance-preserving alpha_bar (Nichol & Dhariwal).
Discrete stream:   absorbing mask-probability schedule m_t, derived from the
                   continuous schedule by an ALIGNMENT rule so a shared
                   diffusion index t corrupts both streams at commensurate
                   rates - or decoupled (linear) as an ablation arm.

Conventions: t is an integer 1..T_d; index 0 of every returned table is a
clean-state sentinel (alpha_bar[0] = 1, m[0] = 0) so tables are indexed
directly by t.
"""

from __future__ import annotations

import math

import torch

ALIGNMENTS = ("sqrt_alpha", "alpha", "linear")


def cosine_alpha_bar(T_d: int, s: float = 0.008,
                     min_alpha_bar: float = 1e-5) -> torch.Tensor:
    """(T_d+1,) table: alpha_bar[t] for t = 0..T_d; alpha_bar[0] = 1."""
    t = torch.arange(T_d + 1, dtype=torch.float64)
    f = torch.cos(((t / T_d) + s) / (1.0 + s) * math.pi / 2.0) ** 2
    ab = (f / f[0]).clamp(min_alpha_bar, 1.0)
    ab[0] = 1.0
    return ab


def mask_prob(alpha_bar: torch.Tensor, alignment: str = "sqrt_alpha") -> torch.Tensor:
    """(T_d+1,) table m[t] = P(token is [MASK] at step t); m[0] = 0, m[T_d] ~ 1.

    sqrt_alpha  [R6 default]: m_t = 1 - sqrt(alpha_bar_t). The continuous
                stream's signal amplitude scales as sqrt(alpha_bar_t); matching
                the discrete survival probability to it keeps the two streams'
                information decay commensurate.
    alpha       m_t = 1 - alpha_bar_t (faster masking early).
    linear      m_t = t / T_d - the classic absorbing-D3PM schedule, DECOUPLED
                from the continuous stream (the 'independent' ablation arm;
                'independent' is accepted as an alias).
    """
    if alignment == "independent":
        alignment = "linear"
    if alignment not in ALIGNMENTS:
        raise ValueError(f"alignment '{alignment}' not in {ALIGNMENTS}")
    T_d = len(alpha_bar) - 1
    if alignment == "sqrt_alpha":
        m = 1.0 - alpha_bar.sqrt()
    elif alignment == "alpha":
        m = 1.0 - alpha_bar
    else:
        m = torch.arange(T_d + 1, dtype=alpha_bar.dtype) / T_d
    m = m.clamp(0.0, 1.0)
    m[0] = 0.0
    return m


def step_mask_rate(m: torch.Tensor) -> torch.Tensor:
    """(T_d+1,) per-step masking probability beta[t] = P(mask at t | alive at
    t-1) = (m_t - m_{t-1}) / (1 - m_{t-1}); beta[0] = 0. Used by ancestral
    reverse steps and available for forward simulation."""
    beta = torch.zeros_like(m)
    denom = (1.0 - m[:-1]).clamp_min(1e-12)
    beta[1:] = ((m[1:] - m[:-1]) / denom).clamp(0.0, 1.0)
    return beta


def elbo_ce_weight(m: torch.Tensor) -> torch.Tensor:
    """(T_d+1,) bound weight w[t] for the x0-parameterized absorbing chain.

    Derivation (MODEL_SPEC §4): a token observed as [MASK] at step t was
    unmasked at t-1 with posterior probability (m_t - m_{t-1})/m_t; the
    per-step KL then reduces to that weight times -log p_theta(x0). Sanity
    anchor: for the linear schedule m_t = t/T_d this gives w_t = 1/t, the
    known masked-diffusion result. w[0] is unused (set 0).
    """
    w = torch.zeros_like(m)
    w[1:] = ((m[1:] - m[:-1]) / m[1:].clamp_min(1e-12)).clamp(0.0, 1.0)
    return w


class ScheduleTables:
    """All tables bundled, indexed by integer t (0..T_d); device-movable."""

    def __init__(self, T_d: int, alignment: str = "sqrt_alpha", s: float = 0.008):
        self.T_d = T_d
        self.alignment = alignment
        self.alpha_bar = cosine_alpha_bar(T_d, s)
        self.m = mask_prob(self.alpha_bar, alignment)
        self.beta = step_mask_rate(self.m)
        self.w_elbo = elbo_ce_weight(self.m)

    def to(self, device, dtype=torch.float32):
        for name in ("alpha_bar", "m", "beta", "w_elbo"):
            setattr(self, name, getattr(self, name).to(device=device, dtype=dtype))
        return self
