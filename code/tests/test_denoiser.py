"""M4 denoiser tests. The scientific contracts, unit-tested:

  1. shapes/dtypes/finiteness at model scale (small trunk)
  2. COUPLING: gradients from a continuous-only loss reach the structure
     head through the Gumbel bridge; are BLOCKED when coupling='detached'
     (the manuscript asserted this property; here it is proven)
  3. diffusion-time conditioning changes the output (adaLN path alive)
  4. dt-aware rungs respond to delta through the trunk; dt-blind rungs don't
  5. ladder rungs are parameter-matched at the whole-model level

Runnable via pytest or `python tests/test_denoiser.py`.
"""

import torch

from dmd.models.denoiser import DualManifoldDenoiser
from dmd.utils.params import count_params

B, T, P, K = 2, 32, 88, 2
SMALL = dict(P=P, K=K, d_model=64, n_layers=2, n_heads=4, max_T=T)


def _inputs(seed=0):
    g = torch.Generator().manual_seed(seed)
    D = torch.randint(0, 3, (B, T, P), generator=g)
    Cp = torch.randn(B, T, P, K, generator=g)
    Cs = torch.randn(B, T, 1, generator=g)
    dt = torch.rand(B, T, generator=g) + 0.05
    t = torch.tensor([100, 700])
    return D, Cp, Cs, dt, t


def _model(block="cfc", seed=0, **kw):
    torch.manual_seed(seed)
    return DualManifoldDenoiser(block=block, **{**SMALL, **kw})


def test_shapes_and_finiteness():
    m = _model()
    out = m(*_inputs(), tau=1.0)
    assert out.logits.shape == (B, T, P, 2)
    assert out.eps_pitch.shape == (B, T, P, K)
    assert out.eps_step.shape == (B, T, 1)
    assert out.relaxed.shape == (B, T, P)
    for x in (out.logits, out.eps_pitch, out.eps_step, out.relaxed):
        assert torch.isfinite(x).all()


def test_coupling_gradient_reaches_structure_head():
    """The claim behind manuscript Eq. (7), as an executable assertion."""
    for mode, expects_grad in (("gumbel", True), ("straight_through", True),
                               ("detached", False), ("none", False)):
        m = _model()
        g = torch.Generator().manual_seed(0)
        out = m(*_inputs(), tau=1.0, coupling=mode, generator=g)
        loss = (out.eps_pitch ** 2).mean() + (out.eps_step ** 2).mean()
        loss.backward()
        grad = m.head_structure.weight.grad
        has = grad is not None and grad.abs().sum() > 0
        assert has == expects_grad, f"coupling={mode}: grad={has}"


def test_time_conditioning_changes_output():
    m = _model(); m.eval()
    D, Cp, Cs, dt, _ = _inputs()
    g1 = torch.Generator().manual_seed(0)
    g2 = torch.Generator().manual_seed(0)
    with torch.no_grad():
        a = m(D, Cp, Cs, dt, torch.tensor([10, 10]), coupling="gumbel", generator=g1)
        b = m(D, Cp, Cs, dt, torch.tensor([900, 900]), coupling="gumbel", generator=g2)
    assert not torch.allclose(a.logits, b.logits)


def test_delta_sensitivity_propagates_through_trunk():
    D, Cp, Cs, dt, t = _inputs()
    dt2 = dt.clone(); dt2[:, T // 2:] *= 3.0
    for block, expects in (("cfc", True), ("gated_ffn", False), ("gru", False)):
        m = _model(block); m.eval()
        with torch.no_grad():
            a = m(D, Cp, Cs, dt, t, coupling="none")
            b = m(D, Cp, Cs, dt2, t, coupling="none")
        differs = not torch.allclose(a.logits, b.logits)
        assert differs == expects, f"{block}: delta-sensitivity={differs}"


def test_whole_model_param_matching_across_ladder():
    # d_model=128, not smaller: recurrent-rung width granularity cannot hit
    # the 1% block tolerance below d~128 (see tests/test_temporal_blocks.py).
    from dmd.blocks.temporal import build_temporal_block
    dims = dict(P=P, K=K, d_model=128, n_layers=2, n_heads=4, max_T=T)
    torch.manual_seed(0)
    ref = DualManifoldDenoiser(block="ffn", block_hidden=4 * 128, **dims)
    target_block = count_params(build_temporal_block("ffn", 128, hidden=4 * 128))
    n_ref = count_params(ref)
    for block in ("gated_ffn", "gru", "cfc", "node"):
        torch.manual_seed(0)
        m = DualManifoldDenoiser(block=block, block_target_params=target_block,
                                 **dims)
        rel = abs(count_params(m) - n_ref) / n_ref
        assert rel < 0.01, f"{block}: whole-model mismatch {rel:.3%}"


if __name__ == "__main__":
    import sys, traceback
    fns = [(k, v) for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    failed = 0
    for name, fn in fns:
        try:
            fn(); print(f"PASS  {name}")
        except Exception:
            failed += 1; print(f"FAIL  {name}"); traceback.print_exc()
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
