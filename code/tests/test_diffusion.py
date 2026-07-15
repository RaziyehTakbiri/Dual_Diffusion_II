"""Tests for the M3 diffusion core: schedules, forward corruption, objective.

Encodes the spec contracts:
  - alignment identities [R6] (incl. the 1/t anchor for the linear schedule)
  - forward marginals match their tables (statistical)
  - the continuous loss is blind to inactive positions [R8]
  - focal(rho=0, unit weights) == plain CE [R7]

Runnable via pytest or `python tests/test_diffusion.py`.
"""

import torch

from dmd.diffusion.schedules import (ScheduleTables, cosine_alpha_bar,
                                     elbo_ce_weight, mask_prob, step_mask_rate)
from dmd.diffusion.forward import BifurcatedForward
from dmd.diffusion.objective import continuous_loss, discrete_loss, joint_loss

T_D = 1000


def _tables(alignment="sqrt_alpha"):
    return ScheduleTables(T_D, alignment)


def test_schedule_shapes_and_monotonicity():
    for al in ("sqrt_alpha", "alpha", "linear", "independent"):
        tab = _tables(al)
        ab, m, beta, w = tab.alpha_bar, tab.m, tab.beta, tab.w_elbo
        assert len(ab) == T_D + 1 and len(m) == T_D + 1
        assert ab[0] == 1.0 and m[0] == 0.0
        assert (ab[1:] <= ab[:-1] + 1e-12).all(), "alpha_bar must decrease"
        assert (m[1:] >= m[:-1] - 1e-12).all(), "mask prob must increase"
        assert ab[-1] < 0.01 and m[-1] > 0.95
        for x in (beta, w):
            assert (x >= 0).all() and (x <= 1).all()


def test_alignment_identities():
    tab = _tables("sqrt_alpha")
    assert torch.allclose(tab.m, 1.0 - tab.alpha_bar.sqrt())
    tab = _tables("alpha")
    assert torch.allclose(tab.m, 1.0 - tab.alpha_bar)
    # linear-schedule anchor: w_t == 1/t (known masked-diffusion result)
    tab = _tables("linear")
    t = torch.arange(1, T_D + 1, dtype=tab.w_elbo.dtype)
    assert torch.allclose(tab.w_elbo[1:], 1.0 / t, atol=1e-9)


def test_beta_reconstructs_marginal():
    """Simulating the chain with per-step beta must reproduce the marginal m_t."""
    tab = _tables("sqrt_alpha")
    g = torch.Generator().manual_seed(0)
    n = 200_000
    alive = torch.ones(n, dtype=torch.bool)
    for t in (1, 100, 400, 1000):
        # advance the chain from the previous checkpoint to t
        t_prev = {1: 0, 100: 1, 400: 100, 1000: 400}[t]
        for step in range(t_prev + 1, t + 1):
            u = torch.rand(n, generator=g)
            alive &= u >= tab.beta[step]
        emp = 1.0 - alive.float().mean().item()
        assert abs(emp - tab.m[t].item()) < 0.005, (t, emp, tab.m[t].item())


def test_discrete_corruption_marginal_and_identity():
    tab = _tables()
    fwd = BifurcatedForward(tab, vocab_size=2)
    g = torch.Generator().manual_seed(0)
    D0 = torch.randint(0, 2, (1, 200_000), generator=g)
    for t_val in (50, 500, 950):
        t = torch.tensor([t_val])
        D_t, masked = fwd.corrupt_discrete(D0, t, generator=g)
        emp = masked.float().mean().item()
        assert abs(emp - tab.m[t_val].item()) < 0.005
        assert (D_t[masked] == fwd.MASK_ID).all()
        assert (D_t[~masked] == D0[~masked]).all()


def test_continuous_corruption_moments_and_eps_identity():
    tab = _tables()
    fwd = BifurcatedForward(tab, vocab_size=2)
    g = torch.Generator().manual_seed(0)
    C0 = torch.full((1, 200_000, 1), 0.7)
    for t_val in (50, 500, 950):
        t = torch.tensor([t_val])
        C_t, eps = fwd.corrupt_continuous(C0, t, generator=g)
        ab = tab.alpha_bar[t_val]
        assert abs(C_t.mean().item() - (ab.sqrt() * 0.7).item()) < 0.005
        assert abs(C_t.std().item() - (1 - ab).sqrt().item()) < 0.005
        recon = ab.sqrt() * C0 + (1 - ab).sqrt() * eps
        assert torch.allclose(C_t, recon.to(C_t.dtype), atol=1e-6)


def test_joint_call_shares_t_and_is_seed_deterministic():
    tab = _tables()
    fwd = BifurcatedForward(tab, vocab_size=2)
    D0 = torch.randint(0, 2, (4, 64))
    C0 = torch.randn(4, 64, 2)
    outs = []
    for _ in range(2):
        g = torch.Generator().manual_seed(123)
        jc = fwd(D0, C0, generator=g)
        outs.append(jc)
    a, b = outs
    assert torch.equal(a.t, b.t) and torch.equal(a.D_t, b.D_t)
    assert torch.allclose(a.C_t, b.C_t) and a.t.shape == (4,)
    assert a.t.min() >= 1 and a.t.max() <= T_D


def test_discrete_loss_masked_positions_only_and_focal_reduction():
    tab = _tables()
    g = torch.Generator().manual_seed(0)
    B, N, K = 2, 50, 3
    logits = torch.randn(B, N, K, generator=g)
    D0 = torch.randint(0, K, (B, N), generator=g)
    msk = torch.rand(B, N, generator=g) < 0.4
    t = torch.tensor([100, 700])

    base = discrete_loss(logits, D0, msk, t, tab, mode="focal", focal_rho=0.0)
    # plain masked CE, hand-computed
    ce = torch.nn.functional.cross_entropy(
        logits.reshape(-1, K), D0.reshape(-1), reduction="none").reshape(B, N)
    hand = (ce * msk).sum() / msk.sum()
    assert torch.allclose(base, hand, atol=1e-6)

    # garbage logits at UNMASKED positions must not change the loss
    logits2 = logits.clone()
    logits2[~msk] = 1e3
    again = discrete_loss(logits2, D0, msk, t, tab, mode="focal", focal_rho=0.0)
    assert torch.allclose(base, again)

    # elbo mode matches the analytic weight on a single-(t,position) case
    tab_lin = _tables("linear")
    one = discrete_loss(logits, D0, msk, torch.tensor([10, 10]), tab_lin,
                        mode="elbo_ce")
    hand_w = (tab_lin.T_d * (1.0 / 10) * ce * msk).sum() / msk.sum()
    assert torch.allclose(one, hand_w.to(one.dtype), atol=1e-4)


def test_continuous_loss_blind_to_inactive_positions():
    g = torch.Generator().manual_seed(0)
    B, N, K = 2, 40, 2
    eps = torch.randn(B, N, K, generator=g)
    pred = torch.randn(B, N, K, generator=g)
    active = torch.rand(B, N, generator=g) < 0.3

    base = continuous_loss(pred, eps, active)
    pred2 = pred.clone()
    pred2[~active] = 1e4                       # garbage off the mask [R8]
    assert torch.allclose(base, continuous_loss(pred2, eps, active))
    assert not torch.allclose(base, continuous_loss(pred2, eps, active,
                                                    supervise_silent=True))
    m = active.unsqueeze(-1).float()
    hand = (((pred - eps) ** 2) * m).sum() / (m.sum() * K)
    assert torch.allclose(base, hand)


def test_joint_loss_composition():
    tab = _tables()
    g = torch.Generator().manual_seed(0)
    B, N, Kv, Kc = 2, 30, 2, 2
    total, l_d, l_c = joint_loss(
        logits=torch.randn(B, N, Kv, generator=g),
        D0=torch.randint(0, Kv, (B, N), generator=g),
        mask_positions=torch.rand(B, N, generator=g) < 0.5,
        eps_pred=torch.randn(B, N, Kc, generator=g),
        eps=torch.randn(B, N, Kc, generator=g),
        active=torch.rand(B, N, generator=g) < 0.3,
        t=torch.tensor([5, 500]), tables=tab, gamma=2.5,
    )
    assert torch.allclose(total, l_d + 2.5 * l_c)
    assert total.isfinite()


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
