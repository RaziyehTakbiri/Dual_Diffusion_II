"""Round-trip representation validator (agenda E4.2, MODEL_SPEC §2).

Quantifies exactly what the representation can and cannot carry:
  keep rate      - notes surviving encoding (collisions drop notes)
  wrap rate      - residuals clipped at half-grid (lossy)
  onset MAE/max  - decode(encode(x)) onset error over kept, UNWRAPPED notes;
                   must sit at float precision, since residuals are stored
                   exactly - anything larger is a pipeline bug
  velocity exact - after 1/127 quantization, round-trip velocities are exact
  residual sigma - micro-timing spread in ms (the signal the paper is about)
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from dmd.data.music import PITCH_LO, Encoded, NoteSeq


@dataclass
class RoundTripReport:
    n_notes: int
    keep_rate: float
    collision_rate: float
    wrap_rate: float
    onset_mae_ms: float      # over kept & unwrapped notes
    onset_max_ms: float
    velocity_exact_rate: float
    residual_sigma_ms: float

    def as_dict(self):
        return asdict(self)


def round_trip_report(notes: NoteSeq, enc: Encoded) -> RoundTripReport:
    """Pairwise comparison with no matching heuristic: each kept note's
    (cell, pitch) is unique after collision dropping, so it addresses its own
    entries in (D, C) directly."""
    n = len(notes)
    sel = enc.kept & ~enc.wrapped
    idx = np.nonzero(sel)[0]
    cells = enc.cell[idx]
    pidx = notes.pitch[idx] - PITCH_LO

    dec_onset = (enc.grid.times[cells]
                 + enc.C[cells, pidx, 1].astype(np.float64) * enc.grid.delta[cells])
    dec_vel = np.clip(np.rint(enc.C[cells, pidx, 0] * 127.0), 1, 127)

    err_ms = np.abs(notes.onset[idx] - dec_onset) * 1000.0
    vel_ok = float((notes.velocity[idx] == dec_vel).mean()) if len(idx) else 1.0

    active = enc.D.astype(bool)
    r = enc.C[active][:, 1].astype(np.float64)
    d = np.broadcast_to(enc.grid.delta[:, None], enc.D.shape)[active]
    return RoundTripReport(
        n_notes=n,
        keep_rate=float(enc.kept.mean()) if n else 1.0,
        collision_rate=enc.n_collisions / max(n, 1),
        wrap_rate=enc.n_wraps / max(n, 1),
        onset_mae_ms=float(err_ms.mean()) if len(err_ms) else 0.0,
        onset_max_ms=float(err_ms.max()) if len(err_ms) else 0.0,
        velocity_exact_rate=vel_ok,
        residual_sigma_ms=float((r * d).std() * 1000.0) if len(r) else 0.0,
    )
