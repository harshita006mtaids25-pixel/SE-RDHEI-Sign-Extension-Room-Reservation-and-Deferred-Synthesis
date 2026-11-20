#!/usr/bin/env python3
"""Minimal end-to-end use of the SE-RDHEI reference implementation.

    python example.py [cover_image]

Without an argument a 512x512 synthetic cover is used. Colour images are
converted to 8-bit luminance, as in the paper's experiments.
"""
import os, sys, time
import numpy as np
import serdhei as S


def load(path):
    from PIL import Image
    im = Image.open(path)
    a = np.asarray(im.convert('RGB') if im.mode not in ('L', 'I;16', 'I') else im).astype(np.float64)
    if a.ndim == 3:
        a = np.floor(0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2] + 0.5)
    a = np.clip(a, 0, 255).astype(np.uint8)
    return a[:16 * (a.shape[0] // 16), :16 * (a.shape[1] // 16)]


def synthetic(n=512):
    y, x = np.mgrid[0:n, 0:n]
    a = 128 + 60 * np.sin(x / 23.0) * np.cos(y / 31.0) + 20 * np.sin((x + y) / 7.0)
    return np.clip(a + np.random.default_rng(0).normal(0, 2, a.shape), 0, 255).astype(np.uint8)


def main():
    I = load(sys.argv[1]) if len(sys.argv) > 1 else synthetic()
    MN = I.size
    K = os.urandom(32)          # master key of the content owner (and cover receiver)
    nonce = os.urandom(12)      # fresh for every image encrypted under K
    K_H = os.urandom(32)        # the data hider's own key (shared with the payload receiver)

    t = time.time()
    # 1. content owner: encrypt, reserve room; hands K_tmap (only) to the data hider
    C, H0, tau1 = S.spec_owner(I, K, nonce)
    K_tmap = S.owner_keys(K, nonce)['tmap']

    # 2. data hider: learns the room histogram, not where it lies; fills it
    room = S.hider_room(H0, K_tmap)
    D = np.random.default_rng(1).integers(0, 2, room).astype(np.uint8)
    Cm, H, tau2 = S.spec_hider(C, H0, tau1, K_tmap, K_H, D)

    # 3. payload receiver (K_tmap, K_H) and 4. cover receiver (K), separately
    D2 = S.spec_extract(Cm, H, tau1, tau2, K_tmap, K_H)
    I2 = S.spec_recover(Cm, H, tau1, K)
    dt = time.time() - t

    print('image          %d x %d, L = %d, B = %d' % (I.shape[0], I.shape[1], H['L'], H['B']))
    print('reserved room  %d bits = %.4f bpp' % (room, room / MN))
    print('payload exact  %s' % (D2 is not None and np.array_equal(D2, D)))
    print('cover exact    %s' % (I2 is not None and np.array_equal(np.asarray(I2), I.astype(np.int64))))
    bad = bytearray(K); bad[0] ^= 1
    print('wrong key      %s' % ('rejected' if S.spec_recover(Cm, H, tau1, bytes(bad)) is None else 'ACCEPTED'))
    print('time           %.2f s' % dt)


if __name__ == '__main__':
    main()
