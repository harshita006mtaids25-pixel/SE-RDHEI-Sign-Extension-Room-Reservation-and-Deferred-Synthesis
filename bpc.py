#!/usr/bin/env python3
"""Reimplementation of Yin, Peng & Xiang, "Reversible data hiding in encrypted
images based on pixel prediction and bit-plane compression" (IEEE TDSC 2022,
arXiv:1911.01699), for a matched-image comparison.

Implemented as described: MED prediction, sign + 7-bit magnitude error planes,
bit-plane rearrangement (four scan types over square blocks, shortest kept),
and bit-stream compression by run-length coding with a fixed raw length Lfix.
Details the paper leaves open (border prediction, block size, Lfix) are
parameters; validate() checks them against the paper's published plane lengths.
"""
import numpy as np
from numba import njit


def med_errors(I, border='reference'):
    I = I.astype(np.int64)
    x2 = np.zeros_like(I); x3 = np.zeros_like(I); x1 = np.zeros_like(I)
    x2[1:, :] = I[:-1, :]; x3[:, 1:] = I[:, :-1]; x1[1:, 1:] = I[:-1, :-1]
    mn = np.minimum(x2, x3); mx = np.maximum(x2, x3)
    p = np.where(x1 <= mn, mx, np.where(x1 >= mx, mn, x2 + x3 - x1))
    if border == 'reference':            # first row and column stored as is (error := 0 here)
        p[0, :] = I[0, :]; p[:, 0] = I[:, 0]
    elif border == 'neighbour':           # first row predicted from left, first column from top
        p[0, 1:] = I[0, :-1]; p[1:, 0] = I[:-1, 0]; p[0, 0] = I[0, 0]
    e = I - p
    over = np.abs(e) > 127
    return e, over


def planes(e):
    """Plane 8 = sign, planes 7..1 = magnitude bits, MSB first. Returns dict k -> 2-D 0/1."""
    m = np.abs(e).clip(0, 127)
    out = {8: (e < 0).astype(np.uint8)}
    for k in range(7, 0, -1):
        out[k] = ((m >> (k - 1)) & 1).astype(np.uint8)
    return out


def rearrange(P, bs, typ):
    h, w = P.shape
    hb, wb = h // bs, w // bs
    core = P[:hb * bs, :wb * bs].reshape(hb, bs, wb, bs)       # (block row, in-row, block col, in-col)
    within_col = typ in (2, 3)          # 10, 11: column-by-column within blocks
    across_col = typ in (1, 3)          # 01, 11: column-by-column across blocks
    blk = core.transpose(0, 2, 1, 3)    # (br, bc, ir, ic)
    if within_col:
        blk = blk.transpose(0, 1, 3, 2)
    if across_col:
        blk = blk.transpose(1, 0, 2, 3)
    s = blk.reshape(-1)
    rest = np.concatenate([P[hb * bs:, :].reshape(-1), P[:hb * bs, wb * bs:].reshape(-1)])
    return np.concatenate([s, rest]).astype(np.uint8)


@njit(cache=True)
def bsc_len(s, Lfix):
    n = s.size
    # run length remaining from each position
    rem = np.empty(n, np.int64)
    rem[n - 1] = 1
    for i in range(n - 2, -1, -1):
        rem[i] = rem[i + 1] + 1 if s[i] == s[i + 1] else 1
    i = 0; tot = 0
    while i < n:
        L = rem[i]
        if L >= 4:
            l = 0
            while (1 << (l + 1)) <= L:
                l += 1
            tot += l + l + 1          # prefix l bits ((l-1) ones + one zero), mid l bits, tail 1
            i += L
        else:
            take = Lfix if i + Lfix <= n else n - i
            tot += 1 + take
            i += take
    return tot


def plane_len(P, bs, Lfix):
    return min(bsc_len(rearrange(P, bs, t), Lfix) for t in range(4)) + 3   # 1 flag + 2-bit type


def compress(I, bs=None, Lfix=None, border='reference', bss=(2, 3, 4, 5, 6, 8), lfs=range(1, 8)):
    """Room in bits: for the run of compressible planes from 7 down, sum (n - compressed length)."""
    e, over = med_errors(I, border)
    Pk = planes(e)
    n = I.size
    best = None
    for b in ([bs] if bs else bss):
        for lf in ([Lfix] if Lfix else lfs):
            lens, room = {}, 0
            for k in range(7, 0, -1):
                c = plane_len(Pk[k], b, lf)
                if c >= n:
                    break
                lens[k] = c; room += n - c
            if best is None or room > best[0]:
                best = (room, b, lf, lens, int(over.sum()))
    return best


# published values, arXiv:1911.01699 Tables I and II
PUBLISHED = {
    'Airplane': dict(lens={7: 5034, 6: 17682, 5: 28408, 4: 71013, 3: 182697}, room=1005781, net=3.8363),
    'Baboon':   dict(lens={7: 39985, 6: 143101, 5: 240610}, room=362673, net=1.3832),
    'Man':      dict(lens={7: 17795, 6: 90490, 5: 346108, 4: 974860}, room=2764959, net=2.6345),
}
