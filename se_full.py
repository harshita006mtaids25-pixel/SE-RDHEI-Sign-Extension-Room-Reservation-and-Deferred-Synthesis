"""SE-RDHEI measurement engine: a line-by-line Python port of the batch mode of
SE_RDHEI.m (functions keys, keystream, permutation, encrypt_embed,
extract_decrypt, tmap_pack, one_image and the helpers they call).

Capacity, side information, container size and exactness do not depend on
the key, so they reproduce the MATLAB run bit for bit on the same cover file.
Ciphertext statistics depend on the key, the nonce and the two credentials
A1, A2; they reproduce MATLAB exactly only when the same audio clips are
supplied (export handel.mat and gong.mat from MATLAB), and otherwise agree
statistically.
"""
import hashlib, math, time
import numpy as np
from scipy.stats import chi2 as _chi2
from scipy.special import erfcinv

try:
    from numba import njit
except Exception:                                    # numba is optional
    def njit(*a, **k):
        if a and callable(a[0]):
            return a[0]
        return lambda f: f

SUB = ['LL', 'HL', 'LH', 'HH']
import os as _os
# Block size B of the block minimum (Eq. 7). The manuscript uses B = 2; set the
# environment variable SE_BLOCK to run another size.
BLOCK = int(_os.environ.get('SE_BLOCK', '2'))
DEFAULT_KEY = bytes(range(32))
DEFAULT_NONCE = b'0123456789ab'
AUDIO_LEN = 160000                                   # 10 s at 16 kHz


# ------------------------------------------------------------- 5/3 lifting
def f1(x):
    x = x.astype(np.int64)
    e, o = x[:, 0::2], x[:, 1::2]
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
    x = np.zeros((e.shape[0], 2 * e.shape[1]), dtype=np.int64)
    x[:, 0::2], x[:, 1::2] = e, o
    return x


def iwt2(I):
    L, H = f1(I)
    LL, LH = f1(L.T)
    HL, HH = f1(H.T)
    return dict(LL=LL.T, LH=LH.T, HL=HL.T, HH=HH.T)


def iiwt2_raw(B):
    L = i1(B['LL'].T, B['LH'].T).T
    H = i1(B['HL'].T, B['HH'].T).T
    return i1(L, H)


def max_levels(shape, cap=4):
    M, N = shape
    L = 0
    while L < cap and M % 2 == 0 and N % 2 == 0 and min(M, N) >= 2:
        M //= 2; N //= 2; L += 1
    return max(L, 1)


def band_names(L):
    det = []
    for lv in range(1, L + 1):
        det += ['HL%d' % lv, 'LH%d' % lv, 'HH%d' % lv]
    return ['LL'] + det, det


def band_id(nm):
    if nm == 'LL':
        return 0
    return (int(nm[2:]) << 4) | (['HL', 'LH', 'HH'].index(nm[:2]) + 1)


def sub_of(nm):
    return 'LL' if nm == 'LL' else nm[:2]


def iwt2_multi(I, L):
    B, cur = {}, I.astype(np.int64)
    for lv in range(1, L + 1):
        Q = iwt2(cur)
        B['HL%d' % lv], B['LH%d' % lv], B['HH%d' % lv] = Q['HL'], Q['LH'], Q['HH']
        cur = Q['LL']
    B['LL'] = cur
    return B


def iiwt2_multi(B, L):
    cur = B['LL']
    for lv in range(L, 0, -1):
        cur = iiwt2_raw(dict(LL=cur, HL=B['HL%d' % lv], LH=B['LH%d' % lv], HH=B['HH%d' % lv]))
    return np.clip(cur, 0, 255).astype(np.uint8)


# ------------------------------------------ field coding and reservation
def band_width(v):
    lo, hi = int(v.min()), int(v.max())
    W = 2
    while not (-(2 ** (W - 1)) <= lo and hi <= 2 ** (W - 1) - 1):
        W += 1
    return W


def lead_ident(u, W):
    sg = (u >> (W - 1)) & 1
    n = np.ones(u.shape, dtype=np.int64)
    for k in range(W - 1, 0, -1):
        n += (((u >> (k - 1)) & 1) == sg) & (n == (W - k))
    return n


def block_t(u, W, tmax, BLK):
    t = np.minimum(lead_ident(u, W) - 1, tmax)
    hh, ww = t.shape
    bh, bw = hh // BLK, ww // BLK
    if bh == 0 or bw == 0:
        return np.zeros((0, 0), dtype=np.int64)
    return t[:bh * BLK, :bw * BLK].reshape(bh, BLK, bw, BLK).min(axis=(1, 3))


def expand_t(tm, shape, BLK):
    f = np.zeros(shape, dtype=np.int64)
    if tm.size:
        f[:tm.shape[0] * BLK, :tm.shape[1] * BLK] = np.kron(tm, np.ones((BLK, BLK), dtype=np.int64))
    return f


def vacate(u, t, W):
    return u & ((1 << (W - t)) - 1)


def restore(u, t, W):
    carrier = (u >> (W - t - 1)) & 1
    return (u & ((1 << (W - t)) - 1)) + ((1 << t) - 1) * (1 << (W - t)) * carrier


def slots(t, W):
    """Row-major flat index and 0-based bit position of every vacated slot."""
    f = t.reshape(-1)
    ii, bb = [], []
    for k in range(1, int(f.max(initial=0)) + 1):
        s = np.nonzero(f >= k)[0]
        ii.append(s); bb.append(np.full(s.size, W - k, dtype=np.int64))
    if not ii:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    return np.concatenate(ii), np.concatenate(bb)


# ---------------------------------------------------- SHA-256 / CTR / HKDF
def sha(b):
    return hashlib.sha256(bytes(b)).digest()


def ctr(key, nbytes):
    key = bytes(key)
    nb = -(-nbytes // 32)
    return b''.join(hashlib.sha256(key + i.to_bytes(4, 'big')).digest() for i in range(nb))[:nbytes]


def hmac256(key, msg):
    key = bytes(key)
    if len(key) > 64:
        key = sha(key)
    k = key + b'\x00' * (64 - len(key))
    return sha(bytes(x ^ 92 for x in k) + sha(bytes(x ^ 54 for x in k) + bytes(msg)))


def hkdf(prk, info, n):
    out, t, i = b'', b'', 1
    while len(out) < n:
        t = hmac256(prk, t + bytes(info) + bytes([i])); out += t; i += 1
    return out[:n]


# ------------------------------------------------------ audio credentials
def canon_audio(y, fs, L=AUDIO_LEN):
    """fetch_audio(): mono, linear resample to 16 kHz, loop, crop, peak to int16."""
    y = np.asarray(y, dtype=float)
    if y.ndim > 1:
        y = y.mean(axis=1) if y.shape[0] > y.shape[1] else y.mean(axis=0)
    y = y.ravel()
    if fs != 16000:
        n2 = max(int(round(y.size * 16000 / fs)), 2)
        y = np.interp(np.linspace(0, 1, n2), np.linspace(0, 1, y.size), y)
    if y.size < L:
        y = np.tile(y, -(-L // y.size))
    y = y[:L]
    m = np.abs(y).max() or 1.0
    return np.floor(y / m * 32767 + 0.5).astype(np.int16)


def synthetic_audio(k, L=AUDIO_LEN):
    t = np.arange(L) / 16000
    if k == 1:
        y = np.sin(2 * np.pi * 220 * t) * (1 + 0.5 * np.sin(2 * np.pi * 3 * t))
    else:
        y = np.sign(np.sin(2 * np.pi * 90 * t)) * np.exp(-np.mod(t, 0.5) * 6)
    return canon_audio(y, 16000, L)


def load_audio(path):
    """WAV/FLAC/OGG (via soundfile or scipy) or a MATLAB .mat with y and Fs."""
    p = str(path).lower()
    if p.endswith('.mat'):
        from scipy.io import loadmat
        S = loadmat(path)
        return canon_audio(S['y'], float(np.squeeze(S['Fs'])))
    try:
        import soundfile as sf
        y, fs = sf.read(path, dtype='float64')
    except Exception:
        from scipy.io import wavfile
        fs, y = wavfile.read(path)
        if y.dtype.kind == 'i':
            y = y / float(2 ** (8 * y.dtype.itemsize - 1))
        elif y.dtype.kind == 'u':
            y = (y.astype(float) - 128) / 128
    return canon_audio(y, fs)


def _stft(a, Wn=1024, Hp=256):
    x = a.astype(float) / 32768
    win = 0.5 - 0.5 * np.cos(2 * np.pi * np.arange(Wn) / Wn)
    T = 1 + (x.size - Wn) // Hp
    idx = np.arange(T)[:, None] * Hp + np.arange(Wn)[None, :]
    return np.fft.fft(x[idx] * win, axis=1)[:, :Wn // 2 + 1]


def _round(x):                                       # MATLAB round, half away from 0
    return np.sign(x) * np.floor(np.abs(x) + 0.5)


def _pct(x, p):
    x = np.sort(x.ravel())
    return x[int(max(1, min(x.size, _round(p / 100 * x.size)))) - 1]


_STFT_CACHE = {}


def _stft_cached(a):
    h = sha(a.astype('<i2').tobytes())
    if h not in _STFT_CACHE:
        if len(_STFT_CACHE) > 8:
            _STFT_CACHE.clear()
        _STFT_CACHE[h] = _stft(a)
    return _STFT_CACHE[h]


def descriptor(a1, a2, alpha, theta):
    X1, X2 = _stft_cached(a1), _stft_cached(a2)
    Ln = np.log(1 + np.abs(X1 + alpha * X2 * np.exp(1j * theta)) ** 2)
    mag = np.abs(X1)
    f = np.arange(mag.shape[1], dtype=float)
    cen = (mag @ f) / (mag.sum(axis=1) + 1e-12)
    en = np.log(1 + (mag ** 2).sum(axis=1))
    return np.array([Ln.mean(), Ln.std(), Ln.max(), cen.mean(), cen.std(),
                     en.mean(), en.std(), _pct(Ln, 10), _pct(Ln, 50), _pct(Ln, 90)])


def qdesc(v):
    q = _round(np.clip(v, -1e4, 1e4) * 128)
    return b''.join((int(x) & (2 ** 64 - 1)).to_bytes(8, 'big') for x in q)


def keys(km, a1, a2, nonce, use_credentials=True):
    K = dict(nonce=bytes(nonce))
    K['h1'] = sha(a1.astype('<i2').tobytes()) if use_credentials else bytes(32)
    K['h2'] = sha(a2.astype('<i2').tobytes()) if use_credentials else bytes(32)
    prk = hmac256(b'SE-RDHEI-v2', km)
    for nm, lab in [('enc', b'ENC'), ('prm', b'PERM'), ('par', b'PARAM'), ('dh', b'DH'),
                    ('mac', b'MAC'), ('pad', b'PAD'), ('tmap', b'TMAP')]:
        K[nm] = hkdf(prk, lab, 32)
    K['F'] = {}
    for b, nm in enumerate(SUB, start=1):
        r = hkdf(K['par'], bytes([b]), 8)
        al = 0.2 + 1.6 * int.from_bytes(r[:4], 'big') / 2 ** 32
        th = 2 * np.pi * int.from_bytes(r[4:], 'big') / 2 ** 32
        K['F'][nm] = sha(qdesc(descriptor(a1, a2, al, th)))[:16] if use_credentials else bytes(16)
    return K


def keystream(K, nm, n, W):
    k = hkdf(K['enc'], bytes([band_id(nm)]) + K['h1'] + K['h2'] + K['F'][sub_of(nm)] + K['nonce'], 32)
    raw = np.frombuffer(ctr(k, 2 * n), dtype='<u2').astype(np.int64)
    return raw[:n] & ((1 << W) - 1)


@njit(cache=True)
def _fisher_yates(r):
    n = r.size
    p = np.arange(n)
    for i in range(n - 1, 0, -1):
        j = r[i] % np.uint64(i + 1)
        t = p[i]; p[i] = p[j]; p[j] = t
    return p


def permutation(K, nm, n):
    raw = ctr(bytes(K['prm']) + b'PERM' + bytes([band_id(nm)]) + K['nonce'], 8 * n)
    r = np.frombuffer(raw, dtype='>u8').astype(np.uint64)
    return _fisher_yates(r)


# ------------------------------------------------------- Huffman side info
def huff_total(cnt):
    """Total bits of an optimal Huffman code (any tie-break gives the same)."""
    import heapq
    w = [int(c) for c in cnt if c > 0]
    if not w:
        return 0
    if len(w) == 1:
        return w[0]
    heapq.heapify(w)
    tot = 0
    while len(w) > 1:
        a = heapq.heappop(w); b = heapq.heappop(w)
        tot += a + b; heapq.heappush(w, a + b)
    return tot


def tmap_pack(tm, det):
    tmax = max(2, max(int(tm[b].max(initial=0)) for b in det))
    alpha = tmax + 2
    sym = np.concatenate([tm[b].ravel() for b in det]) if det else np.zeros(0, np.int64)
    if sym.size == 0:
        return 0
    return huff_total(np.bincount(sym, minlength=alpha)) + 4 * alpha


# ------------------------------------------------- Algorithm 1 / Algorithm 2
def capacity(I, BLK=BLOCK, levels=0):
    """Key-independent quantities of encrypt_embed: raw, side, cap, container."""
    L = min(levels, max_levels(I.shape)) if levels > 0 else max_levels(I.shape)
    B = iwt2_multi(I, L)
    names, det = band_names(L)
    total, tm, cont, wd = 0, {}, 0, {}
    for nm in names:
        W = band_width(B[nm]); cont += W * B[nm].size; rb = 0
        if nm in det:
            u = np.mod(B[nm], 1 << W)
            tm[nm] = block_t(u, W, W - 2, BLK)
            rb = int(tm[nm].sum()) * BLK * BLK; total += rb
        wd[nm] = [int(W), int(B[nm].size), rb]      # width, coefficients, room bits
    side = tmap_pack(tm, det)
    return dict(L=L, raw=total, side=side, cap=max(total - side, 0), cont=cont, tm=tm, bands=wd)


def encrypt_embed(I, km, a1, a2, nonce, payload=None, BLK=BLOCK, levels=0, K=None,
                  rng=None, return_plain_cipher=False):
    L = min(levels, max_levels(I.shape)) if levels > 0 else max_levels(I.shape)
    B = iwt2_multi(I, L)
    names, det = band_names(L)
    if K is None:
        K = keys(km, a1, a2, nonce)
    Wd, shapes, tm, C, sl, total = {}, {}, {}, {}, {}, 0
    for nm in names:
        W = band_width(B[nm]); Wd[nm] = W; shapes[nm] = B[nm].shape
        u = np.mod(B[nm], 1 << W)
        if nm in det:
            tm[nm] = block_t(u, W, W - 2, BLK)
            tf = expand_t(tm[nm], u.shape, BLK)
            u = vacate(u, tf, W)
        n = u.size
        e = u.reshape(-1) ^ keystream(K, nm, n, W)
        p = permutation(K, nm, n)
        C[nm] = e[p]
        if nm in det:
            ii, bb = slots(tf, W)
            pinv = np.empty(n, np.int64); pinv[p] = np.arange(n)
            sl[nm] = (pinv[ii], bb); total += ii.size
    side = tmap_pack(tm, det)
    cap = max(total - side, 0)
    if payload is None:
        rng = rng or np.random.default_rng()
        payload = rng.integers(0, 2, cap).astype(np.uint8)
    if payload.size > total:
        raise ValueError('payload exceeds room')
    npad = total - payload.size
    if npad > 0:
        pb = np.unpackbits(np.frombuffer(ctr(K['pad'] + bytes(nonce), -(-npad // 8)), np.uint8))
        bits = np.concatenate([payload.astype(np.int64), pb[:npad].astype(np.int64)])
    else:
        bits = payload.astype(np.int64)
    Cplain = {nm: C[nm].copy() for nm in names} if return_plain_cipher else None
    off = 0
    for nm in det:
        pos, pb_ = sl[nm]; k = pos.size
        if k == 0:
            continue
        np.bitwise_and.at(C[nm], pos, ~(np.int64(1) << pb_))
        np.bitwise_or.at(C[nm], pos, bits[off:off + k] << pb_)
        off += k
    h = dict(tm=tm, Wd=Wd, nonce=bytes(nonce), shape=I.shape, levels=L, shapes=shapes,
             names=names, det=det, raw=total, side=side, cap=cap, total=total, blk=BLK)
    if return_plain_cipher:
        return C, h, payload, Cplain
    return C, h, payload


def extract_decrypt(C, h, km, a1, a2, K=None):
    BLK = h['blk']
    if K is None:
        K = keys(km, a1, a2, h['nonce'])
    out, Bh = [], {}
    for nm in h['names']:
        W, n, shp = h['Wd'][nm], C[nm].size, h['shapes'][nm]
        p = permutation(K, nm, n)
        isdet = nm in h['det']
        if isdet:
            tf = expand_t(h['tm'][nm], shp, BLK)
            ii, bb = slots(tf, W)
            if ii.size:
                pinv = np.empty(n, np.int64); pinv[p] = np.arange(n)
                out.append((C[nm][pinv[ii]] >> bb) & 1)
        e = np.empty(n, np.int64); e[p] = C[nm]
        u = (e ^ keystream(K, nm, n, W)).reshape(shp)
        if isdet:
            u = restore(u, tf, W)
        Bh[nm] = u - (1 << W) * (u >= (1 << (W - 1)))
    I = iiwt2_multi(Bh, h['levels'])
    pay = np.concatenate(out).astype(np.uint8) if out else np.zeros(0, np.uint8)
    return I, pay


# ------------------------------------------------------------ measurements
def packbits_cipher(C, Wd, names):
    parts = []
    for nm in names:
        W, v = Wd[nm], C[nm]
        m = ((v[:, None] >> np.arange(W - 1, -1, -1)[None, :]) & 1).astype(np.uint8)
        parts.append(m.reshape(-1))
    b = np.concatenate(parts)
    return np.packbits(b[:b.size // 8 * 8])


def entropy8(x):
    p = np.bincount(np.asarray(x).ravel(), minlength=256) / np.asarray(x).size
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def chi2stat(x):
    o = np.bincount(np.asarray(x).ravel(), minlength=256)
    e = np.asarray(x).size / 256
    return float(((o - e) ** 2 / e).sum())


def square(x):
    x = np.asarray(x)
    if x.ndim == 1:
        s = int(math.isqrt(x.size)); x = x[:s * s].reshape(s, s)
    return x


def corr3(x):
    x = square(x).astype(float)
    out = []
    for dy, dx in [(0, 1), (1, 0), (1, 1)]:
        a = x[:x.shape[0] - dy, :x.shape[1] - dx].ravel()
        b = x[dy:, dx:].ravel()
        out.append(float((np.mean(a * b) - a.mean() * b.mean()) / (a.std() * b.std() + 2.2e-16)))
    return out


def npcr_uaci(a, b):
    """NPCR and UACI over the serialised ciphertext bytes. Both ciphertexts of a
    pair have the same length (widths and room depend on the cover only)."""
    assert a.size == b.size, 'ciphertexts of one pair must have equal length'
    a = a.astype(float); b = b.astype(float)
    return float(np.mean(a != b) * 100), float(np.mean(np.abs(a - b)) / 255 * 100)


def npcr_test(v, T, alpha=0.05):
    F = 255; z = -math.sqrt(2) * erfcinv(2 * alpha)
    crit = (F + z * math.sqrt(F / T)) / (F + 1) * 100
    return v > crit, crit


def uaci_test(v, T, alpha=0.05):
    F = 255; mu = (F + 2) / (3 * F + 3)
    sd = math.sqrt((F + 2) * (F ** 2 + 2 * F + 3) / (18 * (F + 1) ** 2 * F * T))
    z = math.sqrt(2) * erfcinv(alpha)
    lo, hi = (mu - z * sd) * 100, (mu + z * sd) * 100
    return lo < v < hi, lo, hi


def cipher_ref(I, km, a1, a2, nonce, BLK, seed, K=None):
    """Ciphertext with the room completely filled by a seeded random payload."""
    cp = capacity(I, BLK)
    full = np.random.default_rng(seed).integers(0, 2, cp['raw']).astype(np.uint8)
    C, h, _ = encrypt_embed(I, km, a1, a2, nonce, full, BLK, K=K)
    return packbits_cipher(C, h['Wd'], h['names'])


def miwt2(I):
    def f1m(x):
        M = 256
        e = np.mod(x[:, 0::2], M); o = np.mod(x[:, 1::2], M)
        en = np.concatenate([e[:, 1:], e[:, -1:]], axis=1)
        d = np.mod(o - np.floor_divide(e + en, 2), M)
        dp = np.concatenate([d[:, :1], d[:, :-1]], axis=1)
        return np.mod(e + np.floor_divide(dp + d + 2, 4), M), d
    L, H = f1m(I.astype(np.int64))
    LL, LH = f1m(L.T); HL, HH = f1m(H.T)
    return dict(LL=LL.T, LH=LH.T, HL=HL.T, HH=HH.T)


def ablation(I, BLK, raw, seed=0):
    rng = np.random.default_rng(seed)
    Bs = iwt2(I); Bq = dict(Bs)
    for nm in ['HL', 'LH', 'HH']:
        W = band_width(Bs[nm]); u = np.mod(Bs[nm], 1 << W)
        tv = expand_t(block_t(u, W, W - 2, BLK), u.shape, BLK)
        u = vacate(u, tv, W) + np.floor(rng.random(u.shape) * 2.0 ** tv).astype(np.int64) * (1 << (W - tv))
        Bq[nm] = u - (1 << W) * (u >= (1 << (W - 1)))
    X = iiwt2_raw(Bq)
    ovf = int(((X < 0) | (X > 255)).sum())
    Bm = miwt2(I)
    mod = sum(int(block_t(Bm[nm], 8, 6, BLK).sum()) * BLK * BLK for nm in ['HL', 'LH', 'HH'])
    return [ovf, 0, mod, int(raw)]


def tmap_leak(h, K):
    tb = np.concatenate([h['tm'][b].T.ravel() for b in h['det']]).astype(np.uint8)
    ks = np.frombuffer(ctr(K['tmap'] + h['nonce'], tb.size), np.uint8)
    return entropy8(tb), entropy8(tb ^ ks)


def display(E, M):
    s = min(M, int(math.isqrt(E.size)))
    return E[:s * s].reshape(s, s)


BSWEEP = (2, 4, 8, 16, 32)


def spec_cipher_bytes(C, H):
    """Serialised ciphertext of the specified construction: every band's W_b-bit
    fields in band order, packed MSB first, final partial byte dropped."""
    return packbits_cipher(C, H['W'], H['names'])


def spec_security(I, K, nonce, KH, BLK, trials, rng, keep=False):
    """Ciphertext statistics and key sensitivity of the specified (AES-256-CTR)
    construction, the one Propositions 1-3 cover. The marked ciphertext carries a
    payload filling the whole room. Key sensitivity: one bit of the master key K
    flipped; nonce, data-hiding key K_H and payload unchanged."""
    import serdhei as SD
    I64 = I.astype(np.int64)

    def marked(Kx, D=None):
        C, H0, t1 = SD.spec_owner(I64, Kx, nonce, BLK=BLK)
        kt = SD.owner_keys(Kx, nonce)['tmap']
        if D is None:
            T = SD._decrypt_tmap(H0, kt)
            room = int(sum(int(T[b].sum()) * BLK * BLK for b in T))
            D = np.random.default_rng(1000).integers(0, 2, room).astype(np.uint8)
        Cm, H1, t2 = SD.spec_hider(C, H0, t1, kt, KH, D)
        return C, H0, Cm, H1, t1, t2, D
    C, H0, Cm, H1, t1, t2, D = marked(K)
    E = spec_cipher_bytes(Cm, H1)
    out = dict(Hciph=entropy8(E), chi2=chi2stat(E))
    out['pchi'] = float(_chi2.sf(out['chi2'], 255)); out['cc'] = corr3(E)
    R = SD.spec_recover(Cm, H1, t1, K)
    out['exact'] = bool(R is not None and np.array_equal(np.asarray(R).astype(np.int64), I64))
    bad = bytearray(K); bad[0] ^= 1
    out['wrong_key_rejected'] = SD.spec_recover(Cm, H1, t1, bytes(bad)) is None
    if keep:
        out['img'] = dict(enc=display(spec_cipher_bytes(C, H0), I.shape[0]), mark=display(E, I.shape[0]),
                          ciph=display(E, I.shape[0]), rec=np.asarray(R).astype(np.uint8))
    if trials > 0:
        # key sensitivity is measured on the content owner's encrypted image, the output
        # K controls; the marked images (same K_H and payload) are recorded as well
        E0 = spec_cipher_bytes(C, H0)

        def wna(A, Bs):
            T = int(A.size); nn = [npcr_uaci(A, b)[0] for b in Bs]; uu = [npcr_uaci(A, b)[1] for b in Bs]
            npass, nstar = npcr_test(float(np.mean(nn)), T); upass, ulo, uhi = uaci_test(float(np.mean(uu)), T)
            return dict(npcr=float(np.mean(nn)), npcr_sd=float(np.std(nn, ddof=1)), uaci=float(np.mean(uu)),
                        uaci_sd=float(np.std(uu, ddof=1)), npcr_trials=nn, uaci_trials=uu,
                        npass_trials=int(sum(bool(npcr_test(x, T)[0]) for x in nn)),
                        upass_trials=int(sum(bool(uaci_test(x, T)[0]) for x in uu)),
                        T=T, nstar=float(nstar), ulo=float(ulo), uhi=float(uhi),
                        npass=bool(npass), upass=bool(upass), trials=len(nn))
        enc, mk = [], []
        for t in range(trials):
            k = bytearray(K); bp = int(rng.integers(0, 256)); k[bp // 8] ^= 1 << (bp % 8)
            Ck, Hk, Cmk, H1k = marked(bytes(k), D)[:4]
            enc.append(spec_cipher_bytes(Ck, Hk)); mk.append(spec_cipher_bytes(Cmk, H1k))
        out['sens'] = wna(E0, enc)
        out['sens_marked'] = wna(E, mk)
        # plaintext sensitivity: one pixel changed by +-1. Under a fresh nonce, as the scheme
        # requires, and, as a diagnostic of the forbidden nonce reuse, under the same nonce.
        fresh, same = [], []
        for t in range(trials):
            for _ in range(50):
                i, j = int(rng.integers(0, I.shape[0])), int(rng.integers(0, I.shape[1]))
                I2 = I64.copy(); I2[i, j] += 1 if I2[i, j] < 255 else -1
                C2, H2, _t = SD.spec_owner(I2, K, nonce, BLK=BLK)
                if H2['W'] == H0['W']:          # same widths, so the two arrays align field by field
                    break
            else:
                continue
            same.append(spec_cipher_bytes(C2, H2))
            C3, H3, _t = SD.spec_owner(I2, K, rng.bytes(12), BLK=BLK)
            fresh.append(spec_cipher_bytes(C3, H3))
        if len(fresh) >= 2:
            out['psens_fresh'] = wna(E0, fresh)
            out['psens_same'] = dict(npcr=float(np.mean([npcr_uaci(E0, b)[0] for b in same])),
                                     uaci=float(np.mean([npcr_uaci(E0, b)[1] for b in same])), trials=len(same))
    return out


def one_image(I, a1, a2, km=DEFAULT_KEY, nonce=DEFAULT_NONCE, BLK=BLOCK, trials=10,
              sweeps=True, seed=0, keep_images=False):
    """Everything one_image() in SE_RDHEI.m reports that the manuscript uses."""
    rng = np.random.default_rng(seed)
    MN = I.size
    r = dict(M=int(I.shape[0]), N=int(I.shape[1]), Hplain=entropy8(I))
    K = keys(km, a1, a2, nonce)
    t0 = time.perf_counter()
    C, h, pl, Cplain = encrypt_embed(I, km, a1, a2, nonce, None, BLK, K=K, rng=rng,
                                     return_plain_cipher=True)
    r['tenc'] = time.perf_counter() - t0
    t0 = time.perf_counter()
    Ir, pe = extract_decrypt(C, h, km, a1, a2, K=K)
    r['tdec'] = time.perf_counter() - t0
    r['exact'] = bool(np.array_equal(Ir, I) and np.array_equal(pe[:pl.size], pl))
    r['maxerr'] = int(np.abs(I.astype(int) - Ir.astype(int)).max())
    r['levels'] = h['levels']
    r['raw'], r['side'], r['net'] = h['raw'] / MN, h['side'] / MN, h['cap'] / MN
    r['cont'] = sum(h['Wd'][b] * C[b].size for b in h['names']) / MN
    r['eff'] = r['net'] - max(r['cont'] - 8, 0)
    r['Wd'] = h['Wd']
    E = packbits_cipher(C, h['Wd'], h['names'])
    r['Hciph'] = entropy8(E); r['chi2'] = chi2stat(E)
    r['pchi'] = float(_chi2.sf(r['chi2'], 255))
    r['cp'] = corr3(I); r['cc'] = corr3(E)
    r['tleak'] = list(tmap_leak(h, K))
    # one-bit wrong key: the recovered image must be unrelated to the cover
    bad = bytearray(km); bad[0] ^= 1
    Iw, _ = extract_decrypt(C, h, bytes(bad), a1, a2)
    r['wrong_match_pct'] = float(np.mean(Iw == I) * 100)
    if keep_images:
        r['img'] = dict(cover=I.astype(np.uint8),
                        enc=display(packbits_cipher(Cplain, h['Wd'], h['names']), I.shape[0]),
                        mark=display(E, I.shape[0]), rec=Ir, ciph=display(E, I.shape[0]))
    # ---- sensitivity: one-bit change of the key, of A1 and of A2
    if trials > 0:
        base = cipher_ref(I, km, a1, a2, nonce, BLK, 1000, K=K)
        for lab in ['key', 'A1', 'A2']:
            nn, uu, npt, upt = [], [], 0, 0
            T = int(base.size)            # number of compared bytes, not M*N
            for t in range(trials):
                k, x1, x2 = bytearray(km), a1.copy(), a2.copy()
                if lab == 'key':
                    bp = int(rng.integers(0, 256)); k[bp // 8] ^= 1 << (bp % 8)
                elif lab == 'A1':
                    j = int(rng.integers(0, x1.size)); x1[j] ^= 1
                else:
                    j = int(rng.integers(0, x2.size)); x2[j] ^= 1
                # same payload and same nonce as the reference: only the key or credential bit differs
                Ec = cipher_ref(I, bytes(k), x1, x2, nonce, BLK, 1000)
                n_, u_ = npcr_uaci(base, Ec); nn.append(n_); uu.append(u_)
                npt += bool(npcr_test(n_, T)[0]); upt += bool(uaci_test(u_, T)[0])
            r['npcr_' + lab] = float(np.mean(nn)); r['npcr_%s_sd' % lab] = float(np.std(nn, ddof=1))
            r['uaci_' + lab] = float(np.mean(uu)); r['uaci_%s_sd' % lab] = float(np.std(uu, ddof=1))
            r['npcr_%s_trials' % lab] = nn; r['uaci_%s_trials' % lab] = uu
            r['npcr_%s_tpass' % lab] = npt; r['uaci_%s_tpass' % lab] = upt
        # Wu-Noonan-Agaian critical values for the number of compared bytes T
        npass, nstar = npcr_test(r['npcr_key'], T)
        upass, ulo, uhi = uaci_test(r['uaci_key'], T)
        r['wu'] = dict(T=T, nstar=nstar, npass=bool(npass), ulo=ulo, uhi=uhi, upass=bool(upass),
                       trials=trials, npass_trials=r['npcr_key_tpass'], upass_trials=r['uaci_key_tpass'])
    # ---- specified construction: ciphertext statistics and key sensitivity
    r['spec'] = spec_security(I, km, nonce, bytes(range(32, 64)), BLK, trials, rng, keep=keep_images)
    if keep_images and 'img' in r['spec']:
        sp = r['spec'].pop('img')
        r['img'].update({'spec_' + k: v for k, v in sp.items()})
    # ---- block-size and level sweeps (key independent)
    if sweeps:
        r['Bnet'] = [capacity(I, b)['cap'] / MN for b in BSWEEP]
        r['Bside'] = [capacity(I, b)['side'] / MN for b in BSWEEP]
        # key-independent values at B = 4, the block size of the recorded MATLAB run,
        # so that the run can still be validated against it
        c4 = capacity(I, 4)
        lv4 = [capacity(I, 4, lv) for lv in (1, 2, 3, 4)]
        det4 = band_names(c4['L'])[1]
        tb4 = np.concatenate([c4['tm'][b].T.ravel() for b in det4]).astype(np.uint8)
        r['val4'] = dict(levels=c4['L'], raw=c4['raw'], side=c4['side'], cap=c4['cap'], cont=c4['cont'],
                         Leff=[(c['cap'] - max(c['cont'] - 8 * MN, 0)) / MN for c in lv4],
                         abl=ablation(I, 4, c4['raw'])[2:], tleak0=entropy8(tb4))
        r['bands'] = capacity(I, BLK)['bands']   # per band: width, coefficients, room
        r['Leff'], r['Lnet'] = [], []
        for lv in (1, 2, 3, 4):
            c = capacity(I, BLK, lv)
            r['Lnet'].append(c['cap'] / MN)
            r['Leff'].append(c['cap'] / MN - max(c['cont'] / MN - 8, 0))
        r['abl'] = ablation(I, BLK, h['raw'])
    return r


def credential_ablation_Hc(I, a1, a2, km=DEFAULT_KEY, nonce=DEFAULT_NONCE, BLK=BLOCK, seed=0):
    """Ciphertext entropy with the credentials on and with them removed."""
    out = []
    for use in (True, False):
        K = keys(km, a1, a2, nonce, use_credentials=use)
        C, h, _ = encrypt_embed(I, km, a1, a2, nonce, None, BLK, K=K,
                                rng=np.random.default_rng(seed))
        out.append(entropy8(packbits_cipher(C, h['Wd'], h['names'])))
    return out


def to_gray(arr):
    """load_cover(): uint8(0.299R + 0.587G + 0.114B), crop to a multiple of 16."""
    a = np.asarray(arr)
    if a.ndim == 3:
        a = a[:, :, :3].astype(float)
        a = np.floor(0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2] + 0.5)
    a = np.clip(a, 0, 255).astype(np.uint8)
    return a[:16 * (a.shape[0] // 16), :16 * (a.shape[1] // 16)]


def read_cover(path):
    from PIL import Image
    im = Image.open(path)
    if im.mode in ('RGB', 'RGBA', 'P', 'CMYK', 'YCbCr', 'LA'):
        im = im.convert('RGB')
    elif im.mode not in ('L', '1'):
        a = np.array(im)
        if a.dtype != np.uint8:                       # 16-bit greyscale: MATLAB uint8() saturates
            a = np.clip(a, 0, 255)
        return to_gray(a)
    return to_gray(np.array(im))


def classic_overflow(I, a1, a2, km=DEFAULT_KEY, nonce=DEFAULT_NONCE, BLK=BLOCK, seed=0):
    """Classic ordering through the full pipeline: the same L-level transform,
    the same reservation and the same pseudorandom payload as the proposed
    scheme; the receiver decrypts and synthesises *before* restoring the
    vacated bits.  Returns the number of pixels outside [0, 255] and, as a
    check, the count under deferred synthesis (always 0)."""
    K = keys(km, a1, a2, nonce)
    C, h, _ = encrypt_embed(I, km, a1, a2, nonce, None, BLK, K=K, rng=np.random.default_rng(seed))
    Bc, Bd = {}, {}
    for nm in h['names']:
        W, n, shp = h['Wd'][nm], C[nm].size, h['shapes'][nm]
        p = permutation(K, nm, n)
        e = np.empty(n, np.int64); e[p] = C[nm]
        u = (e ^ keystream(K, nm, n, W)).reshape(shp)            # decrypted, payload still in place
        Bc[nm] = u - (1 << W) * (u >= (1 << (W - 1)))
        if nm in h['det']:
            u = restore(u, expand_t(h['tm'][nm], shp, BLK), W)
        Bd[nm] = u - (1 << W) * (u >= (1 << (W - 1)))
    def raw_synth(B):
        cur = B['LL']
        for lv in range(h['levels'], 0, -1):
            cur = iiwt2_raw(dict(LL=cur, HL=B['HL%d' % lv], LH=B['LH%d' % lv], HH=B['HH%d' % lv]))
        return cur
    Xc, Xd = raw_synth(Bc), raw_synth(Bd)
    return int(((Xc < 0) | (Xc > 255)).sum()), int(((Xd < 0) | (Xd > 255)).sum()), bool(np.array_equal(Xd, I))


def modular_room(I, BLK=BLOCK, levels=0):
    """Room under modular Z_256 lifting at the same depth as the scheme: every
    detail band of every level, 8-bit fields, block minimum, t capped at 6."""
    L = min(levels, max_levels(I.shape)) if levels > 0 else max_levels(I.shape)
    cur, room = I.astype(np.int64), 0
    for _ in range(L):
        Bm = miwt2(cur)
        room += sum(int(block_t(Bm[nm], 8, 6, BLK).sum()) * BLK * BLK for nm in ['HL', 'LH', 'HH'])
        cur = Bm['LL']
    return room


def ablation_full(I, a1, a2, BLK=BLOCK, seeds=(0, 1, 2)):
    """Ablation at the scheme's own depth L, own reservation and real payload."""
    cl = [classic_overflow(I, a1, a2, BLK=BLK, seed=s) for s in seeds]
    assert all(c[1] == 0 and c[2] for c in cl), 'deferred synthesis must give zero and exact recovery'
    return dict(levels=max_levels(I.shape), classic=[c[0] for c in cl], deferred=0,
                modular_room=modular_room(I, BLK), proposed_room=capacity(I, BLK)['raw'])
