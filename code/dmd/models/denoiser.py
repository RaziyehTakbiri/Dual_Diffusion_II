"""Dual-manifold denoiser (MODEL_SPEC §5-§6, v0.2).

Layout: one token per GRID STEP (T tokens; the 88-pitch frame is folded into
the token embedding), a DiT-style trunk with adaLN-Zero diffusion-time
conditioning, and the B0-B5 temporal block in the FFN slot - the ONLY thing
that differs across ladder rungs.

Heads:
  structure:  logits (B, T, P, 2) for x0 in {off, on} per cell (D3PM x0-param)
  continuous: eps for C^pitch (B, T, P, K) AND C^step (B, T, K_step) [R14]
The continuous pathway is conditioned on the Gumbel-relaxed structure
D~0 (MODEL_SPEC §5), so gradients from the continuous loss reach the
structure head - the coupling is unit-tested, not assumed.

Delta (B, T) enters ONLY the temporal blocks (dt-aware rungs). At training
time it is the data's grid-period map; at sampling it is derived from the
model's own x0-estimate of C^step, refreshed each step ([R15], sampler M6).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

from dmd.blocks.temporal import build_temporal_block


def timestep_embedding(t: torch.Tensor, dim: int) -> torch.Tensor:
    half = dim // 2
    freqs = torch.exp(-math.log(10_000.0)
                      * torch.arange(half, device=t.device, dtype=torch.float32)
                      / max(half - 1, 1))
    ang = t.float().unsqueeze(-1) * freqs
    return torch.cat([ang.sin(), ang.cos()], dim=-1)


class AdaLN(nn.Module):
    """adaLN-Zero: LayerNorm modulated by the diffusion-time embedding."""

    def __init__(self, d_model: int, d_cond: int):
        super().__init__()
        self.norm = nn.LayerNorm(d_model, elementwise_affine=False)
        self.mod = nn.Linear(d_cond, 3 * d_model)
        nn.init.zeros_(self.mod.weight)
        nn.init.zeros_(self.mod.bias)

    def forward(self, x, cond):
        shift, scale, gate = self.mod(cond).unsqueeze(1).chunk(3, dim=-1)
        return self.norm(x) * (1 + scale) + shift, gate


class Layer(nn.Module):
    def __init__(self, d_model: int, n_heads: int, d_cond: int,
                 block_name: str, block_hidden: Optional[int],
                 block_target_params: Optional[int]):
        super().__init__()
        self.ln1 = AdaLN(d_model, d_cond)
        self.attn = nn.MultiheadAttention(d_model, n_heads, batch_first=True)
        self.ln2 = AdaLN(d_model, d_cond)
        self.block = build_temporal_block(block_name, d_model,
                                          hidden=block_hidden,
                                          target_params=block_target_params)

    def forward(self, x, cond, dt):
        h, gate = self.ln1(x, cond)
        a, _ = self.attn(h, h, h, need_weights=False)
        x = x + gate * a
        h, gate = self.ln2(x, cond)
        x = x + gate * self.block(h, dt)
        return x


@dataclass
class DenoiserOutput:
    logits: torch.Tensor      # (B, T, P, 2)
    eps_pitch: torch.Tensor   # (B, T, P, K)
    eps_step: torch.Tensor    # (B, T, K_step)
    relaxed: torch.Tensor     # (B, T, P) Gumbel-relaxed P(on) fed to cont. head


class DualManifoldDenoiser(nn.Module):
    N_DSTATE = 3  # off / on / [MASK]

    def __init__(self, P: int = 88, K: int = 2, K_step: int = 1,
                 d_model: int = 512, n_layers: int = 12, n_heads: int = 8,
                 block: str = "cfc", block_hidden: Optional[int] = None,
                 block_target_params: Optional[int] = None,
                 max_T: int = 1024):
        super().__init__()
        self.P, self.K, self.K_step = P, K, K_step
        d_cond = d_model
        self.embed = nn.Linear(P * (self.N_DSTATE + K) + K_step, d_model)
        self.pos = nn.Parameter(torch.randn(1, max_T, d_model) * 0.01)
        self.t_mlp = nn.Sequential(nn.Linear(d_model, d_cond), nn.SiLU(),
                                   nn.Linear(d_cond, d_cond))
        self.layers = nn.ModuleList([
            Layer(d_model, n_heads, d_cond, block, block_hidden,
                  block_target_params)
            for _ in range(n_layers)])
        self.final_norm = AdaLN(d_model, d_cond)
        self.head_structure = nn.Linear(d_model, P * 2)
        # continuous head sees trunk features AND the relaxed structure [§5]
        self.bridge_embed = nn.Linear(P, d_model)
        self.head_continuous = nn.Sequential(
            nn.Linear(2 * d_model, d_model), nn.SiLU(),
            nn.Linear(d_model, P * K + K_step))

    def forward(self, D_t: torch.Tensor, C_pitch_t: torch.Tensor,
                C_step_t: torch.Tensor, delta: torch.Tensor, t: torch.Tensor,
                tau: float = 1.0,
                coupling: str = "gumbel",
                generator: Optional[torch.Generator] = None) -> DenoiserOutput:
        """D_t: (B,T,P) long in {0,1,2=MASK}; C_pitch_t: (B,T,P,K);
        C_step_t: (B,T,K_step); delta: (B,T); t: (B,)."""
        B, T, P = D_t.shape
        d_onehot = F.one_hot(D_t, self.N_DSTATE).float()          # (B,T,P,3)
        frame = torch.cat([d_onehot, C_pitch_t], dim=-1).reshape(B, T, -1)
        x = self.embed(torch.cat([frame, C_step_t], dim=-1)) + self.pos[:, :T]
        cond = self.t_mlp(timestep_embedding(t, x.shape[-1]))

        for layer in self.layers:
            x = layer(x, cond, delta)
        x, _ = self.final_norm(x, cond)

        logits = self.head_structure(x).reshape(B, T, P, 2)

        # ---- differentiable coupling (MODEL_SPEC §5) ----
        if coupling == "gumbel":
            g = -torch.log(-torch.log(
                torch.rand(logits.shape, device=logits.device,
                           generator=generator).clamp_min(1e-20)).clamp_min(1e-20))
            relaxed = F.softmax((logits + g) / tau, dim=-1)[..., 1]
        elif coupling == "straight_through":
            hard = logits.argmax(-1).float()
            soft = F.softmax(logits / tau, dim=-1)[..., 1]
            relaxed = hard + (soft - soft.detach())
        elif coupling == "detached":
            relaxed = F.softmax(logits / tau, dim=-1)[..., 1].detach()
        elif coupling == "none":
            relaxed = torch.zeros_like(logits[..., 1])
        else:
            raise ValueError(f"unknown coupling '{coupling}'")

        cont_in = torch.cat([x, self.bridge_embed(relaxed)], dim=-1)
        cont = self.head_continuous(cont_in)
        eps_pitch = cont[..., : P * self.K].reshape(B, T, P, self.K)
        eps_step = cont[..., P * self.K:]
        return DenoiserOutput(logits, eps_pitch, eps_step, relaxed)
