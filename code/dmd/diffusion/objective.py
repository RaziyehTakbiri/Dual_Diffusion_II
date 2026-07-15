"""Joint training objective (MODEL_SPEC §4, revisions [R7]-[R9]).

L = L_D + gamma * L_C
  L_D: cross-entropy over MASKED positions only.
       mode 'elbo_ce': exact discrete-time bound weight w_t (schedules.py) -
                       the bound-faithful arm.
       mode 'focal'  : focal-modulated CE, class-weighted - the practical
                       surrogate [R7]; with rho=0 and unit class weights it
                       reduces exactly to unweighted CE (unit-tested).
  L_C: epsilon-prediction MSE masked to ACTIVE events [R8];
       `supervise_silent=True` reproduces the legacy behavior (ablation).
  gamma: set once at init from gradient-norm matching [R9] - helper here,
       called by the trainer.
"""

from __future__ import annotations

from typing import Optional

import torch
import torch.nn.functional as F

from dmd.diffusion.schedules import ScheduleTables


def discrete_loss(
    logits: torch.Tensor,          # (B, N, K_v) - over DATA vocab (no mask class)
    D0: torch.Tensor,              # (B, N) long targets in 0..K_v-1
    mask_positions: torch.Tensor,  # (B, N) bool - loss only where True
    t: torch.Tensor,               # (B,) long shared diffusion index
    tables: ScheduleTables,
    mode: str = "focal",
    focal_rho: float = 2.0,
    class_weight: Optional[torch.Tensor] = None,  # (K_v,) alpha_y
) -> torch.Tensor:
    if mode not in ("focal", "elbo_ce"):
        raise ValueError(f"unknown discrete loss mode '{mode}'")
    logp = F.log_softmax(logits, dim=-1)
    ce = -logp.gather(-1, D0.unsqueeze(-1)).squeeze(-1)          # (B, N)

    if mode == "elbo_ce":
        w = tables.w_elbo.to(ce.device)[t].unsqueeze(-1)         # (B, 1)
        per_pos = tables.T_d * w * ce                            # bound scale
    else:
        p_true = ce.neg().exp().clamp(1e-12, 1.0)
        mod = (1.0 - p_true) ** focal_rho
        aw = (class_weight.to(ce.device)[D0]
              if class_weight is not None else torch.ones_like(ce))
        per_pos = aw * mod * ce

    msk = mask_positions.to(per_pos.dtype)
    return (per_pos * msk).sum() / msk.sum().clamp_min(1.0)


def continuous_loss(
    eps_pred: torch.Tensor,     # (B, N, K)
    eps: torch.Tensor,          # (B, N, K)
    active: torch.Tensor,       # (B, N) bool - activity mask M [R2]
    supervise_silent: bool = False,
) -> torch.Tensor:
    se = (eps_pred - eps) ** 2
    if supervise_silent:
        return se.mean()
    m = active.to(se.dtype).unsqueeze(-1)
    return (se * m).sum() / (m.sum() * se.shape[-1]).clamp_min(1.0)


@torch.no_grad()
def grad_match_gamma(grad_norm_discrete: float, grad_norm_continuous: float,
                     floor: float = 1e-3, ceil: float = 1e3) -> float:
    """[R9] gamma such that gamma * ||grad L_C|| = ||grad L_D|| at init.

    The trainer computes the two norms with one backward pass each on the
    first batch, calls this, logs the value, and freezes it for the run."""
    g = grad_norm_discrete / max(grad_norm_continuous, 1e-12)
    return float(min(max(g, floor), ceil))


def joint_loss(logits, D0, mask_positions, eps_pred, eps, active, t, tables,
               gamma: float, mode: str = "focal", focal_rho: float = 2.0,
               class_weight=None, supervise_silent: bool = False):
    """Convenience wrapper returning (total, L_D, L_C) - all scalars."""
    l_d = discrete_loss(logits, D0, mask_positions, t, tables, mode,
                        focal_rho, class_weight)
    l_c = continuous_loss(eps_pred, eps, active, supervise_silent)
    return l_d + gamma * l_c, l_d, l_c
