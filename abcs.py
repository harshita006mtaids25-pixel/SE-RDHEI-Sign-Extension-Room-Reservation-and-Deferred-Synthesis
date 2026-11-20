#!/usr/bin/env python3
"""Reimplementation of the capacity of Xiao, Wang, Shen & Yao (2024),
'High-capacity reversible data hiding in encrypted images based on adaptive
block coding selection', J. Vis. Commun. Image R. 104, 104291 (ABCS).

Only the embedding rate is computed. Iterative encryption is constructed so
that every encrypted block has the same prediction errors (PEs) as the
original block (Sec. 3.1.2), and block permutation only reorders blocks, so
the rate is key independent and can be computed from the plaintext blocks.

Equations follow the paper: Eq. (1) block PEs (first pixel kept, first row
predicted from the left, first column from above, the rest by MED); Eq. (3)
entropy coding with threshold T; Eqs. (5)-(8) zero-valued high bit-plane
compression; Sec. 3.2.3 per-block selection and global auxiliary information.
"""
import heapq, math
import numpy as np


def block_pes(I, t):
    H, W = I.shape
    bh, bw = H // t, W // t
    B = I[:bh * t, :bw * t].astype(np.int64).reshape(bh, t, bw, t).transpose(0, 2, 1, 3).reshape(-1, t, t)
    P = np.zeros_like(B)
    P[:, 0, 1:] = B[:, 0, :-1]                     # first row: left neighbour (a)
    P[:, 1:, 0] = B[:, :-1, 0]                     # first column: upper neighbour (b)
    a, b, c = B[:, 1:, :-1], B[:, :-1, 1:], B[:, :-1, :-1]
    med = np.where(c <= np.minimum(a, b), np.maximum(a, b),
                   np.where(c >= np.maximum(a, b), np.minimum(a, b), a + b - c))
    P[:, 1:, 1:] = med
    E = (B - P).reshape(len(B), -1)[:, 1:]          # drop the reference pixel
    return E                                        # shape (n, t*t-1)


def huff_lengths(counts):
    """Huffman code lengths for the symbols with nonzero count (dict sym->count)."""
    syms = [s for s, c in counts.items() if c > 0]
    if len(syms) == 1:
        return {syms[0]: 1}
    h = [(counts[s], i, [s]) for i, s in enumerate(syms)]
    heapq.heapify(h); L = {s: 0 for s in syms}; k = len(h)
    while len(h) > 1:
        x = heapq.heappop(h); y = heapq.heappop(h)
        for s in x[2] + y[2]:
            L[s] += 1
        heapq.heappush(h, (x[0] + y[0], k, x[2] + y[2])); k += 1
    return L


def ec_entropy(E, T):
    m = E.shape[1]
    sym = np.where(np.abs(E) > T, T + 1, E)          # T+1 stands for the class |E|>T
    vals, cnt = np.unique(sym, return_counts=True)
    L = huff_lengths(dict(zip(vals.tolist(), cnt.tolist())))
    lut = np.zeros(2 * T + 3, np.int64)
    for v, l in L.items():
        lut[v + T] = l
    NT = (np.abs(E) > T).sum(1)
    ec1 = 8 * (m - NT) - lut[sym + T].sum(1)
    table_bits = (2 * T + 2) * math.ceil(math.log2(2 * T + 2)) + sum(L.values())
    return ec1, table_bits


def ec_bitplanes(E, t):
    n, m = E.shape
    w_pos = math.ceil(math.log2(m))
    # |F|max: largest |F| whose description still saves bits on an m-bit plane (Eqs. 6-7)
    Fmax = 0
    for k in range(1, m):
        if m - (1 + max(1, math.ceil(math.log2(k + 1))) + k * w_pos) > 0:
            Fmax = k
    A = np.abs(E)
    planes = np.stack([(A >> (8 - k)) & 1 for k in range(1, 9)], 1)   # (n, 8, m), k=1 is MSB
    ones = planes.sum(2)
    allzero = ones == 0
    N = np.argmin(np.concatenate([allzero, np.zeros((n, 1), bool)], 1), 1)  # leading all-zero planes
    N = np.where(allzero.all(1), 8, N)
    minority = np.minimum(ones, m - ones)
    usable = minority <= Fmax
    k_idx = np.arange(8)[None, :]
    after = k_idx >= N[:, None]
    use = usable & after
    # |F| is written in a fixed field of ceil(log2(|F|max+1)) bits: the worked
    # example of Sec. 3.2.4 writes |F|=1 as '01' and |F|=0 as '00' for |F|max=2,
    # and only a fixed width can be parsed by the receiver.
    w_cnt = max(1, math.ceil(math.log2(Fmax + 1)))
    inf = np.where(use, 1 + w_cnt + minority * w_pos, 0).sum(1)
    lenM = 8 - N
    freed = N + use.sum(1)
    vals, cnt = np.unique(N, return_counts=True)
    LN = huff_lengths(dict(zip(vals.tolist(), cnt.tolist())))
    lN = np.array([LN[v] for v in N.tolist()])
    # The sign sequence L_sign (m bits, Sec. 3.2.2) must be kept for exact
    # recovery; Eq. (8) as printed omits it, and only with it do the published
    # per-image rates reproduce (within 1.4%, see validate.py).
    ec2 = freed * m - lN - lenM - inf - m
    return ec2


def rate(I, t=8, T=None, Trange=range(2, 160)):
    E = block_pes(I, t)
    n = len(E)
    ec2 = ec_bitplanes(E, t)
    best = None
    for TT in ([T] if T is not None else Trange):
        ec1, tbl = ec_entropy(E, TT)
        tot = np.maximum(ec1, ec2).sum() - (n + 8 + tbl + 72)
        if best is None or tot > best[0]:
            best = (tot, TT, int((ec2 > ec1).sum()))
    tot, TT, n2 = best
    return dict(er=tot / I.size, T=TT, coding2_blocks=n2, blocks=n)


if __name__ == '__main__':
    import sys
    from PIL import Image
    for p in sys.argv[1:]:
        I = np.array(Image.open(p).convert('L'))
        print(p, rate(I))


def selftest():
    """Worked example of Sec. 3.2.4 (t = 4): N = 5, |F|max = 2, planes 6 and 8
    usable, plane 7 not; the paper gives EC2 = 89 with l(N) = 3. The sign
    sequence (15 bits) is added back here because Eq. (8) as printed omits it."""
    E = np.zeros((1, 15), np.int64)
    E[0, 14] = 4                      # one '1' in plane 6, 15 positions from the first pixel
    E[0, [0, 2, 4, 6, 8]] = 2         # five '1's in plane 7
    ec2 = ec_bitplanes(E, 4)[0]
    lN_here = 1                       # a single block gives a 1-bit Huffman code for N
    return int(ec2 + lN_here - 3 + 15) == 89
