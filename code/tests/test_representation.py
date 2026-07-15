"""Ground-truth tests for the representation + measurement pipeline (M2).

Strategy (this is the W6 fix in test form): synthesize performances with KNOWN
tempo, rubato magnitude (sigma), rubato structure (AR(1) phi), and chord
asynchrony - then require the pipeline to recover each number. If these pass,
the human-ACF study measures what it claims to measure.

Runnable two ways:
  pytest tests/test_representation.py -q
  python tests/test_representation.py          (no pytest needed)
"""

import numpy as np

from dmd.data.music import (Grid, NoteSeq, encode, decode, estimate_fixed_grid,
                            excerpts, grid_from_beats)
from dmd.data.validate import round_trip_report
from dmd.eval.human_acf import (acf, analyze_piece, chord_group, chord_series,
                                deviation_series_ms, metrical_profile)

BEAT = 0.5          # 120 bpm
S = 4               # sixteenth subdivision
DELTA = BEAT / S    # 0.125 s
N_BEATS = 512


def beat_grid(n_beats=N_BEATS):
    return grid_from_beats(np.arange(n_beats) * BEAT, subdivision=S, source="synthetic")


def ar1(n, sigma, phi, rng):
    e = rng.normal(0.0, sigma * np.sqrt(1.0 - phi**2), n)
    x = np.empty(n)
    x[0] = rng.normal(0.0, sigma)
    for i in range(1, n):
        x[i] = phi * x[i - 1] + e[i]
    return x


def melody(rng, sigma_ms=15.0, phi=0.5, n_steps=N_BEATS * S - S):
    """One note per grid step with AR(1) rubato; returns (NoteSeq, injected r)."""
    r = ar1(n_steps, sigma_ms / 1000.0, phi, rng)
    r = np.clip(r, -DELTA / 2 + 1e-6, DELTA / 2 - 1e-6)
    onsets = np.arange(n_steps) * DELTA + r
    pitches = 60 + (np.arange(n_steps) % 12)
    vels = rng.integers(20, 110, n_steps)
    return NoteSeq(onsets, pitches, vels), r


# ------------------------------------------------------------------ the tests
def test_grid_estimation_recovers_tempo_and_phase():
    rng = np.random.default_rng(0)
    n = 3000
    keep = rng.random(n) < 0.6                      # sparse occupancy
    onsets = (np.arange(n) * DELTA + 0.037)[keep]   # exact grid, shifted phase
    grid = estimate_fixed_grid(onsets)
    step = float(np.median(np.diff(grid.times)))
    assert abs(step - DELTA) / DELTA < 0.005, f"step {step} vs {DELTA}"
    # every onset should sit essentially ON the estimated grid
    k = np.array([np.argmin(np.abs(grid.times - o)) for o in onsets[:200]])
    resid_ms = np.abs(onsets[:200] - grid.times[k]) * 1000.0
    assert resid_ms.max() < 2.0, f"max residual {resid_ms.max():.3f} ms"


def test_grid_estimation_prefers_coarsest_consistent_step():
    """Onsets on a 0.125 s grid also fit 0.0625 s perfectly; the largest-delta
    rule must pick 0.125 s, not a harmonic."""
    rng = np.random.default_rng(1)
    keep = rng.random(2000) < 0.7
    onsets = (np.arange(2000) * DELTA)[keep]
    step = float(np.median(np.diff(estimate_fixed_grid(onsets).times)))
    assert step > 0.9 * DELTA


def test_encode_decode_roundtrip_exact():
    rng = np.random.default_rng(2)
    notes, _ = melody(rng)
    enc = encode(notes, beat_grid())
    rep = round_trip_report(notes, enc)
    assert rep.keep_rate == 1.0 and rep.collision_rate == 0.0
    assert rep.wrap_rate == 0.0
    assert rep.onset_max_ms < 1e-3, f"onset err {rep.onset_max_ms} ms"
    assert rep.velocity_exact_rate == 1.0
    assert abs(rep.residual_sigma_ms - 15.0) < 2.0


def test_residual_bound_and_wrap_counting():
    rng = np.random.default_rng(3)
    onsets = np.sort(rng.uniform(0, N_BEATS * BEAT - BEAT, 500))
    # thin to avoid same-cell collisions polluting the wrap count check
    onsets = onsets[np.concatenate([[True], np.diff(onsets) > DELTA])]
    notes = NoteSeq(onsets, np.full(len(onsets), 60), np.full(len(onsets), 64))
    enc = encode(notes, beat_grid())
    active = enc.D.astype(bool)
    assert np.abs(enc.C[active][:, 1]).max() <= 0.5 + 1e-9
    # nearest-cell assignment on a uniform grid cannot exceed half a step
    assert enc.n_wraps == 0


def test_collision_keeps_earliest_and_counts():
    notes = NoteSeq(np.array([1.000, 1.010]), np.array([60, 60]), np.array([80, 90]))
    enc = encode(notes, beat_grid(8))
    assert enc.n_collisions == 1
    assert enc.kept.tolist() == [True, False]
    dec = decode(enc.D, enc.C, enc.grid)
    assert len(dec) == 1 and dec.velocity[0] == 80


def test_acf_recovers_injected_ar1_structure():
    rng = np.random.default_rng(4)
    notes, r = melody(rng, sigma_ms=15.0, phi=0.5, n_steps=4000)
    enc = encode(notes, grid_from_beats(np.arange(1002) * BEAT, S))
    dev = deviation_series_ms(notes, enc)
    assert np.allclose(dev, r * 1000.0, atol=1e-6)      # measurement == injection
    gid = chord_group(notes.onset[enc.kept])
    cmeans, _ = chord_series(dev, gid)
    assert len(cmeans) == len(dev)                       # no accidental grouping
    rho = acf(cmeans, 4)
    assert abs(rho[0] - 0.5) < 0.06, f"rho1 {rho[0]:.3f} vs 0.5"
    assert abs(rho[1] - 0.25) < 0.08, f"rho2 {rho[1]:.3f} vs 0.25"
    assert abs(dev.std() - 15.0) < 1.5


def test_chord_grouping_and_asynchrony_recovery():
    rng = np.random.default_rng(5)
    base = np.arange(0, 400) * BEAT                      # chord on every beat
    spread = 0.004
    onsets, pitches = [], []
    for t in base:
        for j, p in enumerate((48, 60, 72)):
            onsets.append(t + rng.normal(0, spread))
            pitches.append(p)
    notes = NoteSeq(np.array(onsets), np.array(pitches),
                    np.full(len(onsets), 64))
    enc = encode(notes, beat_grid(402))
    dev = deviation_series_ms(notes, enc)
    gid = chord_group(notes.onset[enc.kept])
    cmeans, asyn = chord_series(dev, gid)
    assert len(cmeans) == len(base)
    assert 2.0 < asyn.std() < 7.0, f"asynchrony sigma {asyn.std():.2f} ms"


def test_metrical_profile_detects_position_dependence():
    """Downbeats get sigma=25 ms rubato, other positions 8 ms - the profile
    must expose it (this is the conditional-structure metric E1.2 relies on)."""
    rng = np.random.default_rng(6)
    n = N_BEATS * S - S
    sig = np.where(np.arange(n) % S == 0, 0.025, 0.008)
    r = rng.normal(0, sig)
    r = np.clip(r, -DELTA / 2 + 1e-6, DELTA / 2 - 1e-6)
    notes = NoteSeq(np.arange(n) * DELTA + r, 60 + (np.arange(n) % 24),
                    np.full(n, 64))
    enc = encode(notes, beat_grid())
    prof = metrical_profile(notes, enc)
    assert prof["sigma_ms"][0] > 2.0 * prof["sigma_ms"][2]


def test_excerpts_shapes_and_content():
    rng = np.random.default_rng(7)
    notes, _ = melody(rng)
    enc = encode(notes, beat_grid())
    D, C, Dl, starts = excerpts(enc, T=256, hop=128)
    assert D.shape[1:] == (256, 88) and C.shape[1:] == (256, 88, 2)
    assert Dl.shape[1:] == (256,) and len(starts) == len(D)
    assert all(d.any() for d in D)
    assert np.allclose(Dl, DELTA)


def test_asap_annotation_parser_confirmed_format(tmp_path=None):
    """Format per the ASAP README: 'time\ttime\tlabel'; labels b / db / bR,
    with time-signature and key changes riding as comma tokens; non-beat
    lines ignored; bR included as a grid anchor."""
    import os, tempfile
    from dmd.data.music import beats_from_annotation_txt
    content = (
        "0.500000\t0.500000\tdb,4/4\n"
        "1.020000\t1.020000\tb\n"
        "1.480000\t1.480000\tbR\n"
        "2.010000\t2.010000\tb,-3\n"      # key change on a beat line
        "garbage line without tabs\n"
        "2.470000\t2.470000\tdb\n"
        "1.020000\t1.020000\tb\n"          # duplicate -> deduped
    )
    fd, path = tempfile.mkstemp(suffix="_annotations.txt")
    with os.fdopen(fd, "w") as fh:
        fh.write(content)
    try:
        times, is_db = beats_from_annotation_txt(path)
    finally:
        os.unlink(path)
    assert np.allclose(times, [0.5, 1.02, 1.48, 2.01, 2.47])
    assert is_db.tolist() == [True, False, False, False, True]


def test_analyze_piece_end_to_end():
    rng = np.random.default_rng(8)
    notes, _ = melody(rng, n_steps=3000)
    row = analyze_piece(notes, grid_from_beats(np.arange(752) * BEAT, S))
    assert row["keep_rate"] == 1.0
    assert abs(row["sigma_ms"] - 15.0) < 2.0
    assert abs(row["rho_1"] - 0.5) < 0.08


if __name__ == "__main__":
    import sys, traceback
    fns = [(k, v) for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    failed = 0
    for name, fn in fns:
        try:
            fn()
            print(f"PASS  {name}")
        except Exception:
            failed += 1
            print(f"FAIL  {name}")
            traceback.print_exc()
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
