"""Generate the measured-data figures for the CAEE manuscript.
Every value is read from data.json, written by run_all.py (final run, B = 2)."""
import json, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

D = json.load(open('data.json'))

# ---- house style -----------------------------------------------------------
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['TeX Gyre Termes', 'Nimbus Roman', 'Times New Roman', 'DejaVu Serif'],
    'mathtext.fontset': 'stix',
    'font.size': 8.5,
    'axes.labelsize': 8.5,
    'axes.titlesize': 9,
    'xtick.labelsize': 7.8,
    'ytick.labelsize': 7.8,
    'legend.fontsize': 7.6,
    'axes.linewidth': 0.6,
    'xtick.major.width': 0.6,
    'ytick.major.width': 0.6,
    'xtick.direction': 'out',
    'ytick.direction': 'out',
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.grid': True,
    'grid.linewidth': 0.4,
    'grid.alpha': 0.35,
    'grid.color': '#999999',
    'legend.frameon': False,
    'figure.dpi': 200,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.02,
})
# Okabe-Ito, colour-blind safe
C = {'k':'#000000','orange':'#E69F00','sky':'#56B4E9','green':'#009E73',
     'yellow':'#F0E442','blue':'#0072B2','verm':'#D55E00','purple':'#CC79A7'}
GREY = '#BBBBBB'

ORDER = ['Airplane','Baboon','Jetplane','Lena','Man','Tiffany',
          'barbara','boat','goldhill','lake','livingroom','peppers']
COVERS = [c for c in ORDER if c in D['cap']] + sorted(c for c in D['cap'] if c not in ORDER)
DS = [d for d in ['USC-SIPI','BOSSbase','BOWS-2','UCID'] if d in D['ds']]
REF = next((c for c in COVERS if D.get('size', {}).get(c) == [512, 512]), COVERS[0])
import os as _os
_NPZ = set(np.load('secdata.npz').files) if _os.path.exists('secdata.npz') else set()
def _three(pref):
    have = [c for c in pref if c + '_cover' in _NPZ]
    rest = [c for c in COVERS if c + '_cover' in _NPZ and c not in have]
    return (have + rest)[:3]

# ===========================================================================
# Fig: comparison with published methods
# ===========================================================================
def fig_sota():
    meth = [   # published database means, in Table 6 order (names, not citation numbers)
        ('Zhang 2012',       [None,   None,   0.033 ]),
        ('Puteaux 2018',     [None,   None,   0.8930]),
        ('Yi 2019',          [1.9656, 1.8808, 1.5860]),
        ('Wu 2020',          [2.5613, 2.5194, 2.2751]),
        ('Yin 2020',         [None,   None,   2.6880]),
        ('Yin BPC 2022',     [3.6248, 3.4948, 2.8990]),
        ('Ankur 2023',       [3.8977, 3.7863, None  ]),
        ('Xiao 2024',        [4.041,  3.929,  3.181 ]),
        ('Dong 2025',        [2.9652, 2.7615, None  ]),
        ('Ren 2025',         [3.177,  3.098,  2.722 ]),
        ('Ankur 2025',       [3.9036, 3.8431, None  ]),
        ('Pham Van 2025',    [3.0163, 3.1643, 2.4741]),
        ('Ren 2026',         [2.4938, 2.3508, None  ]),
    ]
    prop_net = [D['ds'][d]['net'] if d in D['ds'] else np.nan for d in ['BOSSbase','BOWS-2','UCID']]
    prop_eff = [D['ds'][d]['eff'] if d in D['ds'] else np.nan for d in ['BOSSbase','BOWS-2','UCID']]
    dbs = ['BOSSbase','BOWS-2','UCID']
    fig, axs = plt.subplots(1, 3, figsize=(6.6, 2.75), sharex=True)
    for k, (ax, db) in enumerate(zip(axs, dbs)):
        rows = [(nm, v[k]) for nm, v in meth if v[k] is not None]
        rows += [(r'Proposed $R_{\mathrm{net}}$', prop_net[k]), (r'Proposed $R_{\mathrm{eff}}$', prop_eff[k])]
        rows.sort(key=lambda r: r[1])
        y = np.arange(len(rows))
        col = [C['blue'] if 'net' in nm else C['orange'] if 'eff' in nm else '#BBBBBB' for nm, _ in rows]
        ax.barh(y, [r[1] for r in rows], 0.72, color=col, edgecolor='#444444', linewidth=0.4)
        ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows], fontsize=6.4)
        ax.set_title(db, fontsize=8)
        ax.set_xlim(0, 4.4); ax.xaxis.set_major_locator(MultipleLocator(1.0))
        ax.tick_params(axis='x', labelsize=6.8)
        ax.set_xlabel('rate (bpp)', fontsize=7)
        ax.grid(axis='y', visible=False)
    fig.tight_layout(w_pad=0.6)
    fig.savefig('fig_sota.pdf'); plt.close(fig)
    print('  fig_sota.pdf')

# ===========================================================================
# Fig: capacity breakdown, per cover and per dataset
# ===========================================================================
def fig_capacity():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.8, 2.25),
                                 gridspec_kw={'width_ratios':[2.1,1],'wspace':0.42})
    raw = [D['cap'][c][1] for c in COVERS]
    tm  = [D['cap'][c][2] for c in COVERS]
    net = [D['cap'][c][3] for c in COVERS]
    eff = [D['cap'][c][5] for c in COVERS]
    x = np.arange(len(COVERS)); w = 0.27
    a1.bar(x-w, raw, w, label=r'$R_{\mathrm{raw}}$', color=GREY,
           edgecolor='#555555', linewidth=0.4)
    a1.bar(x,   net, w, label=r'$R_{\mathrm{net}}$', color=C['blue'],
           edgecolor='black', linewidth=0.4)
    a1.bar(x+w, eff, w, label=r'$R_{\mathrm{eff}}$', color=C['orange'],
           edgecolor='black', linewidth=0.4)
    a1.set_xticks(x)
    a1.set_xticklabels(COVERS, rotation=38, ha='right')
    a1.set_ylabel('rate (bpp)')
    a1.set_ylim(0, 5.0)
    a1.legend(ncol=3, loc='upper right', fontsize=7.4,
              columnspacing=1.0, handlelength=1.1)
    a1.set_title('(a) per cover, USC-SIPI', fontsize=8.5, pad=4)

    mn  = [D['ds'][d]['net'] for d in DS]
    msd = [D['ds'][d]['nsd'] for d in DS]
    me  = [D['ds'][d]['eff'] for d in DS]
    esd = [D['ds'][d]['esd'] for d in DS]
    y = np.arange(len(DS))
    a2.errorbar(mn, y+0.12, xerr=msd, fmt='o', ms=4, color=C['blue'],
                ecolor=C['blue'], elinewidth=1.0, capsize=2.5,
                label=None)
    a2.errorbar(me, y-0.12, xerr=esd, fmt='s', ms=4, color=C['orange'],
                ecolor=C['orange'], elinewidth=1.0, capsize=2.5,
                label=r'$R_{\mathrm{eff}}$')
    a2.set_yticks(y); a2.set_yticklabels(DS)
    a2.invert_yaxis()
    a2.set_xlabel('rate (bpp)')
    a2.set_xlim(1.4, 4.8)
    a2.set_title(r'(b) dataset mean $\pm$ s.d.', fontsize=8.5, pad=4)
    fig.savefig('fig_capacity.pdf'); plt.close(fig)
    print('  fig_capacity.pdf')

# ===========================================================================
# Fig: parameter sweeps
# ===========================================================================
def fig_sweeps():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.6, 2.10))
    fig.subplots_adjust(wspace=0.28, bottom=0.27)
    B = [2,4,8,16,32][-len(D['blk'][COVERS[0]]):]    # 2-32 in the final run, 4-32 in earlier ones
    sel = [c for c in ['Jetplane','Tiffany','Man','peppers','Lena','Baboon'] if c in COVERS] or COVERS[:6]
    mk = ['o','s','^','D','v','P']
    cols = [C['blue'],C['orange'],C['sky'],C['green'],C['purple'],C['verm']]
    for i,c in enumerate(sel):
        a1.plot(B, D['blk'][c], marker=mk[i], ms=3.6, lw=1.0,
                color=cols[i], label=c)
    allb = np.array([D['blk'][c] for c in COVERS])
    a1.plot(B, allb.mean(0), 'k--', lw=1.2, label='mean (12)')
    a1.set_xscale('log', base=2); a1.set_xticks(B)
    a1.set_xticklabels([str(b) for b in B])
    a1.set_xlabel(r'block size $B$'); a1.set_ylabel(r'$R_{\mathrm{net}}$ (bpp)')

    a1.set_title(r'(a) block size', fontsize=8.5)

    L = [1,2,3,4]
    for i,c in enumerate(sel):
        a2.plot(L, D['lvl'][c], marker=mk[i], ms=3.6, lw=1.0,
                color=cols[i], label=c)
    alll = np.array([D['lvl'][c] for c in COVERS])
    a2.plot(L, alll.mean(0), 'k--', lw=1.2, label='mean (12)')
    a2.set_xticks(L)
    a2.set_xlabel(r'decomposition level $L$')
    a2.set_ylabel(r'$R_{\mathrm{eff}}$ (bpp)')
    a2.set_title(r'(b) decomposition depth', fontsize=8.5)
    h,l = a1.get_legend_handles_labels()
    fig.legend(h, l, ncol=7, fontsize=7.2, loc='lower center',
               bbox_to_anchor=(0.5,-0.12), handlelength=1.4,
               columnspacing=1.1, frameon=False)
    fig.savefig('fig_sweeps.pdf'); plt.close(fig)
    print('  fig_sweeps.pdf')

# ===========================================================================
# Fig: ciphertext statistics
# ===========================================================================
def fig_stats():
    fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(6.8, 2.15))
    fig.subplots_adjust(wspace=0.46)
    Hp = [D['stats'][c]['Hp'] for c in COVERS]
    Hc = [D['stats'][c]['Hc'] for c in COVERS]
    y = np.arange(len(COVERS))
    a1.barh(y, Hp, 0.62, color=GREY, edgecolor='#555555', linewidth=0.4,
            label='cover')
    a1.plot(Hc, y, 'o', ms=3.4, color=C['verm'], label='ciphertext')
    a1.axvline(8, color='k', ls=':', lw=0.9)
    a1.set_yticks(y); a1.set_yticklabels(COVERS, fontsize=6.8)
    a1.invert_yaxis(); a1.set_xlim(3.5, 8.45)
    a1.set_xlabel('entropy (bits/byte)')
    a1.set_title('(a) entropy: bars cover, dots cipher', fontsize=8.0)

    pl = np.array([D['stats'][c]['plain'] for c in COVERS])
    ci = np.array([D['stats'][c]['ciph']  for c in COVERS])
    lbl = ['H','V','D']
    for j in range(3):
        a2.plot(np.abs(pl[:,j]), np.full(len(COVERS), 1.0+0.12*(j-1)), 'o', ms=3.2,
                color=GREY, markeredgecolor='#555555', markeredgewidth=0.3)
        a2.plot(np.abs(ci[:,j]), np.full(len(COVERS), 0.0+0.12*(j-1)), 'o', ms=3.2,
                color=[C['blue'],C['green'],C['verm']][j], label=lbl[j])
    a2.set_yticks([0,1]); a2.set_yticklabels(['cipher','cover'])
    a2.set_xlim(-0.05, 1.05); a2.set_ylim(-0.5, 1.6)
    a2.set_xlabel(r'$|\rho|$, adjacent samples')
    a2.legend(ncol=3, fontsize=6.9, loc='upper center',
              bbox_to_anchor=(0.5,1.03), handlelength=0.8, columnspacing=0.8)
    a2.set_title('(b) correlation', fontsize=8.5)

    pv = sorted(D['stats'][c]['p'] for c in COVERS)
    a3.plot(pv, np.arange(1,len(COVERS)+1)/float(len(COVERS)), 'o-', ms=3.4, lw=1.0, color=C['blue'],
            label='observed')
    a3.plot([0,1],[0,1],'k--',lw=0.9, label='Uniform(0,1)')
    a3.axvline(0.05, color=C['verm'], ls=':', lw=1.0)
    a3.text(0.075, 0.90, r'$\alpha=0.05$', fontsize=6.8, color=C['verm'])
    a3.set_xlim(0,1); a3.set_ylim(0,1.02)
    a3.set_xlabel(r'$\chi^2$ $p$-value'); a3.set_ylabel('empirical CDF')
    a3.legend(loc='lower right', fontsize=6.9, handlelength=1.3)
    a3.set_title('(c) uniformity', fontsize=8.5)
    fig.savefig('fig_stats.pdf'); plt.close(fig)
    print('  fig_stats.pdf')

# ===========================================================================
# Fig: ablation
# ===========================================================================
def fig_ablation():
    # legends sit above the axes so they cannot collide with the bars, and
    # the ratio statement lives in the body text, not on the figure
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.6, 2.45))
    ovf = [D['abl'][c][0] for c in COVERS]
    x = np.arange(len(COVERS)); w = 0.62
    a1.bar(x, ovf, w, color=C['verm'], edgecolor='black', linewidth=0.4,
           label='classic ordering')
    a1.plot(x, [1.35]*len(COVERS), 'o', ms=4.2, color=C['blue'],
            markeredgecolor='black', markeredgewidth=0.4,
            label='deferred synthesis (exactly 0)', clip_on=False, zorder=5)
    a1.set_yscale('log'); a1.set_ylim(1.0, 3e6)
    a1.set_xticks(x); a1.set_xticklabels(COVERS, rotation=38, ha='right')
    a1.set_ylabel('pixels outside $[0,255]$')
    a1.set_xlabel('(a) inverse-transform overflow', fontsize=8.5, labelpad=2)
    a1.legend(fontsize=7.0, handlelength=1.1, ncol=1,
              loc='lower left', bbox_to_anchor=(0.0, 1.02), borderaxespad=0)

    rm_mod = [D['abl'][c][2] for c in COVERS]
    rm_our = [D['abl'][c][3] for c in COVERS]
    a2.bar(x-0.175, rm_mod, 0.34, color=C['verm'],
           edgecolor='black', linewidth=0.4, label=r'modular $\mathbb{Z}_{256}$')
    a2.bar(x+0.175, rm_our, 0.34, color=C['blue'], edgecolor='black',
           linewidth=0.4, label='proposed')
    a2.set_yscale('log'); a2.set_ylim(1e2, 3e7)
    a2.set_xticks(x); a2.set_xticklabels(COVERS, rotation=38, ha='right')
    a2.set_ylabel('exploitable room (bits)')
    a2.set_xlabel('(b) transform choice', fontsize=8.5, labelpad=2)
    a2.legend(fontsize=7.0, handlelength=1.1, ncol=2,
              loc='lower left', bbox_to_anchor=(0.0, 1.02), borderaxespad=0)
    fig.tight_layout(pad=0.3, w_pad=1.2)
    fig.savefig('fig_ablation.pdf')
    fig.savefig('p_fig_ablation.png', dpi=150)
    plt.close(fig)
    print('  fig_ablation.pdf')

# ===========================================================================
# Fig: key sensitivity
# ===========================================================================
def fig_sensitivity():
    """Each cover against its own Wu-Noonan-Agaian region (T = compared bytes)."""
    fig, ax = plt.subplots(figsize=(3.3, 2.7))
    mu = 257 / 768 * 100
    x = [D['npcr'][c]['n'] - D['npcr'][c]['nstar'] for c in COVERS]
    y = [(D['npcr'][c]['u'] - mu) / ((D['npcr'][c]['uhi'] - D['npcr'][c]['ulo']) / 2) for c in COVERS]
    ax.axhspan(-1, 1, xmin=0, xmax=1, color=C['sky'], alpha=0.16, lw=0)
    ax.axvline(0, color=C['verm'], ls='--', lw=0.9)
    xe = [D['npcr'][c].get('nsd1', D['npcr'][c]['nsd']) for c in COVERS]
    ye = [D['npcr'][c].get('usd1', D['npcr'][c]['usd']) / ((D['npcr'][c]['uhi'] - D['npcr'][c]['ulo']) / 2) for c in COVERS]
    ax.errorbar(x, y, xerr=xe, yerr=ye, fmt='none', ecolor='#666666', elinewidth=0.6, capsize=1.5, zorder=1)
    big = [D.get('size', {}).get(c) != [512, 512] for c in COVERS]
    ax.plot([a for a, b in zip(x, big) if not b], [a for a, b in zip(y, big) if not b], 'o', ms=4.2,
            color=C['blue'], markeredgecolor='black', markeredgewidth=0.4, label=r'$512\times512$')
    ax.plot([a for a, b in zip(x, big) if b], [a for a, b in zip(y, big) if b], 's', ms=4.2,
            color=C['green'], markeredgecolor='black', markeredgewidth=0.4, label=r'\emph{Man}, $1024^2$' if plt.rcParams.get('text.usetex') else r'Man, $1024\times1024$')
    ax.set_xlabel(r'NPCR $-\ N^{*}$ (percentage points)'); ax.set_ylabel('UACI within its interval')
    ax.set_xlim(-0.008, 0.040); ax.set_ylim(-1.35, 1.35)
    ax.text(0.0008, -1.25, r'$N^*$', fontsize=7.2, color=C['verm'])
    ax.text(0.0145, 1.07, 'UACI acceptance region', fontsize=6.8, color='#30627f')
    ax.legend(loc='lower right', fontsize=7.0, handlelength=1.0)
    ax.xaxis.set_major_locator(MultipleLocator(0.01))
    fig.savefig('fig_sensitivity.pdf'); plt.close(fig)
    print('  fig_sensitivity.pdf')

import traceback
for f in (fig_sota, fig_capacity, fig_sweeps, fig_stats, fig_ablation,
          fig_sensitivity):
    try:
        f()
    except Exception:
        print('  ! %s failed:' % f.__name__); traceback.print_exc()
print('done')


# ===========================================================================
# Fig: histograms, cover against ciphertext
# ===========================================================================
def fig_hist():
    Z = np.load('secdata.npz')
    fig, ax = plt.subplots(2, 2, figsize=(6.6, 2.75), sharex=True)
    rows = [(c, c) for c in _three(['Airplane', 'barbara'])[:2]]
    for r, (key, lab) in enumerate(rows):
        cov = Z[key + '_cover'].ravel()
        cip = Z[key + '_ciph'].ravel()
        for c, (dat, ttl, col) in enumerate(
                [(cov, 'cover', GREY), (cip, 'ciphertext', C['blue'])]):
            a = ax[r][c]
            a.hist(dat, bins=256, range=(0, 256), color=col,
                   edgecolor='none', linewidth=0)
            a.set_xlim(0, 255)
            a.grid(axis='y')
            a.set_axisbelow(True)
            if r == 0:
                a.set_title('%s' % ttl, fontsize=8.5, pad=4)
            if c == 0:
                a.set_ylabel('%s\ncount' % lab, fontsize=8.0)
            if r == 1:
                a.set_xlabel('byte value', fontsize=8.5)
    # a flat reference line on each ciphertext panel
    for r, (key, _) in enumerate(rows):
        n = Z[key + '_ciph'].size
        ax[r][1].axhline(n / 256.0, color=C['verm'], lw=0.9, ls='--',
                         zorder=5)
    fig.tight_layout(pad=0.3, h_pad=0.6, w_pad=1.0)
    fig.savefig('fig_hist.pdf')
    fig.savefig('p_fig_hist.png', dpi=150)
    plt.close(fig)
    return 'fig_hist.pdf'


# ===========================================================================
# Fig: adjacent-sample correlation, stacked by image, cover against ciphertext
# ===========================================================================
CORR_IMGS = _three(['Airplane', 'barbara', 'livingroom'])   # image index 1..3
CORR_COLS = ['#5B2A86', '#D6589F', '#6F9BC6']

def fig_corr():
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
    Z = np.load('secdata.npz')
    rng = np.random.default_rng(7)
    dirs = [('horizontal', (0, 1)), ('vertical', (1, 0)), ('diagonal', (1, 1))]
    fig = plt.figure(figsize=(7.0, 4.9))
    for r, kind in enumerate(['cover', 'ciph']):
        for c, (dname, (dy, dx)) in enumerate(dirs):
            ax = fig.add_subplot(2, 3, r * 3 + c + 1, projection='3d')
            for k, nm in enumerate(CORR_IMGS):
                M = Z['%s_%s' % (nm, kind)].astype(float)
                a = M[:M.shape[0] - dy, :M.shape[1] - dx].ravel()
                b = M[dy:, dx:].ravel()
                idx = rng.choice(a.size, 2500, replace=False)
                ax.scatter(a[idx], b[idx], np.full(idx.size, k + 1.0), s=0.9,
                           c=CORR_COLS[k], alpha=0.55, linewidths=0,
                           depthshade=False, rasterized=True)
            ax.set_xlim(0, 255); ax.set_ylim(0, 255); ax.set_zlim(0.6, 3.4)
            ax.set_xticks([0, 128, 255]); ax.set_yticks([0, 128, 255])
            ax.set_zticks([1, 2, 3])
            ax.tick_params(labelsize=6.2, pad=-2)
            ax.set_xlabel('sample', fontsize=7, labelpad=-7)
            ax.set_ylabel('adjacent sample', fontsize=7, labelpad=-7)
            ax.set_zlabel('image index', fontsize=7, labelpad=-10)
            ax.view_init(elev=22, azim=-72)
            ax.set_box_aspect((1, 1, 0.82))
            for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
                axis.pane.set_facecolor('white'); axis.pane.set_edgecolor('#BBBBBB')
                axis._axinfo['grid'].update(linewidth=0.3, color='#DDDDDD')
            ax.set_title('%s, %s' % ('cover' if kind == 'cover' else 'ciphertext', dname),
                         fontsize=8.2, pad=-4)
    fig.subplots_adjust(left=0.0, right=0.94, bottom=0.04, top=0.97,
                        wspace=0.13, hspace=0.14)
    fig.savefig('fig_corr.pdf', dpi=300)
    fig.savefig('p_fig_corr.png', dpi=150)
    plt.close(fig)
    return 'fig_corr.pdf'


# ===========================================================================
# Fig: visual results -- cover, encrypted, marked encrypted, recovered
# ===========================================================================
def fig_visual():
    Z = np.load('montage.npz')
    rows = _three(['Airplane', 'barbara', 'livingroom'])
    cols = [('cover', 'cover'), ('enc', 'encrypted'),
            ('mark', 'marked encrypted'), ('rec', 'recovered')]
    fig, ax = plt.subplots(3, 4, figsize=(6.4, 4.95))
    for r, nm in enumerate(rows):
        for c, (key, ttl) in enumerate(cols):
            a = ax[r][c]
            a.imshow(Z['%s_%s' % (nm, key)], cmap='gray', vmin=0, vmax=255,
                     interpolation='nearest')
            a.set_xticks([]); a.set_yticks([]); a.grid(False)
            for sp in a.spines.values():
                sp.set_visible(True); sp.set_linewidth(0.5); sp.set_color('#444444')
            if r == 0:
                a.set_title(ttl, fontsize=8.5, pad=4)
            if c == 0:
                a.set_ylabel(nm, fontsize=8.5)
    fig.subplots_adjust(left=0.04, right=0.995, top=0.95, bottom=0.01,
                        wspace=0.04, hspace=0.04)
    fig.savefig('fig_visual.pdf', dpi=220)
    fig.savefig('p_fig_visual.png', dpi=110)
    plt.close(fig)
    return 'fig_visual.pdf'


if __name__ == '__main__' or True:
    if _NPZ:
        for f in (fig_hist, fig_corr, fig_visual):
            try:
                print(' ', f())
            except Exception:
                print('  ! %s failed:' % f.__name__); traceback.print_exc()
