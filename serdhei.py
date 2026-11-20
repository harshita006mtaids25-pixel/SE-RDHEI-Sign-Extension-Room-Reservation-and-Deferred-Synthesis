#!/usr/bin/env python3
"""SE-RDHEI: reversible data hiding in encrypted images by sign-extension room
reservation and deferred synthesis.

REFERENCE IMPLEMENTATION of the specified construction analysed in the paper
(Section 4.6, Algorithm 3, Propositions 1-3): AES-256-CTR keystreams, HKDF key
derivation, nonce-bound rejection-sampled block permutations, Huffman-coded
encrypted t-map, and a data hider holding a key of its own.

Roles (each takes only the keys it holds):
    spec_owner(I, K, nonce)                         -> C, H0, tau1   content owner
    spec_hider(C, H0, tau1, K_tmap, K_H, D)         -> C', H, tau2   data hider
    spec_extract(C', H, tau1, tau2, K_tmap, K_H)    -> D or None     payload receiver
    spec_recover(C', H, tau1, K)                    -> I or None     cover receiver
K_tmap = owner_keys(K, nonce)['tmap'] is the only owner-derived key the data
hider receives. See example.py; spec_test_vector.py checks an implementation
bit for bit.

The module also holds the shared transform and bit-level helpers (5/3 lifting,
band widths, block minimum) and the SHA-256 counter-mode stream of the base
construction (the MATLAB prototype), which the experiments use for comparison.
Pure Python + NumPy; AES-256, SHA-256, HMAC and HKDF are implemented here and
checked against RFC 5869 and NIST SP 800-38A by selftest().
"""
import numpy as np, hashlib
import os as _os
BLOCK = int(_os.environ.get('SE_BLOCK', '2'))   # block size B; the manuscript uses B = 2

# ----------------------------------------------------------- 5/3 lifting
def f1(x):
    """Row-wise integer 5/3 analysis, matching f1() in SE_RDHEI.m."""
    x = x.astype(np.int64)
    e = x[:, 0::2]
    o = x[:, 1::2]
    en = np.concatenate([e[:, 1:], e[:, -1:]], axis=1)
    d = o - np.floor_divide(e + en, 2)
    dp = np.concatenate([d[:, :1], d[:, :-1]], axis=1)
    s = e + np.floor_divide(dp + d + 2, 4)
    return s, d


def i1(s, d):
    dp = np.concatenate([d[:, :1], d[:, :-1]], axis=1)
    e = s - np.floor_divide(dp + d + 2, 4)
    en = np.concatenate([e[:, 1:], e[:, -1:]], axis=1)
    o = d + np.floor_divide(e + en, 2)
    x = np.zeros((e.shape[0], e.shape[1] * 2), dtype=np.int64)
    x[:, 0::2] = e
    x[:, 1::2] = o
    return x


def iwt2(I):
    L, H = f1(I)
    LL, LH = f1(L.T)
    HL, HH = f1(H.T)
    return dict(LL=LL.T, LH=LH.T, HL=HL.T, HH=HH.T)


def iiwt2(B):
    L = i1(B['LL'].T, B['LH'].T).T
    H = i1(B['HL'].T, B['HH'].T).T
    return i1(L, H)


def max_levels(shape, cap=4):
    M, N = shape
    L = 0
    while L < cap and M % 2 == 0 and N % 2 == 0 and min(M, N) >= 2:
        M //= 2
        N //= 2
        L += 1
    return L


def iwt2_multi(I, L):
    bands, cur = {}, I.astype(np.int64)
    for lv in range(1, L + 1):
        B = iwt2(cur)
        bands[f'HL{lv}'] = B['HL']
        bands[f'LH{lv}'] = B['LH']
        bands[f'HH{lv}'] = B['HH']
        cur = B['LL']
    bands['LL'] = cur
    return bands


def iiwt2_multi(bands, L):
    cur = bands['LL']
    for lv in range(L, 0, -1):
        cur = iiwt2(dict(LL=cur, LH=bands[f'LH{lv}'],
                         HL=bands[f'HL{lv}'], HH=bands[f'HH{lv}']))
    return cur


def band_names(L):
    det = []
    for lv in range(1, L + 1):
        det += [f'HL{lv}', f'LH{lv}', f'HH{lv}']
    return ['LL'] + det


def band_id(nm):
    if nm == 'LL':
        return 0
    k = ['HL', 'LH', 'HH'].index(nm[:2]) + 1
    return (int(nm[2:]) << 4) | k


# ------------------------------------------------- widths and reservation
def band_width(v):
    lo, hi = int(v.min()), int(v.max())
    W = 2
    while not (-(2 ** (W - 1)) <= lo and hi <= 2 ** (W - 1) - 1):
        W += 1
    return W


def lead_ident(u, W):
    """Number of leading bits equal to the sign bit, as in lead_ident()."""
    sg = (u >> (W - 1)) & 1
    n = np.ones(u.shape, dtype=np.int64)
    for k in range(W - 1, 0, -1):
        bit = (u >> (k - 1)) & 1
        n = n + ((bit == sg) & (n == (W - k))).astype(np.int64)
    return n


def block_t(u, W, tmax, BLK):
    t = np.minimum(lead_ident(u, W) - 1, tmax)
    hh, ww = t.shape
    bh, bw = hh // BLK, ww // BLK
    if bh == 0 or bw == 0:
        return np.zeros((0, 0), dtype=np.int64)
    t = t[:bh * BLK, :bw * BLK]
    return t.reshape(bh, BLK, bw, BLK).min(axis=(1, 3))


def expand_t(tm, shape, BLK):
    f = np.zeros(shape, dtype=np.int64)
    if tm.size:
        f[:tm.shape[0] * BLK, :tm.shape[1] * BLK] = np.kron(tm, np.ones((BLK, BLK), dtype=np.int64))
    return f


# ----------------------------------------------------- SHA-256 CTR / HKDF
def sha(b):
    return hashlib.sha256(bytes(b)).digest()


def ctr(key, nbytes):
    out = bytearray()
    i = 0
    while len(out) < nbytes:
        out += sha(bytes(key) + i.to_bytes(4, 'big'))
        i += 1
    return bytes(out[:nbytes])


def hmac256(key, msg):
    key = bytes(key)
    if len(key) > 64:
        key = sha(key)
    k = key + b'\x00' * (64 - len(key))
    inner = sha(bytes(x ^ 0x36 for x in k) + bytes(msg))
    return sha(bytes(x ^ 0x5c for x in k) + inner)


def hkdf(prk, info, n):
    out, t, i = b'', b'', 1
    while len(out) < n:
        t = hmac256(prk, t + bytes(info) + bytes([i]))
        out += t
        i += 1
    return out[:n]


def keys(km, nonce):
    prk = hmac256(b'SE-RDHEI-v2', km)
    return dict(enc=hkdf(prk, b'ENC', 32), prm=hkdf(prk, b'PERM', 32),
                nonce=nonce)


def keystream(K, nm, n, W):
    k = hkdf(K['enc'], bytes([band_id(nm)]) + K['nonce'], 32)
    by = ctr(k, 2 * n)
    raw = np.frombuffer(by, dtype='<u2').astype(np.int64)
    return raw[:n] & (2 ** W - 1)


def permutation(K, nm, n):
    raw = ctr(bytes(K['prm']) + b'PERM' + bytes([band_id(nm)]) + K['nonce'], 8 * n)
    r = np.frombuffer(raw, dtype='>u8')
    p = np.arange(n)
    for i in range(n - 1, 0, -1):
        j = int(r[i] % (i + 1))
        p[i], p[j] = p[j], p[i]
    return p


# ------------------------------------------------------------- pipeline
def encrypt(I, km=b'\x00' * 32, nonce=b'\x01' * 12, BLK=BLOCK, Lcap=4):
    I = I.astype(np.int64)
    L = max_levels(I.shape, Lcap)
    bands = iwt2_multi(I, L)
    names = band_names(L)
    Wd, C, room = {}, {}, 0
    for nm in names:
        v = bands[nm]
        W = band_width(v)
        Wd[nm] = W
        u = v % (2 ** W)
        if nm != 'LL':                     # LL carries no room
            tm = block_t(u, W, W - 2, BLK)
            t = expand_t(tm, u.shape, BLK)
            u = u & (2 ** (W - t) - 1)     # vacate
            room += int(tm.sum()) * BLK * BLK
        n = u.size
        ks = keystream({'enc': km if False else _K['enc'], 'nonce': nonce}, nm, n, W) \
            if False else keystream(_K, nm, n, W)
        flat = u.T.reshape(-1)             # MATLAB column-major flatten
        diff = (flat ^ ks)
        p = permutation(_K, nm, n)
        C[nm] = diff[p]
    return C, Wd, names, room, L


def packbits_cipher(C, Wd, names):
    bits = []
    for nm in names:
        W, v = Wd[nm], C[nm]
        m = np.zeros((W, v.size), dtype=np.uint8)
        for k in range(W):
            m[k] = (v >> (W - 1 - k)) & 1
        bits.append(m.T.reshape(-1))       # per coefficient, MSB first
    b = np.concatenate(bits)
    b = b[:len(b) // 8 * 8].reshape(-1, 8)
    return (b * (1 << np.arange(7, -1, -1))).sum(axis=1).astype(np.uint8)


# ------------------------------------------------------------ statistics
def entropy8(x):
    p = np.bincount(np.asarray(x).ravel(), minlength=256) / np.asarray(x).size
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def chi2stat(x):
    o = np.bincount(np.asarray(x).ravel(), minlength=256)
    e = np.asarray(x).size / 256
    return float(((o - e) ** 2 / e).sum())


def corr3(x):
    x = np.asarray(x, dtype=float)
    if x.ndim == 1:
        s = int(np.sqrt(x.size))
        x = x[:s * s].reshape(s, s)
    out = []
    for dy, dx in [(0, 1), (1, 0), (1, 1)]:
        a = x[:x.shape[0] - dy, :x.shape[1] - dx].ravel()
        b = x[dy:, dx:].ravel()
        out.append(float((np.mean(a * b) - a.mean() * b.mean()) /
                         (a.std() * b.std() + 1e-300)))
    return out


_K = None


def run(path, km=b'\x00' * 32, nonce=b'\x01' * 12, BLK=BLOCK):
    global _K
    _K = keys(km, nonce)
    from PIL import Image
    I = np.array(Image.open(path).convert('L'))
    C, Wd, names, room, L = encrypt(I, km, nonce, BLK)
    E = packbits_cipher(C, Wd, names)
    cont = sum(Wd[nm] * C[nm].size for nm in names) / I.size
    return dict(I=I, E=E, Hp=entropy8(I), Hc=entropy8(E),
                chi=chi2stat(E), cp=corr3(I),
                cc=corr3(E[:I.size].reshape(I.shape) if E.size >= I.size else E),
                raw=room / I.size, cont=cont, L=L, Wd=Wd)


# ------------------------------------------- full embed / extract / recover
def roundtrip(path, km=b'\x00' * 32, nonce=b'\x01' * 12, BLK=BLOCK, Lcap=4, seed=11):
    """Encrypt, embed a random payload filling the room, extract it and
    recover the cover. Returns arrays for display plus exactness flags."""
    global _K
    _K = keys(km, nonce)
    from PIL import Image
    I = np.array(Image.open(path).convert('L')).astype(np.int64)
    L = max_levels(I.shape, Lcap)
    bands = iwt2_multi(I, L)
    names = band_names(L)
    rng = np.random.default_rng(seed)
    Wd, Cenc, Cmrk, meta, sent = {}, {}, {}, {}, []
    for nm in names:
        v = bands[nm]; W = band_width(v); Wd[nm] = W
        u = v % (2 ** W)
        t = np.zeros(u.shape, dtype=np.int64)
        if nm != 'LL':
            t = expand_t(block_t(u, W, W - 2, BLK), u.shape, BLK)
            u = u & (2 ** (W - t) - 1)
        n = u.size
        ks = keystream(_K, nm, n, W)
        p = permutation(_K, nm, n)
        tf = t.T.reshape(-1)
        diff = u.T.reshape(-1) ^ ks
        pay = np.array([int(rng.integers(0, 2 ** int(k))) if k else 0 for k in tf],
                       dtype=np.int64)
        mark = (diff & (2 ** (W - tf) - 1)) | (pay << (W - tf))
        Cenc[nm] = diff[p]; Cmrk[nm] = mark[p]
        meta[nm] = (W, tf, ks, p, v.shape); sent.append((nm, pay))
    # receiver
    rec, pay_ok, bits = {}, True, 0
    for nm, pay in sent:
        W, tf, ks, p, shp = meta[nm]
        inv = np.empty_like(p); inv[p] = np.arange(p.size)
        m = Cmrk[nm][inv]
        pay_ok &= bool(np.array_equal(m >> (W - tf), pay))
        bits += int(tf.sum())
        x = (m ^ ks) & (2 ** (W - tf) - 1)
        carrier = (x >> (W - tf - 1)) & 1
        u = x + carrier * (2 ** tf - 1) * 2 ** (W - tf)
        v = np.where(u >= 2 ** (W - 1), u - 2 ** W, u)
        rec[nm] = v.reshape(shp[::-1]).T
    R = iiwt2_multi(rec, L)
    def img(C):
        E = packbits_cipher(C, Wd, names)
        s = min(I.shape[0], int(np.sqrt(E.size)))
        return E[:s * s].reshape(s, s)
    return dict(cover=I.astype(np.uint8), enc=img(Cenc), mark=img(Cmrk),
                rec=R, exact=bool(np.array_equal(R, I)), pay_ok=pay_ok,
                bits=bits, rate=bits / I.size)


# ------------------------------- leakage-reduced variant (block permutation)
def block_perm(key, tag, n):
    """Pseudorandom permutation of n blocks from a key."""
    raw = ctr(bytes(key) + tag, 8 * max(n, 1))
    r = np.frombuffer(raw, dtype='>u8')
    p = np.arange(n)
    for i in range(n - 1, 0, -1):
        j = int(r[i] % (i + 1)); p[i], p[j] = p[j], p[i]
    return p


def owner_encrypt_lr(I, Kown, BLK=BLOCK, Lcap=4):
    """Owner side. Coefficients are grouped by block, blocks are permuted by
    sigma (key K_prm, never given to the data hider), and the t-map is
    published in the same permuted order."""
    I = I.astype(np.int64); L = max_levels(I.shape, Lcap)
    bands = iwt2_multi(I, L); names = band_names(L); out = {}
    for nm in names:
        v = bands[nm]; W = band_width(v); u = v % (2 ** W)
        h, w = u.shape
        bh, bw = (h // BLK, w // BLK) if nm != 'LL' else (0, 0)
        tm = block_t(u, W, W - 2, BLK) if nm != 'LL' and bh and bw else np.zeros((0, 0), np.int64)
        t = expand_t(tm, u.shape, BLK)
        uv = u & (2 ** (W - t) - 1)
        # groups: full blocks first (B*B coefficients each), then remainder
        inblk = np.zeros(u.shape, bool); inblk[:bh * BLK, :bw * BLK] = True
        blocks = uv[:bh * BLK, :bw * BLK].reshape(bh, BLK, bw, BLK).transpose(0, 2, 1, 3).reshape(bh * bw, BLK * BLK)
        rest = uv[~inblk]
        sig = block_perm(Kown['prm'], b'BLK' + nm.encode(), bh * bw)
        rho = block_perm(Kown['prm'], b'REST' + nm.encode(), rest.size)
        flat = np.concatenate([blocks[sig].reshape(-1), rest[rho]])
        ks = keystream(Kown, nm, flat.size, W)
        out[nm] = dict(C=flat ^ ks, W=W, Tperm=tm.reshape(-1)[sig] if tm.size else np.zeros(0, np.int64),
                       shape=u.shape, bh=bh, bw=bw, nrest=rest.size)
    return out, L, names


def hider_embed_lr(ct, names, payload_bits, K_hide, nonce, BLK=BLOCK):
    """Data hider: sees only C, the permuted t-map and W_b. No K_prm, no K_enc."""
    tot = sum(int(ct[nm]['Tperm'].sum()) * BLK * BLK for nm in names)
    assert payload_bits.size <= tot
    stream = np.unpackbits(np.frombuffer(ctr(bytes(K_hide) + nonce, (tot + 7) // 8), np.uint8))[:tot]
    pad = np.zeros(tot, np.uint8); pad[:payload_bits.size] = payload_bits
    bits = pad ^ stream                               # payload encrypted under the hider's own key
    k = 0
    for nm in names:
        c = ct[nm]; W = c['W']; C = c['C'].copy()
        for g, T in enumerate(c['Tperm']):
            for j in range(BLK * BLK):
                i = g * BLK * BLK + j
                for q in range(T):                   # top T bits, MSB first
                    p = W - 1 - q
                    C[i] = (C[i] & ~(1 << p)) | (int(bits[k]) << p); k += 1
        c['Cm'] = C
    return tot


def receiver_extract_lr(ct, names, n_payload, K_hide, nonce, BLK=BLOCK):
    """Path a: needs only the permuted t-map and K_hide."""
    bits = []
    for nm in names:
        c = ct[nm]; W = c['W']
        for g, T in enumerate(c['Tperm']):
            for j in range(BLK * BLK):
                i = g * BLK * BLK + j
                for q in range(T):
                    bits.append((int(c['Cm'][i]) >> (W - 1 - q)) & 1)
    bits = np.array(bits, np.uint8)
    stream = np.unpackbits(np.frombuffer(ctr(bytes(K_hide) + nonce, (bits.size + 7) // 8), np.uint8))[:bits.size]
    return (bits ^ stream)[:n_payload]


def receiver_recover_lr(ct, names, L, Kown, BLK=BLOCK):
    """Path b: needs the master key."""
    rec = {}
    for nm in names:
        c = ct[nm]; W = c['W']; bh, bw = c['bh'], c['bw']; h, w = c['shape']
        ks = keystream(Kown, nm, c['Cm'].size, W)
        x = c['Cm'] ^ ks
        nb = bh * bw
        tb = np.repeat(c['Tperm'], BLK * BLK) if nb else np.zeros(0, np.int64)
        tf = np.concatenate([tb, np.zeros(c['nrest'], np.int64)])
        x = x & (2 ** (W - tf) - 1)
        car = (x >> (W - tf - 1)) & 1
        uu = x + car * (2 ** tf - 1) * 2 ** (W - tf)
        sig = block_perm(Kown['prm'], b'BLK' + nm.encode(), nb)
        rho = block_perm(Kown['prm'], b'REST' + nm.encode(), c['nrest'])
        blocks = np.empty((nb, BLK * BLK), np.int64); blocks[sig] = uu[:nb * BLK * BLK].reshape(nb, BLK * BLK)
        rest = np.empty(c['nrest'], np.int64); rest[rho] = uu[nb * BLK * BLK:]
        U = np.zeros((h, w), np.int64)
        if nb:
            U[:bh * BLK, :bw * BLK] = blocks.reshape(bh, bw, BLK, BLK).transpose(0, 2, 1, 3).reshape(bh * BLK, bw * BLK)
        m = np.zeros((h, w), bool); m[:bh * BLK, :bw * BLK] = True
        U[~m] = rest
        rec[nm] = np.where(U >= 2 ** (W - 1), U - 2 ** W, U)
    return iiwt2_multi(rec, L)


def huff_len(sym):
    """Total Huffman code length of a symbol sequence (zeroth order)."""
    import heapq
    f = np.bincount(sym) if sym.size else np.zeros(0, int)
    f = [int(x) for x in f if x > 0]
    if len(f) <= 1:
        return int(sum(f))
    h = list(f); heapq.heapify(h); tot = 0
    while len(h) > 1:
        a = heapq.heappop(h); b = heapq.heappop(h); tot += a + b; heapq.heappush(h, a + b)
    return tot


def huff_code_lengths(cnt):
    """Optimal (Huffman) code length per symbol; 0 for unused symbols."""
    import heapq
    act = [i for i, c in enumerate(cnt) if c > 0]
    L = [0] * len(cnt)
    if len(act) == 1:
        L[act[0]] = 1
        return L
    h = [(int(cnt[i]), k, [i]) for k, i in enumerate(act)]
    heapq.heapify(h); k = len(h)
    while len(h) > 1:
        a = heapq.heappop(h); b = heapq.heappop(h)
        for i in a[2] + b[2]:
            L[i] += 1
        heapq.heappush(h, (a[0] + b[0], k, a[2] + b[2])); k += 1
    return L


def _canonical(L):
    """Canonical codewords from code lengths: symbol -> (code, length)."""
    code, prev, out = 0, 0, {}
    for ln, sym in sorted((ln, s) for s, ln in enumerate(L) if ln > 0):
        code <<= ln - prev; out[sym] = (code, ln); code += 1; prev = ln
    return out


def tmap_encode(syms):
    """Specified t-map descriptor, Eq. (h0): one byte alpha, a 4-bit code length
    per symbol (the code table), then the Huffman-coded symbols; zero-padded to
    whole bytes.  Returns (bytes, number of meaningful bits)."""
    syms = np.asarray(syms, np.int64)
    alpha = max(2, int(syms.max(initial=0))) + 2
    cnt = np.bincount(syms, minlength=alpha)
    L = huff_code_lengths(cnt)
    assert max(L) <= 15 and alpha <= 255
    bits = [(alpha >> (7 - q)) & 1 for q in range(8)]
    for ln in L:
        bits += [(ln >> (3 - q)) & 1 for q in range(4)]
    cw = _canonical(L)
    for x in syms.tolist():
        c, ln = cw[x]
        bits += [(c >> (ln - 1 - q)) & 1 for q in range(ln)]
    nbits = len(bits)
    return np.packbits(np.array(bits + [0] * (-nbits % 8), np.uint8)).tobytes(), nbits


def tmap_decode(data, nsym):
    bits = np.unpackbits(np.frombuffer(data, np.uint8)).tolist()
    alpha = int(''.join(map(str, bits[:8])), 2); pos = 8
    L = []
    for _ in range(alpha):
        L.append(int(''.join(map(str, bits[pos:pos + 4])), 2)); pos += 4
    inv = {(c, ln): s for s, (c, ln) in _canonical(L).items()}
    out = []
    while len(out) < nsym:
        c = ln = 0
        while (c, ln) not in inv:
            c = (c << 1) | bits[pos]; pos += 1; ln += 1
            if ln > 15:
                raise ValueError('invalid t-map code')
        out.append(inv[(c, ln)])
    return np.array(out, np.int64)


def _nblocks(H, nm):
    if nm == 'LL':
        return 0
    lv = int(nm[2:]); B = H['B']
    return ((H['M'] >> lv) // B) * ((H['N'] >> lv) // B)


# --------------------------- specified stream: AES-256-CTR (SP 800-38A)
CTR_MAX_BYTES = 16 * 2 ** 24        # 2^24 counter blocks per stream


def aes_ctr(key32, iv16, nbytes):
    """AES-256-CTR keystream (SP 800-38A). The 16-byte counter block is
    nonce (12 B) || domain byte || 24-bit block counter, big-endian, starting
    at 0: the first keystream block is AES_K(nonce || dom || 0x000000). The
    counter is incremented by one per block as a big-endian integer; a request
    that would wrap it (more than 2^24 blocks) is rejected rather than allowed
    to carry into the domain byte. The last block is truncated to nbytes."""
    iv16 = bytes(iv16)
    if len(iv16) != 16 or iv16[13:] != b'\x00\x00\x00':
        raise ValueError('counter block must end in a zero 24-bit counter')
    if not 0 <= nbytes <= CTR_MAX_BYTES:
        raise ValueError('keystream request exceeds 2^24 counter blocks')
    return _aes_ctr_raw(key32, iv16, nbytes)


def _aes_ctr_raw(key32, iv16, nbytes):
    """Plain SP 800-38A CTR from an arbitrary counter block (self-test only)."""
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    enc = Cipher(algorithms.AES(bytes(key32)), modes.CTR(bytes(iv16))).encryptor()
    return enc.update(b'\x00' * nbytes) + enc.finalize()


def hkdf_extract(salt, ikm):
    return hmac256(salt, ikm)


def iv_for(nonce, dom):
    """Initial counter block: 96-bit nonce || one domain byte || 24-bit counter = 0.
    Matches aes_ctr() in SE_RDHEI.m, which pads [nonce band_id] with zeros."""
    return bytes(nonce) + bytes([dom]) + b'\x00\x00\x00'


DOM_TMAP, DOM_HIDE = 0xF0, 0xF1          # domain bytes outside the band_id range


def spec_perm(K_prm, tag, nm, nonce, n):
    """sigma_b / rho_b of the specified construction: Fisher-Yates driven by
    64-bit big-endian words of AES-256-CTR under a key bound to K_prm, the
    purpose tag, the band and the nonce, so every image gets fresh permutations.

    Each index is drawn without modulo bias by rejection sampling: for step i
    (i = n-1 down to 1, m = i+1) the next unused word w is accepted iff
    w < 2^64 - (2^64 mod m), and then j = w mod m. Words are consumed strictly
    in stream order; a rejected word is skipped. With a uniform stream the
    result is exactly uniform over all n! permutations."""
    k = hkdf(K_prm, tag + bytes([band_id(nm)]) + bytes(nonce), 32)
    iv = iv_for(nonce, band_id(nm))
    avail = n + 64                                   # words generated so far
    r = np.frombuffer(aes_ctr(k, iv, 8 * avail), dtype='>u8')
    p = np.arange(n); pos = 0; R = 1 << 64
    for i in range(n - 1, 0, -1):
        m = i + 1; lim = R - (R % m)
        while True:
            if pos == avail:                         # extend; CTR output is prefix-stable
                avail *= 2
                r = np.frombuffer(aes_ctr(k, iv, 8 * avail), dtype='>u8')
            w = int(r[pos]); pos += 1
            if w < lim:
                break
        j = w % m; p[i], p[j] = p[j], p[i]
    return p


def keystream_aes(K, nm, n, W):
    """Coefficient keystream of the specification (= SE_RDHEI.m with useAES)."""
    assert 2 <= W <= 16, 'a band width above 16 bits needs a wider keystream word'
    k = hkdf(K['enc'], bytes([band_id(nm)]) + K.get('h1', b'') + K.get('h2', b'')
             + K.get('F', {}).get(nm, b'') + K['nonce'], 32)
    by = aes_ctr(k, iv_for(K['nonce'], band_id(nm)), 2 * n)
    raw = np.frombuffer(by, dtype='<u2').astype(np.int64)
    return raw[:n] & (2 ** W - 1)


def selftest():
    # RFC 5869, Test Case 1 (SHA-256)
    ikm = bytes([0x0b] * 22); salt = bytes(range(13)); info = bytes(range(0xf0, 0xfa))
    okm = hkdf(hkdf_extract(salt, ikm), info, 42).hex()
    ok1 = okm == ('3cb25f25faacd57a90434f64d0362f2a2d2d0a90cf1a5a4c5db02d56ecc4c5bf'
                  '34007208d5b887185865')
    # NIST SP 800-38A F.5.5 CTR-AES256.Encrypt, first block
    key = bytes.fromhex('603deb1015ca71be2b73aef0857d77811f352c073b6108d72d9810a30914dff4')
    ctr0 = bytes.fromhex('f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff')
    pt = bytes.fromhex('6bc1bee22e409f96e93d7e117393172a')
    ct = bytes(a ^ b for a, b in zip(_aes_ctr_raw(key, ctr0, 16), pt)).hex()
    ok2 = ct == '601ec313775789a5b7a7f504bbf3d228'
    return ok1, ok2


# ============================================================================
# SPECIFIED CONSTRUCTION: leakage-reduced descriptor + AES-256-CTR + key split
# Each role is a separate function that receives only the keys that role holds.
# ============================================================================
def owner_keys(K, nonce):
    prk = hkdf_extract(b'SE-RDHEI-v2', K)
    return dict(enc=hkdf(prk, b'ENC', 32), prm=hkdf(prk, b'PERM', 32),
                tmap=hkdf(prk, b'TMAP', 32), mac=hkdf(prk, b'MAC', 32), nonce=bytes(nonce))


def hider_keys(KH):
    prk = hkdf_extract(b'SE-RDHEI-hider', KH)
    return dict(hide=hkdf(prk, b'HIDE', 32), tag=hkdf(prk, b'TAG', 32))


def _bits_hi(v, W, k):           # top k bits of a W-bit word, MSB first
    return [(v >> (W - 1 - q)) & 1 for q in range(k)]


def _ser_header(H):
    out = bytearray(H['nonce'] + H['M'].to_bytes(4, 'big') + H['N'].to_bytes(4, 'big')
                    + bytes([H['L'], H['B']]))
    for nm in H['names']:
        out += bytes([H['W'][nm]])
    out += H['Tcode']
    if 'nD' in H:
        out += H['nD'].to_bytes(3, 'big')
    return bytes(out)


def _tfield(H, nm, n):
    B2 = H['B'] ** 2
    t = np.repeat(H['Tplain'][nm], B2) if H['Tplain'][nm].size else np.zeros(0, np.int64)
    return np.concatenate([t, np.zeros(n - t.size, np.int64)])


def _ser_nonreserved(C, H):
    bits = []
    for nm in H['names']:
        W = H['W'][nm]; c = C[nm]; tf = _tfield(H, nm, c.size)
        for v, t in zip(c.tolist(), tf.tolist()):
            low = W - t
            bits += [(v >> (low - 1 - q)) & 1 for q in range(low)]
    return np.packbits(np.array(bits, np.uint8)).tobytes()


def _ser_all(C, H):
    out = bytearray()
    for nm in H['names']:
        out += C[nm].astype('>u2').tobytes()
    return bytes(out)


def spec_owner(I, K, nonce, BLK=BLOCK, Lcap=4):
    """Content owner. Holds K. Emits (C, H0, tau1); gives the data hider K_tmap only."""
    k = owner_keys(K, nonce)
    I = I.astype(np.int64); L = max_levels(I.shape, Lcap)
    bands = iwt2_multi(I, L); names = band_names(L)
    C, H = {}, dict(nonce=bytes(nonce), M=I.shape[0], N=I.shape[1], L=L, B=BLK,
                    names=names, W={}, Tplain={})
    for nm in names:
        v = bands[nm]; W = band_width(v); u = v % (2 ** W); h, w = u.shape
        bh, bw = (h // BLK, w // BLK) if nm != 'LL' else (0, 0)
        tm = block_t(u, W, W - 2, BLK) if (nm != 'LL' and bh and bw) else np.zeros((0, 0), np.int64)
        uv = u & (2 ** (W - expand_t(tm, u.shape, BLK)) - 1)
        inb = np.zeros(u.shape, bool); inb[:bh * BLK, :bw * BLK] = True
        blocks = uv[:bh * BLK, :bw * BLK].reshape(bh, BLK, bw, BLK).transpose(0, 2, 1, 3).reshape(bh * bw, BLK * BLK)
        rest = uv[~inb]
        sig = spec_perm(k['prm'], b'BLK', nm, k['nonce'], bh * bw)
        rho = spec_perm(k['prm'], b'REST', nm, k['nonce'], rest.size)
        flat = np.concatenate([blocks[sig].reshape(-1), rest[rho]])
        C[nm] = flat ^ keystream_aes(k, nm, flat.size, W)
        tp = tm.reshape(-1)[sig].astype(np.int64) if tm.size else np.zeros(0, np.int64)
        H['W'][nm] = W; H['Tplain'][nm] = tp
    code, nbits = tmap_encode(np.concatenate([H['Tplain'][nm] for nm in names]))
    ks = np.frombuffer(aes_ctr(k['tmap'], iv_for(nonce, DOM_TMAP), len(code)), np.uint8)
    H['Tcode'] = bytes(np.frombuffer(code, np.uint8) ^ ks); H['Tbits'] = nbits
    H0 = {kk: vv for kk, vv in H.items() if kk != 'Tplain'}
    tau1 = hmac256(k['mac'], _ser_header(H0) + _ser_nonreserved(C, H))
    return C, H0, tau1


def _decrypt_tmap(H0, K_tmap):
    e = np.frombuffer(H0['Tcode'], np.uint8)
    ks = np.frombuffer(aes_ctr(K_tmap, iv_for(H0['nonce'], DOM_TMAP), max(e.size, 1)), np.uint8)[:e.size]
    n = [_nblocks(H0, nm) for nm in H0['names']]
    syms = tmap_decode(bytes(e ^ ks), sum(n))
    T, o = {}, 0
    for nm, k in zip(H0['names'], n):
        T[nm] = syms[o:o + k]; o += k
    return T


def spec_recover(Cm, H1, tau1, K):
    """Cover receiver. Holds K. Verifies tau1 over H0 and non-reserved bits, then recovers."""
    k = owner_keys(K, H1['nonce'])
    H0 = {kk: vv for kk, vv in H1.items() if kk != 'nD'}
    H = dict(H0)
    try:                                    # a corrupt descriptor cannot authenticate
        H['Tplain'] = _decrypt_tmap(H0, k['tmap'])
    except (ValueError, IndexError):
        return None
    if hmac256(k['mac'], _ser_header(H0) + _ser_nonreserved(Cm, H)) != tau1:
        return None
    B = H['B']; rec = {}
    for nm in H['names']:
        W = H['W'][nm]; c = Cm[nm]; tf = _tfield(H, nm, c.size)
        x = (c ^ keystream_aes(k, nm, c.size, W)) & (2 ** (W - tf) - 1)
        car = (x >> (W - tf - 1)) & 1
        uu = x + car * (2 ** tf - 1) * 2 ** (W - tf)
        # shape of the band
        lv = 0 if nm == 'LL' else int(nm[2:])
        lvl = H['L'] if nm == 'LL' else lv
        h, w = H['M'] >> lvl, H['N'] >> lvl
        bh, bw = (h // B, w // B) if nm != 'LL' else (0, 0)
        nb = bh * bw; nrest = h * w - nb * B * B
        sig = spec_perm(k['prm'], b'BLK', nm, k['nonce'], nb)
        rho = spec_perm(k['prm'], b'REST', nm, k['nonce'], nrest)
        blocks = np.empty((nb, B * B), np.int64); blocks[sig] = uu[:nb * B * B].reshape(nb, B * B)
        rest = np.empty(nrest, np.int64); rest[rho] = uu[nb * B * B:]
        U = np.zeros((h, w), np.int64)
        if nb:
            U[:bh * B, :bw * B] = blocks.reshape(bh, bw, B, B).transpose(0, 2, 1, 3).reshape(bh * B, bw * B)
        m = np.zeros((h, w), bool); m[:bh * B, :bw * B] = True; U[~m] = rest
        rec[nm] = np.where(U >= 2 ** (W - 1), U - 2 ** W, U)
    return iiwt2_multi(rec, H['L'])


# ---- vectorised versions of the bit-level helpers (same semantics) ----
def _bitmat(c, W):                 # rows = coefficients, cols = bits MSB first
    return ((c[:, None] >> (W - 1 - np.arange(W))[None, :]) & 1).astype(np.uint8)


def _ser_nonreserved(C, H):
    out = []
    for nm in H['names']:
        W = H['W'][nm]; c = C[nm]; tf = _tfield(H, nm, c.size)
        m = _bitmat(c, W)
        keep = np.arange(W)[None, :] >= tf[:, None]
        out.append(m[keep])
    return np.packbits(np.concatenate(out)).tobytes()


def _reserved_bits(C, H):
    out = []
    for nm in H['names']:
        W = H['W'][nm]; c = C[nm]; tf = _tfield(H, nm, c.size)
        m = _bitmat(c, W)
        out.append(m[np.arange(W)[None, :] < tf[:, None]])
    return np.concatenate(out)


def _write_reserved(C, H, bits):
    Cm, k = {}, 0
    for nm in H['names']:
        W = H['W'][nm]; c = C[nm]; tf = _tfield(H, nm, c.size)
        m = _bitmat(c, W); sel = np.arange(W)[None, :] < tf[:, None]
        n = int(sel.sum()); m[sel] = bits[k:k + n]; k += n
        Cm[nm] = (m.astype(np.int64) << (W - 1 - np.arange(W))[None, :]).sum(axis=1)
    return Cm


def hider_room(H0, K_tmap):
    """Number of reserved bits the data hider can fill, from the encrypted t-map."""
    T = _decrypt_tmap(H0, K_tmap)
    return sum(int(T[nm].sum()) for nm in H0['names']) * H0['B'] ** 2


def spec_hider(C, H0, tau1, K_tmap, KH, D):
    """Data hider. Holds K_tmap (from the owner) and its own K_H; never K, K_enc,
    K_prm or K_mac. Writes the payload D (0/1 array), encrypted under K_hide,
    into the reserved bits and returns (C', H, tau2)."""
    kh = hider_keys(KH)
    H = dict(H0); H['Tplain'] = _decrypt_tmap(H0, K_tmap)
    tot = sum(int(H['Tplain'][nm].sum()) * H['B'] ** 2 for nm in H['names'])
    assert D.size <= tot, 'payload exceeds room'
    st = np.unpackbits(np.frombuffer(aes_ctr(kh['hide'], iv_for(H0['nonce'], DOM_HIDE), (tot + 7) // 8), np.uint8))[:tot]
    bits = np.zeros(tot, np.uint8); bits[:D.size] = D; bits ^= st
    Cm = _write_reserved(C, H, bits)
    H1 = dict(H0); H1['nD'] = int(D.size)
    tau2 = hmac256(kh['tag'], _ser_header(H1) + _ser_all(Cm, H1) + tau1)
    return Cm, H1, tau2


def spec_extract(Cm, H1, tau1, tau2, K_tmap, KH):
    """Payload receiver. Holds K_tmap and K_H. Verifies tau2, then returns the
    payload, or None if the tag does not verify."""
    kh = hider_keys(KH)
    if hmac256(kh['tag'], _ser_header(H1) + _ser_all(Cm, H1) + tau1) != tau2:
        return None
    H = dict(H1); H['Tplain'] = _decrypt_tmap(H1, K_tmap)
    bits = _reserved_bits(Cm, H)
    st = np.unpackbits(np.frombuffer(aes_ctr(kh['hide'], iv_for(H1['nonce'], DOM_HIDE), (bits.size + 7) // 8), np.uint8))[:bits.size]
    return (bits ^ st)[:H1['nD']]
