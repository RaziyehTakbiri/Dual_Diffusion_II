"""Bifurcated forward corruption (MODEL_SPEC §3).

Both streams share ONE diffusion index t per sample; corruptions are
conditionally independent given the clean state (manuscript Eq. 3). Shapes
follow the flattened convention: N positions per sample (music: N = T*P after
the model wrapper flattens the grid; blocks re-fold as needed).

Discrete: absorbing chain over vocab {0..K_v-1} plus MASK_ID = K_v.
Continuous: variance-preserving Gaussian, epsilon-parameterized.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import torch

from dmd.diffusion.schedules import ScheduleTables


@dataclass
class JointCorruption:
    """Outputs of one forward draw at shared t."""

    t: torch.Tensor            # (B,) long, 1..T_d
    D_t: torch.Tensor          # (B, N) long with MASK_ID at masked positions
    mask_positions: torch.Tensor  # (B, N) bool - True where D was masked
    C_t: torch.Tensor          # (B, N, K) float
    eps: torch.Tensor          # (B, N, K) float - injected noise


class BifurcatedForward:
    def __init__(self, tables: ScheduleTables, vocab_size: int):
        self.tab = tables
        self.K_v = vocab_size
        self.MASK_ID = vocab_size  # one past the data vocab

    def sample_t(self, batch: int, device,
                 generator: Optional[torch.Generator] = None) -> torch.Tensor:
        return torch.randint(1, self.tab.T_d + 1, (batch,), device=device,
                             generator=generator)

    def corrupt_discrete(self, D0: torch.Tensor, t: torch.Tensor,
                         generator: Optional[torch.Generator] = None
                         ) -> Tuple[torch.Tensor, torch.Tensor]:
        """q(D_t | D_0): each token independently -> MASK w.p. m_t."""
        m_t = self.tab.m.to(D0.device)[t].unsqueeze(-1)          # (B,1)
        u = torch.rand(D0.shape, device=D0.device, generator=generator)
        masked = u < m_t
        D_t = torch.where(masked, torch.full_like(D0, self.MASK_ID), D0)
        return D_t, masked

    def corrupt_continuous(self, C0: torch.Tensor, t: torch.Tensor,
                           generator: Optional[torch.Generator] = None
                           ) -> Tuple[torch.Tensor, torch.Tensor]:
        """q(C_t | C_0) = N(sqrt(ab_t) C_0, (1 - ab_t) I); returns (C_t, eps).

        Runs on ALL positions (inactive ones carry pure noise through the
        network); supervision is masked to active events downstream [R8]."""
        ab_t = self.tab.alpha_bar.to(C0.device)[t].view(-1, *([1] * (C0.dim() - 1)))
        eps = torch.randn(C0.shape, device=C0.device, generator=generator,
                          dtype=C0.dtype)
        C_t = ab_t.sqrt() * C0 + (1.0 - ab_t).sqrt() * eps
        return C_t, eps

    def __call__(self, D0: torch.Tensor, C0: torch.Tensor,
                 t: Optional[torch.Tensor] = None,
                 generator: Optional[torch.Generator] = None) -> JointCorruption:
        if t is None:
            t = self.sample_t(D0.shape[0], D0.device, generator)
        D_t, masked = self.corrupt_discrete(D0, t, generator)
        C_t, eps = self.corrupt_continuous(C0, t, generator)
        return JointCorruption(t=t, D_t=D_t, mask_positions=masked,
                               C_t=C_t, eps=eps)
