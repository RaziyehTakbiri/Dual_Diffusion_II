"""Dependency-free Standard MIDI File reader (onsets/pitches/velocities only).

Purpose: (a) run analyses in environments without PyPI access, (b) fallback
for restricted clusters. Parses SMF format 0/1: variable-length quantities,
running status, meta events (tempo map), and note-on events; converts ticks
to seconds via the merged tempo map. Durations/note-offs are ignored by
design - the DMD representation only consumes onsets (MODEL_SPEC §2).

Cross-validated against pretty_midi note counts on the ASAP corpus (see
tests + PROGRESS run log).
"""

from __future__ import annotations

import struct
from typing import List, Tuple

import numpy as np

from dmd.data.music import NoteSeq

_DATA_LEN = {0x80: 2, 0x90: 2, 0xA0: 2, 0xB0: 2, 0xC0: 1, 0xD0: 1, 0xE0: 2}


def _vlq(data: bytes, i: int) -> Tuple[int, int]:
    val = 0
    while True:
        b = data[i]
        i += 1
        val = (val << 7) | (b & 0x7F)
        if not b & 0x80:
            return val, i


def _parse_track(data: bytes, notes: list, tempi: list):
    """Collect (tick, pitch, velocity) note-ons and (tick, us_per_qn) tempi."""
    i, tick, status = 0, 0, 0
    n = len(data)
    while i < n:
        delta, i = _vlq(data, i)
        tick += delta
        b = data[i]
        if b >= 0x80:
            status = b
            i += 1
        if status == 0xFF:                     # meta
            mtype = data[i]
            length, i2 = _vlq(data, i + 1)
            payload = data[i2 : i2 + length]
            if mtype == 0x51 and length == 3:  # set tempo
                tempi.append((tick, (payload[0] << 16) | (payload[1] << 8)
                              | payload[2]))
            i = i2 + length
            if mtype == 0x2F:                  # end of track
                return
        elif status in (0xF0, 0xF7):           # sysex
            length, i = _vlq(data, i)
            i += length
        else:                                  # channel message (running status ok)
            kind = status & 0xF0
            nd = _DATA_LEN.get(kind)
            if nd is None:
                raise ValueError(f"bad status byte 0x{status:02X}")
            if kind == 0x90 and data[i + 1] > 0:
                notes.append((tick, data[i], data[i + 1]))
            i += nd


def _ticks_to_seconds(ticks: np.ndarray, tempi: List[Tuple[int, int]],
                      tpqn: int) -> np.ndarray:
    """Piecewise-linear tick->second conversion from the merged tempo map."""
    tempi = sorted(set(tempi))
    if not tempi or tempi[0][0] > 0:
        tempi = [(0, 500_000)] + tempi         # MIDI default 120 bpm
    seg_ticks = np.array([t for t, _ in tempi], dtype=np.float64)
    seg_us = np.array([u for _, u in tempi], dtype=np.float64)
    seg_start_s = np.zeros(len(tempi))
    for k in range(1, len(tempi)):
        seg_start_s[k] = seg_start_s[k - 1] + (
            (seg_ticks[k] - seg_ticks[k - 1]) * seg_us[k - 1] / (tpqn * 1e6))
    idx = np.searchsorted(seg_ticks, ticks, side="right") - 1
    idx = np.clip(idx, 0, len(tempi) - 1)
    return seg_start_s[idx] + (ticks - seg_ticks[idx]) * seg_us[idx] / (tpqn * 1e6)


def load_midi_lite(path: str) -> NoteSeq:
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:4] != b"MThd":
        raise ValueError(f"{path}: not a MIDI file")
    hlen, fmt, ntrk, division = struct.unpack(">IHHH", data[4:14])
    if division & 0x8000:
        raise ValueError(f"{path}: SMPTE division unsupported")
    notes: list = []
    tempi: list = []
    i = 8 + hlen
    for _ in range(ntrk):
        if data[i : i + 4] != b"MTrk":
            raise ValueError(f"{path}: bad track chunk")
        tlen = struct.unpack(">I", data[i + 4 : i + 8])[0]
        _parse_track(data[i + 8 : i + 8 + tlen], notes, tempi)
        i += 8 + tlen
    if not notes:
        return NoteSeq(np.zeros(0), np.zeros(0, np.int64), np.zeros(0, np.int64))
    arr = np.asarray(notes, dtype=np.float64)
    onsets = _ticks_to_seconds(arr[:, 0], tempi, division)
    return NoteSeq(onsets, arr[:, 1].astype(np.int64), arr[:, 2].astype(np.int64))
