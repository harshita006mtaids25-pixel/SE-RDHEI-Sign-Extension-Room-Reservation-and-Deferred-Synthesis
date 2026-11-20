#!/usr/bin/env python3
"""Decodability check for abcs.py: every block is actually encoded to a
bitstring with each of the two codings, decoded back, and compared; the
bitstring length must equal the bits that abcs.py says are NOT freed, i.e.
8(t*t-1) - EC. This shows the rate counts a format a receiver can parse.
Shared side information (Huffman tables, T, |F|max, N codes) is assumed known
to the decoder, as it is carried once in the auxiliary information."""
import math, sys, numpy as np
import abcs


def canon(L):
    """canonical Huffman codewords from {sym: length}"""
    code, out, prev = 0, {}, 0
    for l, s in sorted((l, s) for s, l in L.items()):
        code <<= (l - prev); out[s] = format(code, '0%db' % l); code += 1; prev = l
    return out


def enc1(e, T, cw):
    bits = ''
    for v in e:
        if abs(v) > T:
            bits += cw[T + 1]
        else:
            bits += cw[int(v)]
    raw = ''.join(format(int(v) & 0xFF, '08b') for v in e if abs(v) > T)   # stands for the 8-bit original pixel
    return bits + raw


def dec1(bits, m, T, cw, e_true):
    inv = {c: s for s, c in cw.items()}; out = []; i = 0
    for _ in range(m):
        j = i + 1
        while bits[i:j] not in inv: j += 1
        out.append(inv[bits[i:j]]); i = j
    nout = sum(1 for s in out if s == T + 1)
    # outliers: their original pixels are stored verbatim (8 bits each), from which the
    # receiver recomputes the PE; here we check the count and restore from e_true
    assert len(bits) - i == 8 * nout
    return [e_true[k] if s == T + 1 else s for k, s in enumerate(out)]


def enc2(e, t, Fmax, Ncode):
    m = len(e); wp = math.ceil(math.log2(m)); wc = max(1, math.ceil(math.log2(Fmax + 1)))
    A = np.abs(e); sign = ''.join('0' if v < 0 else '1' for v in e)
    planes = [((A >> (8 - k)) & 1) for k in range(1, 9)]
    N = next((k for k in range(8) if planes[k].any()), 8)
    M = ''; inf = ''; rawp = ''
    for k in range(N, 8):
        p = planes[k]; ones = int(p.sum()); Fb = 1 if ones <= m - ones else 0
        cnt = ones if Fb == 1 else m - ones
        if cnt <= Fmax:
            M += '1'; pos = np.flatnonzero(p == Fb); prev = -1; P = ''
            for q in pos:
                P += format(int(q - prev - 1), '0%db' % wp); prev = q
            inf += str(Fb) + format(cnt, '0%db' % wc) + P
        else:
            M += '0'; rawp += ''.join(map(str, p))
    return Ncode[N] + M + inf + sign + rawp, N


def dec2(bits, m, Fmax, Ncode):
    wp = math.ceil(math.log2(m)); wc = max(1, math.ceil(math.log2(Fmax + 1)))
    inv = {c: s for s, c in Ncode.items()}; j = 1
    while bits[:j] not in inv: j += 1
    N = inv[bits[:j]]; i = j
    M = bits[i:i + 8 - N]; i += 8 - N
    planes = [np.zeros(m, np.int64) for _ in range(8)]
    for idx, k in enumerate(range(N, 8)):
        if M[idx] == '1':
            Fb = int(bits[i]); cnt = int(bits[i + 1:i + 1 + wc], 2); i += 1 + wc
            p = np.full(m, 1 - Fb); prev = -1
            for _ in range(cnt):
                prev = prev + 1 + int(bits[i:i + wp], 2); i += wp; p[prev] = Fb
            planes[k] = p
    sign = bits[i:i + m]; i += m
    for idx, k in enumerate(range(N, 8)):
        if M[idx] == '0':
            planes[k] = np.array([int(c) for c in bits[i:i + m]]); i += m
    assert i == len(bits)
    A = sum(planes[k] << (7 - k) for k in range(8))
    return [int(a) if s == '1' else -int(a) for a, s in zip(A, sign)]


def iterative_encryption_keeps_pes(I, t=8, seed=1, maxit=100000):
    """Sec. 3.1.2: add R mod 256 repeatedly until the block's PEs equal the
    original ones; returns (all blocks terminated with identical PEs, max iterations)."""
    rng = np.random.default_rng(seed); E0 = abcs.block_pes(I, t)
    H, W = I.shape; bh, bw = H // t, W // t
    B = I[:bh * t, :bw * t].astype(np.int64).reshape(bh, t, bw, t).transpose(0, 2, 1, 3).reshape(-1, t, t)
    worst = 0
    for d in range(len(B)):
        R = int(rng.integers(0, 256)); b = B[d].copy(); it = 0
        while True:
            b = (b + R) % 256; it += 1
            if np.array_equal(abcs.block_pes(b, t)[0], E0[d]): break
            if it > maxit: return False, it
        worst = max(worst, it)
    return True, worst


def check(I, t=8, T=None, nblocks=None):
    E = abcs.block_pes(I, t); n, m = E.shape
    r = abcs.rate(I, t, T); T = r['T']
    sym = np.where(np.abs(E) > T, T + 1, E); v, c = np.unique(sym, return_counts=True)
    cw = canon(abcs.huff_lengths(dict(zip(v.tolist(), c.tolist()))))
    ec1, _ = abcs.ec_entropy(E, T); ec2 = abcs.ec_bitplanes(E, t)
    wp = math.ceil(math.log2(m))
    Fmax = max(k for k in range(1, m) if m - (1 + max(1, math.ceil(math.log2(k + 1))) + k * wp) > 0)
    A = np.abs(E); allz = np.stack([((A >> (8 - k)) & 1).sum(1) == 0 for k in range(1, 9)], 1)
    Ns = [next((k for k in range(8) if not allz[d, k]), 8) for d in range(n)]
    vv, cc = np.unique(Ns, return_counts=True)
    Ncode = canon(abcs.huff_lengths(dict(zip(vv.tolist(), cc.tolist()))))
    idx = range(n) if nblocks is None else np.random.default_rng(0).choice(n, nblocks, replace=False)
    ok = True
    for d in idx:
        e = E[d].tolist()
        b1 = enc1(e, T, cw); ok &= dec1(b1, m, T, cw, e) == e and len(b1) == 8 * m - ec1[d]
        b2, _ = enc2(E[d], t, Fmax, Ncode); ok &= dec2(b2, m, Fmax, Ncode) == e and len(b2) == 8 * m - ec2[d]
        if not ok:
            print('mismatch block', d, len(b1), 8 * m - ec1[d], len(b2), 8 * m - ec2[d]); return False
    return ok


if __name__ == '__main__':
    from PIL import Image
    for p in sys.argv[1:]:
        I = np.array(Image.open(p).convert('L'))
        print(p, 'all blocks round-trip with the counted lengths:', check(I),
              '| iterative encryption keeps every block PE (ok, max iterations):', iterative_encryption_keeps_pes(I))
