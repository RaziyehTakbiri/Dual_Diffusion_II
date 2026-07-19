# Databricks notebook source
# MAGIC %md
# MAGIC # Speed check — seconds per training step, per model, at full size
# MAGIC
# MAGIC Run this BEFORE launching long training runs. It builds each of the six
# MAGIC models at full size (d=512, 12 layers), times 3 training steps on one
# MAGIC GPU, and prints the projected hours for a 100,000-step run.
# MAGIC
# MAGIC Takes about 3 minutes. Needs one GPU (ML runtime).

# COMMAND ----------

CODE_DIR = "/Workspace/Users/Hadi.Mohebalizadeh@nike.com/Diffusion II/Dual_Diffusion_II/code"

import sys, time
sys.path.insert(0, CODE_DIR)
for _m in [m for m in list(sys.modules) if m == "dmd" or m.startswith("dmd.")]:
    del sys.modules[_m]
import torch
assert torch.cuda.is_available(), "needs a GPU cluster"

from dmd.blocks.temporal import build_temporal_block
from dmd.models.denoiser import DualManifoldDenoiser
from dmd.utils.params import count_params

D_MODEL, LAYERS, HEADS, BATCH, T, P = 512, 12, 8, 64, 256, 88
target = count_params(build_temporal_block("ffn", D_MODEL, hidden=4 * D_MODEL))

def time_block(block_name, n_steps=3):
    torch.manual_seed(0)
    m = DualManifoldDenoiser(P=P, K=2, d_model=D_MODEL, n_layers=LAYERS,
                             n_heads=HEADS, block=block_name,
                             block_target_params=target, max_T=T).cuda()
    opt = torch.optim.AdamW(m.parameters(), lr=1e-4)
    D = torch.randint(0, 3, (BATCH, T, P), device="cuda")
    Cp = torch.randn(BATCH, T, P, 2, device="cuda")
    Cs = torch.randn(BATCH, T, 1, device="cuda")
    dt = torch.rand(BATCH, T, device="cuda") * 0.2 + 0.05
    t = torch.randint(1, 1001, (BATCH,), device="cuda")
    # one warm-up step (compilation, allocator), then timed steps
    times = []
    for s in range(n_steps + 1):
        torch.cuda.synchronize(); t0 = time.time()
        out = m(D, Cp, Cs, dt, t, coupling="gumbel")
        loss = ((out.eps_pitch ** 2).mean() + (out.eps_step ** 2).mean()
                + out.logits.square().mean())
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        torch.cuda.synchronize()
        if s > 0:
            times.append(time.time() - t0)
    peak = torch.cuda.max_memory_allocated() / 2**30
    torch.cuda.reset_peak_memory_stats()
    del m, opt
    torch.cuda.empty_cache()
    return sum(times) / len(times), peak

print(f"{'model':<14}{'sec/step':>10}{'hours/100k':>12}{'peak GB':>9}")
for name in ("ffn", "gated_ffn", "gru", "cfc", "node"):
    try:
        spd, peak = time_block(name)
        print(f"{name:<14}{spd:>10.2f}{spd * 100_000 / 3600:>12.1f}{peak:>9.1f}")
    except torch.cuda.OutOfMemoryError:
        print(f"{name:<14}{'OOM':>10} - report to Claude")
        torch.cuda.empty_cache()

print("\nDecision rule: if cfc is under ~0.5 sec/step (~14 h per run) and node")
print("is under ~1.0 (~28 h), launch the remaining grid runs. Otherwise send")
print("this table to Claude before launching anything.")
