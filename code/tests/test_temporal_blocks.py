"""CPU unit tests for the temporal-block ladder.

These tests encode the *scientific* contract, not just shapes:
- rungs declared dt-blind must be exactly invariant to dt;
- rungs declared dt-aware must respond to dt;
- the CFC decay is monotone in dt; the loop-free scan equals the sequential
  recurrence exactly [R17]; NODE checkpointing changes nothing but memory;
- all rungs are parameter-matchable within 1%.

Fully rewritten 2026-07-19 after a Git-sync clobber left this file in a
mixed state (see PROGRESS.md).
"""

import pytest
import torch

from dmd.blocks.temporal import (LADDER, CFCBlock, build_temporal_block,
                                 cfc_linear_scan, _CfCCell)
from dmd.utils.params import count_params

# d_model = 128, not smaller: recurrent rungs have ~quadratic-in-width counts,
# so at tiny d the 1% param-matching tolerance is unreachable by any integer
# width (granularity ~3% at d=32, ~0.4% at d=128 and above).
B, L, D = 2, 17, 128
HID = 96


def _block(name):
    torch.manual_seed(0)
    return build_temporal_block(name, D, hidden=HID)


def _inputs(seed=0):
    g = torch.Generator().manual_seed(seed)
    x = torch.randn(B, L, D, generator=g)
    dt_regular = torch.ones(B, L)
    dt_irregular = torch.rand(B, L, generator=g) * 2.0 + 0.01
    return x, dt_regular, dt_irregular


@pytest.mark.parametrize("name", sorted(LADDER))
def test_shape_and_grad(name):
    block, (x, dt, _) = _block(name), _inputs()
    x = x.requires_grad_(True)
    y = block(x, dt)
    assert y.shape == (B, L, D)
    y.sum().backward()
    assert x.grad is not None and torch.isfinite(x.grad).all()
    assert all(torch.isfinite(p).all() for p in block.parameters())


@pytest.mark.parametrize("name", sorted(LADDER))
def test_dt_sensitivity_matches_declaration(name):
    """The dissociation at the heart of the paper, as a unit test."""
    block, (x, dt_reg, dt_irr) = _block(name), _inputs()
    block.eval()
    with torch.no_grad():
        y_reg = block(x, dt_reg)
        y_irr = block(x, dt_irr)
    if block.USES_DT:
        assert not torch.allclose(y_reg, y_irr), f"{name} must respond to dt"
    else:
        assert torch.allclose(y_reg, y_irr), f"{name} must ignore dt"


def test_cfc_linear_scan_matches_sequential_reference():
    """[R17] The loop-free chunked scan must equal the step-by-step recurrence
    exactly, including the padding path (L not divisible by the chunk) and
    extreme decay."""
    torch.manual_seed(0)
    b_, l_, h_ = 2, 50, 7        # 50 % 16 != 0 -> exercises padding
    la = -(torch.rand(b_, l_, h_) * 3.0)
    la[0, 3] = -18.0             # near-total decay
    c = torch.randn(b_, l_, h_)
    h0 = torch.randn(h_)
    h = h0.unsqueeze(0).expand(b_, h_).clone()
    ref = torch.empty(b_, l_, h_)
    for i in range(l_):
        a = torch.exp(la[:, i])
        h = a * h + (1 - a) * c[:, i]
        ref[:, i] = h
    fast = cfc_linear_scan(la, c, h0)
    assert torch.allclose(fast, ref, atol=1e-5), (fast - ref).abs().max()


def test_cfc_decay_monotone_and_delta_zero_identity():
    """a = exp(-softplus(lam) dt): dt=0 => a=1 (state unchanged - the exact
    physical limit of the closed-form solution); a decreases as dt grows."""
    torch.manual_seed(0)
    block = CFCBlock(D, HID)
    block.eval()
    x = torch.randn(1, 4, D)
    with torch.no_grad():
        y0 = block.direction_scan(x, torch.zeros(1, 4), reverse=False)
        # dt=0 everywhere: a=1, h stays at h0 for every position
        assert torch.allclose(
            y0, block.h0[0].view(1, 1, -1).expand_as(y0), atol=1e-6)
        prev = None
        for scale in (0.01, 0.1, 1.0, 10.0):
            y = block.direction_scan(x, torch.full((1, 4), scale),
                                     reverse=False)
            d = (y - block.h0[0].view(1, 1, -1)).norm()
            if prev is not None:
                assert d >= prev - 1e-6  # larger dt pulls harder off h0
            prev = d


def test_cfc_irregular_dt_changes_output_locally():
    """Perturbing one interval must change hidden states from that position
    on, and must NOT affect the forward scan before it (causality)."""
    torch.manual_seed(0)
    block = CFCBlock(D, HID)
    block.eval()
    x, dt, _ = _inputs()
    dt2 = dt.clone()
    k = L // 2
    dt2[:, k] = 5.0
    with torch.no_grad():
        f1 = block.direction_scan(x, dt, reverse=False)
        f2 = block.direction_scan(x, dt2, reverse=False)
    assert torch.allclose(f1[:, :k], f2[:, :k]), "fwd scan leaked dt backwards"
    assert not torch.allclose(f1[:, k:], f2[:, k:])


def test_cfc_seq_gate_monotone_in_dt():
    """Appendix variant: gate sigmoid(-softplus(f) dt) decays with dt."""
    torch.manual_seed(0)
    cell = _CfCCell(D, HID)
    u = torch.randn(5, D + HID)
    prev = None
    for dt in (0.0, 0.1, 1.0, 10.0, 1000.0):
        w = cell.gate(u, torch.full((5,), dt))
        assert torch.isfinite(w).all() and (w >= 0).all() and (w <= 0.5 + 1e-6).all()
        if prev is not None:
            assert (w <= prev + 1e-6).all()
        prev = w


@pytest.mark.parametrize("name", sorted(LADDER))
def test_param_matching_within_tolerance(name):
    target = count_params(build_temporal_block("ffn", D, hidden=4 * D))
    block = build_temporal_block(name, D, target_params=target)
    achieved = count_params(block)
    assert abs(achieved - target) / target <= 0.01, (
        f"{name}: {achieved} vs target {target}")


def test_node_checkpointing_grads_identical():
    """Gradient checkpointing must be an exact memory/compute trade: same
    forward, same gradients, to float precision."""
    x, dt, _ = _inputs()
    grads = {}
    out_ckpt = None
    for flag in (True, False):
        torch.manual_seed(0)
        block = build_temporal_block("node", D, hidden=HID)
        block.train()
        block.use_checkpoint = flag
        y = block(x.clone().requires_grad_(True), dt)
        y.square().mean().backward()
        grads[flag] = [p.grad.clone() for p in block.parameters()
                       if p.grad is not None]
        if flag:
            out_ckpt = y.detach().clone()
        else:
            assert torch.allclose(out_ckpt, y.detach(), atol=1e-6)
    for ga, gb in zip(grads[True], grads[False]):
        assert torch.allclose(ga, gb, atol=1e-5)


def test_node_deterministic_and_counts_nfe():
    block = _block("node")
    block.eval()
    x, dt, _ = _inputs()
    with torch.no_grad():
        y1 = block(x, dt)
        nfe1 = block.nfe
        y2 = block(x, dt)
    assert torch.allclose(y1, y2)
    assert block.nfe == 2 * nfe1  # NFE accumulates and is loggable


if __name__ == "__main__":
    import sys, traceback
    fns = [(k, v) for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)
           and not hasattr(v, "pytestmark")]
    failed = 0
    for name, fn in fns:
        try:
            fn(); print(f"PASS  {name}")
        except Exception:
            failed += 1; print(f"FAIL  {name}"); traceback.print_exc()
    print(f"\n{len(fns) - failed}/{len(fns)} passed (parametrized tests run "
          f"under pytest only)")
    sys.exit(1 if failed else 0)
