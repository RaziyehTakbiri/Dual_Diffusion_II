"""Ground-truth test for the stdlib MIDI reader: a hand-assembled SMF with
known byte-level content - tempo change mid-file, running status, velocity-0
note-ons and explicit note-offs (both must be ignored), a CC event - and
hand-computed expected onset times.

Runnable via pytest or `python tests/test_midi_lite.py`.
"""

import os
import struct
import tempfile

import numpy as np

from dmd.data.midi_lite import load_midi_lite


def vlq(n: int) -> bytes:
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.append(0x80 | (n & 0x7F))
        n >>= 7
    return bytes(reversed(out))


def track(events: bytes) -> bytes:
    events += vlq(0) + b"\xff\x2f\x00"          # end of track
    return b"MTrk" + struct.pack(">I", len(events)) + events


def build_test_midi(path: str, tpqn: int = 480):
    header = b"MThd" + struct.pack(">IHHH", 6, 1, 2, tpqn)
    # track 0: tempo map - 120 bpm at tick 0, 240 bpm at tick 960
    t0 = (vlq(0) + b"\xff\x51\x03" + (500_000).to_bytes(3, "big")
          + vlq(960) + b"\xff\x51\x03" + (250_000).to_bytes(3, "big"))
    # track 1: notes (times hand-computed below)
    t1 = (
        vlq(0) + bytes([0x90, 60, 80])          # tick 0    -> 0.000 s
        + vlq(480) + bytes([62, 70])            # tick 480  -> 0.500 s (running status)
        + vlq(0) + bytes([0xB0, 64, 0])         # CC event - ignored
        + vlq(480) + bytes([0x90, 64, 60])      # tick 960  -> 1.000 s
        + vlq(240) + bytes([60, 0])             # v=0 note-on - ignored
        + vlq(240) + bytes([0x80, 62, 40])      # explicit note-off - ignored
        + vlq(0) + bytes([0x90, 65, 50])        # tick 1440 -> 1.000 + 480*0.25/480... see below
    )
    with open(path, "wb") as fh:
        fh.write(header + track(t0) + track(t1))


def test_hand_assembled_midi_exact_onsets():
    # timing: ticks 0..960 at 500000 us/qn (0.5 s per 480 ticks);
    # from tick 960 at 250000 us/qn (0.25 s per 480 ticks).
    # tick 1440 = 1.0 s + 480 ticks * 0.25/480 s = 1.25 s.
    fd, path = tempfile.mkstemp(suffix=".mid")
    os.close(fd)
    try:
        build_test_midi(path)
        ns = load_midi_lite(path)
    finally:
        os.unlink(path)
    assert ns.pitch.tolist() == [60, 62, 64, 65]
    assert ns.velocity.tolist() == [80, 70, 60, 50]
    assert np.allclose(ns.onset, [0.0, 0.5, 1.0, 1.25], atol=1e-9)


if __name__ == "__main__":
    test_hand_assembled_midi_exact_onsets()
    print("PASS  test_hand_assembled_midi_exact_onsets")
