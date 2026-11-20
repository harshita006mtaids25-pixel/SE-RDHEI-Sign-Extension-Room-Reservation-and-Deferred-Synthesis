#!/usr/bin/env python3
"""Validate abcs.py against Table 5 of Xiao et al. (2024): ER (bpp) for square block sizes."""
import json, numpy as np, abcs
from PIL import Image
PUB = {  # Table 5 of the paper, square block sizes only
 'Lena':     {6: 3.2579, 7: 3.3166, 8: 3.3564, 9: 3.2569},
 'Baboon':   {6: 1.5386, 7: 1.5819, 8: 1.6552, 9: 1.5570},
 'Airplane': {6: 3.5717, 7: 3.6338, 8: 3.6758, 9: 3.5581},
 'Man':      {6: 2.8720, 7: 2.9231, 8: 2.9585, 9: 2.9292},
}
# Their 'Airplane' is USC-SIPI 4.2.05 (F-16, entropy 6.7025 in their Table 3), our 'Jetplane'.
FILES = {'Lena': '/home/claude/imgs/lena_gray_512.tif',
         'Baboon': '/home/claude/sipi/gray/4.2.03_matlab_rgb2gray.png',
         'Airplane': '/home/claude/sipi/gray/4.2.05_matlab_rgb2gray.png',
         'Man': '/home/claude/sipi/gray/5.3.01_gray.png'}
out = {}
for nm, p in FILES.items():
    I = np.array(Image.open(p).convert('L'))
    out[nm] = {}
    for t, pub in PUB[nm].items():
        r = abcs.rate(I, t)
        out[nm][t] = dict(ours=round(r['er'], 4), published=pub, rel=round(r['er'] / pub - 1, 4), T=r['T'])
        print('%-9s t=%d ours %.4f published %.4f  %+.2f%%  T=%d' % (nm, t, r['er'], pub, 100 * (r['er'] / pub - 1), r['T']), flush=True)
json.dump(out, open('validation.json', 'w'), indent=1)
