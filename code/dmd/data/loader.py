"""v0.2 dataset loader: npz excerpts -> training tensors (MODEL_SPEC §2, [R14]).

From each excerpt (built by dmd.data.build_music):
  D       (T, P) uint8      -> long {0,1}; MASKing happens in the forward proc.
  C       (T, P, 2) float32 -> C_pitch; channels [velocity, residual] as-is
                               (velocity in [0,1] is roughly [0,1]-ranged; the
                               VP process is variance-preserving on the
                               standardized scale below)
  Delta   (T,) float64      -> C_step = (log Delta - mu_logd) / sd_logd  [R14]
                               (per-CORPUS statistics, stored with the dataset
                               so generation can invert exactly)

Standardization of C_pitch: velocity -> (v - 0.5) * 2 (range ~[-1, 1]);
residual r_norm in (-1/2, 1/2] -> * 2 (range ~[-1, 1]). Inverses live here too
so samplers/metrics can round-trip without duplicating constants.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np
import torch


@dataclass
class CorpusStats:
    mu_logd: float
    sd_logd: float

    def as_dict(self):
        return {"mu_logd": self.mu_logd, "sd_logd": self.sd_logd}


def standardize_pitch(C: torch.Tensor) -> torch.Tensor:
    out = C.clone()
    out[..., 0] = (out[..., 0] - 0.5) * 2.0
    out[..., 1] = out[..., 1] * 2.0
    return out


def destandardize_pitch(C: torch.Tensor) -> torch.Tensor:
    out = C.clone()
    out[..., 0] = out[..., 0] / 2.0 + 0.5
    out[..., 1] = out[..., 1] / 2.0
    return out


def delta_to_step_channel(delta: torch.Tensor, stats: CorpusStats) -> torch.Tensor:
    return (delta.clamp_min(1e-4).log() - stats.mu_logd) / stats.sd_logd


def step_channel_to_delta(c_step: torch.Tensor, stats: CorpusStats) -> torch.Tensor:
    return (c_step * stats.sd_logd + stats.mu_logd).exp()


class ExcerptDataset(torch.utils.data.Dataset):
    """Loads one npz produced by build_music. Returns per item:
    D (T,P) long {0,1}; C_pitch (T,P,2) float standardized; C_step (T,1) float;
    delta (T,) float seconds; active (T,P) bool."""

    def __init__(self, npz_path: str, stats: Optional[CorpusStats] = None):
        z = np.load(npz_path)
        self.D = torch.from_numpy(z["D"]).long()
        self.C = torch.from_numpy(z["C"]).float()
        self.delta = torch.from_numpy(z["Delta"]).float()
        logd = self.delta.clamp_min(1e-4).log()
        self.stats = stats or CorpusStats(float(logd.mean()),
                                          float(logd.std().clamp_min(1e-3)))

    def __len__(self):
        return len(self.D)

    def __getitem__(self, i) -> Dict[str, torch.Tensor]:
        D = self.D[i]
        C_pitch = standardize_pitch(self.C[i])
        delta = self.delta[i]
        C_step = delta_to_step_channel(delta, self.stats).unsqueeze(-1)
        return {"D": D, "C_pitch": C_pitch, "C_step": C_step,
                "delta": delta, "active": D.bool()}


def make_loader(npz_path: str, batch_size: int, shuffle: bool = True,
                stats: Optional[CorpusStats] = None, seed: int = 0,
                num_workers: int = 0) -> Tuple[torch.utils.data.DataLoader,
                                               CorpusStats]:
    ds = ExcerptDataset(npz_path, stats)
    g = torch.Generator().manual_seed(seed)
    dl = torch.utils.data.DataLoader(ds, batch_size=batch_size,
                                     shuffle=shuffle, generator=g,
                                     num_workers=num_workers, drop_last=True)
    return dl, ds.stats
