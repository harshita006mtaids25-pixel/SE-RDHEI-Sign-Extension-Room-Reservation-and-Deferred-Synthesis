#!/usr/bin/env python3
"""Colour covers: the scheme applied per RGB channel and after the reversible
colour transform (RCT) of lossless JPEG 2000,
    Y = floor((R + 2G + B) / 4),  Cb = B - G,  Cr = R - G,
which is inverted exactly by G = Y - floor((Cb + Cr) / 4), R = Cr + G, B = Cb + G.

Each component is processed as an integer image by the specified construction
(serdhei.py) with a payload filling its whole room, and recovered exactly.
Rates are bits per pixel per component (the grey-level unit of the paper), and
the storage-normalised rate charges container expansion beyond 8 bits per
component, i.e. beyond a 24-bit colour image.

    python colour_experiment.py OUT.json img1.tiff img2.tiff ...
"""
import json, os, sys
import numpy as np
from PIL import Image
import serdhei as S
import se_full as F


def rct(rgb):
    R, G, B = (rgb[..., k].astype(np.int64) for k in range(3))
    return {'Y': (R + 2 * G + B) >> 2, 'Cb': B - G, 'Cr': R - G}


def irct(c):
    G = c['Y'] - ((c['Cb'] + c['Cr']) >> 2)
    return np.stack([c['Cr'] + G, G, c['Cb'] + G], axis=-1)


def component(X, K, nonce, KH, seed):
    """Capacity (key independent) and an end-to-end run of the specified construction."""
    MN = X.size
    c = F.capacity(X, S.BLOCK)
    C, H0, t1 = S.spec_owner(X.astype(np.int64), K, nonce)
    kt = S.owner_keys(K, nonce)['tmap']
    room = S.hider_room(H0, kt)
    assert room == c['raw']
    D = np.random.default_rng(seed).integers(0, 2, room).astype(np.uint8)
    Cm, H, t2 = S.spec_hider(C, H0, t1, kt, KH, D)
    D2 = S.spec_extract(Cm, H, t1, t2, kt, KH)
    X2 = S.spec_recover(Cm, H, t1, K)
    return dict(raw=c['raw'] / MN, side=c['side'] / MN, cont=c['cont'] / MN,
                payload_exact=bool(np.array_equal(D2, D)),
                exact=bool(np.array_equal(np.asarray(X2), X.astype(np.int64)))), np.asarray(X2)


def main():
    out, paths = sys.argv[1], sys.argv[2:]
    K, KH = bytes(range(32)), bytes(range(32, 64))
    res = {}
    for i, p in enumerate(paths):
        rgb = np.asarray(Image.open(p).convert('RGB'))
        nm = os.path.splitext(os.path.basename(p))[0]
        r = {'size': list(rgb.shape[:2])}
        for mode, comps in (('RGB', {'R': rgb[..., 0], 'G': rgb[..., 1], 'B': rgb[..., 2]}), ('RCT', rct(rgb))):
            parts, rec = {}, {}
            for j, (cn, X) in enumerate(comps.items()):
                nonce = bytes([i, j, len(mode)]) + bytes(9)
                parts[cn], rec[cn] = component(X, K, nonce, KH, 100 * i + j)
            if mode == 'RGB':
                back = np.stack([rec['R'], rec['G'], rec['B']], axis=-1)
            else:
                back = irct(rec)
            raw = np.mean([v['raw'] for v in parts.values()])
            side = np.mean([v['side'] for v in parts.values()])
            cont = np.mean([v['cont'] for v in parts.values()])
            net = raw - side
            r[mode] = dict(components=parts, raw=raw, side=side, net=net, cont=cont,
                           eff=net - max(cont - 8, 0),
                           exact=bool(np.array_equal(back, rgb.astype(np.int64))),
                           all_payloads_exact=all(v['payload_exact'] for v in parts.values()))
        res[nm] = r
        print('%-10s RGB net %.4f eff %.4f cont %.3f | RCT net %.4f eff %.4f cont %.3f | exact %s %s'
              % (nm, r['RGB']['net'], r['RGB']['eff'], r['RGB']['cont'], r['RCT']['net'], r['RCT']['eff'],
                 r['RCT']['cont'], r['RGB']['exact'], r['RCT']['exact']), flush=True)
    json.dump(res, open(out, 'w'), indent=1)


if __name__ == '__main__':
    main()
