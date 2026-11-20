#!/usr/bin/env python3
"""Checks of the SPECIFIED construction (Section 4.6, Algorithm 3), written to spec.json.

 1. role-separated round trip on every verified cover: room, payload, cover
 2. integrity: what each kind of tampering does to tau1, tau2 and recovery,
    including a malicious data hider that writes arbitrary reserved bits
 3. ciphertext statistics under AES-256-CTR, 20 keys x every verified cover
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from scipy.stats import chi2 as C2
import serdhei as S

HERE = os.path.dirname(os.path.abspath(__file__))
V = json.load(open(os.path.join(HERE, 'verified_covers.json')))
D = json.load(open(os.path.join(HERE, 'data.json')))
ORDER = ['Airplane', 'Baboon', 'Jetplane', 'Lena', 'Man', 'Tiffany', 'barbara',
         'boat', 'goldhill', 'lake', 'livingroom', 'peppers']
names = sorted(V, key=lambda k: ORDER.index(k) if k in ORDER else 99)
ok = S.selftest(); assert all(ok), ok
out = dict(selftest=dict(hkdf_rfc5869=ok[0], aes_sp800_38a=ok[1]), covers=names,
           roundtrip={}, tamper={}, stats={})
rng = np.random.default_rng(2026)

def img(nm): return np.array(Image.open(os.path.join(HERE, V[nm]) if not os.path.isabs(V[nm]) else V[nm]).convert('L')).astype(np.int64)

for nm in names:
    I = img(nm); K = rng.bytes(32); KH = rng.bytes(32); N = rng.bytes(12)
    t0 = time.time()
    C, H0, t1 = S.spec_owner(I, K, N)
    kt = S.owner_keys(K, N)['tmap']
    T = S._decrypt_tmap(H0, kt)
    room = sum(int(T[b].sum()) for b in names and H0['names']) * H0['B'] ** 2
    Dp = rng.integers(0, 2, room).astype(np.uint8)                      # fill the room
    Cm, H1, t2 = S.spec_hider(C, H0, t1, kt, KH, Dp)
    got = S.spec_extract(Cm, H1, t1, t2, kt, KH)
    R = S.spec_recover(Cm, H1, t1, K)
    out['roundtrip'][nm] = dict(room_bpp=room / I.size, recorded_raw=D['cap'][nm][1],
                                payload_exact=bool(got is not None and np.array_equal(got, Dp)),
                                cover_exact=bool(R is not None and np.array_equal(R, I)),
                                seconds=round(time.time() - t0, 1))
    # ---- tampering, one change at a time, on a fresh copy each time
    H = dict(H0); H['Tplain'] = T
    def tamper(kind):
        Cx = {b: v.copy() for b, v in Cm.items()}; Hx = dict(H1); Hx['W'] = dict(H1['W']); Hx['Tcode'] = H1['Tcode']
        t2x = t2
        if kind == 'hider_rewrites_reserved':        # malicious hider: arbitrary payload, valid tau2
            bits = rng.integers(0, 2, room).astype(np.uint8)
            Cx = S._write_reserved(Cm, H, bits)
            t2x = S.hmac256(S.hider_keys(KH)['tag'], S._ser_header(Hx) + S._ser_all(Cx, Hx) + t1)
        elif kind == 'outsider_flips_reserved_bit':
            b = 'HL1'; tf = S._tfield(H, b, Cx[b].size); i = int(np.nonzero(tf)[0][0])
            Cx[b][i] ^= 1 << (H['W'][b] - 1)
        elif kind == 'outsider_flips_nonreserved_bit':
            b = 'HL1'; Cx[b][0] ^= 1
        elif kind == 'header_tmap_byte':
            e = bytearray(Hx['Tcode']); e[len(e) // 2] ^= 1; Hx['Tcode'] = bytes(e)
        elif kind == 'header_payload_length':
            Hx['nD'] = Hx['nD'] - 8
        p = S.spec_extract(Cx, Hx, t1, t2x, kt, KH)
        r = S.spec_recover(Cx, Hx, t1, K)
        return dict(tau2_accepts=p is not None, tau1_accepts=r is not None,
                    cover_exact_if_accepted=(None if r is None else bool(np.array_equal(r, I))))
    out['tamper'][nm] = {k: tamper(k) for k in ['hider_rewrites_reserved', 'outsider_flips_reserved_bit',
                         'outsider_flips_nonreserved_bit', 'header_tmap_byte', 'header_payload_length']}
    # ---- statistics under AES-256-CTR, 20 independent keys and nonces
    Hc, P, Rh = [], [], []
    for _ in range(20):
        Cs, Hs, _t = S.spec_owner(I, rng.bytes(32), rng.bytes(12))
        E = S.packbits_cipher(Cs, Hs['W'], Hs['names'])
        s = min(I.shape[0], int(np.sqrt(E.size)))
        Hc.append(S.entropy8(E)); P.append(float(1 - C2.cdf(S.chi2stat(E), 255)))
        Rh.append(max(abs(x) for x in S.corr3(E[:s * s].reshape(s, s))))
    out['stats'][nm] = dict(Hc=Hc, p=P, rho=Rh)
    r = out['roundtrip'][nm]
    print('%-11s room %.4f/%.4f payload %s cover %s %5.1fs | tamper %s | Hc %.4f-%.4f rej %d/20 max|rho| %.4f' % (
        nm, r['room_bpp'], r['recorded_raw'], r['payload_exact'], r['cover_exact'], r['seconds'],
        {k: (v['tau2_accepts'], v['tau1_accepts'], v['cover_exact_if_accepted']) for k, v in out['tamper'][nm].items()}
        if nm == names[0] else '...', min(Hc), max(Hc), sum(p < 0.05 for p in P), max(Rh)))
json.dump(out, open(os.path.join(HERE, 'spec.json'), 'w'), indent=1)
