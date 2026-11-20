#!/usr/bin/env python3
"""SE-RDHEI: reproduce every measured result of the CAEE manuscript.

    python run_all.py --data DATA_DIR --out OUT_DIR [--n 100] [--trials 10]
                      [--a1 A1.wav --a2 A2.wav] [--stage all]

DATA_DIR holds one folder per dataset (USC-SIPI, BOSSbase, BOWS-2, UCID; any
other folder is processed as an extra dataset). Images may sit in sub-folders.
Per-image results are cached in OUT_DIR/cache, so an interrupted run resumes
where it stopped. Outputs:

  data.json      capacity, statistics, NPCR/UACI, sweeps, ablation, runtime,
                 per-dataset means              (Tables 3, 4, 6, 7; Figs 4-11)
  extra.json     block-minimum efficiency, leakage-reduced descriptor,
                 20-key statistics                         (Table 8, Sec. 7)
  spec.json      specified construction: round trip, tampering, AES statistics
  matched.json   matched comparison with the reimplemented BPC method (Table 5)
  matched_db.json  the same comparison on the database samples
  figures/       every data figure of the manuscript (PDF + PNG)
  REPORT.md      all tables in readable form, plus validation against the
                 recorded MATLAB run
  results_SE-RDHEI.zip   everything above, to send back
"""
import argparse, json, os, re, shutil, subprocess, sys, time, zipfile, platform
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import se_full as S

IMG_EXT = ('.png', '.tif', '.tiff', '.bmp', '.pgm', '.jpg', '.jpeg', '.ppm', '.gif')
ORDER = ['Airplane', 'Baboon', 'Jetplane', 'Lena', 'Man', 'Tiffany', 'barbara',
         'boat', 'goldhill', 'lake', 'livingroom', 'peppers']
ALIASES = {
    'Airplane': ['airplane', '7.1.02'],
    'Baboon': ['baboon', 'mandrill', 'mandril', '4.2.03'],
    'Jetplane': ['jetplane', 'jet', 'f16', 'f-16', '4.2.05'],
    'Lena': ['lena', 'lenna', '4.2.04'],
    'Man': ['man', '5.3.01'],
    'Tiffany': ['tiffany', '4.2.02'],
    'barbara': ['barbara'],
    'boat': ['boat', 'boats', 'boat.512'],
    'goldhill': ['goldhill', 'gold_hill', 'gold-hill'],
    'lake': ['lake', '4.2.06'],
    'livingroom': ['livingroom', 'living_room', 'living-room'],
    'peppers': ['peppers', 'pepper', '4.2.07'],
}
# BOWS-2 is tested before BOSSbase so that a folder named BOSS-2 (how the MATLAB run
# stored its BOWS-2 copy) is not taken for BOSSbase
DS_ALIASES = {'USC-SIPI': ['usc-sipi', 'usc_sipi', 'sipi', 'usc', 'standard'],
              'BOWS-2': ['bows-2', 'bows2', 'bows_2', 'bows', 'boss-2', 'boss2', 'boss_2', 'bose-2', 'bose2'],
              'BOSSbase': ['bossbase', 'boss'],
              'UCID': ['ucid']}
MONTAGE = ['Airplane', 'barbara', 'livingroom']


def canon_ds(folder):
    f = folder.lower()
    for k, al in DS_ALIASES.items():
        if any(f.startswith(a) for a in al):
            return k
    return folder


def canon_cover(stem, rename):
    if stem in rename:
        return rename[stem]
    s = stem.lower()
    tok = [t for t in re.split(r'[_\- ]+', s) if t]
    cands = [s] + ([tok[0], tok[0].split('.')[0]] if tok else [])
    for c in cands:
        for k, al in ALIASES.items():
            if c in al:
                return k
    return stem


def discover(data, n_per_db, seed, rename, dsmap=None):
    """Group images into datasets.  dsmap maps a folder name found anywhere in a
    file's path (case-insensitive) to a dataset name, e.g. {"BOSS-2": "BOWS-2"}."""
    dsmap = {k.lower(): v for k, v in (dsmap or {}).items()}
    sets, origin = {}, {}
    for d in sorted(os.listdir(data)):
        p = os.path.join(data, d)
        if not os.path.isdir(p) or d.startswith(('.', '__')):
            continue
        for root, _, fs in os.walk(p, followlinks=True):
            for f in fs:
                if not f.lower().endswith(IMG_EXT) or f.startswith('._'):
                    continue
                fp = os.path.join(root, f)
                parts = os.path.relpath(fp, data).replace(os.sep, '/').split('/')[:-1]
                ds = next((dsmap[c.lower()] for c in reversed(parts) if c.lower() in dsmap), None)
                if ds is not None and ds.strip().lower() in ('', 'skip', 'exclude'):
                    continue
                ds = ds or canon_ds(d)
                sets.setdefault(ds, []).append(fp)
                origin.setdefault(ds, {}).setdefault('/'.join(parts), 0)
                origin[ds]['/'.join(parts)] += 1
    # a folder of standard covers under any name (e.g. "Image") is the USC-SIPI set
    for ds in list(sets):
        if ds in DS_ALIASES:
            continue
        hits = [f for f in sets[ds] if canon_cover(os.path.splitext(os.path.basename(f))[0], rename) in ORDER]
        if len(hits) >= 3:
            print('  folder "%s" holds standard covers: treated as USC-SIPI' % ds)
            sets.setdefault('USC-SIPI', []).extend(sets.pop(ds))
            o = origin.pop(ds)
            for k, v in o.items():
                origin.setdefault('USC-SIPI', {})[k] = v
    for ds, o in origin.items():
        if len(o) > 1 and ds != 'USC-SIPI':
            print('  ! %s mixes images from %d folders: %s' % (ds, len(o), ', '.join('%s (%d)' % kv for kv in sorted(o.items()))))
            print('    if they are different datasets, name each one in DATASET_MAP, e.g. {"<folder name>": "<dataset name>"}')
    out = {}
    for ds, files in sets.items():
        files = sorted(set(files))
        if ds == 'USC-SIPI':
            m = {}
            for f in files:
                nm = canon_cover(os.path.splitext(os.path.basename(f))[0], rename)
                if nm in m:
                    print('  ! duplicate cover %s: keeping %s, ignoring %s' % (nm, m[nm], f))
                    continue
                m[nm] = f
            out[ds] = dict(sorted(m.items(), key=lambda kv: (ORDER.index(kv[0]) if kv[0] in ORDER else 99, kv[0])))
        else:
            if n_per_db and len(files) > n_per_db:
                idx = np.random.default_rng(seed).choice(len(files), n_per_db, replace=False)
                files = [files[i] for i in sorted(idx)]
            out[ds] = {os.path.relpath(f, data).replace(os.sep, '/'): f for f in files}
    return out


def jdump(o, p):
    def conv(x):
        if isinstance(x, (np.integer,)): return int(x)
        if isinstance(x, (np.floating,)): return float(x)
        if isinstance(x, np.bool_): return bool(x)
        if isinstance(x, np.ndarray): return x.tolist()
        raise TypeError(type(x))
    with open(p, 'w') as f:
        json.dump(o, f, indent=1, default=conv)


def safe(s):
    return re.sub(r'[^A-Za-z0-9._-]', '_', s)


# ------------------------------------------------------------------ stages
def stage_main(cfg, sets, a1, a2):
    cache = os.path.join(cfg.out, 'cache'); os.makedirs(cache, exist_ok=True)
    usc = sets.get('USC-SIPI', {})
    mont = [c for c in MONTAGE if c in usc] + [c for c in usc if c not in MONTAGE]
    mont = mont[:3]
    for ds, items in sets.items():
        full = ds == 'USC-SIPI'
        d = os.path.join(cache, safe(ds)); os.makedirs(d, exist_ok=True)
        t_ds = time.time()
        for i, (nm, path) in enumerate(items.items()):
            cj = os.path.join(d, safe(nm) + '.json')
            if os.path.exists(cj):
                continue
            t0 = time.time()
            try:
                I = S.read_cover(path)
            except Exception as e:
                print('  skip unreadable %s (%s)' % (path, e)); continue
            r = S.one_image(I, a1, a2, BLK=S.BLOCK, trials=cfg.trials if full else 0,
                            sweeps=full, seed=i, keep_images=(full and nm in mont))
            if full:
                r['cred_Hc'] = S.credential_ablation_Hc(I, a1, a2, seed=i)
            if 'img' in r:
                np.savez_compressed(os.path.join(d, safe(nm) + '_img.npz'), **r.pop('img'))
            r['file'] = path
            jdump(r, cj)
            print('  [%s %d/%d] %-28s %4dx%-4d net %.4f eff %.4f exact %s  %.1fs'
                  % (ds, i + 1, len(items), nm[-28:], r['M'], r['N'], r['net'], r['eff'],
                     'YES' if r['exact'] else 'NO', time.time() - t0), flush=True)
        print('  %s done (%.0fs)' % (ds, time.time() - t_ds), flush=True)


def load_cache(cfg, sets):
    R = {}
    for ds, items in sets.items():
        d = os.path.join(cfg.out, 'cache', safe(ds))
        R[ds] = {}
        for nm in items:
            p = os.path.join(d, safe(nm) + '.json')
            if os.path.exists(p):
                R[ds][nm] = json.load(open(p))
    return R


def r4(x): return round(float(x), 4)


def assemble(cfg, sets, R, audio_src):
    D = dict(cap={}, stats={}, stats_base={}, val4={}, npcr_base={}, npcr_marked={}, psens={}, bands={}, blk={}, lvl={}, abl={}, rt={}, npcr={}, ds={}, size={},
             npcr_cred={}, tleak={}, wrong_key={}, cred_ablation={}, files={}, meta={})
    usc = R.get('USC-SIPI', {})
    for nm, r in usc.items():
        D['cap'][nm] = [r['levels'], r4(r['raw']), r4(r['side']), r4(r['net']),
                        round(r['cont'], 3), r4(r['eff'])]
        sp = r['spec']          # ciphertext statistics: specified (AES-256-CTR) construction
        D['stats'][nm] = dict(Hp=r4(r['Hplain']), Hc=r4(sp['Hciph']), chi=round(sp['chi2'], 1),
                              p=round(sp['pchi'], 3), plain=[r4(x) for x in r['cp']],
                              ciph=[r4(x) for x in sp['cc']])
        D['stats_base'][nm] = dict(Hc=r4(r['Hciph']), chi=round(r['chi2'], 1), p=round(r['pchi'], 3),
                                   ciph=[r4(x) for x in r['cc']])
        if 'val4' in r:
            v = r['val4']; MN = r['M'] * r['N']
            D['val4'][nm] = dict(cap=[v['levels'], r4(v['raw'] / MN), r4(v['side'] / MN), r4(v['cap'] / MN),
                                      round(v['cont'] / MN, 3), r4(v['cap'] / MN - max(v['cont'] / MN - 8, 0))],
                                 lvl=[r4(x) for x in v['Leff']], abl=v['abl'], tleak0=r4(v['tleak0']))
        D['blk'][nm] = [r4(x) for x in r['Bnet']]
        D['lvl'][nm] = [r4(x) for x in r['Leff']]
        if 'bands' in r:
            D['bands'][nm] = r['bands']
        D['abl'][nm] = r['abl']
        D['rt'][nm] = [r['M'] * r['N'], round(r['tenc'], 3), round(r['tdec'], 3)]
        D['size'][nm] = [r['M'], r['N']]
        if 'sens' in r['spec']:
            q = r['spec']['sens']          # key sensitivity of the specified construction
            D['npcr'][nm] = dict(n=r4(q['npcr']), nstar=r4(q['nstar']), npass='YES' if q['npass'] else 'NO',
                                 u=r4(q['uaci']), ulo=r4(q['ulo']), uhi=r4(q['uhi']), upass='YES' if q['upass'] else 'NO',
                                 nsd=r4(q['npcr_sd']), usd=r4(q['uaci_sd']),
                                 nsd1=r4(q['npcr_sd']), usd1=r4(q['uaci_sd']),
                                 nmin=r4(min(q['npcr_trials'])), nmax=r4(max(q['npcr_trials'])),
                                 umin=r4(min(q['uaci_trials'])), umax=r4(max(q['uaci_trials'])),
                                 T=q['T'], trials=q['trials'], npass_trials=q['npass_trials'], upass_trials=q['upass_trials'])
            if 'psens_fresh' in r['spec']:
                f_, s_ = r['spec']['psens_fresh'], r['spec']['psens_same']
                D['psens'][nm] = dict(n=r4(f_['npcr']), u=r4(f_['uaci']), nsd1=r4(f_['npcr_sd']), usd1=r4(f_['uaci_sd']),
                                      npass_trials=f_['npass_trials'], upass_trials=f_['upass_trials'], trials=f_['trials'],
                                      n_same=round(s_['npcr'], 5), u_same=round(s_['uaci'], 6))
            m = r['spec']['sens_marked']   # marked images, same K_H and payload, one bit of K flipped
            D['npcr_marked'][nm] = dict(n=r4(m['npcr']), nsd1=r4(m['npcr_sd']), u=r4(m['uaci']), usd1=r4(m['uaci_sd']),
                                        npass_trials=m['npass_trials'], upass_trials=m['upass_trials'], T=m['T'],
                                        npass='YES' if m['npass'] else 'NO', upass='YES' if m['upass'] else 'NO')
        if 'wu' in r:
            w = r['wu']
            D['npcr_base'][nm] = dict(n=r4(r['npcr_key']), nstar=r4(w['nstar']),
                                 npass='YES' if w['npass'] else 'NO', u=r4(r['uaci_key']),
                                 ulo=r4(w['ulo']), uhi=r4(w['uhi']), upass='YES' if w['upass'] else 'NO',
                                 nsd=r4(r['npcr_key_sd']), usd=r4(r['uaci_key_sd']),
                                 nsd1=r4(r['npcr_key_sd']), usd1=r4(r['uaci_key_sd']),   # sample SD (ddof=1)
                                 nmin=r4(min(r['npcr_key_trials'])), nmax=r4(max(r['npcr_key_trials'])),
                                 umin=r4(min(r['uaci_key_trials'])), umax=r4(max(r['uaci_key_trials'])),
                                 T=w.get('T'), trials=w.get('trials'),
                                 npass_trials=w.get('npass_trials'), upass_trials=w.get('upass_trials'))
            D['npcr_cred'][nm] = {q: dict(n=r4(r['npcr_' + q]), u=r4(r['uaci_' + q]),
                                          nsd=r4(r['npcr_%s_sd' % q]), usd=r4(r['uaci_%s_sd' % q]))
                                  for q in ('A1', 'A2')}
        D['tleak'][nm] = [r4(x) for x in r['tleak']]
        D['wrong_key'][nm] = r4(r['wrong_match_pct'])
    if usc:
        cw = [r['cred_Hc'][0] for r in usc.values()]
        cn = [r['cred_Hc'][1] for r in usc.values()]
        D['cred_ablation'] = dict(with_credentials=round(float(np.mean(cw)), 5),
                                  without_credentials=round(float(np.mean(cn)), 5), n=len(cw))
    for ds, items in R.items():
        if not items:
            continue
        net = np.array([r['net'] for r in items.values()])
        eff = np.array([r['eff'] for r in items.values()])
        D['ds'][ds] = dict(N=len(items), net=r4(net.mean()), nsd=r4(net.std()),
                           eff=r4(eff.mean()), esd=r4(eff.std()),
                           H=r4(np.mean([r['spec']['Hciph'] for r in items.values()])),
                           rho=r4(np.mean([max(abs(x) for x in r['spec']['cc']) for r in items.values()])),
                           chi_rej=int(sum(r['spec']['pchi'] < 0.05 for r in items.values())),
                           Hmin=r4(min(r['spec']['Hciph'] for r in items.values())),
                           Hmax=r4(max(r['spec']['Hciph'] for r in items.values())),
                           rho_max=r4(max(max(abs(x) for x in r['spec']['cc']) for r in items.values())),
                           exact=int(sum(r['exact'] and r['spec']['exact'] for r in items.values())),
                           net_min=r4(net.min()), net_max=r4(net.max()),
                           sizes=sorted({'%dx%d' % (r['M'], r['N']) for r in items.values()}))
        D['files'][ds] = {nm: r['file'] for nm, r in items.items()}
    D['meta'] = dict(date=time.strftime('%Y-%m-%d %H:%M:%S'), python=platform.python_version(),
                     machine=platform.processor() or platform.machine(), numpy=np.__version__,
                     key='bytes 0..31', nonce='0123456789ab', block=S.BLOCK, trials=cfg.trials,
                     n_per_db=cfg.n, sample_seed=cfg.seed, audio=audio_src,
                     note='capacity values are key independent; statistics depend on key, nonce and A1/A2')
    return D


def stage_ablation(cfg, sets, a1, a2):
    """Ablation at the scheme's own depth, reservation and payload (Table 6, Fig. 8)."""
    p = os.path.join(cfg.out, 'ablation.json')
    out = json.load(open(p)) if os.path.exists(p) else {}
    for nm, path in sets.get('USC-SIPI', {}).items():
        if nm in out:
            continue
        t0 = time.time()
        out[nm] = S.ablation_full(S.read_cover(path), a1, a2, BLK=S.BLOCK)
        jdump(out, p)
        c = out[nm]['classic']
        print('  [ablation] %-11s L=%d classic %d..%d px out of range, deferred 0, modular room %d, proposed room %d  %.1fs'
              % (nm, out[nm]['levels'], min(c), max(c), out[nm]['modular_room'], out[nm]['proposed_room'], time.time() - t0), flush=True)


def stage_spec_all(cfg, sets):
    """Specified construction (AES-256-CTR, block permutation, independent K_H)
    end to end on every image: payload and cover exact, room equal to the base."""
    import serdhei as SD
    p = os.path.join(cfg.out, 'spec_all.json')
    out = json.load(open(p)) if os.path.exists(p) else {}
    rng = np.random.default_rng(cfg.seed)
    for ds, items in sets.items():
        rows = out.setdefault(ds, {})
        for i, (nm, path) in enumerate(items.items()):
            if nm in rows:
                continue
            try:
                I = S.read_cover(path).astype(np.int64)
            except Exception as e:
                print('  skip unreadable %s (%s)' % (path, e)); continue
            t0 = time.time()
            K, KH, N = rng.bytes(32), rng.bytes(32), rng.bytes(12)
            C, H0, t1 = SD.spec_owner(I, K, N, BLK=S.BLOCK)
            kt = SD.owner_keys(K, N)['tmap']
            T = SD._decrypt_tmap(H0, kt)
            room = int(sum(int(T[b].sum()) * H0['B'] ** 2 for b in T))
            D = rng.integers(0, 2, room).astype(np.uint8)          # fill the room completely
            Cm, H1, t2 = SD.spec_hider(C, H0, t1, kt, KH, D)
            got = SD.spec_extract(Cm, H1, t1, t2, kt, KH)
            R = SD.spec_recover(Cm, H1, t1, K)
            cp = S.capacity(I.astype(np.uint8), S.BLOCK)
            hdr_bits = 8 * (len(SD._ser_header(H1)) + 64)                 # header plus both tags
            rows[nm] = dict(room=room, base_room=cp['raw'], Rt_bits=int(cp['side']),
                            tmap_stored_bits=8 * len(H0['Tcode']), header_and_tags_bits=hdr_bits,
                            meta_bits=hdr_bits - int(cp['side']),
                            payload_exact=bool(got is not None and np.array_equal(got, D)),
                            cover_exact=bool(R is not None and np.array_equal(np.asarray(R).astype(np.int64), I)),
                            seconds=round(time.time() - t0, 2))
            if (i + 1) % 25 == 0 or i + 1 == len(items):
                jdump(out, p)
                print('  [spec] %s %d/%d' % (ds, i + 1, len(items)), flush=True)
    jdump(out, p)
    for ds, rows in out.items():
        n = len(rows)
        print('  %-9s %d images: payload exact %d, cover exact %d, room = base room %d'
              % (ds, n, sum(r['payload_exact'] for r in rows.values()), sum(r['cover_exact'] for r in rows.values()),
                 sum(r['room'] == r['base_room'] for r in rows.values())))


def stage_extra(cfg, sets):
    """Run the manuscript's own experiment scripts on the uploaded covers."""
    w = os.path.join(cfg.out, 'work'); os.makedirs(w, exist_ok=True)
    for f in ['serdhei.py', 'bpc.py', 'extra_experiments.py', 'spec_experiments.py',
              'matched_comparison.py', 'mkfigs.py']:
        shutil.copy(os.path.join(HERE, f), w)
    shutil.copy(os.path.join(cfg.out, 'data.json'), w)
    jdump({nm: os.path.abspath(p) for nm, p in sets.get('USC-SIPI', {}).items()},
          os.path.join(w, 'verified_covers.json'))
    for sc in ['extra_experiments.py', 'spec_experiments.py', 'matched_comparison.py']:
        out = sc.replace('_experiments.py', '.json').replace('matched_comparison.py', 'matched.json')
        if os.path.exists(os.path.join(cfg.out, out)) and not cfg.force:
            print('  %s exists, skipping %s' % (out, sc)); continue
        print('  running %s ...' % sc, flush=True); t0 = time.time()
        subprocess.run([sys.executable, sc], cwd=w, check=True)
        shutil.copy(os.path.join(w, out), cfg.out)
        print('  %s written (%.0fs)' % (out, time.time() - t0), flush=True)


def stage_matched_db(cfg, sets, R):
    import math
    import bpc
    p = os.path.join(cfg.out, 'matched_db.json')
    out = json.load(open(p)) if os.path.exists(p) else {'rows': {}, 'summary': {}}
    for ds, items in sets.items():
        if ds == 'USC-SIPI':
            continue
        rows = out['rows'].setdefault(ds, {})
        for i, (nm, path) in enumerate(items.items()):
            if nm in rows or nm not in R.get(ds, {}):
                continue
            I = S.read_cover(path).astype(np.int64)
            room, bs, lf, lens, ov = bpc.compress(I, border='reference')
            aux = 18 + math.ceil(math.log2(I.size)) * ov + 4 + 3 + 3
            rows[nm] = dict(bpc_net=(room - aux) / I.size, overflow=int(ov),
                            prop_net=R[ds][nm]['net'], prop_eff=R[ds][nm]['eff'])
            if (i + 1) % 25 == 0:
                print('  matched %s %d/%d' % (ds, i + 1, len(items)), flush=True); jdump(out, p)
        if rows:
            b = np.array([r['bpc_net'] for r in rows.values()])
            pn = np.array([r['prop_net'] for r in rows.values()])
            pe = np.array([r['prop_eff'] for r in rows.values()])
            out['summary'][ds] = dict(N=len(rows), bpc_net=r4(b.mean()), bpc_sd=r4(b.std()),
                                      prop_net=r4(pn.mean()), prop_eff=r4(pe.mean()),
                                      prop_net_wins=int((pn > b).sum()), prop_eff_wins=int((pe > b).sum()))
    jdump(out, p)
    for ds, s in out['summary'].items():
        print('  %-9s N=%d  BPC %.4f  proposed net %.4f eff %.4f  (net wins %d, eff wins %d)'
              % (ds, s['N'], s['bpc_net'], s['prop_net'], s['prop_eff'], s['prop_net_wins'], s['prop_eff_wins']))


def stage_xiao(cfg, sets, R):
    """Identical-image comparison with the reimplemented ABCS method of Xiao et al.
    (2024), t = 8, T searched per image as in the paper. Covers: the twelve
    standard covers. Databases: exactly the images of matched_db.json, so the
    BPC, ABCS and proposed columns refer to the same files."""
    import abcs
    p = os.path.join(cfg.out, 'xiao.json')
    out = json.load(open(p)) if os.path.exists(p) else {'rows': {}, 'summary': {}}
    md = json.load(open(os.path.join(cfg.out, 'matched_db.json'))) if os.path.exists(
        os.path.join(cfg.out, 'matched_db.json')) else {'rows': {}}
    for ds, items in sets.items():
        names = list(items) if ds == 'USC-SIPI' else [n for n in items if n in md['rows'].get(ds, {})]
        rows = out['rows'].setdefault(ds, {})
        for i, nm in enumerate(names):
            if nm in rows or nm not in R.get(ds, {}):
                continue
            I = S.read_cover(items[nm])
            r = abcs.rate(I, 8)
            rows[nm] = dict(xiao_net=float(r['er']), T=int(r['T']), coding2_blocks=int(r['coding2_blocks']),
                            prop_net=R[ds][nm]['net'], prop_eff=R[ds][nm]['eff'])
            if (i + 1) % 25 == 0:
                print('  xiao %s %d/%d' % (ds, i + 1, len(names)), flush=True); jdump(out, p)
        if rows:
            x = np.array([r['xiao_net'] for r in rows.values()])
            pn = np.array([r['prop_net'] for r in rows.values()])
            pe = np.array([r['prop_eff'] for r in rows.values()])
            out['summary'][ds] = dict(N=len(rows), xiao_net=r4(x.mean()), xiao_sd=r4(x.std()),
                                      prop_net=r4(pn.mean()), prop_eff=r4(pe.mean()),
                                      prop_net_wins=int((pn > x).sum()), prop_eff_wins=int((pe > x).sum()))
    jdump(out, p)
    for ds, s_ in out['summary'].items():
        print('  %-9s N=%d  ABCS %.4f  proposed net %.4f eff %.4f  (net wins %d, eff wins %d)'
              % (ds, s_['N'], s_['xiao_net'], s_['prop_net'], s_['prop_eff'], s_['prop_net_wins'], s_['prop_eff_wins']))


def stage_figs(cfg, sets):
    w = os.path.join(cfg.out, 'work'); os.makedirs(w, exist_ok=True)
    shutil.copy(os.path.join(HERE, 'mkfigs.py'), w)
    shutil.copy(os.path.join(cfg.out, 'data.json'), w)
    d = os.path.join(cfg.out, 'cache', 'USC-SIPI')
    sec, mon = {}, {}
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if f.endswith('_img.npz'):
            nm = f[:-8]; Z = np.load(os.path.join(d, f))
            g = lambda k: Z['spec_' + k] if 'spec_' + k in Z.files else Z[k]   # specified construction
            sec[nm + '_cover'] = Z['cover']; sec[nm + '_ciph'] = g('ciph')
            mon['%s_cover' % nm] = Z['cover']
            for k in ('enc', 'mark', 'rec'):
                mon['%s_%s' % (nm, k)] = g(k)
    if sec:
        np.savez_compressed(os.path.join(w, 'secdata.npz'), **sec)
        np.savez_compressed(os.path.join(w, 'montage.npz'), **mon)
        shutil.copy(os.path.join(w, 'secdata.npz'), cfg.out)
        shutil.copy(os.path.join(w, 'montage.npz'), cfg.out)
    subprocess.run([sys.executable, 'mkfigs.py'], cwd=w, check=True)
    fd = os.path.join(cfg.out, 'figures'); os.makedirs(fd, exist_ok=True)
    for f in os.listdir(w):
        if f.startswith('fig_') and f.endswith('.pdf') or f.startswith('p_fig_') and f.endswith('.png'):
            shutil.copy(os.path.join(w, f), fd)
    print('  figures ->', fd)


# ------------------------------------------------------------------ report
def table(head, rows):
    s = '| ' + ' | '.join(head) + ' |\n|' + '---|' * len(head) + '\n'
    for r in rows:
        s += '| ' + ' | '.join(str(x) for x in r) + ' |\n'
    return s + '\n'


def f4(x): return '%.4f' % x


def report(cfg, sets, D):
    rec = json.load(open(os.path.join(HERE, 'recorded_matlab.json')))
    L = ['# SE-RDHEI results\n', 'Generated %s on %s, Python %s.  Key bytes 0..31, nonce "0123456789ab", '
         'B = %d, %d sensitivity trials.  Credentials A1/A2: %s.\n\n'
         % (D['meta']['date'], D['meta']['machine'], D['meta']['python'], S.BLOCK, cfg.trials, D['meta']['audio'])]
    covers = list(D['cap'])
    # validation
    if covers:
        L.append('## 0. Validation against the recorded MATLAB run (key-independent quantities, at its block size B = 4)\n')
        rows, allok = [], True
        for nm in covers:
            if nm not in rec['cap']:
                rows.append([nm, 'not in recorded run', '', '', '', '']); continue
            v4 = D['val4'].get(nm)
            if v4 is None:
                rows.append([nm, 'no B = 4 values', '', '', '', '']); allok = False; continue
            ok = [v4['cap'] == rec['cap'][nm], D['blk'][nm][1:] == rec['blk'][nm],
                  v4['lvl'] == rec['lvl'][nm], v4['abl'] == [rec['modroom'][nm], rec['ourroom'][nm]],
                  abs(v4['tleak0'] - rec['tleak'][nm][0]) < 1e-4]
            allok &= all(ok)
            rows.append([nm] + ['match' if o else '**DIFFERENT**' for o in ok])
        L.append(table(['cover', 'capacity row', 'B sweep', 'L sweep', 'room (ablation)', 't-map entropy'], rows))
        L.append('All key-independent values %s the recorded run on the same cover files. '
                 'A difference means the uploaded file is not the file used in the MATLAB run.\n\n'
                 % ('reproduce' if allok else 'do NOT all reproduce'))
        # capacity
        L.append('## 1. Capacity and reversibility (Table 3, Fig. 5)\n')
        rows = [[nm, D['cap'][nm][0], 'YES' if R_exact(cfg, nm) else 'NO'] + [f4(x) for x in D['cap'][nm][1:4]]
                + ['%.3f' % D['cap'][nm][4], f4(D['cap'][nm][5])] for nm in covers]
        m = np.array([D['cap'][nm][1:] for nm in covers]).mean(0)
        rows.append(['MEAN', '', ''] + [f4(x) for x in m[:3]] + ['%.3f' % m[3], f4(m[4])])
        L.append(table(['image', 'L', 'exact', 'raw', 'side', 'net', 'container', 'eff'], rows))
    L.append('## 2. Per-dataset rates (Table 4, Figs. 5-6)\n')
    L.append(table(['dataset', 'N', 'sizes', 'exact', 'net mean', 'net sd', 'net min', 'net max', 'eff mean', 'eff sd', 'H cipher', 'mean max|rho|', 'chi2 rejections'],
                   [[ds, v['N'], ' '.join(v['sizes']), '%d/%d' % (v['exact'], v['N']), f4(v['net']), f4(v['nsd']),
                     f4(v['net_min']), f4(v['net_max']), f4(v['eff']), f4(v['esd']), f4(v['H']), f4(v['rho']),
                     '%s/%d' % (v.get('chi_rej', '-'), v['N'])]
                    for ds, v in D['ds'].items()]))
    if covers:
        L.append('## 3. Ciphertext statistics (Table 7, Figs. 9-10)\n')
        L.append(table(['image', 'H plain', 'H cipher', 'chi2', 'p', 'plain H,V,D', 'cipher H,V,D'],
                       [[nm, f4(s['Hp']), f4(s['Hc']), s['chi'], s['p'], ', '.join('%+.4f' % x for x in s['plain']),
                         ', '.join('%+.4f' % x for x in s['ciph'])] for nm, s in D['stats'].items()]))
        if D['npcr']:
            L.append('## 4. Key and credential sensitivity, Wu-Noonan-Agaian tests at alpha = 0.05 (Fig. 11)\n')
            L.append('Key: one bit of the master key K of the specified construction flipped, encrypted images compared. '
                     'A1/A2: credentials of the base construction.\n')
            L.append(table(['image', 'NPCR key', 'sd', 'N*', 'pass', 'UACI key', 'sd', 'U*-', 'U*+', 'pass', 'NPCR/UACI A1', 'NPCR/UACI A2'],
                           [[nm, f4(v['n']), f4(v['nsd']), f4(v['nstar']), v['npass'], f4(v['u']), f4(v['usd']), f4(v['ulo']), f4(v['uhi']), v['upass'],
                             '%.4f / %.4f' % (D['npcr_cred'][nm]['A1']['n'], D['npcr_cred'][nm]['A1']['u']),
                             '%.4f / %.4f' % (D['npcr_cred'][nm]['A2']['n'], D['npcr_cred'][nm]['A2']['u'])]
                            for nm, v in D['npcr'].items()]))
            n = [v['n'] for v in D['npcr'].values()]; u = [v['u'] for v in D['npcr'].values()]
            L.append('NPCR mean %.4f (range %.4f to %.4f), UACI mean %.4f (range %.4f to %.4f); NPCR passed %d/%d, UACI passed %d/%d.\n\n'
                     % (np.mean(n), min(n), max(n), np.mean(u), min(u), max(u),
                        sum(v['npass'] == 'YES' for v in D['npcr'].values()), len(n),
                        sum(v['upass'] == 'YES' for v in D['npcr'].values()), len(n)))
        if D.get('psens'):
            L.append('## 4b. Plaintext sensitivity, one pixel +-1 (specified construction)\n')
            L.append(table(['image', 'NPCR fresh nonce', 'UACI fresh nonce', 'passed N/U', 'NPCR same nonce', 'UACI same nonce'],
                           [[nm, f4(v['n']), f4(v['u']), '%d/%d, %d/%d' % (v['npass_trials'], v['trials'], v['upass_trials'], v['trials']),
                             '%.5f' % v['n_same'], '%.6f' % v['u_same']] for nm, v in D['psens'].items()]))
        if D.get('npcr_marked'):
            L.append('## 4c. Key sensitivity on marked images (same K_H and payload)\n')
            L.append(table(['image', 'NPCR', 'UACI', 'passed N/U'],
                           [[nm, f4(v['n']), f4(v['u']), '%d, %d' % (v['npass_trials'], v['upass_trials'])] for nm, v in D['npcr_marked'].items()]))
        L.append('## 5. Block-size sweep, net bpp (Fig. 7)\n')
        L.append(table(['image'] + ['B=%d' % b for b in S.BSWEEP], [[nm] + [f4(x) for x in v] for nm, v in D['blk'].items()]))
        L.append('## 6. Decomposition-level sweep, effective bpp (Fig. 7)\n')
        L.append(table(['image', 'L=1', 'L=2', 'L=3', 'L=4'], [[nm] + [f4(x) for x in v] for nm, v in D['lvl'].items()]))
        L.append('## 7. Ablations (Table 6, Fig. 8)\n')
        L.append(table(['image', 'overflow, classic order', 'overflow, ours', 'room, modular lifting', 'room, ours'],
                       [[nm] + v for nm, v in D['abl'].items()]))
        L.append('## 8. Runtime (Section 6.6), this machine\n')
        L.append(table(['image', 'pixels', 'encrypt s', 'decrypt s'], [[nm] + v for nm, v in D['rt'].items()]))
        s512 = [v for v in D['rt'].values() if v[0] == 262144]
        if s512:
            L.append('512x512 mean: encrypt %.3f s, decrypt %.3f s.\n\n' % (np.mean([v[1] for v in s512]), np.mean([v[2] for v in s512])))
        L.append('## 9. t-map leakage and wrong-key recovery (Section 7)\n')
        L.append(table(['image', 't-map entropy plain', 'encrypted', 'pixels equal to cover after 1-bit wrong key (%)'],
                       [[nm, f4(v[0]), f4(v[1]), f4(D['wrong_key'][nm])] for nm, v in D['tleak'].items()]))
        if D['cred_ablation']:
            c = D['cred_ablation']
            L.append('## 10. Credential ablation (Section 7.6)\n\nMean ciphertext entropy over %d covers: with credentials %.5f, '
                     'with the credential terms removed %.5f.\n\n' % (c['n'], c['with_credentials'], c['without_credentials']))
    A_ = os.path.join(cfg.out, 'ablation.json')
    if os.path.exists(A_):
        A = json.load(open(A_))
        L.append('## 7b. Ablation at full depth L, same reservation and payload as the scheme (three payloads)\n')
        L.append(table(['image', 'L', 'classic ordering: px out of range (min..max)', 'deferred', 'modular room', 'proposed room'],
                       [[nm, a['levels'], '%d..%d' % (min(a['classic']), max(a['classic'])), 0, a['modular_room'], a['proposed_room']]
                        for nm, a in A.items()]))
    SA = os.path.join(cfg.out, 'spec_all.json')
    if os.path.exists(SA):
        SA = json.load(open(SA))
        L.append('## 14b. Specified construction end to end on every image (AES-256-CTR, full payload)\n')
        L.append('Stored header and tags minus the Huffman t-map cost R_t (bits): %s\n\n'
                 % ', '.join('%s %d' % (n, v['meta_bits']) for r in SA.values() for n, v in r.items() if 'meta_bits' in v))
        L.append(table(['dataset', 'images', 'payload exact', 'cover exact', 'room = base room', 'mean s'],
                       [[ds, len(r), sum(v['payload_exact'] for v in r.values()), sum(v['cover_exact'] for v in r.values()),
                         sum(v['room'] == v['base_room'] for v in r.values()), '%.2f' % np.mean([v['seconds'] for v in r.values()])]
                        for ds, r in SA.items() if r]))
    X = os.path.join(cfg.out, 'extra.json')
    if os.path.exists(X):
        X = json.load(open(X))
        L.append('## 11. Block-minimum efficiency (Table 8)\n')
        L.append(table(['image', 'sum t (bpp)', 'room (bpp)', 'eta', 'eta B=2', 'eta B=4', 'eta B=8', 'oracle net'],
                       [[nm, f4(e['sum_t']), f4(e['room']), '%.3f' % e['eta']]
                        + ['%.3f' % e.get('eta_by_B', {}).get(b, float('nan')) for b in ('2', '4', '8')]
                        + [f4(e['oracle_net'])] for nm, e in X['eff'].items()]))
        L.append('## 12. Leakage-reduced descriptor (Proposition 1)\n')
        L.append(table(['image', 'room', 'payload exact', 'cover exact', 't-map length same', 'rho spatial', 'rho permuted'],
                       [[nm, f4(l['room']), l['payload_exact'], l['cover_exact'], l['tmap_len_same'],
                         ', '.join('%.3f' % x for x in l['rho_spatial']), ', '.join('%.3f' % x for x in l['rho_permuted'])]
                        for nm, l in X['lr'].items()]))
        mk = X['multikey']; P = [p for m in mk.values() for p in m['p']]
        L.append('## 13. Statistics under 20 independent keys per cover (base construction)\n\n'
                 'H cipher %.5f to %.5f; chi-square rejections %d of %d at alpha = 0.05 (expected %.1f); max |rho| %.4f.\n\n'
                 % (min(min(m['Hc']) for m in mk.values()), max(max(m['Hc']) for m in mk.values()),
                    sum(p < 0.05 for p in P), len(P), 0.05 * len(P), max(max(m['rho']) for m in mk.values())))
    P_ = os.path.join(cfg.out, 'spec.json')
    if os.path.exists(P_):
        SP = json.load(open(P_))
        L.append('## 14. Specified construction (Section 4.6, Algorithm 3)\n\nSelf-tests: HKDF RFC 5869 %s, AES SP 800-38A %s.\n\n'
                 % (SP['selftest']['hkdf_rfc5869'], SP['selftest']['aes_sp800_38a']))
        L.append(table(['image', 'room bpp', 'raw (base)', 'payload exact', 'cover exact', 'seconds'],
                       [[nm, f4(r['room_bpp']), f4(r['recorded_raw']), r['payload_exact'], r['cover_exact'], r['seconds']]
                        for nm, r in SP['roundtrip'].items()]))
        kinds = list(next(iter(SP['tamper'].values())))
        L.append(table(['tampering', 'tau2 accepts', 'tau1 accepts', 'cover exact if accepted', 'identical on all covers'],
                       [[k] + [str(next(iter(SP['tamper'].values()))[k][q]) for q in ('tau2_accepts', 'tau1_accepts', 'cover_exact_if_accepted')]
                        + [len({json.dumps(SP['tamper'][n][k], sort_keys=True) for n in SP['tamper']}) == 1] for k in kinds]))
        st = SP['stats']; P = [p for m in st.values() for p in m['p']]
        L.append('AES-256-CTR, 20 keys per cover: H cipher %.5f to %.5f; chi-square rejections %d of %d (expected %.1f); max |rho| %.4f.\n\n'
                 % (min(min(m['Hc']) for m in st.values()), max(max(m['Hc']) for m in st.values()),
                    sum(p < 0.05 for p in P), len(P), 0.05 * len(P), max(max(m['rho']) for m in st.values())))
    M_ = os.path.join(cfg.out, 'matched.json')
    if os.path.exists(M_):
        MT = json.load(open(M_))
        L.append('## 15. Matched comparison with reimplemented BPC (Table 5)\n')
        if MT['validation']:
            L.append(table(['cover', 'published BPC net', 'reimplemented', 'room deviation %'],
                           [[nm, f4(v['published_net']), f4(v['reimpl_net']), '%+.2f' % v['room_dev_pct']] for nm, v in MT['validation'].items()]))
        L.append(table(['cover', 'BPC net', 'overflow px', 'bs', 'Lfix', 'proposed net', 'proposed eff'],
                       [[nm, f4(r['bpc_net']), r['overflow'], r['bs'], r['Lfix'], f4(r.get('prop_net', float('nan'))), f4(r.get('prop_eff', float('nan')))]
                        for nm, r in MT['rows'].items()]))
    Q = os.path.join(cfg.out, 'matched_db.json')
    if os.path.exists(Q):
        Q = json.load(open(Q))
        if Q['summary']:
            L.append('## 16. Matched comparison on the database samples\n')
            L.append(table(['dataset', 'N', 'BPC net', 'BPC sd', 'proposed net', 'proposed eff', 'net wins', 'eff wins'],
                           [[ds, s['N'], f4(s['bpc_net']), f4(s['bpc_sd']), f4(s['prop_net']), f4(s['prop_eff']), s['prop_net_wins'], s['prop_eff_wins']]
                            for ds, s in Q['summary'].items()]))
    X = os.path.join(cfg.out, 'xiao.json')
    if os.path.exists(X):
        X = json.load(open(X))
        if X['summary']:
            L.append('## 17. Identical-image comparison with Xiao et al. (2024), reimplemented (t = 8)\n')
            L.append(table(['dataset', 'N', 'ABCS net', 'ABCS sd', 'proposed net', 'proposed eff', 'net wins', 'eff wins'],
                           [[ds, s_['N'], f4(s_['xiao_net']), f4(s_['xiao_sd']), f4(s_['prop_net']), f4(s_['prop_eff']),
                             s_['prop_net_wins'], s_['prop_eff_wins']] for ds, s_ in X['summary'].items()]))
            if 'USC-SIPI' in X['rows']:
                L.append(table(['cover', 'ABCS net', 'T', 'proposed net', 'proposed eff'],
                               [[nm, f4(r['xiao_net']), r['T'], f4(r['prop_net']), f4(r['prop_eff'])]
                                for nm, r in X['rows']['USC-SIPI'].items()]))
    L.append('## Files processed\n')
    for ds, m in D['files'].items():
        L.append('- %s: %d images\n' % (ds, len(m)))
    txt = re.sub(r'^(#+ [^\n]*)\n(?!\n)', r'\1\n\n', ''.join(L), flags=re.M)
    open(os.path.join(cfg.out, 'REPORT.md'), 'w').write(txt)
    # per-image CSV for every dataset
    import csv
    with open(os.path.join(cfg.out, 'per_image.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['dataset', 'image', 'file', 'M', 'N', 'levels', 'exact', 'raw', 'side', 'net', 'container', 'eff',
                    'H_plain', 'H_cipher', 'chi2', 'p', 'cc_H', 'cc_V', 'cc_D'])
        for ds, items in _R.items():
            for nm, r in items.items():
                w.writerow([ds, nm, r['file'], r['M'], r['N'], r['levels'], r['exact']] +
                           ['%.6f' % r[k] for k in ('raw', 'side', 'net', 'cont', 'eff', 'Hplain', 'Hciph', 'chi2', 'pchi')] +
                           ['%.6f' % x for x in r['cc']])


_R = {}


def R_exact(cfg, nm):
    return _R.get('USC-SIPI', {}).get(nm, {}).get('exact', False)


def bundle(cfg):
    z = os.path.join(cfg.out, 'results_SE-RDHEI.zip')
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as Z:
        for f in ['REPORT.md', 'per_image.csv', 'data.json', 'ablation.json', 'spec_all.json', 'extra.json', 'spec.json', 'matched.json',
                  'matched_db.json', 'xiao.json', 'secdata.npz', 'montage.npz', 'run_log.txt']:
            p = os.path.join(cfg.out, f)
            if os.path.exists(p):
                Z.write(p, f)
        for sub in ['figures', 'cache']:
            for root, _, fs in os.walk(os.path.join(cfg.out, sub)):
                for f in fs:
                    if f.endswith('_img.npz'):
                        continue
                    p = os.path.join(root, f); Z.write(p, os.path.relpath(p, cfg.out))
    print('  bundle ->', z, '(%.1f MB)' % (os.path.getsize(z) / 2 ** 20))
    return z


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--n', type=int, default=100, help='images sampled per database (0 = all)')
    ap.add_argument('--seed', type=int, default=2026)
    ap.add_argument('--trials', type=int, default=10)
    ap.add_argument('--a1'); ap.add_argument('--a2')
    ap.add_argument('--rename', default='{}', help='JSON map file-stem -> cover name')
    ap.add_argument('--dsmap', default='{}', help='JSON map folder name -> dataset name')
    ap.add_argument('--stage', default='all',
                    choices=['all', 'main', 'ablation', 'spec_all', 'extra', 'matched_db', 'xiao', 'figs', 'report'])
    ap.add_argument('--force', action='store_true')
    cfg = ap.parse_args(argv)
    os.makedirs(cfg.out, exist_ok=True)
    # results computed with another block size must never be mixed with these
    mk = os.path.join(cfg.out, 'BLOCK_SIZE')
    if os.path.exists(mk):
        if int(open(mk).read().strip()) != S.BLOCK:
            raise SystemExit('%s holds results for B = %s, this run uses B = %d: use a new output folder'
                             % (cfg.out, open(mk).read().strip(), S.BLOCK))
    elif os.path.isdir(os.path.join(cfg.out, 'cache')):
        raise SystemExit('%s holds results of an earlier run (B = 4): use a new output folder' % cfg.out)
    else:
        open(mk, 'w').write(str(S.BLOCK))
    sets = discover(cfg.data, cfg.n, cfg.seed, json.loads(cfg.rename), json.loads(cfg.dsmap))
    print('datasets found:')
    for ds, m in sets.items():
        print('  %-10s %d images' % (ds, len(m)) + (':  ' + ', '.join(m) if ds == 'USC-SIPI' else ''))
    if 'USC-SIPI' not in sets:
        print('  ! no USC-SIPI covers found: per-cover tables, sweeps and figures need them')
    else:
        miss = [c for c in ORDER if c not in sets['USC-SIPI']]
        if miss:
            print('  ! covers missing: %s (their rows will be absent from Tables 3, 5-8)' % ', '.join(miss))
    if cfg.a1 and cfg.a2:
        a1, a2 = S.load_audio(cfg.a1), S.load_audio(cfg.a2)
        src = '%s, %s' % (os.path.basename(cfg.a1), os.path.basename(cfg.a2))
    else:
        a1, a2 = S.synthetic_audio(1), S.synthetic_audio(2)
        src = 'deterministic synthetic clips (SE_RDHEI.m fallback)'
    st = cfg.stage
    if st in ('all', 'main'):
        print('\n== main measurements'); stage_main(cfg, sets, a1, a2)
    global _R
    _R = load_cache(cfg, sets)
    D = assemble(cfg, sets, _R, src)
    jdump(D, os.path.join(cfg.out, 'data.json'))
    if st in ('all', 'ablation') and 'USC-SIPI' in sets:
        print('\n== ablation at full depth'); stage_ablation(cfg, sets, a1, a2)
    if st in ('all', 'spec_all'):
        print('\n== specified construction, end to end on every image'); stage_spec_all(cfg, sets)
    if st in ('all', 'extra') and 'USC-SIPI' in sets:
        print('\n== manuscript experiment scripts'); stage_extra(cfg, sets)
    if st in ('all', 'matched_db'):
        print('\n== matched comparison on database samples'); stage_matched_db(cfg, sets, _R)
    if st in ('all', 'matched_db', 'xiao'):
        print('\n== identical-image comparison with Xiao et al. (2024), reimplemented'); stage_xiao(cfg, sets, _R)
    if st in ('all', 'figs') and 'USC-SIPI' in sets:
        print('\n== figures'); stage_figs(cfg, sets)
    print('\n== report'); report(cfg, sets, D)
    bundle(cfg)


if __name__ == '__main__':
    main()
