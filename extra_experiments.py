#!/usr/bin/env python3
"""Additional measurements for the revised manuscript, written to extra.json.

  1. block-minimum efficiency against a per-coefficient oracle
  2. leakage-reduced slot descriptor: room, t-map length, exactness, and the
     spatial structure of the t-map the data hider sees
  3. ciphertext statistics under many independent keys and nonces

Runs on any 8-bit greyscale cover. verified_covers.json lists the covers
whose public copies reproduce the recorded run bit-exactly; pass other paths
on the command line to extend the measurement to full databases.
"""
import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from scipy.stats import chi2 as C2
import serdhei as S

HERE = os.path.dirname(os.path.abspath(__file__))
covers = json.load(open(os.path.join(HERE, 'verified_covers.json')))
for p in sys.argv[1:]:
    covers[os.path.splitext(os.path.basename(p))[0]] = p
ORDER = ['Airplane', 'Baboon', 'Jetplane', 'Lena', 'Man', 'Tiffany', 'barbara',
         'boat', 'goldhill', 'lake', 'livingroom', 'peppers']
NAMES = sorted(covers, key=lambda k: ORDER.index(k) if k in ORDER else 99)


def H0(x):
    p = np.bincount(x.ravel()) / x.size
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def adjc(T):
    T = T.astype(float)
    a = np.concatenate([T[:, :-1].ravel(), T[:-1, :].ravel()])
    b = np.concatenate([T[:, 1:].ravel(), T[1:, :].ravel()])
    return float(np.corrcoef(a, b)[0, 1])


out = {'covers': NAMES, 'eff': {}, 'lr': {}, 'multikey': {}}
Kown = S.keys(b'\x00' * 32, b'\x01' * 12)
K_hide, nonce = bytes(range(32)), b'\x01' * 12

for nm in NAMES:
    I = np.array(Image.open(covers[nm]).convert('L')).astype(np.int64)
    MN = I.size
    L = S.max_levels(I.shape, 4)
    bands = S.iwt2_multi(I, L)

    # ---- 1. efficiency
    st = om = lab = 0.0; omB = {2: 0.0, 4: 0.0, 8: 0.0}
    for b in S.band_names(L):
        if b == 'LL':
            continue
        v = bands[b]; W = S.band_width(v); u = v % (2 ** W)
        t = np.minimum(S.lead_ident(u, W) - 1, W - 2)
        st += t.sum(); lab += H0(t) * t.size
        om += S.block_t(u, W, W - 2, S.BLOCK).sum() * S.BLOCK ** 2
        for bb in omB:
            omB[bb] += S.block_t(u, W, W - 2, bb).sum() * bb * bb
    out['eff'][nm] = dict(sum_t=st / MN, room=om / MN, eta=om / st,
                          oracle_net=(st - lab) / MN, block=S.BLOCK,
                          eta_by_B={str(bb): v / st for bb, v in omB.items()})

    # ---- 2. leakage-reduced descriptor
    ct, L2, names = S.owner_encrypt_lr(I, Kown)
    tot = sum(int(ct[n]['Tperm'].sum()) * S.BLOCK ** 2 for n in names)
    pay = np.random.default_rng(3).integers(0, 2, tot - 1000).astype(np.uint8)
    S.hider_embed_lr(ct, names, pay, K_hide, nonce)
    got = S.receiver_extract_lr(ct, names, pay.size, K_hide, nonce)
    R = S.receiver_recover_lr(ct, names, L2, Kown)
    same_len = all(S.huff_len(ct[n]['Tperm']) == S.huff_len(np.sort(ct[n]['Tperm']))
                   for n in names if n != 'LL' and ct[n]['Tperm'].size)
    sp, pm = [], []
    for b in ['HL1', 'LH1', 'HH1']:
        v = bands[b]; W = S.band_width(v)
        T = S.block_t(v % (2 ** W), W, W - 2, S.BLOCK)
        sp.append(adjc(T)); pm.append(adjc(ct[b]['Tperm'].reshape(T.shape)))
    out['lr'][nm] = dict(room=tot / MN, payload_exact=bool(np.array_equal(got, pay)),
                         cover_exact=bool(np.array_equal(R, I)), tmap_len_same=bool(same_len),
                         rho_spatial=sp, rho_permuted=pm)

    # ---- 3. many keys
    rng = np.random.default_rng(1)
    Hc, P, Rh = [], [], []
    for k in range(20):
        r = S.run(covers[nm], km=rng.bytes(32), nonce=rng.bytes(12))
        Hc.append(r['Hc']); P.append(float(1 - C2.cdf(r['chi'], 255)))
        Rh.append(max(abs(x) for x in r['cc']))
    out['multikey'][nm] = dict(Hc=Hc, p=P, rho=Rh)

json.dump(out, open(os.path.join(HERE, 'extra.json'), 'w'), indent=1)
for nm in NAMES:
    e, l, m = out['eff'][nm], out['lr'][nm], out['multikey'][nm]
    print('%-11s eta %.3f oracle-net %.4f | LR room %.4f exact %s/%s len %s rho %s->%s | '
          'keys Hc %.4f-%.4f rej %d/20 max|rho| %.4f'
          % (nm, e['eta'], e['oracle_net'], l['room'], l['payload_exact'], l['cover_exact'],
             l['tmap_len_same'], [round(x, 3) for x in l['rho_spatial']],
             [round(x, 3) for x in l['rho_permuted']], min(m['Hc']), max(m['Hc']),
             sum(p < 0.05 for p in m['p']), max(m['rho'])))
