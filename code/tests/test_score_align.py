"""Ground-truth test for E4.1b score alignment: synthesize a score, a tempo
warp, and a performance with KNOWN micro-timing statistics; require recovery.

Runnable via pytest or `python tests/test_score_align.py`.
"""

import numpy as np

from dmd.data.music import NoteSeq
from dmd.eval.score_align import make_warp, match_notes, metrical_split
from dmd.eval.human_acf import acf


def _ar1(n, sigma, phi, rng):
    e = rng.normal(0, sigma * np.sqrt(1 - phi**2), n)
    x = np.empty(n); x[0] = rng.normal(0, sigma)
    for i in range(1, n):
        x[i] = phi * x[i - 1] + e[i]
    return x


def _setup(rng, n_beats=800, phi=0.4, sig_ms=8.0):
    beats_s = np.arange(n_beats) * 0.5                       # score: 120 bpm
    periods = 0.5 * (1 + 0.15 * np.sin(2 * np.pi * np.arange(n_beats) / 64))
    beats_p = np.concatenate([[10.0], 10.0 + np.cumsum(periods[:-1])])
    # score: a sixteenth-note melody + a chord on every beat
    mel_on = np.arange((n_beats - 1) * 4) * 0.125
    mel_pitch = 60 + (np.arange(len(mel_on)) % 12)
    ch_on = np.repeat(beats_s[:-1], 2)
    ch_pitch = np.tile([36, 43], n_beats - 1)
    on_s = np.concatenate([mel_on, ch_on])
    pi_s = np.concatenate([mel_pitch, ch_pitch])
    score = NoteSeq(on_s, pi_s, np.full(len(on_s), 64))
    # performance: warp + AR(1) micro-timing (same series, note-level)
    warp = make_warp(beats_s, beats_p)
    dev = _ar1(len(score), sig_ms / 1000.0, phi, rng)
    perf = NoteSeq(warp(score.onset) + dev, score.pitch,
                   np.full(len(score), 64))
    return beats_s, beats_p, score, perf, dev


def test_warp_is_exact_on_beats_and_extrapolates():
    rng = np.random.default_rng(0)
    bs, bp, *_ = _setup(rng)
    w = make_warp(bs, bp)
    assert np.allclose(w(bs), bp, atol=1e-12)
    s0 = (bp[1] - bp[0]) / (bs[1] - bs[0])
    assert np.isclose(w(bs[0] - 1.0), bp[0] - s0, atol=1e-9)


def test_matching_and_recovery_of_injected_statistics():
    rng = np.random.default_rng(1)
    bs, bp, score, perf, dev = _setup(rng)
    warped = make_warp(bs, bp)(score.onset)
    mi, mj = match_notes(warped, score.pitch, perf)
    assert len(mi) / len(score) > 0.995
    d_ms = (perf.onset[mj] - warped[mi]) * 1000.0
    assert abs(d_ms.std() - 8.0) < 1.0
    # note-level ACF on the per-note deviation series (sorted by warped time)
    order = np.argsort(warped[mi])
    on_sorted = score.onset[mi][order]
    gid = np.concatenate([[0], np.cumsum(np.diff(on_sorted) > 1e-6)])
    cmean = np.bincount(gid, weights=d_ms[order]) / np.bincount(gid)
    rho = acf(cmean, 2)
    # chord-mean of iid-ish AR(1) members preserves the AR structure
    assert abs(rho[0] - 0.4) < 0.08, rho


def test_metrical_split_flags_triplets():
    bs = np.arange(10) * 0.5
    on = np.array([0.0, 0.125, 0.25, 1/6, 1/3, 0.5])   # duple x3, triplets x2, beat
    pos, duple = metrical_split(on, bs)
    assert duple.tolist() == [True, True, True, False, False, True]
    assert pos.tolist() == [0, 1, 2, 1, 3, 0]


def test_matching_robust_to_extra_and_missing_notes():
    rng = np.random.default_rng(2)
    bs, bp, score, perf, _ = _setup(rng, n_beats=200)
    # delete 5% of performed notes, add 5% spurious ones
    n = len(perf)
    keep = rng.random(n) > 0.05
    extra_on = rng.uniform(perf.onset.min(), perf.onset.max(), n // 20)
    perf2 = NoteSeq(np.concatenate([perf.onset[keep], extra_on]),
                    np.concatenate([perf.pitch[keep],
                                    rng.integers(60, 72, len(extra_on))]),
                    np.full(keep.sum() + len(extra_on), 64))
    warped = make_warp(bs, bp)(score.onset)
    mi, mj = match_notes(warped, score.pitch, perf2)
    assert 0.90 < len(mi) / len(score) <= 1.0
    d_ms = (perf2.onset[mj] - warped[mi]) * 1000.0
    assert abs(np.median(d_ms)) < 3.0          # matching stays unbiased


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
