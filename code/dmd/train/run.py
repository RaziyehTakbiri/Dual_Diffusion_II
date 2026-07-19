"""Trainer v1 (M5): minimal, correct, single-process.

Deliberately deferred to the next iteration: MLflow autologging, DDP/
TorchDistributor, mid-run checkpoint resume. Present and correct now:
config-driven build, [R9] gamma from gradient-norm matching at init, EMA,
cosine LR with warmup, loss = discrete (focal|elbo_ce) + gamma * (masked
pitch MSE + step MSE), deterministic seeding, JSON metrics log, checkpoint.

Notebook usage:
  from dmd.train.run import main
  main(["--config", f"{CODE_DIR}/configs/music_cfc.yaml",
        "--data", "/dbfs/.../maestro_asap_all.npz",
        "--out", "/dbfs/.../runs/cfc_seed0", "--seed", "0",
        "--max_steps", "200"])   # override for smoke runs
"""

from __future__ import annotations

import argparse
import json
import math
import os
import time
from typing import Dict, List, Optional

import torch
import yaml

from dmd.data.loader import make_loader
from dmd.diffusion.forward import BifurcatedForward
from dmd.diffusion.objective import continuous_loss, discrete_loss, grad_match_gamma
from dmd.diffusion.schedules import ScheduleTables
from dmd.models.denoiser import DualManifoldDenoiser
from dmd.blocks.temporal import build_temporal_block
from dmd.utils.params import count_params


def build_model(cfg: Dict, device) -> DualManifoldDenoiser:
    mc = cfg["model"]
    d = mc["d_model"]
    target = None
    if mc.get("param_match", {}).get("reference", "ffn") == "ffn":
        target = count_params(build_temporal_block("ffn", d, hidden=4 * d))
    model = DualManifoldDenoiser(
        P=cfg["data"]["P"], K=cfg["data"]["K"], K_step=1,
        d_model=d, n_layers=mc["trunk_layers"], n_heads=mc.get("n_heads", 8),
        block=mc["block"], block_target_params=target,
        max_T=cfg["data"]["T"],
    ).to(device)
    return model


def load_checkpoint(path: str, device: str = "cpu", use_ema: bool = True):
    """Reconstruct model + schedules + corpus stats FROM the checkpoint's own
    stored config. The single supported way to load a trained model - manual
    reconstruction drifts from the trainer (param-matched widths, 2026-07-15)
    and is therefore banned in notebooks and evaluation code.

    Returns (model.eval(), ScheduleTables, CorpusStats, config_dict)."""
    from dmd.data.loader import CorpusStats

    ck = torch.load(path, map_location=device, weights_only=False)
    model = build_model(ck["config"], torch.device(device))
    model.load_state_dict(ck["ema" if use_ema else "model"])
    model.eval()
    tables = ScheduleTables(ck["config"]["diffusion"]["T_d"],
                            ck["config"]["diffusion"]["schedule_alignment"])
    return model, tables, CorpusStats(**ck["corpus_stats"]), ck["config"]


def losses_for_batch(model, fwd, tables, batch, cfg, device, tau: float,
                     gamma: float, generator=None):
    D0 = batch["D"].to(device)                       # (B,T,P) {0,1}
    Cp0 = batch["C_pitch"].to(device)
    Cs0 = batch["C_step"].to(device)
    delta = batch["delta"].to(device)
    active = batch["active"].to(device)
    B, T, P = D0.shape

    t = fwd.sample_t(B, device, generator)
    D_t_flat, masked_flat = fwd.corrupt_discrete(D0.reshape(B, -1), t, generator)
    Cp_t, eps_p = fwd.corrupt_continuous(Cp0, t, generator)
    Cs_t, eps_s = fwd.corrupt_continuous(Cs0, t, generator)

    out = model(D_t_flat.reshape(B, T, P), Cp_t, Cs_t, delta, t, tau=tau,
                coupling=cfg["model"].get("coupling", "gumbel"),
                generator=generator)

    l_d = discrete_loss(out.logits.reshape(B, T * P, 2), D0.reshape(B, -1),
                        masked_flat, t, tables,
                        mode=cfg["loss"]["discrete"],
                        focal_rho=cfg["loss"]["focal"]["rho"])
    l_cp = continuous_loss(out.eps_pitch.reshape(B, T * P, -1),
                           eps_p.reshape(B, T * P, -1),
                           active.reshape(B, -1),
                           supervise_silent=cfg["loss"]["supervise_silent"])
    l_cs = continuous_loss(out.eps_step, eps_s,
                           torch.ones(B, T, dtype=torch.bool, device=device))
    return l_d, l_cp + l_cs


def main(argv: Optional[List[str]] = None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", required=True)
    ap.add_argument("--data", required=True, help="training npz")
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--max_steps", type=int, default=0, help="0 = from config")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available()
                    else "cpu")
    ap.add_argument("--log_every", type=int, default=25)
    args = ap.parse_args(argv)

    with open(args.config) as fh:
        cfg = yaml.safe_load(fh)
    os.makedirs(args.out, exist_ok=True)
    torch.manual_seed(args.seed)
    device = torch.device(args.device)
    # explicit generator only on CPU: torch.rand(device=cuda, generator=cpu)
    # is illegal; on GPU, global torch.manual_seed governs determinism
    gen = (torch.Generator(device="cpu").manual_seed(args.seed)
           if device.type == "cpu" else None)

    dl, stats = make_loader(args.data, cfg["train"]["batch_size"],
                            seed=args.seed)
    tables = ScheduleTables(cfg["diffusion"]["T_d"],
                            cfg["diffusion"]["schedule_alignment"])
    fwd = BifurcatedForward(tables, vocab_size=2)
    model = build_model(cfg, device)
    n_params = count_params(model)

    max_steps = args.max_steps or cfg["train"]["max_steps"]
    warmup = min(cfg["train"].get("warmup_steps", 2000), max(max_steps // 10, 1))
    base_lr = float(cfg["train"]["lr"])
    opt = torch.optim.AdamW(model.parameters(), lr=base_lr, weight_decay=0.01)
    ema = {k: v.detach().clone() for k, v in model.state_dict().items()}
    ema_decay = float(cfg["train"].get("ema", 0.999))

    # ---- [R9] gamma from gradient-norm matching on the first batch
    tau0 = float(cfg["model"]["tau"]["start"])
    first = next(iter(dl))
    l_d, l_c = losses_for_batch(model, fwd, tables, first, cfg, device,
                                tau0, 1.0, gen)
    gnorm = {}
    for name, loss in (("d", l_d), ("c", l_c)):
        opt.zero_grad(set_to_none=True)
        loss.backward(retain_graph=(name == "d"))
        gnorm[name] = math.sqrt(sum(float((p.grad ** 2).sum())
                                    for p in model.parameters()
                                    if p.grad is not None))
    gamma = (float(cfg["loss"]["gamma"])
             if str(cfg["loss"]["gamma"]).replace(".", "").isdigit()
             else grad_match_gamma(gnorm["d"], gnorm["c"]))
    opt.zero_grad(set_to_none=True)

    log = {"config": cfg, "seed": args.seed, "n_params": n_params,
           "gamma": gamma, "grad_norms_init": gnorm,
           "corpus_stats": stats.as_dict(), "history": []}
    print(f"params={n_params:,} gamma={gamma:.4f} device={device} "
          f"steps={max_steps}")

    step, t0 = 0, time.time()
    tau_s, tau_e = tau0, float(cfg["model"]["tau"]["end"])
    while step < max_steps:
        for batch in dl:
            if step >= max_steps:
                break
            frac = step / max_steps
            tau = tau_e + 0.5 * (tau_s - tau_e) * (1 + math.cos(math.pi * frac))
            for pg in opt.param_groups:
                pg["lr"] = base_lr * (min(1.0, (step + 1) / warmup)
                                      * 0.5 * (1 + math.cos(math.pi * frac)))
            l_d, l_c = losses_for_batch(model, fwd, tables, batch, cfg,
                                        device, tau, gamma, gen)
            loss = l_d + gamma * l_c
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            with torch.no_grad():
                for k, v in model.state_dict().items():
                    if v.dtype.is_floating_point:
                        ema[k].mul_(ema_decay).add_(v, alpha=1 - ema_decay)
            if step % args.log_every == 0 or step == max_steps - 1:
                rec = {"step": step, "loss": float(loss), "l_d": float(l_d),
                       "l_c": float(l_c), "tau": tau,
                       "lr": opt.param_groups[0]["lr"],
                       "sec": round(time.time() - t0, 1)}
                if device.type == "cuda":
                    rec["peak_gb"] = round(
                        torch.cuda.max_memory_allocated() / 2**30, 2)
                    torch.cuda.reset_peak_memory_stats()
                log["history"].append(rec)
                print(rec)
            step += 1

    torch.save({"model": model.state_dict(), "ema": ema, "config": cfg,
                "gamma": gamma, "corpus_stats": stats.as_dict(),
                "seed": args.seed, "step": step},
               os.path.join(args.out, "ckpt.pt"))
    with open(os.path.join(args.out, "train_log.json"), "w") as fh:
        json.dump(log, fh, indent=2)
    print(f"saved -> {args.out}")
    return log


if __name__ == "__main__":
    main()
