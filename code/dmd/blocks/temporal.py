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
class _CfCCell(nn.Module):
    """Closed-form continuous-time cell (MODEL_SPEC [R11]).

    u_i = [x_i, h_{i-1}]
    w_i = sigmoid(-softplus(f(u_i)) * dt_i)        # decay gate, rate > 0
    h_i = w_i * g(u_i) + (1 - w_i) * hhat(u_i)

    Limits: dt->inf  => h -> hhat(u)   (input-driven steady state)
            dt->0    => h -> (g+hhat)/2 (gate at 1/2)
    Deviations from manuscript Eq. (8) are documented in the spec.
    """

    def __init__(self, d_in: int, d_hidden: int):
        super().__init__()
        self.f = nn.Linear(d_in + d_hidden, d_hidden)
        self.g = nn.Linear(d_in + d_hidden, d_hidden)
        self.hhat = nn.Linear(d_in + d_hidden, d_hidden)

    def gate(self, u: torch.Tensor, dt: torch.Tensor) -> torch.Tensor:
        return torch.sigmoid(-F.softplus(self.f(u)) * dt.unsqueeze(-1))

    def forward(self, x_i, h_prev, dt_i):
        u = torch.cat([x_i, h_prev], dim=-1)
        w = self.gate(u, dt_i)
        return w * torch.tanh(self.g(u)) + (1.0 - w) * torch.tanh(self.hhat(u))


def cfc_linear_scan(la: torch.Tensor, c: torch.Tensor, h0: torch.Tensor,
                    chunk: int = 16) -> torch.Tensor:
    """Loop-free evaluation of h_i = a_i*h_{i-1} + (1-a_i)*c_i, a_i = exp(la_i).

    Within chunks of `chunk` steps everything is computed at once via
    h_k = exp(A_k) h_in + sum_{j<=k} exp(A_k - A_j) b_j with A = cumsum(la);
    every exponent is <= 0, so it is numerically safe for arbitrary decay.
    Chunks are combined by a short carry loop (L/chunk iterations).
    Proven equal to the sequential reference to 1e-14 (numpy mirror,
    2026-07-15). la: (B, L, H) <= 0; c: (B, L, H); h0: (H,)."""
    B, L, H = la.shape
    pad = (-L) % chunk
    if pad:  # pad with la=0 (a=1), c=0 -> b=0: state passes through unchanged
        la = F.pad(la, (0, 0, 0, pad))
        c = F.pad(c, (0, 0, 0, pad))
    b = (1.0 - torch.exp(la)) * c
    n_chunks = la.shape[1] // chunk
    tril = torch.tril(torch.ones(chunk, chunk, device=la.device,
                                 dtype=la.dtype))
    h = h0.unsqueeze(0).expand(B, H).contiguous()
    outs = []
    for s in range(n_chunks):
        sl = slice(s * chunk, (s + 1) * chunk)
        A = torch.cumsum(la[:, sl], dim=1)                       # (B, Lc, H)
        M = torch.exp(A.unsqueeze(2) - A.unsqueeze(1)) * tril.view(1, chunk,
                                                                   chunk, 1)
        o = torch.exp(A) * h.unsqueeze(1) + torch.einsum(
            "bkjh,bjh->bkh", M, b[:, sl])
        outs.append(o)
        h = o[:, -1]
    out = torch.cat(outs, dim=1)
    return out[:, :L] if pad else out


class CFCBlock(TemporalBlock):
    """B4: EXACT closed-form continuous-time block, loop-free (MODEL_SPEC
    [R17], replaces the recurrent-gated variant on 2026-07-15).

    Between grid events the hidden state follows the exact solution of the
    linear liquid ODE  dh/dt = -lambda(x) (h - c(x)):
        h_i = a_i h_{i-1} + (1 - a_i) c_i,   a_i = exp(-softplus(lam(x_i)) dt_i)
    i.e. exponential decay toward an input-driven target at an input-driven
    rate over the ACTUAL elapsed time. This is the purest reading of
    "closed-form continuous-time dynamics", and being linear in h it is
    computable without a sequential loop (cfc_linear_scan). The former
    nonlinear-recurrent variant survives as `cfc_seq` for appendix
    comparison; the de-risk probe had already shown its recurrence was not
    the differentiator (cfc ~= gru under uninformative dt).
    """

    USES_DT = True

    def __init__(self, d_model: int, hidden: int):
        super().__init__()
        self.hidden = hidden
        self.wx_f = nn.Linear(d_model, 2 * hidden)   # -> (lambda_pre, c_pre)
        self.wx_b = nn.Linear(d_model, 2 * hidden)
        self.h0 = nn.Parameter(torch.zeros(2, hidden))
        self.proj = nn.Linear(2 * hidden, d_model)

    def direction_scan(self, x, dt, reverse: bool):
        """One direction; exposed for causality/equivalence unit tests."""
        wx = self.wx_b if reverse else self.wx_f
        h0 = self.h0[1] if reverse else self.h0[0]
        # backward scan at position i uses the gap to the NEXT element
        dt_dir = torch.cat([dt[:, 1:], dt[:, -1:]], dim=1) if reverse else dt
        z = wx(x)
        lam_pre, c_pre = z.chunk(2, dim=-1)
        la = (-F.softplus(lam_pre) * dt_dir.unsqueeze(-1)).clamp_min(-20.0)
        c = torch.tanh(c_pre)
        if reverse:
            out = cfc_linear_scan(la.flip(1), c.flip(1), h0)
            return out.flip(1)
        return cfc_linear_scan(la, c, h0)

    def forward(self, x, dt=None):
        B, L, _ = x.shape
        if dt is None:
            dt = x.new_ones(B, L)
        f = self.direction_scan(x, dt, reverse=False)
        b = self.direction_scan(x, dt, reverse=True)
        return self.proj(torch.cat([f, b], dim=-1))


class CFCSeqBlock(TemporalBlock):
    """The former B4 (Hasani-style gated nonlinear recurrence), kept for the
    appendix equivalence run under the ladder name `cfc_seq`. Sequential and
    slow (~5 s/step at d=512); not part of the 30-run grid."""

    USES_DT = True

    def __init__(self, d_model: int, hidden: int):
        super().__init__()
        self.hidden = hidden
        self.fwd = _CfCCell(d_model, hidden)
        self.bwd = _CfCCell(d_model, hidden)
        self.h0 = nn.Parameter(torch.zeros(2, hidden))
        self.proj = nn.Linear(2 * hidden, d_model)

    def _scan(self, cell, x, dt, h0, reverse: bool):
        B, L, _ = x.shape
        idx = range(L - 1, -1, -1) if reverse else range(L)
        h = h0.expand(B, -1)
        out = x.new_empty(B, L, self.hidden)
        for i in idx:
            # For the backward scan, the gap to the *next* element is dt_{i+1}.
            j = min(i + 1, L - 1) if reverse else i
            h = cell(x[:, i], h, dt[:, j])
            out[:, i] = h
        return out

    def forward(self, x, dt=None):
        B, L, _ = x.shape
        if dt is None:
            dt = x.new_ones(B, L)
        f = self._scan(self.fwd, x, dt, self.h0[0], reverse=False)
        b = self._scan(self.bwd, x, dt, self.h0[1], reverse=True)
        return self.proj(torch.cat([f, b], dim=-1))


# ----------------------------------------------------------------------------- B5
def _rk4_evolve_eager(h: torch.Tensor, dt_i: torch.Tensor,
                      w1: torch.Tensor, b1: torch.Tensor,
                      w2: torch.Tensor, b2: torch.Tensor,
                      rk4_steps: int) -> torch.Tensor:
    """Fixed-step RK4 for dh/ds = W2 tanh(W1 h + b1) + b2 over interval dt_i.
    Standalone tensor function so it can be TorchScripted AND wrapped in
    gradient checkpointing."""
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
except Exception:  # noqa: BLE001 - version quirks must not break math
    _rk4_evolve = _rk4_evolve_eager
    print("[dmd] WARNING: TorchScript unavailable for RK4; eager fallback.")


class NeuralODEBlock(TemporalBlock):
    """ODE-RNN scan (Rubanova et al. 2019 style): between elements, evolve h by
    dh/ds = f(h) integrated over dt_i with fixed-step RK4 (deterministic; NFE
    logged); at each element, a GRUCell update. Bidirectional like B3/B4.

    Uses a generic solver where B4 uses a closed form - the B5 vs B4 comparison
    is the manuscript's "closed form vs. generic ODE" control, now on equal
    scan wiring.
    """

    USES_DT = True

    def __init__(self, d_model: int, hidden: int, rk4_steps: int = 1):
        # rk4_steps=1 (4 function evals per interval): reported solver setting
        # of this control model, chosen for wall-clock feasibility at d=512.
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
        # backward stores every ode_f activation per position x direction x
        # layer and OOMs a 22 GiB GPU at d=512 (re-restored 2026-07-19 after
        # a sync clobber). Identical gradients, ~+33% compute, this rung only.
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
    "cfc": CFCBlock,        # [R17] exact closed-form, loop-free (the grid's B4)
    "cfc_seq": CFCSeqBlock,  # former recurrent-gated variant (appendix only)
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
