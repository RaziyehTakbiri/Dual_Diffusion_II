"""Music representation (MODEL_SPEC.md §2, revisions [R3]-[R5]).

Pure-numpy core: MIDI I/O is a thin optional adapter (pretty_midi), so the
encode/decode/analysis logic is unit-testable against synthetic ground truth
without any dataset present.

Representation summary
    D      (G, P) uint8   onset indicator per grid cell x pitch
    C      (G, P, 2)      [velocity/127, residual r / delta_ref] on active cells
    Delta  (G,)           local grid step in seconds (irregular grids supported)
    M = D                 activity mask; C is UNDEFINED off the mask [R2]

Grids ([R3]): `asap` (annotated beats, subdivided), `fixed` (legacy: single
period + phase fit by a Fourier comb), `tracked` (windowed fixed fit,
EXPERIMENTAL). Durations are not modeled in v0.1 (matches manuscript scope).

Open item for spec v0.2: sustain/duration channel.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

PITCH_LO, PITCH_HI = 21, 108
P = PITCH_HI - PITCH_LO + 1  # 88


# ---------------------------------------------------------------- containers
@dataclass
class NoteSeq:
    """Plain sorted note arrays. Filters out-of-range pitches, velocity 0."""

    onset: np.ndarray
    pitch: np.ndarray
    velocity: np.ndarray

    def __post_init__(self):
        o = np.asarray(self.onset, dtype=np.float64)
        p = np.asarray(self.pitch, dtype=np.int64)
        v = np.asarray(self.velocity, dtype=np.int64)
        ok = (p >= PITCH_LO) & (p <= PITCH_HI) & (v > 0)
        order = np.argsort(o[ok], kind="stable")
        self.onset, self.pitch, self.velocity = o[ok][order], p[ok][order], v[ok][order]

    def __len__(self):
        return len(self.onset)


@dataclass
class Grid:
    """Grid-point times (strictly increasing) + provenance."""

    times: np.ndarray
    source: str = "unknown"
    subdivision: int = 4  # grid points per beat (metrical position = k % subdivision
    #                       is meaningful only for beat-anchored grids: asap/synthetic)

    def __post_init__(self):
        self.times = np.asarray(self.times, dtype=np.float64)
        if len(self.times) < 2 or np.any(np.diff(self.times) <= 0):
            raise ValueError("grid needs >=2 strictly increasing times")

    @property
    def delta(self) -> np.ndarray:
        """Local step: gap to next grid point; last gap duplicated."""
        d = np.diff(self.times)
        return np.concatenate([d, d[-1:]])


# ------------------------------------------------------------- grid builders
def grid_from_beats(beat_times: np.ndarray, subdivision: int = 4,
                    source: str = "asap") -> Grid:
    """Subdivide consecutive annotated beats linearly; extend one beat at end."""
    b = np.asarray(beat_times, dtype=np.float64)
    if len(b) < 2:
        raise ValueError("need >=2 beats")
    b = np.concatenate([b, [b[-1] + (b[-1] - b[-2])]])
    frac = np.arange(subdivision) / subdivision
    pts = (b[:-1, None] + frac[None, :] * np.diff(b)[:, None]).ravel()
    return Grid(np.append(pts, b[-1]), source=source, subdivision=subdivision)


def beats_from_annotation_txt(path: str) -> Tuple[np.ndarray, np.ndarray]:
    """Parse an ASAP-style annotation file.

    Robust to minor format variants: per line, first parseable float = beat
    time; downbeat iff 'db' appears in the last field. Returns (times, is_db).
    VERIFY against the concrete ASAP files once access lands (PROGRESS E4.1).
    """
    times, is_db = [], []
    with open(path) as fh:
        for line in fh:
            parts = line.split()
            if not parts:
                continue
            try:
                t = float(parts[0])
            except ValueError:
                continue
            times.append(t)
            is_db.append("db" in parts[-1].lower())
    if len(times) < 2:
        raise ValueError(f"no beats parsed from {path}")
    return np.asarray(times), np.asarray(is_db, dtype=bool)


def comb_amplitude(onsets: np.ndarray, delta: float) -> float:
    """Fourier comb fit |mean exp(2*pi*i*onset/delta)| in [0, 1].

    Phase-free: high whenever values CLUSTER modulo delta (suitable for
    absolute onsets, where grid phase is unknown)."""
    ang = 2.0 * math.pi * onsets / delta
    return float(np.hypot(np.cos(ang).mean(), np.sin(ang).mean()))


def comb_score(values: np.ndarray, delta: float) -> float:
    """Signed comb fit mean(cos(2*pi*values/delta)) in [-1, 1].

    Peaks at +1 only when values are integer MULTIPLES of delta - the right
    criterion for inter-onset intervals. (The phase-free amplitude is wrong
    there: near-constant IOIs cluster mod ANY larger delta and score high.)"""
    return float(np.cos(2.0 * math.pi * values / delta).mean())


def estimate_fixed_grid(
    onsets: np.ndarray,
    delta_lo: float = 0.05,
    delta_hi: float = 0.5,
    n_coarse: int = 600,
    rel_tol: float = 0.95,
    subdivision: int = 4,
) -> Grid:
    """Legacy single-period grid ([R3] fallback), deterministic. Two stages:

    1. Period from INTER-ONSET INTERVALS: the comb amplitude on absolute
       onsets has peak width ~delta^2/span (far below any feasible scan
       resolution on multi-minute pieces - a scan there locks onto whichever
       harmonic a candidate happens to graze). IOIs are bounded (<2 s), so the
       IOI comb peak is wide enough for a coarse scan. IOI combs still peak at
       delta AND its integer subdivisions delta/k (never at multiples with
       mixed IOI multiplicities), so among candidates within `rel_tol` of the
       max we take the LARGEST step: the coarsest grid consistent with the
       data. If a piece contains only even multiples of the notated sixteenth
       (no sixteenth-note IOIs at all), the estimator returns that coarser
       step by design.
    2. Exact step + phase by sequential unwrapping and least squares:
       k_i = k_{i-1} + round((o_i - o_{i-1})/delta0), then regress
       o ~ phase + delta * k (one refinement iteration).
    """
    onsets = np.asarray(onsets, dtype=np.float64)
    if len(onsets) < 8:
        raise ValueError("too few onsets to estimate a grid")
    iois = np.diff(onsets)
    iois = iois[(iois > 0.020) & (iois < 2.0)]
    if len(iois) < 8:
        raise ValueError("too few usable inter-onset intervals")

    cand = np.geomspace(delta_lo, delta_hi, n_coarse)
    score = np.array([comb_score(iois, d) for d in cand])
    if score.max() < 0.1:  # no periodic structure detected - degenerate input
        delta = float(np.median(iois))
    else:
        best = cand[score >= rel_tol * score.max()].max()
        fine = np.linspace(best * 0.97, best * 1.03, 400)
        delta = float(fine[np.argmax([comb_score(iois, d) for d in fine])])
    if np.median(np.rint(iois / delta)) < 1:  # grid coarser than typical IOI
        delta = float(np.median(iois))

    phase = float(onsets[0])
    for _ in range(2):  # unwrap -> regress, then refine once with better delta
        k = np.concatenate([[0], np.cumsum(np.rint(np.diff(onsets) / delta))])
        if k[-1] <= 0:  # degenerate unwrapping; keep stage-1 estimate
            break
        A = np.stack([np.ones_like(k), k], axis=1)
        sol, *_ = np.linalg.lstsq(A, onsets, rcond=None)
        if (not np.all(np.isfinite(sol))
                or not delta_lo / 4 <= sol[1] <= delta_hi * 8):
            break
        phase, delta = float(sol[0]), float(sol[1])

    k_lo = math.floor((onsets.min() - phase) / delta) - 1
    k_hi = math.ceil((onsets.max() - phase) / delta) + 2
    times = phase + delta * np.arange(k_lo, k_hi)
    return Grid(times, source="fixed", subdivision=subdivision)


def tracked_grid(onsets: np.ndarray, window_s: float = 12.0,
                 subdivision: int = 4, **est_kw) -> Grid:
    """EXPERIMENTAL windowed tempo grid: piecewise step, phase-continuous.

    Placeholder for a proper beat tracker; kept only so `grid.source` has a
    third arm in comparisons. Prefer `asap`.
    """
    onsets = np.asarray(onsets, dtype=np.float64)
    span = onsets.max() - onsets.min()
    n_win = max(1, int(round(span / window_s)))
    edges = np.linspace(onsets.min(), onsets.max(), n_win + 1)
    centers, steps = [], []
    for a, b in zip(edges[:-1], edges[1:]):
        sel = onsets[(onsets >= a - 2.0) & (onsets <= b + 2.0)]
        if len(sel) >= 8:
            g = estimate_fixed_grid(sel, subdivision=subdivision, **est_kw)
            centers.append(0.5 * (a + b))
            steps.append(float(np.median(np.diff(g.times))))
    if not centers:
        return estimate_fixed_grid(onsets, subdivision=subdivision, **est_kw)
    t, times = onsets.min() - steps[0], [onsets.min() - steps[0]]
    while t < onsets.max() + steps[-1]:
        t += float(np.interp(t, centers, steps))
        times.append(t)
    return Grid(np.asarray(times), source="tracked", subdivision=subdivision)


# ------------------------------------------------------------- encode/decode
@dataclass
class Encoded:
    D: np.ndarray          # (G, P) uint8
    C: np.ndarray          # (G, P, 2) float32; garbage off-mask by design [R2]
    grid: Grid
    kept: np.ndarray       # (n_notes,) bool - survived encoding
    cell: np.ndarray       # (n_notes,) int  - grid index (kept notes; -1 else)
    wrapped: np.ndarray    # (n_notes,) bool - residual clipped to +/-0.5
    n_wraps: int           # residuals clipped to +/-0.5 (half-grid overflow)
    n_collisions: int      # same (cell, pitch) already occupied - note dropped

    @property
    def delta(self) -> np.ndarray:
        return self.grid.delta


def encode(notes: NoteSeq, grid: Grid) -> Encoded:
    """Nearest-grid assignment; residual normalized by the local step [R4].

    Collisions keep the EARLIEST note (stable, documented); wrap events are
    clipped and counted - both rates are round-trip-audited (E4.2).
    """
    G = len(grid.times)
    D = np.zeros((G, P), dtype=np.uint8)
    C = np.zeros((G, P, 2), dtype=np.float32)
    kept = np.zeros(len(notes), dtype=bool)
    cell = np.full(len(notes), -1, dtype=np.int64)
    wrapped = np.zeros(len(notes), dtype=bool)
    delta_ref = grid.delta
    n_wraps = n_coll = 0

    right = np.searchsorted(grid.times, notes.onset)
    for i in range(len(notes)):
        k = right[i]
        cands = [c for c in (k - 1, k) if 0 <= c < G]
        k_star = min(cands, key=lambda c: abs(notes.onset[i] - grid.times[c]))
        p_idx = notes.pitch[i] - PITCH_LO
        if D[k_star, p_idx]:
            n_coll += 1
            continue
        r_norm = (notes.onset[i] - grid.times[k_star]) / delta_ref[k_star]
        if abs(r_norm) > 0.5:
            n_wraps += 1
            wrapped[i] = True
            r_norm = float(np.clip(r_norm, -0.5, 0.5))
        D[k_star, p_idx] = 1
        C[k_star, p_idx, 0] = notes.velocity[i] / 127.0
        C[k_star, p_idx, 1] = r_norm
        kept[i], cell[i] = True, k_star
    return Encoded(D, C, grid, kept, cell, wrapped, n_wraps, n_coll)


def decode(D: np.ndarray, C: np.ndarray, grid: Grid) -> NoteSeq:
    """Inverse map on the mask; exact for kept, unwrapped notes."""
    t_idx, p_idx = np.nonzero(D)
    onset = grid.times[t_idx] + C[t_idx, p_idx, 1].astype(np.float64) * grid.delta[t_idx]
    vel = np.clip(np.rint(C[t_idx, p_idx, 0] * 127.0), 1, 127).astype(np.int64)
    return NoteSeq(onset, p_idx + PITCH_LO, vel)


def excerpts(enc: Encoded, T: int = 256, hop: Optional[int] = None):
    """Slice (D, C, Delta) into fixed-length windows; drop empty windows.

    Returns (D_x, C_x, Delta_x, start_indices) stacked along axis 0.
    Memory note: train-split MAESTRO at T=256 is a few GB in float32 - fine on
    Databricks; a streaming loader arrives with M5.
    """
    hop = hop or T
    Ds, Cs, Deltas, starts = [], [], [], []
    delta = enc.delta
    for s in range(0, len(enc.grid.times) - T + 1, hop):
        d = enc.D[s : s + T]
        if d.any():
            Ds.append(d)
            Cs.append(enc.C[s : s + T])
            Deltas.append(delta[s : s + T])
            starts.append(s)
    if not Ds:
        return (np.zeros((0, T, P), np.uint8), np.zeros((0, T, P, 2), np.float32),
                np.zeros((0, T), np.float64), np.zeros(0, np.int64))
    return (np.stack(Ds), np.stack(Cs), np.stack(Deltas),
            np.asarray(starts, dtype=np.int64))


# ------------------------------------------------------------------- MIDI IO
def load_midi(path: str) -> NoteSeq:
    """Thin adapter; requires pretty_midi (install extra: `pip install -e .[music]`)."""
    import pretty_midi  # optional dependency by design

    pm = pretty_midi.PrettyMIDI(str(path))
    onset, pitch, vel = [], [], []
    for inst in pm.instruments:
        if inst.is_drum:
            continue
        for n in inst.notes:
            onset.append(n.start)
            pitch.append(n.pitch)
            vel.append(n.velocity)
    return NoteSeq(np.asarray(onset), np.asarray(pitch), np.asarray(vel))


def make_grid(notes: NoteSeq, source: str, subdivision: int = 4,
              beat_annotation: Optional[str] = None) -> Grid:
    if source == "asap":
        if beat_annotation is None:
            raise ValueError("grid source 'asap' needs a beat annotation file")
        beats, _ = beats_from_annotation_txt(beat_annotation)
        return grid_from_beats(beats, subdivision)
    if source == "fixed":
        return estimate_fixed_grid(notes.onset, subdivision=subdivision)
    if source == "tracked":
        return tracked_grid(notes.onset, subdivision=subdivision)
    raise ValueError(f"unknown grid source '{source}'")
