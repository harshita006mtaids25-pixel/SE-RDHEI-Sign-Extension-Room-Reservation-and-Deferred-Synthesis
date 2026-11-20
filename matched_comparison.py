#!/usr/bin/env python3
"""Matched-image comparison: the proposed scheme and the reimplemented
bit-plane-compression method of Yin et al. [arXiv:1911.01699] on identical
covers, written to matched.json. Pass extra image paths to extend it, e.g. the
100-image database samples used in Section 6.1."""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import bpc

HERE = os.path.dirname(os.path.abspath(__file__))
V = json.load(open(os.path.join(HERE, 'verified_covers.json')))
D = json.load(open(os.path.join(HERE, 'data.json')))
for p in sys.argv[1:]:
    V[os.path.splitext(os.path.basename(p))[0]] = p
ORDER = ['Airplane', 'Baboon', 'Jetplane', 'Lena', 'Man', 'Tiffany', 'barbara',
         'boat', 'goldhill', 'lake', 'livingroom', 'peppers']
names = sorted(V, key=lambda k: ORDER.index(k) if k in ORDER else 99)
out = {'validation': {}, 'rows': {}}
for nm in names:
    p = V[nm] if os.path.isabs(V[nm]) else os.path.join(HERE, V[nm])
    I = np.array(Image.open(p).convert('L')).astype(np.int64)
    room, bs, lf, lens, ov = bpc.compress(I, border='reference')
    aux = 18 + math.ceil(math.log2(I.size)) * ov + 4 + 3 + 3      # count, locations, bs, Lfix, s
    bpc_net = (room - aux) / I.size
    row = dict(bpc_net=bpc_net, bpc_room=room, overflow=ov, bs=bs, Lfix=lf)
    if nm in D['cap']:
        row.update(prop_net=D['cap'][nm][3], prop_eff=D['cap'][nm][5])
    out['rows'][nm] = row
    if nm in bpc.PUBLISHED:
        pub = bpc.PUBLISHED[nm]
        out['validation'][nm] = dict(published_net=pub['net'], reimpl_net=bpc_net,
                                     published_room=pub['room'], reimpl_room=room,
                                     room_dev_pct=100 * (room - pub['room']) / pub['room'])
json.dump(out, open(os.path.join(HERE, 'matched.json'), 'w'), indent=1)
print('validation:')
for nm, v in out['validation'].items():
    print('  %-9s published %.4f  reimplemented %.4f  room %+.2f%%' % (nm, v['published_net'], v['reimpl_net'], v['room_dev_pct']))
print('%-11s %8s %8s %8s' % ('cover', 'BPC', 'R_net', 'R_eff'))
for nm, r in out['rows'].items():
    print('%-11s %8.4f %8.4f %8.4f' % (nm, r['bpc_net'], r.get('prop_net', float('nan')), r.get('prop_eff', float('nan'))))
rs = [r for r in out['rows'].values() if 'prop_net' in r]
print('mean       %8.4f %8.4f %8.4f' % tuple(np.mean([r[k] for r in rs]) for k in ['bpc_net', 'prop_net', 'prop_eff']))
