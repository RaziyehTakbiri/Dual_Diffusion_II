"""CPU unit tests for the temporal-block ladder.

These tests encode the *scientific* contract, not just shapes:
- rungs declared dt-blind (B0-B3) must be exactly invariant to dt;
- rungs declared dt-aware (B4-B5) must respond to dt;
- CFC decay gate must be monotone in dt;
- all rungs must be parameter-matchable within 1%.
"""

import pytest
import torch

from dmd.blocks.temporal import LADDER, CFCBlock, build_temporal_block, _CfCCell
from dmd.utils.params import count_params, match_width

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


def test_cfc_gate_monotone_in_dt():
    torch.manual_seed(0)
    cell = _CfCCell(D, HID)
    u = torch.randn(5, D + HID)
    dts = torch.tensor([0.0, 0.1, 1.0, 10.0, 1000.0])
    prev = None
    for dt in dts:
        w = cell.gate(u, dt.expand(5))
        assert torch.isfinite(w).all() and (w >= 0).all() and (w <= 0.5 + 1e-6).all()
        if prev is not None:
            assert (w <= prev + 1e-6).all(), "gate must decay as dt grows"
        prev = w
    # dt=0 limit: gate exactly 1/2 (MODEL_SPEC [R11])
    w0 = cell.gate(u, torch.zeros(5))
    assert torch.allclose(w0, torch.full_like(w0, 0.5))


def test_cfc_irregular_dt_changes_output_locally():
    """Perturbing one interval must change hidden states, and the forward scan
    must not be affected *before* the perturbed index (causality of the scan)."""
    torch.manual_seed(0)
    block = CFCBlock(D, HID)
    block.eval()
    x, dt, _ = _inputs()
    dt2 = dt.clone()
    k = L // 2
    dt2[:, k] = 5.0
    with torch.no_grad():
        f1 = block._scan(block.fwd, x, dt, block.h0[0], reverse=False)
        f2 = block._scan(block.fwd, x, dt2, block.h0[0], reverse=False)
    assert torch.allclose(f1[:, :k], f2[:, :k]), "fwd scan leaked dt backwards"
    assert not torch.allclose(f1[:, k:], f2[:, k:])


@pytest.mark.parametrize("name", sorted(LADDER))
def test_param_matching_within_tolerance(name):
    target = count_params(build_temporal_block("ffn", D, hidden=4 * D))
    block = build_temporal_block(name, D, target_params=target)
    achieved = count_params(block)
    assert abs(achieved - target) / target <= 0.01, (
        f"{name}: {achieved} vs target {target}"
    )


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
