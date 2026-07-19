"""Temporal block ladder B0-B5 (MODEL_SPEC.md §6).

Every block maps (B, L, d) -> (B, L, d). `dt` has shape (B, L): dt[:, i] is the
data-time interval between sequence elements i-1 and i (MODEL_SPEC [R1]).
Blocks that are *defined* to ignore dt (B0-B3) accept it and must not use it;
tests enforce this dissociation, mirroring the paper's claim structure.

Ladder (one factor per rung):
  B0 ffn           position-wise MLP                     (grid baseline)
  B1 ffn_timecond  MLP + explicit time features          (is a time input enough?)
  B2 gated_ffn     GLU gating, no recurrence, no dt      (is it just gating?)
  B3 gru           bidirectional GRU scan                (is it just recurrence?)
  B4 cfc           bidirectional closed-form continuous- (the claim)
                   time scan, dt in the decay gate
  B5 node          ODE-RNN scan, generic solver on dt    (closed form vs. solver)
"""

from __future__ import annotations

import math
from typing import Callable, Dict, Optional, Type

import torch
import torch.nn as nn
import torch.nn.functional as F


class TemporalBlock(nn.Module):
    """Base class. Subclasses set USES_DT correctly; tests rely on it."""

    USES_DT: bool = False

    def forward(self, x: torch.Tensor, dt: Optional[torch.Tensor] = None) -> torch.Tensor:
        raise NotImplementedError


# ----------------------------------------------------------------------------- B0
class PositionwiseFFN(TemporalBlock):
    USES_DT = False

    def __init__(self, d_model: int, hidden: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_model, hidden), nn.GELU(), nn.Linear(hidden, d_model)
        )

    def forward(self, x, dt=None):
        return self.net(x)


# ----------------------------------------------------------------------------- B1
class TimeCondFFN(TemporalBlock):
    """B0 plus explicit continuous-time features.

    Time features per position: [dt_i, cumulative time (min-max normalized per
    sequence), sin/cos of cumulative time at two learned frequencies].
    The block *sees* time but has no continuous-time dynamics.
    """

    USES_DT = True
    N_TIME_FEATS = 6

    def __init__(self, d_model: int, hidden: int):
        super().__init__()
        self.freq = nn.Parameter(torch.tensor([1.0, 8.0]))
        self.net = nn.Sequential(
            nn.Linear(d_model + self.N_TIME_FEATS, hidden),
            nn.GELU(),
            nn.Linear(hidden, d_model),
        )

    def forward(self, x, dt=None):
        B, L, _ = x.shape
        if dt is None:
            dt = x.new_ones(B, L)
        cum = dt.cumsum(dim=1)
        span = cum[:, -1:].clamp_min(1e-8)
        cum_n = cum / span
        feats = [dt.unsqueeze(-1), cum_n.unsqueeze(-1)]
        for k in range(2):
            ang = 2 * math.pi * self.freq[k] * cum_n
            feats += [ang.sin().unsqueeze(-1), ang.cos().unsqueeze(-1)]
        return self.net(torch.cat([x] + feats, dim=-1))


# ----------------------------------------------------------------------------- B2
class GatedFFN(TemporalBlock):
    """SwiGLU-style gated unit: isolates *gating* without recurrence or dt.

    If CFC's advantage were mere input-dependent gating, this rung would match it.
    """

    USES_DT = False

    def __init__(self, d_model: int, hidden: int):
        super().__init__()
        self.w_gate = nn.Linear(d_model, hidden)
        self.w_val = nn.Linear(d_model, hidden)
        self.w_out = nn.Linear(hidden, d_model)

    def forward(self, x, dt=None):
        return self.w_out(F.silu(self.w_gate(x)) * self.w_val(x))


# ----------------------------------------------------------------------------- B3
class GRUBlock(TemporalBlock):
    """Bidirectional GRU scan: isolates *recurrence* without continuous time."""

    USES_DT = False

    def __init__(self, d_model: int, hidden: int):
        super().__init__()
        self.rnn = nn.GRU(
            d_model, hidden, batch_first=True, bidirectional=True
        )
        self.proj = nn.Linear(2 * hidden, d_model)

    def forward(self, x, dt=None):
        y, _ = self.rnn(x)
        return self.proj(y)


# ----------------------------------------------------------------------------- B4
def _cfc_scan_eager(px: torch.Tensor, wh: torch.Tensor, dt: torch.Tensor,
                    h0: torch.Tensor, reverse: bool) -> torch.Tensor:
    """The CFC recurrence (MODEL_SPEC [R11]) over one direction.

    px: (B, L, 3H) input-side projections W_x x_i + b, PREcomputed for all
        steps in one batched matmul (the cuDNN-RNN trick); wh: (3H, H) the
        hidden-side weight; dt: (B, L); h0: (H,).

    Per step: z = px_i + h W_h^T; split z -> (f, g, hhat);
              w = sigmoid(-softplus(f) * dt); h = w*tanh(g) + (1-w)*tanh(hhat)
    Identical math and identical parameter count to the original three-Linear
    cell (W [x;h] = W_x x + W_h h); rewritten 2026-07-15 because the original
    launched ~10 kernels per step and was wall-clock infeasible at d=512.
    """
    B, L, H3 = px.shape
    H = H3 // 3
    h = h0.unsqueeze(0).expand(B, H).contiguous()
    out = torch.empty(B, L, H, dtype=px.dtype, device=px.device)
    for k in range(L):
        i = L - 1 - k if reverse else k
        j = min(i + 1, L - 1) if reverse else i
        z = px[:, i] + h @ wh.t()
        f, g, hh = z.chunk(3, dim=-1)
        w = torch.sigmoid(-F.softplus(f) * dt[:, j].unsqueeze(-1))
        h = w * torch.tanh(g) + (1.0 - w) * torch.tanh(hh)
        out[:, i] = h
    return out


try:  # TorchScript removes per-step Python overhead; fall back if scripting
    _cfc_scan = torch.jit.script(_cfc_scan_eager)
except Exception:  # noqa: BLE001 - runtime-version quirks must not break math
    _cfc_scan = _cfc_scan_eager
    print("[dmd] WARNING: TorchScript unavailable for CFC scan; using eager "
          "fallback (slower, same results). Report this.")


def cfc_decay_gate(f_pre: torch.Tensor, dt: torch.Tensor) -> torch.Tensor:
    """w = sigmoid(-softplus(f_pre) * dt); exposed for unit tests."""
    return torch.sigmoid(-F.softplus(f_pre) * dt)


class CFCBlock(TemporalBlock):
    """Bidirectional CFC scan; dt enters *only* through the decay gate.

    B4 vs B3 isolates the continuous-time gate given recurrence;
    B4 vs B2 isolates it given gating.
    """

    USES_DT = True

    def __init__(self, d_model: int, hidden: int):
        super().__init__()
        self.hidden = hidden
        # per direction: input-side Linear(d->3H, bias) + hidden-side (3H, H)
        self.wx_f = nn.Linear(d_model, 3 * hidden)
        self.wx_b = nn.Linear(d_model, 3 * hidden)
        k = 1.0 / (hidden ** 0.5)
        self.wh_f = nn.Parameter(torch.empty(3 * hidden, hidden).uniform_(-k, k))
        self.wh_b = nn.Parameter(torch.empty(3 * hidden, hidden).uniform_(-k, k))
        self.h0 = nn.Parameter(torch.zeros(2, hidden))
        self.proj = nn.Linear(2 * hidden, d_model)

    def direction_scan(self, x, dt, reverse: bool):
        """One direction; exposed for causality unit tests."""
        px = self.wx_b(x) if reverse else self.wx_f(x)
        wh = self.wh_b if reverse else self.wh_f
        h0 = self.h0[1] if reverse else self.h0[0]
        return _cfc_scan(px, wh, dt, h0, reverse)

    def forward(self, x, dt=None):
        B, L, _ = x.shape
        if dt is None:
            dt = x.new_ones(B, L)
        f = self.direction_scan(x, dt, reverse=False)
        b = self.direction_scan(x, dt, reverse=True)
        return self.proj(torch.cat([f, b], dim=-1))


# ----------------------------------------------------------------------------- B5
def _rk4_evolve_eager(h: torch.Tensor, dt_i: torch.Tensor,
                      w1: torch.Tensor, b1: torch.Tensor,
                      w2: torch.Tensor, b2: torch.Tensor,
                      rk4_steps: int) -> torch.Tensor:
    """Fixed-step RK4 for dh/ds = W2 tanh(W1 h + b1) + b2 over interval dt_i.
    Standalone tensor function so it can be TorchScripted AND wrapped in
    gradient checkpointing (both needed at d=512)."""
    step = (dt_i / rk4_steps).unsqueeze(-1)
    for _ in range(rk4_steps):
        k1 = torch.tanh(h @ w1.t() + b1) @ w2.t() + b2
        k2 = torch.tanh((h + 0.5 * step * k1) @ w1.t() + b1) @ w2.t() + b2
        k3 = torch.tanh((h + 0.5 * step * k2) @ w1.t() + b1) @ w2.t() + b2
        k4 = torch.tanh((h + step * k3) @ w1.t() + b1) @ w2.t() + b2
        h = h + step / 6.0 * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
    return h


try:
    _rk4_evolve = torch.jit.script(_rk4_evolve_eager)
except Exception:  # noqa: BLE001
    _rk4_evolve = _rk4_evolve_eager
    print("[dmd] WARNING: TorchScript unavailable for RK4; eager fallback.")


class NeuralODEBlock(TemporalBlock):
    """ODE-RNN scan (Rubanova et al. 2019 style): between elements, evolve h by
    dh/ds = f(h) integrated over dt_i with fixed-step RK4 (deterministic; NFE
    logged); at each element, a GRUCell update. Bidirectional like B3/B4.

    Uses a generic solver where B4 uses a closed form - the B5 vs B4 comparison
    is the manuscript's "closed form vs. generic ODE" control, now on equal
    scan wiring.

    Solver setting: rk4_steps=1 (4 function evaluations per inter-note
    interval) - reduced from 4 on 2026-07-15 for wall-clock feasibility at
    d=512; a REPORTED hyperparameter of the control, not a tuned quantity.
    """

    USES_DT = True

    def __init__(self, d_model: int, hidden: int, rk4_steps: int = 1):
        super().__init__()
        self.hidden = hidden
        self.rk4_steps = rk4_steps
        self.ode_f = nn.Sequential(
            nn.Linear(hidden, hidden), nn.Tanh(), nn.Linear(hidden, hidden)
        )
        self.cell_fwd = nn.GRUCell(d_model, hidden)
        self.cell_bwd = nn.GRUCell(d_model, hidden)
        self.h0 = nn.Parameter(torch.zeros(2, hidden))
        self.proj = nn.Linear(2 * hidden, d_model)
        self.nfe = 0  # diagnostics, logged by the trainer
        # Gradient-checkpoint the RK4 evolution during training: without it,
        # backward stores 16 ode_f activation sets per position x 2 directions
        # x n_layers - OOM'd a 22 GiB GPU at pilot scale (2026-07-15).
        # Checkpointing recomputes RK4 in backward: IDENTICAL gradients,
        # ~16x less scan-activation memory, ~+33% compute for this rung only.
        self.use_checkpoint = True

    def _evolve(self, h, dt_i):
        w1, b1 = self.ode_f[0].weight, self.ode_f[0].bias
        w2, b2 = self.ode_f[2].weight, self.ode_f[2].bias
        self.nfe += 4 * self.rk4_steps
        return _rk4_evolve(h, dt_i, w1, b1, w2, b2, self.rk4_steps)

    def _scan(self, cell, x, dt, h0, reverse: bool):
        B, L, _ = x.shape
        idx = range(L - 1, -1, -1) if reverse else range(L)
        h = h0.expand(B, -1).contiguous()
        out = x.new_empty(B, L, self.hidden)
        ckpt = (self.use_checkpoint and self.training
                and torch.is_grad_enabled())
        for i in idx:
            j = min(i + 1, L - 1) if reverse else i
            if ckpt:
                h = torch.utils.checkpoint.checkpoint(
                    self._evolve, h, dt[:, j], use_reentrant=False)
            else:
                h = self._evolve(h, dt[:, j])
            h = cell(x[:, i], h)
            out[:, i] = h
        return out

    def forward(self, x, dt=None):
        B, L, _ = x.shape
        if dt is None:
            dt = x.new_ones(B, L)
        f = self._scan(self.cell_fwd, x, dt, self.h0[0], reverse=False)
        b = self._scan(self.cell_bwd, x, dt, self.h0[1], reverse=True)
        return self.proj(torch.cat([f, b], dim=-1))


# ------------------------------------------------------------------- registry
LADDER: Dict[str, Type[TemporalBlock]] = {
    "ffn": PositionwiseFFN,
    "ffn_timecond": TimeCondFFN,
    "gated_ffn": GatedFFN,
    "gru": GRUBlock,
    "cfc": CFCBlock,
    "node": NeuralODEBlock,
}


def build_temporal_block(
    name: str, d_model: int, hidden: Optional[int] = None,
    target_params: Optional[int] = None, match_rtol: float = 0.01,
) -> TemporalBlock:
    """Build a ladder rung. If `target_params` is given, the hidden width is
    solved so total trainable parameters match within `match_rtol`
    (MODEL_SPEC [R12]; default 1%). NOTE: recurrent rungs have ~quadratic
    parameter growth in width, so 1% is unreachable below d_model ~ 128 -
    small-scale probes should pass a looser match_rtol and report counts."""
    if name not in LADDER:
        raise KeyError(f"unknown block '{name}'; choose from {sorted(LADDER)}")
    cls = LADDER[name]
    if target_params is not None:
        from dmd.utils.params import match_width
        hidden = match_width(lambda w: cls(d_model, w), target_params,
                             rtol=match_rtol)
    if hidden is None:
        hidden = 4 * d_model
    return cls(d_model, hidden)
