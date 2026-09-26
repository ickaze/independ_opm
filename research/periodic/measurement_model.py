# SPDX-License-Identifier: 0BSD
# Copyright (C) 2026 by I.C.KaZe
"""Measured steady-state candidates, not a complete YM2151 implementation.
See REPORT.md for scope, fitted phase origin, and missing write-transition rules.
No dB constant or measured pitch table is a universal internal-chip specification.
"""
def reverse4(x):
    x &= 15
    return ((x & 1) << 3) | ((x & 2) << 1) | ((x & 4) >> 1) | ((x & 8) >> 3)

def phase_increment(counter, low_nibble):
    return 1 + int(reverse4(counter) < (low_nibble & 15))

def steady_am_wave(shape, tick):
    i = tick & 255
    if shape == 0:
        return 255 - i
    if shape == 1:
        return 255 if i < 128 else 0
    if shape == 2:
        return 255 - 2*i if i < 128 else 2*i - 256
    raise ValueError('random waveform is outside this measurement suite')

def am_units(shape, tick, amd):
    return (steady_am_wave(shape, tick) * (amd & 127)) >> 7

def steady_pm_wave(shape, tick):
    i = tick & 255
    if shape == 0:
        return i if i < 128 else i - 255
    if shape == 2:
        if i < 64: return 2*i
        if i < 128: return 255 - 2*i
        if i < 192: return 256 - 2*i
        return 2*i - 511
    raise ValueError('square and random PM are outside these new recordings')

def pm_pitch_units(shape, tick, pmd, pms):
    w = steady_pm_wave(shape, tick)
    magnitude = (abs(w) * (pmd & 127)) >> 7
    pms &= 7
    if pms == 0: return 0
    if pms <= 5: magnitude >>= 6-pms
    else: magnitude <<= pms-5
    return -magnitude if w < 0 else magnitude
