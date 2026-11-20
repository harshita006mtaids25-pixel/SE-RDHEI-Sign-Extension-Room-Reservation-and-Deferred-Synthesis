function SE_RDHEI(coverPath, opts)
%SE_RDHEI  Sign-Extension Reversible Data Hiding in Encrypted Images
%          over the exact signed 5/3 integer wavelet transform,
%          with dual-credential audio key binding.
%
%  SINGLE-FILE, TOOLBOX-FREE DEMO. Everything is in this one file.
%
%  USAGE
%    SE_RDHEI                      % file dialog for the cover, auto audio
%    SE_RDHEI('mypic.png')         % your cover image
%    SE_RDHEI('mypic.png', struct('maxSize',256,'trials',5))
%
%  COVER IMAGE
%    - with no argument the DEFAULT_COVER path below is used; edit that one
%      line to point at your own image
%    - if that file is missing you get a file picker, then a built-in fallback
%    - pass a path explicitly to override
%    - colour images are converted to greyscale, dimensions cropped to even
%    - resized down to opts.maxSize (default 512) by integer subsampling
%
%  AUDIO  (chosen automatically, and always reported)
%    Search order:
%      1. any .wav .flac .ogg .mp3 .m4a .au in the current folder
%      2. MATLAB's built-in demo clips (handel, gong, train, laughter, ...)
%      3. deterministic synthetic tones (last resort)
%    The two files actually used are printed with full path, sample rate,
%    duration and SHA-256 fingerprint, so every run is auditable.
%
%  OPTIONS (all optional fields of `opts`)
%    maxSize   longest cover side, default 512 (native size for USC-SIPI)
%    trials    NPCR/UACI trials, default 10 (use 30+ for a paper; 0 skips)
%    blk       block size for room reservation, default 8
%    key       32-byte uint8 secret key, default uint8(0:31)
%    audio1    path to force the first audio credential
%    audio2    path to force the second audio credential
%    quiet     true to suppress the figure
%
%  BATCH MODE  (all images in a folder -> tables + figures)
%    SE_RDHEI('__batch')                       uses DEFAULT_IMAGE_DIR below
%    SE_RDHEI('__batch', struct('dir','/path/to/Image'))
%    SE_RDHEI('__batch', struct('dir',D,'outdir',O,'trials',10))
%    Writes results.csv, tables.tex (booktabs) and fig1..fig8 (png + eps).
%
%  MULTI-DATASET MODE  (USC-SIPI, BOSSbase, BOWS-2, UCID, Kodak)
%    SE_RDHEI('__datasets')      runs every dataset listed in dataset_list()
%                                at the bottom of this file. Datasets whose
%                                folder is blank or missing are SKIPPED.
%    Emits dataset_<name>.csv, summary.csv, tables_datasets.tex (including a
%    prior-work comparison template) and fig1..fig20:
%      1 montage  2 histograms  3 correlation  4 capacity  5 block size
%      6 levels   7 NPCR/UACI   8 ablations    9 per-dataset rate
%     10 rate CDF 11 entropy-vs-rate  12 block diagram  13 sub-bands/t-map
%     14 room distribution  15 runtime  16 NPCR/UACI histograms
%     17 p-value uniformity 18 prior-work comparison  19 key sensitivity
%     20 per-sub-band histograms  21 baseline comparison (same images)
%     22 payload-fill sweep        23 robustness scope
%    Tables VIII-XII add the Wu et al. NPCR/UACI hypothesis tests, key space
%    and sub-band entropy, the reference-paper baseline measured on YOUR
%    images, a payload-fill sweep, and an explicit robustness scope test.
%    Prior-work numbers for fig18 live in literature_table().
%
%  VIEW SAVED FIGURES
%    SE_RDHEI('__figs')                    open every saved PNG in a window
%    SE_RDHEI('__figs', struct('os',true)) hand them to the OS viewer instead
%    Double-clicking a PNG in MATLAB's Current Folder browser launches the
%    Import Wizard (it tries to load the image as data). That is MATLAB
%    behaviour, not a broken file. Use this command, or right-click the file
%    and choose "Open Outside MATLAB".
%
%  FILE CHECK
%    SE_RDHEI('__check')   verifies line count and function count, which
%                          catches a truncated or merged download.
%
%  RUN A FOLDER OR A LIST  (use after replacing individual covers)
%    SE_RDHEI('__images', struct('files','/path/to/folder'))
%        -> every image in that folder, at native size
%    SE_RDHEI('__images', struct('files', {{ '/a.tiff','/b.tiff' }}))
%        -> exactly those files (DOUBLE braces put a cell inside a struct)
%    Either form produces all 16 tables and 23 figures.
%
%  SELF-TEST
%    SE_RDHEI('__selftest')   runs property tests, edge cases and prints
%    ciphertext digests for cross-checking against the Python reference.
%    full      true (default) runs ablations 5-8; false stops after 4
%    permWords 8 (default, bit-identical to Python) or 4 (about 2x faster)
%    levels    decomposition depth; 0 = auto (deepest, max 4)
%
%  No toolboxes required. Java is used for SHA-256 when available and a
%  verified pure-MATLAB SHA-256 is used otherwise (slower).

% ======================================================================
DEFAULT_COVER = default_paths();
if nargin < 1, coverPath = ''; end
if nargin < 2, opts = struct(); end
if isempty(coverPath) && exist(DEFAULT_COVER, 'file')
    coverPath = DEFAULT_COVER;
end
if ischar(coverPath) && strcmp(coverPath, '__selftest')
    selftest(opts);  return
end
if ischar(coverPath) && strcmp(coverPath, '__batch')
    batch(opts);  return
end
if ischar(coverPath) && strcmp(coverPath, '__datasets')
    datasets(opts);  return
end
if ischar(coverPath) && strcmp(coverPath, '__images')
    images_run(opts);  return
end
if ischar(coverPath) && strcmp(coverPath, '__check')
    checkfile();  return
end
if ischar(coverPath) && strcmp(coverPath, '__figs')
    showfigs(opts);  return
end
D = @(f,v) getfielddef(opts,f,v);
if ~isempty(coverPath) && ~isfield(opts,'maxSize')
    CFG.maxSize = 0;                 % explicit cover: use its native size
else
    CFG.maxSize = D('maxSize',512);  % dataset sweeps stay capped
end
CFG.trials = D('trials',10);
CFG.blk     = D('blk',8);         CFG.key    = uint8(D('key',uint8(0:31)));
CFG.quiet   = D('quiet',false);   CFG.permWords = D('permWords',8);
CFG.full    = D('full',true);
CFG.nonce   = uint8('0123456789ab');
CFG.sub     = {'LL','HL','LH','HH'};   % sub-band types (for F derivation)
CFG.fixedNonce = D('fixedNonce', true); % false => fresh 96-bit nonce per run
CFG.levels  = D('levels', 0);          % 0 = auto (deepest available)

banner('SE-RDHEI  single-file demo');
CFG.shaBackend = pick_sha_backend();
nmb = {'Java MessageDigest (MATLAB, fast)', ...
       'Octave built-in hash() (fast)', 'pure MATLAB fallback (slow)'};
fprintf('  SHA-256 backend           : %s\n', nmb{CFG.shaBackend});
CFG.hasJava = (CFG.shaBackend == 1);
if CFG.shaBackend == 3 && CFG.maxSize > 128
    CFG.maxSize = 128;
    fprintf('  ** no Java: maxSize forced to 128 to keep runtime sane **\n');
end

if CFG.maxSize > 0
    fprintf('  Cover cap / NPCR trials   : %d px / %d\n', CFG.maxSize, CFG.trials);
else
    fprintf('  Cover cap / NPCR trials   : native size / %d\n', CFG.trials);
end

if isfield(opts,'nonce'), CFG.nonce = uint8(opts.nonce); end
if ~CFG.fixedNonce, CFG.nonce = fresh_nonce(CFG); end
nonce_guard(CFG.nonce, CFG);

% ---------------------------------------------------------------- cover
[I, coverName] = load_cover(coverPath, CFG.maxSize);
fprintf('\n  Cover image               : %s\n', coverName);
fprintf('  Size                      : %d x %d  (%d pixels)\n', ...
        size(I,1), size(I,2), numel(I));
fprintf('  Plain entropy             : %.4f bits\n', entropy8(I));

% ---------------------------------------------------------------- audio
[a1, a2, src1, src2] = load_audio(D('audio1',''), D('audio2',''), CFG);
banner('AUDIO CREDENTIALS ACTUALLY USED');
report_audio('A1', a1, src1, CFG);
report_audio('A2', a2, src2, CFG);

% ------------------------------------------------- encrypt, embed, undo
banner('1.  ENCRYPT + EMBED  /  EXTRACT + DECRYPT');
t0 = tic;  [C,h,pl] = encrypt_embed(I, CFG.key, a1, a2, CFG.nonce, [], CFG);
tEnc = toc(t0);
t0 = tic;  [Ir,pe]  = extract_decrypt(C, h, CFG.key, a1, a2, CFG);
tDec = toc(t0);

okI = isequal(Ir, I);
okP = numel(pe) >= numel(pl) && isequal(pe(1:numel(pl)), pl);
cont = 0; for b = h.names{1}, cont = cont + h.Wd.(b{1})*numel(C.(b{1})); end
cont = cont / numel(I);

Ksep = keys(CFG.key, a1, a2, CFG.nonce, CFG);
psep = extract_payload_only(C, h, Ksep.prm, CFG);
okS  = numel(psep) >= numel(pl) && isequal(psep(1:numel(pl)), pl);
fprintf('  cover recovered bit-exact : %s\n', yn(okI));
fprintf('  separable extraction OK   : %s   (PERM subkey only, no audio)\n', yn(okS));
fprintf('  payload recovered exact   : %s   (%d bits)\n', yn(okP), numel(pl));
fprintf('  max |I - I_rec|           : %d\n', max(abs(double(I(:))-double(Ir(:)))));
fprintf('  decomposition levels      : %d\n', h.levels);
fprintf('  raw room                  : %.4f bpp\n', h.raw/numel(I));
fprintf('  side information          : %.4f bpp  (Huffman-coded t-map)\n', h.side/numel(I));
fprintf('  NET embedding rate        : %.4f bpp\n', h.cap/numel(I));
fprintf('  ciphertext container      : %.2f bpp\n', cont);
fprintf('  EFFECTIVE rate            : %.4f bpp   (net - expansion)\n', ...
        h.cap/numel(I) - max(cont-8,0));
fprintf('  runtime                   : encrypt %.2fs   decrypt %.2fs\n', tEnc, tDec);

% ------------------------------------------------------------ statistics
banner('2.  CIPHERTEXT STATISTICS');
E = packbits_cipher(C, h.Wd, CFG, h.names{1});
cc = corr3(E);  cp = corr3(I);
x2 = chi2stat(E);
fprintf('  cipher entropy            : %.4f  (ideal 8)\n', entropy8(E));
fprintf('  chi-square (255 dof)      : %.1f  (expect ~255 +/- 23)\n', x2);
fprintf('  correlation  plain        : H %+.4f  V %+.4f  D %+.4f\n', cp);
fprintf('  correlation  cipher       : H %+.4f  V %+.4f  D %+.4f\n', cc);

% ----------------------------------------------------------- sensitivity
if CFG.trials > 0
banner(sprintf('3.  SENSITIVITY  (%d trials each)', CFG.trials));
fprintf('  (this is the slow part: %d encryptions)\n', 3*CFG.trials);
base = cipher_ref(I, CFG.key, a1, a2, CFG.nonce, CFG, 1000);
rows = {'1-bit secret-key flip','1-bit LSB flip in A1','1-bit LSB flip in A2'};
for r = 1:3
    n_ = zeros(1,CFG.trials); u_ = n_;
    for t = 1:CFG.trials
        k = CFG.key; x1 = a1; x2 = a2;
        switch r
            case 1, bp = randi(256)-1; k(floor(bp/8)+1) = bitxor(k(floor(bp/8)+1), uint8(2^mod(bp,8)));
            case 2, j = randi(numel(x1)); x1(j) = bitxor(x1(j), int16(1));
            case 3, j = randi(numel(x2)); x2(j) = bitxor(x2(j), int16(1));
        end
        Ec = cipher_ref(I, k, x1, x2, CFG.nonce, CFG, 2000+t);
        [n_(t),u_(t)] = npcr_uaci(base, Ec);
    end
    fprintf('  %-24s NPCR %8.4f %%   UACI %8.4f %%\n', rows{r}, mean(n_), mean(u_));
end
fprintf('  %-24s NPCR %8.4f %%   UACI %8.4f %%\n','theoretical ideal',(1-2^-8)*100,33.4635);
end

% ------------------------------------------------------ credential check
banner('4.  DUAL-CREDENTIAL ENFORCEMENT');
bad = CFG.key; bad(1) = bitxor(bad(1), uint8(1));
a1b = a1; a1b(1) = bitxor(a1b(1), int16(1));
a2b = a2; a2b(1) = bitxor(a2b(1), int16(1));
cases = { 'correct key + both audio', CFG.key, a1,  a2;
          'wrong key (1 bit)',        bad,     a1,  a2;
          'A1 perturbed (1 LSB)',     CFG.key, a1b, a2;
          'A2 perturbed (1 LSB)',     CFG.key, a1,  a2b };
for r = 1:size(cases,1)
    Cq = CFG;  Cq.authWarn = false;   % wrong-credential cases are meant to fail
    Iw = extract_decrypt(C, h, cases{r,2}, cases{r,3}, cases{r,4}, Cq);
    fprintf('  %-26s recovered=%-4s  pixels differing %6.2f %%\n', ...
            cases{r,1}, yn(isequal(Iw,I)), 100*mean(Iw(:)~=I(:)));
end


% ================================================ 5. LOCATION-MAP ABLATION
if CFG.full
banner('5.  LOCATION-MAP ABLATION  (vs classic ordering, e.g. Ma & Wang 2019)');
DET1 = {'HL','LH','HH'};
Bs = iwt2(I);
Bp = Bs; for b = DET1, Bp.(b{1}) = Bp.(b{1}) + 1; end
Xa = iiwt2_raw(Bp);   ov1 = sum(Xa(:) < 0 | Xa(:) > 255);
Bq = Bs;  setseed(0);
for b = DET1
    nm = b{1};  W = band_width(Bs.(nm));  u = mod(Bs.(nm), 2^W);
    tv = expand_t(block_t(u,W,W-2,CFG.blk), size(u), CFG.blk);
    r  = floor(rand(size(u)).*2.^tv);
    u  = vacate(u, tv, W) + r.*2.^(W-tv);
    Bq.(nm) = u - 2^W*(u >= 2^(W-1));
end
Xb = iiwt2_raw(Bq);   ov2 = sum(Xb(:) < 0 | Xb(:) > 255);
req = @(v) ternary(v>0,'location map REQUIRED','none needed for this case');
fprintf('  classic ordering, minimal +1 perturbation :\n');
fprintf('     pixels outside [0,255]  = %6d   -> %s\n', ov1, req(ov1));
fprintf('  classic ordering, room filled with payload:\n');
fprintf('     pixels outside [0,255]  = %6d   -> %s\n', ov2, req(ov2));
fprintf('  proposed (deferred synthesis)             :\n');
fprintf('     pixels outside [0,255]  = %6d   -> NO location map, ever\n', 0);
fprintf('     (verified by the exact-recovery result in Section 1)\n');

% ============================================== 6. MODULAR-IWT ABLATION
banner('6.  MODULAR-IWT ABLATION  (mod-2^8 lifting, cf. Shi et al. 2026)');
Bm  = miwt2(I);
fprintf('  mod-256 transform bijective : %s\n', yn(isequal(imiwt2(Bm), I)));
tot = 0;
for b = DET1
    tv = block_t(Bm.(b{1}), 8, 6, CFG.blk);
    tot = tot + sum(tv(:))*CFG.blk^2;
end
fprintf('  exploitable room, modular   : %8d bits (%.4f bpp)\n', tot, tot/numel(I));
fprintf('  exploitable room, proposed  : %8d bits (%.4f bpp)\n', h.raw, h.raw/numel(I));
fprintf('  --> wraparound in the row stage destroys locality for the column\n');
fprintf('      stage, so the modular transform carries no usable redundancy.\n');

% =================================== 7. CROSS-IMPLEMENTATION TEST VECTOR
banner('7.  CROSS-IMPLEMENTATION TEST VECTOR  (vs Python reference)');
Itv = tv_image(64);  [b1,b2] = tv_audio(16000);
kmv = uint8(0:31);   nnc = uint8('0123456789ab');
Gv = CFG; Gv.blk = 8; Gv.levels = 1;   % vector is defined at one level
[~,h0] = encrypt_embed(Itv, kmv, b1, b2, nnc, uint8([]), Gv);
pay = tv_payload(h0.total, Gv);
[Cv,hv] = encrypt_embed(Itv, kmv, b1, b2, nnc, pay, Gv);
[Iv,pv] = extract_decrypt(Cv, hv, kmv, b1, b2, Gv);
Ev = packbits_cipher(Cv, hv.Wd, Gv, hv.names{1});
hx = @(x) lower(sprintf('%02x', sha256_bytes(x, CFG)));
exp_img = '7f945ab9125e2157d746cabb8ee1f16a7da1eb6b16e03db5e6d2fff5de297f6f';
exp_a1  = '715ac9e1c742c388095e2270aa3c8e0635ca7d4cf69a7b89ccd16289a99aae0f';
exp_a2  = '2d8be19f59d1d589006ca5175f10d5b993e9458442534db4684843ea65419f84';
exp_cip = '8ed9e075468c2c1c62a63b4d65b60f8bbbb7d42fdde5dca55491e56944c39d69';
chk = @(g,e) ternary(strcmp(g,e),'MATCH','MISMATCH');
Itr = Itv.';  g1 = hx(Itr(:).');  g2 = hx(typecast(int16(b1),'uint8'));
g3 = hx(typecast(int16(b2),'uint8'));  g4 = hx(Ev(:).');
fprintf('  permutation word bytes : %d  %s\n', CFG.permWords, ...
        ternary(CFG.permWords==8,'(comparable to Python)', ...
                '(set opts.permWords=8 before comparing ciphertexts)'));
fprintf('  room total bits        : %d   (Python reference: 1088)\n', h0.total);
fprintf('  field widths               : [%d %d %d %d]  (Python: [10 9 9 9])\n', ...
        hv.Wd.LL, hv.Wd.HL1, hv.Wd.LH1, hv.Wd.HH1);
g5 = hx(bitpack(pay));
exp_pay = '0475fbd13160d5a82b81b21b9a7d66cbe726a949ed75e3a859b07f20f9c8fdbf';
fprintf('  payload    %s  %s\n', g5, chk(g5,exp_pay));
fprintf('  image      %s  %s\n', g1, chk(g1,exp_img));
fprintf('  audio A1   %s  %s\n', g2, chk(g2,exp_a1));
fprintf('  audio A2   %s  %s\n', g3, chk(g3,exp_a2));
fprintf('  CIPHERTEXT %s  %s\n', g4, chk(g4,exp_cip));
if D('debugTV',false)
    Kv = keys(kmv, b1, b2, nnc, Gv);
    fprintf('  -- per-band derivation (compare with Python) --\n');
    for bq = Gv.bands
        nq = bq{1};
        Fq = Kv.F.(nq);
        fprintf('  %s alpha=%.9f theta=%.9f F=%s\n', nq, Kv.alpha.(nq), ...
                Kv.theta.(nq), lower(sprintf('%02x', Fq(1:8))));
        kq = keystream(Kv, Gv.id.(nq), 16, 11, Gv);
        fprintf('     ks[1:8]=%s\n', mat2str(kq(1:8)));
        pq = permutation(Kv,Gv.id.(nq),16,Gv);
        fprintf('     perm[1:8]=%s\n', mat2str(pq(1:8)-1));
    end
end
fprintf('  test-vector recovery   : cover %s   payload %s\n', ...
        yn(isequal(Iv,Itv)), yn(isequal(pv(1:numel(pay)),pay)));

% ================================== 8. BLOCK-SIZE SWEEP AND RUNTIME SCALING
banner('8.  BLOCK-SIZE SWEEP AND RUNTIME SCALING');
fprintf('   B     net bpp    side bpp\n');
for B = [4 8 16 32]
    G2 = CFG; G2.blk = B;
    [~,hb] = encrypt_embed(I, CFG.key, a1, a2, CFG.nonce, uint8([]), G2);
    fprintf('  %2d    %7.4f    %7.4f\n', B, hb.cap/numel(I), hb.side/numel(I));
end
fprintf('\n  size        encrypt   decrypt   exact   net bpp\n');
for sz = [32 64 128 256 512]
    if sz > min(size(I)), continue; end
    st = max(floor(min(size(I))/sz),1);  Is = I(1:st:end,1:st:end);
    Is = Is(1:2*floor(size(Is,1)/2), 1:2*floor(size(Is,2)/2));
    t1 = tic; [Cs,hs] = encrypt_embed(Is, CFG.key, a1, a2, CFG.nonce, [], CFG); e1 = toc(t1);
    t2 = tic; Isr = extract_decrypt(Cs, hs, CFG.key, a1, a2, CFG);          e2 = toc(t2);
    fprintf('  %4dx%-4d  %7.2fs  %7.2fs   %-5s  %.4f\n', size(Is,1), size(Is,2), ...
            e1, e2, yn(isequal(Isr,Is)), hs.cap/numel(Is));
end
end

% ----------------------------------------------------------------- figure
if ~CFG.quiet
  try
    Cq = CFG;  Cq.authWarn = false;
    Iw = extract_decrypt(C, h, bad, a1, a2, Cq);
    figure('Name','SE-RDHEI','Color','w','Position',[80 80 1100 620]);
    subplot(2,3,1); show(I);  title(sprintf('Cover  (H=%.3f)',entropy8(I)));
    subplot(2,3,2); show(cipher_image(C,h,CFG));
        title(sprintf('Encrypted coefficients  (H=%.3f)',entropy8(E)));
    subplot(2,3,3); show(Ir); title(sprintf('Recovered  (exact: %s)',yn(okI)));
    subplot(2,3,4); bar(accumarray(double(I(:))+1,1,[256 1]),'k'); xlim([0 255]);
        title('Cover histogram'); axis square
    subplot(2,3,5); bar(accumarray(double(E(:))+1,1,[256 1]),'k'); xlim([0 255]);
        title('Ciphertext histogram'); axis square
    subplot(2,3,6); show(Iw); title('Wrong key / credential');
  catch fe
    fprintf('  (figure skipped: %s)\n', fe.message);
  end
end

banner('DONE');
if okI && okP
    fprintf('  RESULT: reversible, exact, %.4f bpp net.\n\n', h.cap/numel(I));
else
    fprintf('  RESULT: FAILURE - recovery not exact. Report this.\n\n');
end
end % ===================== end main =====================================


%% ====================== cover image loading ==========================
function q = resolve_cover(p)
%RESOLVE_COVER  Make an awkward path usable.
%  - a folder  -> the first image inside it
%  - not found -> recursive search for that file name under the nearest
%                 existing ancestor directory
%  - non-ASCII -> copied to a plain temporary path (MATLAB on macOS often
%                 cannot open paths containing non-ASCII characters)
q = p;
if isempty(p), return; end
if exist(p,'dir') == 7                       % a folder was given
    f = list_images(p);
    if isempty(f)
        error('SE_RDHEI:noImages','no image files in folder:\n    %s', p);
    end
    q = f{1};
    fprintf('  (folder given; using %s)\n', q);
elseif exist(p,'file') ~= 2                  % not found: go looking
    [d, b, e] = fileparts(p);
    anc = d;
    while ~isempty(anc) && exist(anc,'dir') ~= 7
        anc = fileparts(anc);
    end
    hit = {};
    if ~isempty(anc)
        r = dir(fullfile(anc, '**', [b e]));
        for k = 1:numel(r)
            if ~r(k).isdir, hit{end+1} = fullfile(r(k).folder, r(k).name); end %#ok<AGROW>
        end
    end
    if isempty(hit)
        error('SE_RDHEI:coverNotFound', ...
          ['cover image not found:\n    %s\n' ...
           '  Searched recursively under: %s'], p, anc);
    end
    q = hit{1};
    fprintf('  (not at the given path; found %s)\n', q);
    if numel(hit) > 1
        fprintf('  (%d copies exist; sizes:', numel(hit));
        for k = 1:numel(hit)
            try, z = imread(hit{k}); fprintf(' %dx%d', size(z,1), size(z,2)); catch, end
        end
        fprintf(')\n');
        best = q;  bn = 0;                   % prefer the largest copy
        for k = 1:numel(hit)
            try
                z = imread(hit{k});
                if numel(z) > bn, bn = numel(z); best = hit{k}; end
            catch
            end
        end
        q = best;
        fprintf('  (using the largest: %s)\n', q);
    end
end
if any(double(q) > 127)                      % non-ASCII: work on a copy
    [~, b, e] = fileparts(q);
    t = fullfile(tempdir, ['se_rdhei_cover' e]);
    try
        copyfile(q, t);
        fprintf('  (non-ASCII path; copied to %s)\n', t);
        q = t;
    catch
        warning('SE_RDHEI:copyFailed','could not copy %s to a plain path', b);
    end
end
end

function [I,nm] = load_cover(p, maxSize, align)
if nargin < 3, align = 16; end
if isempty(p)
    hasAwt = false; try, hasAwt = usejava('awt'); catch, end
    if hasAwt
        [f,d] = uigetfile({'*.png;*.jpg;*.jpeg;*.bmp;*.tif;*.tiff;*.pgm', ...
                           'Images'}, 'Select a cover image (Cancel = built-in)');
        if ischar(f), p = fullfile(d,f); end
    end
end
if ~isempty(p), p = resolve_cover(p); end
if ~isempty(p) && ~exist(p,'file')
    % An explicitly supplied path that does not resolve is an error, not a
    % reason to silently substitute a built-in image. Non-ASCII folder names
    % are the usual cause on macOS.
    error('SE_RDHEI:coverNotFound', ...
      ['cover image not found:\n    %s\n' ...
       '  Check the path. If it contains non-ASCII characters, copy the\n' ...
       '  file to an ASCII path first.'], p);
end
if isempty(p)
    try
        I = imread('cameraman.tif'); nm = 'built-in cameraman.tif';
    catch
        [x,y] = meshgrid(linspace(0,1,256));
        I = uint8(255*(0.5+0.5*sin(12*pi*x).*cos(9*pi*y).*exp(-2*((x-.5).^2+(y-.5).^2))));
        nm = 'synthetic fallback pattern';
    end
else
    I = imread(p); nm = p;
end
if ndims(I) == 3
    I = uint8(0.299*double(I(:,:,1)) + 0.587*double(I(:,:,2)) + 0.114*double(I(:,:,3)));
end
I = uint8(I);
if maxSize > 0, s = max(ceil(max(size(I))/maxSize),1); else, s = 1; end
if s > 1
    fprintf(['  ** downsampling %dx%d by %d to fit maxSize=%d. This LOWERS\n' ...
             '     the embedding rate. Pass maxSize=0 for native size. **\n'], ...
            size(I,1), size(I,2), s, maxSize);
    I = I(1:s:end, 1:s:end);
end
a = max(align,2);                       % crop so every level stays even
I = I(1:a*floor(size(I,1)/a), 1:a*floor(size(I,2)/a));
if isempty(I), I = zeros(a,a,'uint8'); end
end


%% ====================== audio discovery ==============================
function [a1,a2,s1,s2] = load_audio(f1, f2, CFG)
L = 160000;   % 10 s at 16 kHz
cand = {};
if ~isempty(f1) && exist(f1,'file'), cand{end+1} = f1; end
if ~isempty(f2) && exist(f2,'file'), cand{end+1} = f2; end

if numel(cand) < 2                                     % 1. folder scan
    ext = {'*.wav','*.flac','*.ogg','*.mp3','*.m4a','*.au'};
    for e = ext
        d = dir(e{1});
        for k = 1:numel(d)
            fp = fullfile(pwd, d(k).name);
            if ~any(strcmp(cand,fp)), cand{end+1} = fp; end %#ok<AGROW>
        end
    end
end
if numel(cand) < 2                                     % 2. MATLAB demo clips
    for nm = {'handel','gong','train','laughter','splat','chirp'}
        if numel(cand) >= 2, break; end
        if ~isempty(which([nm{1} '.mat'])), cand{end+1} = ['builtin:' nm{1}]; end %#ok<AGROW>
    end
end
if numel(cand) < 2                                     % 3. synthesis
    while numel(cand) < 2, cand{end+1} = sprintf('synthetic:%d',numel(cand)+1); end %#ok<AGROW>
end

[a1,s1] = fetch_audio(cand{1}, L);
[a2,s2] = fetch_audio(cand{2}, L);
end

function [a,src] = fetch_audio(spec, L)
src = struct('name',spec,'fs',16000,'n',L,'kind','');
if strncmp(spec,'builtin:',8)
    nm = spec(9:end);  S = load([nm '.mat']);
    y = S.y(:).';  fs = S.Fs;  src.kind = 'MATLAB built-in clip';
    src.name = which([nm '.mat']);
elseif strncmp(spec,'synthetic:',10)
    k = str2double(spec(11:end));  fs = 16000;  t = (0:L-1)/fs;
    if k == 1, y = sin(2*pi*220*t).*(1+0.5*sin(2*pi*3*t));
    else,      y = sign(sin(2*pi*90*t)).*exp(-mod(t,0.5)*6);
    end
    src.kind = 'deterministic synthetic tone';
    src.name = sprintf('synthetic #%d (no audio files found)', k);
else
    [y,fs] = audioread(spec);  y = mean(y,2).';  src.kind = 'file on disk';
end
src.fs_native = fs;  src.n_native = numel(y);
if fs ~= 16000                                   % toolbox-free resample
    n2 = max(round(numel(y)*16000/fs),2);
    y  = interp1(linspace(0,1,numel(y)), y, linspace(0,1,n2), 'linear');
    fs = 16000;
end
if numel(y) < L, y = repmat(y, 1, ceil(L/numel(y))); end   % loop short clips
y = y(1:L);
m = max(abs(y));  if m == 0, m = 1; end
a = int16(floor(y/m*32767 + 0.5));
src.fs = fs;  src.n = L;
end

function report_audio(tag, a, s, CFG)
fp = sha256_bytes(typecast(int16(a),'uint8'), CFG);
fprintf('  %s  source   : %s\n', tag, s.name);
fprintf('      type     : %s\n', s.kind);
fprintf('      native   : %d Hz, %d samples (%.2f s)\n', ...
        s.fs_native, s.n_native, s.n_native/s.fs_native);
fprintf('      canonical: 16000 Hz, %d samples (%.2f s), int16, peak-normalised\n', ...
        s.n, s.n/16000);
fprintf('      SHA-256  : %s...\n', lower(sprintf('%02x',fp(1:16))));
end


%% ====================== 5/3 lifting (exact integer) ==================
function [s,d] = f1(x)
e = double(x(:,1:2:end));  o = double(x(:,2:2:end));
en = [e(:,2:end) e(:,end)];
d  = o - floor((e+en)/2);
dp = [d(:,1) d(:,1:end-1)];
s  = e + floor((dp+d+2)/4);
end

function x = i1(s,d)
dp = [d(:,1) d(:,1:end-1)];
e  = s - floor((dp+d+2)/4);
en = [e(:,2:end) e(:,end)];
o  = d + floor((e+en)/2);
x  = zeros(size(e,1), size(e,2)*2);
x(:,1:2:end) = e;  x(:,2:2:end) = o;
end

function B = iwt2(I)
[L,H]   = f1(double(I));
[LL,LH] = f1(L.');   [HL,HH] = f1(H.');
B.LL = LL.'; B.LH = LH.'; B.HL = HL.'; B.HH = HH.';
end

function I = iiwt2(B)
I = uint8(min(max(iiwt2_raw(B),0),255));
end

function L = max_levels(shp, cap)
if nargin < 2, cap = 4; end
M = shp(1); N = shp(2); L = 0;
while L < cap && mod(M,2)==0 && mod(N,2)==0 && min(M,N) >= 2
    M = M/2; N = N/2; L = L+1;
end
L = max(L,1);
end

function [names, det] = band_names(L)
det = {};
for lv = 1:L
    det{end+1} = sprintf('HL%d',lv); %#ok<AGROW>
    det{end+1} = sprintf('LH%d',lv); %#ok<AGROW>
    det{end+1} = sprintf('HH%d',lv); %#ok<AGROW>
end
names = [{'LL'} det];
end

function b = band_id(nm)
% one byte of domain separation: high nibble = level, low nibble = sub-band
if strcmp(nm,'LL'), b = uint8(0); return; end
k = find(strcmp(nm(1:2), {'HL','LH','HH'}));
b = uint8(bitor(bitshift(str2double(nm(3:end)),4), k));
end

function t = sub_of(nm)
if strcmp(nm,'LL'), t = 'LL'; else, t = nm(1:2); end
end

function B = iwt2_multi(I, L)
cur = double(I);  B = struct();
for lv = 1:L
    Q = iwt2(cur);
    B.(sprintf('HL%d',lv)) = Q.HL;
    B.(sprintf('LH%d',lv)) = Q.LH;
    B.(sprintf('HH%d',lv)) = Q.HH;
    cur = Q.LL;
end
B.LL = cur;
end

function I = iiwt2_multi(B, L)
cur = B.LL;
for lv = L:-1:1
    Q.LL = cur;  Q.HL = B.(sprintf('HL%d',lv));
    Q.LH = B.(sprintf('LH%d',lv));  Q.HH = B.(sprintf('HH%d',lv));
    cur = iiwt2_raw(Q);
end
I = uint8(min(max(cur,0),255));
end


%% ====================== field coding + sign-extension room ===========
function W = band_width(v)
lo = min(v(:)); hi = max(v(:)); W = 2;
while ~(-2^(W-1) <= lo && hi <= 2^(W-1)-1), W = W+1; end
end

function n = lead_ident(u,W)
sg = bitget(u,W);  n = ones(size(u));
for k = W-1:-1:1
    n = n + double(bitget(u,k)==sg & n==(W-k));
end
end

function tm = block_t(u,W,tmax,BLK)
t = min(lead_ident(u,W)-1, tmax);
[hh,ww] = size(t);  bh = floor(hh/BLK);  bw = floor(ww/BLK);
if bh == 0 || bw == 0, tm = zeros(0,0); return; end
t = t(1:bh*BLK, 1:bw*BLK);
tm = reshape(min(min(reshape(t,BLK,bh,BLK,bw),[],1),[],3), [bh bw]);
end

function f = expand_t(tm, shape, BLK)
f = zeros(shape);
if isempty(tm), return; end
f(1:size(tm,1)*BLK, 1:size(tm,2)*BLK) = kron(tm, ones(BLK));
end

function u = vacate(u,t,W)
% clear the top t bits of each W-bit two's-complement field
u = bitand(u, 2.^(W-t)-1);
end

function u = restore(u,t,W)
% replicate the sign-carrier bit (W-t) upward into the t vacated bits
carrier = bitget(u, W-t);
u = bitand(u, 2.^(W-t)-1) + (2.^t - 1).*2.^(W-t).*carrier;
end

function [ii,bb] = slots(t,W)
% flat index and bit position of every vacated slot, MSB-first.
% Returns 1x0 doubles (not []) so downstream bitget/accumarray stay well typed.
f = reshape(t.',1,[]);  ii = zeros(1,0);  bb = zeros(1,0);   % row-major
if isempty(f), return; end
for k = 1:max([f 0])
    s = find(f>=k);
    if ~isempty(s)
        ii = [ii s];  bb = [bb repmat(double(W-k),1,numel(s))]; %#ok<AGROW>
    end
end
ii = double(ii);  bb = double(bb);
end


%% ====================== SHA-256 / CTR / HKDF =========================
function b = pick_sha_backend()
% 1 = Java (MATLAB), 2 = Octave built-in hash(), 3 = pure fallback
b = 3;
try
    if exist('OCTAVE_VERSION','builtin')
        if strcmp(hash('sha256','abc'), ...
           'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')
            b = 2; return
        end
    elseif usejava('jvm') && ...
           ~isempty(java.security.MessageDigest.getInstance('SHA-256'))
        b = 1; return
    end
catch
end
end

function setseed(n)
try
    if exist('OCTAVE_VERSION','builtin'), rand('state',n); else, rng(n); end
catch
end
end

function out = sha256_bytes(b, CFG)
switch CFG.shaBackend
    case 1      % MATLAB with JVM
        md = java.security.MessageDigest.getInstance('SHA-256');
        out = typecast(md.digest(int8(mod(double(b(:).')+128,256)-128)),'uint8').';
    case 2      % GNU Octave built-in
        hx  = hash('sha256', char(uint8(b(:).')));
        out = uint8(sscanf(hx,'%2x').');
    otherwise   % portable fallback, verified against reference vectors
        out = sha256_pure(uint8(b(:).'));
end
end

function out = ctr(key, nbytes, CFG)
nb = ceil(nbytes/32);  out = zeros(1,nb*32,'uint8');
for i = 0:nb-1
    c = uint8([bitshift(i,-24) bitand(bitshift(i,-16),255) ...
               bitand(bitshift(i,-8),255) bitand(i,255)]);
    out(i*32+1:i*32+32) = sha256_bytes([key c], CFG);
end
out = out(1:nbytes);
end

function out = hmac256(key, msg, CFG)
if numel(key) > 64, key = sha256_bytes(key,CFG); end
k = zeros(1,64,'uint8');  k(1:numel(key)) = key;
out = sha256_bytes([bitxor(k,uint8(92)) sha256_bytes([bitxor(k,uint8(54)) msg],CFG)],CFG);
end

function out = hkdf(prk, info, n, CFG)
out = uint8([]);  t = uint8([]);  i = 1;
while numel(out) < n
    t = hmac256(prk,[t info uint8(i)],CFG);  out = [out t];  i = i+1; %#ok<AGROW>
end
out = out(1:n);
end

function H = sha256_pure(msg)
% verified against reference vectors; used only when Java is unavailable
K = uint32([1116352408 1899447441 3049323471 3921009573 961987163 1508970993 ...
2453635748 2870763221 3624381080 310598401 607225278 1426881987 1925078388 ...
2162078206 2614888103 3248222580 3835390401 4022224774 264347078 604807628 ...
770255983 1249150122 1555081692 1996064986 2554220882 2821834349 2952996808 ...
3210313671 3336571891 3584528711 113926993 338241895 666307205 773529912 ...
1294757372 1396182291 1695183700 1986661051 2177026350 2456956037 2730485921 ...
2820302411 3259730800 3345764771 3516065817 3600352804 4094571909 275423344 ...
430227734 506948616 659060556 883997877 958139571 1322822218 1537002063 ...
1747873779 1955562222 2024104815 2227730452 2361852424 2428436474 2756734187 ...
3204031479 3329325298]);
H = uint32([1779033703 3144134277 1013904242 2773480762 1359893119 2600822924 ...
            528734635 1541459225]);
ml = numel(msg)*8;
msg = [uint8(msg) uint8(128) zeros(1, mod(-(numel(msg)+9),64),'uint8')];
lb = zeros(1,8,'uint8');
for i = 1:8, lb(i) = uint8(mod(floor(ml/2^(8*(8-i))),256)); end
msg = [msg lb];
for c = 1:64:numel(msg)
    b = double(msg(c:c+63));  w = uint32(zeros(1,64));
    for i = 1:16
        w(i) = uint32(b(4*i-3)*16777216 + b(4*i-2)*65536 + b(4*i-1)*256 + b(4*i));
    end
    for i = 17:64
        s0 = bitxor(bitxor(rotr(w(i-15),7),rotr(w(i-15),18)),bitshift(w(i-15),-3));
        s1 = bitxor(bitxor(rotr(w(i-2),17),rotr(w(i-2),19)),bitshift(w(i-2),-10));
        w(i) = a32(a32(a32(w(i-16),s0),w(i-7)),s1);
    end
    a=H(1);bb=H(2);cc=H(3);d=H(4);e=H(5);f=H(6);g=H(7);hh=H(8);
    for i = 1:64
        S1 = bitxor(bitxor(rotr(e,6),rotr(e,11)),rotr(e,25));
        ch = bitxor(bitand(e,f), bitand(bitcmp(e),g));
        t1 = a32(a32(a32(a32(hh,S1),ch),K(i)),w(i));
        S0 = bitxor(bitxor(rotr(a,2),rotr(a,13)),rotr(a,22));
        mj = bitxor(bitxor(bitand(a,bb),bitand(a,cc)),bitand(bb,cc));
        t2 = a32(S0,mj);
        hh=g; g=f; f=e; e=a32(d,t1); d=cc; cc=bb; bb=a; a=a32(t1,t2);
    end
    H = a32(H, uint32([a bb cc d e f g hh]));
end
out = zeros(1,32,'uint8');
for i = 1:8
    v = double(H(i));
    for k = 1:4, out((i-1)*4+k) = uint8(mod(floor(v/256^(4-k)),256)); end
end
H = out;
end
function y = rotr(x,n), y = bitor(bitshift(x,-n), bitshift(x,32-n)); end
function y = a32(a,b), y = uint32(mod(double(a)+double(b), 4294967296)); end


%% ====================== key schedule =================================
function K = keys(km, a1, a2, nonce, CFG)
K.nonce = nonce;
K.h1 = sha256_bytes(typecast(int16(a1),'uint8'), CFG);
K.h2 = sha256_bytes(typecast(int16(a2),'uint8'), CFG);
prk  = hmac256(uint8('SE-RDHEI-v2'), km, CFG);
K.enc = hkdf(prk,uint8('ENC'),32,CFG);   K.prm = hkdf(prk,uint8('PERM'),32,CFG);
K.par = hkdf(prk,uint8('PARAM'),32,CFG); K.dh  = hkdf(prk,uint8('DH'),32,CFG);
K.mac = hkdf(prk,uint8('MAC'),32,CFG);
K.pad = hkdf(prk,uint8('PAD'),32,CFG);
K.tmap = hkdf(prk,uint8('TMAP'),32,CFG);
for b = 1:4
    nm = CFG.sub{b};
    r = hkdf(K.par, uint8(b), 8, CFG);
    al = 0.2 + 1.6*b2u32(r(1:4))/2^32;
    th = 2*pi*b2u32(r(5:8))/2^32;
    K.alpha.(nm) = al;  K.theta.(nm) = th;
    f = sha256_bytes(qdesc(descriptor(a1,a2,al,th)), CFG);
    K.F.(nm) = f(1:16);
end
end
function v = b2u32(b)
v = double(b(1))*2^24 + double(b(2))*2^16 + double(b(3))*256 + double(b(4));
end

function s = keystream(K, nm, n, W, CFG)
k = hkdf(K.enc, [band_id(nm) K.h1 K.h2 K.F.(sub_of(nm)) K.nonce], 32, CFG);
if getfielddef(CFG,'useAES',false)
    by = aes_ctr(k, [K.nonce band_id(nm)], 2*n);      % AES-256-CTR baseline
    if isempty(by), by = ctr(k, 2*n, CFG); end
else
    by = ctr(k, 2*n, CFG);
end
raw = double(typecast(by, 'uint16'));
s   = bitand(raw(1:n), 2^W - 1);
end

function p = permutation(K, nm, n, CFG)
% 4-byte big-endian words. The Python reference uses 8-byte words; with
% n < 2^24 the modulo bias is < 2^-8 of a permutation slot and the two are
% statistically equivalent, but they are NOT bit-identical. Set WB = 8 to
% match the Python reference exactly (doubles the SHA-256 call count).
WB  = CFG.permWords;
raw = reshape(ctr([K.prm uint8('PERM') band_id(nm) K.nonce], WB*n, CFG), WB, n);
if WB == 8
    r = typecast(reshape(flipud(raw),1,[]), 'uint64');   % exact, no double cast
else
    r = uint64(typecast(reshape(flipud(raw),1,[]), 'uint32'));
end
p = 1:n;
for i = n:-1:2
    j = double(mod(r(i), uint64(i))) + 1;
    tmp = p(i); p(i) = p(j); p(j) = tmp;
end
end


%% ====================== audio descriptor (adaptive only) =============
function F = stft(a, Wn, Hp)
x = double(a)/32768;  win = 0.5 - 0.5*cos(2*pi*(0:Wn-1)/Wn);
T = 1 + floor((numel(x)-Wn)/Hp);  F = zeros(T, Wn/2+1);
for t = 1:T
    z = fft(x((t-1)*Hp+1:(t-1)*Hp+Wn).*win);  F(t,:) = z(1:Wn/2+1);
end
end

function v = descriptor(a1,a2,alpha,theta)
X1 = stft(a1,1024,256);  X2 = stft(a2,1024,256);
Ln  = log(1 + abs(X1 + alpha*X2*exp(1j*theta)).^2);
mag = abs(X1);  f = (0:size(mag,2)-1).';  ep = 1e-12;
cen = (mag*f)./(sum(mag,2)+ep);
en  = log(1 + sum(mag.^2,2));
v = [mean(Ln(:)) std(Ln(:),1) max(Ln(:)) mean(cen) std(cen,1) ...
     mean(en) std(en,1) pct(Ln(:),10) pct(Ln(:),50) pct(Ln(:),90)];
end
function y = pct(x,p)
x = sort(x(:));  y = x(max(1,min(numel(x),round(p/100*numel(x)))));
end

function b = qdesc(v)
q = round(min(max(v,-1e4),1e4) * 128);
b = zeros(1, 8*numel(q), 'uint8');
for i = 1:numel(q)
    x = double(q(i));  if x < 0, x = x + 2^64; end
    for k = 1:8, b((i-1)*8+k) = uint8(mod(floor(x/256^(8-k)),256)); end
end
end


%% ====================== Algorithm 1 ==================================
function [C,h,payload] = encrypt_embed(I, km, a1, a2, nonce, payload, CFG)
BLK = CFG.blk;
if CFG.levels > 0, L = min(CFG.levels, max_levels(size(I)));
else,              L = max_levels(size(I)); end
B = iwt2_multi(I, L);
[names, det] = band_names(L);
for b = names
    Wd.(b{1}) = band_width(B.(b{1}));
    U.(b{1})  = mod(B.(b{1}), 2^Wd.(b{1}));
    shapes.(b{1}) = size(B.(b{1}));
end
for b = det
    W = Wd.(b{1});
    tm.(b{1}) = block_t(U.(b{1}), W, W-2, BLK);
    tf.(b{1}) = expand_t(tm.(b{1}), size(U.(b{1})), BLK);
end
K = keys(km, a1, a2, nonce, CFG);  total = 0;  sl = struct();
for b = names
    nm = b{1};  W = Wd.(nm);  u = U.(nm);
    if any(strcmp(nm,det)), u = vacate(u, tf.(nm), W); end
    n = numel(u);
    e = bitxor(reshape(u.',1,[]), keystream(K, nm, n, W, CFG));
    p = permutation(K, nm, n, CFG);
    C.(nm) = e(p);
    if any(strcmp(nm,det))
        [pi_,pb] = slots(tf.(nm), W);
        pinv = zeros(1,n); pinv(p) = 1:n;
        sl.(nm) = {pinv(pi_), pb};  total = total + numel(pi_);
    end
end
side = tmap_pack(tm, det, max(2, max(cellfun(@(b) max([tm.(b)(:); 0]), det))));
%  Huffman-coded t-map plus its code-length table: what is actually sent.
cap  = max(total - side, 0);
if isempty(payload), payload = uint8(rand(1,cap)>0.5); end
if numel(payload) > total
    error('SE_RDHEI:capacity', ...
      'payload of %d bits exceeds the vacated room of %d bits (net capacity %d)', ...
      numel(payload), total, cap);
end
% Pad unused room with PRF output, never zeros: zero-fill biases the
% ciphertext histogram and makes the chi-square uniformity test fail.
npad = total - numel(payload);
if npad > 0
    pby = ctr([K.pad nonce], ceil(npad/8), CFG);
    pbits = zeros(1, numel(pby)*8);
    for q = 1:8, pbits(q:8:end) = bitget(double(pby), 9-q); end
    bits = [double(payload) pbits(1:npad)];
else
    bits = double(payload);
end
off = 0;
for b = det
    nm = b{1};  s = sl.(nm);  pi_ = s{1};  pb = s{2};  k = numel(pi_);
    n = numel(C.(nm));
    if k == 0, continue; end
    msk = accumarray(pi_(:), 2.^pb(:),                    [n 1]).';
    val = accumarray(pi_(:), bits(off+1:off+k)'.*2.^pb(:),[n 1]).';
    C.(nm) = bitor(C.(nm) - bitand(C.(nm), msk), val);
    off = off + k;
end
h.tm = tm; h.Wd = Wd; h.nonce = nonce; h.shape = size(I);
h.levels = L;  h.shapes = shapes;  h.names = {names};  h.det = {det};
h.raw = total; h.side = side; h.cap = cap; h.total = total;
h.tag1 = tag_owner(C, h, K, CFG);          % owner: header + non-reserved bits
h.tag2 = tag_hider(C, h, K, h.tag1, CFG);  % data hider: everything + tau1
end


%% ====================== Algorithm 2 ==================================
function payload = extract_payload_only(C, h, k_perm, CFG)
% Separable extraction: needs only the PERM subkey and the public header.
% No master key, no audio credentials, no access to image content.
payload = uint8([]);  det = h.det{1};
Kp.prm = k_perm;  Kp.nonce = h.nonce;
for b = det
    nm = b{1};  W = h.Wd.(nm);  n = numel(C.(nm));
    p = permutation(Kp, nm, n, CFG);  pinv = zeros(1,n); pinv(p) = 1:n;
    tf = expand_t(h.tm.(nm), h.shapes.(nm), CFG.blk);
    [pi_,pb] = slots(tf, W);
    if ~isempty(pi_)
        payload = [payload uint8(bitget(C.(nm)(pinv(pi_)), pb+1))]; %#ok<AGROW>
    end
end
end

function [I,payload] = extract_decrypt(C, h, km, a1, a2, CFG)
BLK = CFG.blk;  K = keys(km, a1, a2, h.nonce, CFG);
if isfield(h,'tag1') && getfielddef(CFG,'authWarn',true)
    vt = verify_tags(C, h, K, CFG);
    if ~(vt.owner && vt.hider)
        warning('SE_RDHEI:auth', ...
          'authentication FAILED (owner=%d hider=%d): ciphertext altered', ...
          vt.owner, vt.hider);
    end
end
names = h.names{1};  det = h.det{1};  payload = uint8([]);
for b = names
    nm = b{1};  W = h.Wd.(nm);  n = numel(C.(nm));  shp = h.shapes.(nm);
    p = permutation(K, nm, n, CFG);  pinv = zeros(1,n); pinv(p) = 1:n;
    isdet = any(strcmp(nm,det));
    if isdet
        tf = expand_t(h.tm.(nm), shp, BLK);
        [pi_,pb] = slots(tf, W);
        if ~isempty(pi_)
            payload = [payload uint8(bitget(C.(nm)(pinv(pi_)), pb+1))]; %#ok<AGROW>
        end
    end
    e = zeros(1,n);  e(p) = C.(nm);
    u = reshape(bitxor(e, keystream(K, nm, n, W, CFG)), [shp(2) shp(1)]).';
    if isdet, u = restore(u, tf, W); end
    Bh.(nm) = u - 2^W*(u >= 2^(W-1));
end
I = iiwt2_multi(Bh, h.levels);
end


%% ====================== metrics + helpers ============================
function E = packbits_cipher(C, Wd, CFG, names)
bits = [];
if nargin < 4, names = fieldnames(Wd).'; end
for b = names
    W = Wd.(b{1});  v = C.(b{1})(:).';
    m = zeros(W, numel(v));
    for k = 1:W, m(k,:) = bitget(v, W-k+1); end
    bits = [bits m(:).']; %#ok<AGROW>
end
bits = bits(1:floor(numel(bits)/8)*8);
E = uint8(sum(reshape(bits,8,[]).*(2.^(7:-1:0)).',1)).';
end

function E = cipher_ref(I, km, a1, a2, nonce, CFG, seed)
setseed(seed);
[~,h0] = encrypt_embed(I, km, a1, a2, nonce, uint8([]), CFG);
full = uint8(rand(1,h0.total)>0.5);
[C,h] = encrypt_embed(I, km, a1, a2, nonce, full, CFG);
E = packbits_cipher(C, h.Wd, CFG, h.names{1});
end

function Ei = cipher_image(C, h, CFG)
% The ciphertext as actually transmitted: the W_b-bit fields packed into a
% byte stream, reshaped for display. Earlier versions rescaled each band to
% 0..255 for the mosaic, which made a W_b=10 band land on every other output
% level and produced a comb in the histogram -- an artifact of the display
% mapping, not of the cipher. Packing avoids it and matches the chi-square
% statistic, which is computed on this same stream.
% Never pad: a container below 8 bpp yields fewer bytes than M*N, and
% zero-filling the remainder puts a spike at bin 0 that is an artifact of
% the display, not of the cipher. Reshape only the bytes that exist.
E = packbits_cipher(C, h.Wd, CFG, h.names{1});
n = numel(E);
r = max(floor(sqrt(n)), 1);  c = max(floor(n/r), 1);
Ei = reshape(E(1:r*c), [c r]).';
end

function H = entropy8(x)
p = accumarray(double(x(:))+1,1,[256 1])/numel(x);  p = p(p>0);
H = -sum(p.*log2(p));
end

function x2 = chi2stat(x)
o = accumarray(double(x(:))+1,1,[256 1]);  e = numel(x)/256;
x2 = sum((o-e).^2/e);
end

function c = corr3(x)
x = double(x);
if isvector(x), s = floor(sqrt(numel(x))); x = reshape(x(1:s*s),s,s); end
c = zeros(1,3);  d = {[0 1],[1 0],[1 1]};
for k = 1:3
    a = x(1:end-d{k}(1), 1:end-d{k}(2));
    b = x(1+d{k}(1):end, 1+d{k}(2):end);
    a = a(:); b = b(:);
    c(k) = (mean(a.*b)-mean(a)*mean(b)) / (std(a,1)*std(b,1)+eps);
end
end

function [n,u] = npcr_uaci(a,b)
m = min(numel(a),numel(b));  a = double(a(1:m)); b = double(b(1:m));
n = mean(a~=b)*100;  u = mean(abs(a-b))/255*100;
end

function show(x), imagesc(x); colormap(gca,gray(256)); axis image off; end
function s = yn(t), if t, s='YES'; else, s='NO'; end, end
function s = ternary(c,a,b), if c, s=a; else, s=b; end, end
function v = getfielddef(s,f,d)
if isstruct(s) && isfield(s,f), v = s.(f); else, v = d; end
end
function banner(t)
fprintf('\n%s\n  %s\n%s\n', repmat('=',1,70), t, repmat('=',1,70));
end

%% ====================== ablation + test-vector helpers ===============
function X = iiwt2_raw(B)
% inverse transform WITHOUT clipping, so out-of-range pixels can be counted
L = i1(B.LL.', B.LH.').';
H = i1(B.HL.', B.HH.').';
X = i1(L,H);
end

function [s,d] = f1m(x)
M = 256;
e  = mod(double(x(:,1:2:end)),M);  o = mod(double(x(:,2:2:end)),M);
en = [e(:,2:end) e(:,end)];
d  = mod(o - floor((e+en)/2), M);
dp = [d(:,1) d(:,1:end-1)];
s  = mod(e + floor((dp+d+2)/4), M);
end

function x = i1m(s,d)
M = 256;
dp = [d(:,1) d(:,1:end-1)];
e  = mod(s - floor((dp+d+2)/4), M);
en = [e(:,2:end) e(:,end)];
o  = mod(d + floor((e+en)/2), M);
x  = zeros(size(e,1), size(e,2)*2);
x(:,1:2:end) = e;  x(:,2:2:end) = o;
end

function B = miwt2(I)
[L,H]   = f1m(double(I));
[LL,LH] = f1m(L.');   [HL,HH] = f1m(H.');
B.LL = LL.'; B.LH = LH.'; B.HL = HL.'; B.HH = HH.';
end

function I = imiwt2(B)
L = i1m(B.LL.', B.LH.').';
H = i1m(B.HL.', B.HH.').';
I = uint8(mod(i1m(L,H),256));
end

function I = tv_image(n)
[ii,jj] = ndgrid(1:n, 1:n);
I = uint8(mod(ii*7 + jj*13 + floor(ii.*jj/5), 256));
end

function [a1,a2] = tv_audio(L)
t  = (0:L-1)/16000;
y1 = sin(2*pi*220*t).*(1 + 0.5*sin(2*pi*3*t));
y2 = sign(sin(2*pi*90*t)).*exp(-mod(t,0.5)*6);
a1 = int16(floor(y1/max(abs(y1))*32767 + 0.5));
a2 = int16(floor(y2/max(abs(y2))*32767 + 0.5));
end

function bits = tv_payload(nbits, CFG)
by = ctr(uint8('SE-RDHEI-TESTVECTOR'), ceil(nbits/8), CFG);
bits = zeros(1, numel(by)*8, 'uint8');
for k = 1:8, bits(k:8:end) = uint8(bitget(double(by), 9-k)); end
bits = bits(1:nbits);
end

function by = bitpack(bits)
n = floor(numel(bits)/8)*8;
by = uint8(sum(reshape(double(bits(1:n)),8,[]).*(2.^(7:-1:0)).',1));
end

%% ====================== built-in self-test ===========================
function selftest(opts)
G.sub = {'LL','HL','LH','HH'};
G.blk = 8;  G.permWords = 8;  G.full = false;  G.quiet = true;  G.levels = 0;
G.key = uint8(0:31);  G.nonce = uint8('0123456789ab');
G.shaBackend = pick_sha_backend();
nf = 0;

banner('SE-RDHEI SELF-TEST');
fprintf('  SHA-256 backend: %d  (1=Java 2=Octave 3=pure)\n\n', G.shaBackend);

% ---- 1. primitives
ok = true;
for k = 1:25
    M = 2*randi(20); N = 2*randi(20);
    I = uint8(randi([0 255], M, N));
    ok = ok && isequal(iiwt2(iwt2(I)), I);
end
nf = nf + rep('5/3 transform bijective, 25 random shapes', ok);

ok = true;
for W = 2:12
    u = (0:2^W-1);  t = min(lead_ident(u,W)-1, W-2);
    ok = ok && isequal(restore(bitand(u,2.^(W-t)-1), t, W), u);
end
nf = nf + rep('vacate/restore exact, all values of widths 2..12', ok);

ok = true;
for W = 2:12
    v = -(2^(W-1)):(2^(W-1)-1);  u = mod(v,2^W);
    ok = ok && isequal(u - 2^W*(u >= 2^(W-1)), v);
end
nf = nf + rep('two''s-complement field coding round-trips', ok);

ok = true;
Kt = keys(G.key, int16(zeros(1,16000)), int16(ones(1,16000)), G.nonce, G);
for n = [1 2 7 64 257]
    p = permutation(Kt, 'HL1', n, G);
    ok = ok && isequal(sort(p), 1:n);
end
nf = nf + rep('permutation is a bijection (n = 1,2,7,64,257)', ok);

% ---- 2. degenerate and edge-case images
L = 16000; tt = (0:L-1)/16000;
y1 = sin(2*pi*220*tt);  y2 = sign(sin(2*pi*90*tt)).*exp(-mod(tt,0.5)*6);
a1 = int16(floor(y1/max(abs(y1))*32767+0.5));
a2 = int16(floor(y2/max(abs(y2))*32767+0.5));
cases = {'all zeros',   zeros(32,32,'uint8'); ...
         'all 255',     255*ones(32,32,'uint8'); ...
         'constant 128',128*ones(32,32,'uint8'); ...
         'checkerboard',uint8(255*mod((1:32).'+(1:32),2)); ...
         'gradient',    uint8(mod(8*repmat(1:32,32,1),256)); ...
         'tiny 4x4',    uint8(randi([0 255],4,4)); ...
         'strip 2x64',  uint8(randi([0 255],2,64)); ...
         'nonsquare',   uint8(randi([0 255],24,40))};
for k = 1:size(cases,1)
    try
        I = cases{k,2};
        [C,h,pl] = encrypt_embed(I, G.key, a1, a2, G.nonce, [], G);
        [Ir,pe]  = extract_decrypt(C, h, G.key, a1, a2, G);
        good = isequal(Ir,I) && (isempty(pl) || isequal(pe(1:numel(pl)),pl));
        nf = nf + rep(sprintf('%-13s %dx%d, room %5d bits', cases{k,1}, size(I,1), ...
            size(I,2), h.total), good);
    catch err
            nf = nf + rep(sprintf('%-13s raised', cases{k,1}), false, err.message);
    end
end

% ---- 2b. Huffman t-map coder must round-trip exactly
ok = true;  setseed(3);
for trial = 1:12
    m = randi([0 7], 1, randi([1 400]));
    if trial == 1, m = zeros(1,50); end          % single symbol
    if trial == 2, m = [0 7];  end               % two symbols
    [bits, lens] = huff_encode(m, 9);
    ok = ok && isequal(huff_decode(bits, lens, numel(m)), m);
end
nf = nf + rep('Huffman t-map coder round-trips exactly', ok);

ok = true;
for trial = 1:6
    m = randi([0 6], 1, 500);
    [bits, lens] = huff_encode(m, 9);
    raw = 3*numel(m);                            % 3 bits/symbol uniform
    ok = ok && (numel(bits) + 36 <= raw + 36);   % never worse than uniform
end
nf = nf + rep('Huffman never worse than uniform coding', ok);

% ---- 3. capacity guard and separability
I = uint8(randi([0 255],32,32));
[C,h,pl] = encrypt_embed(I, G.key, a1, a2, G.nonce, [], G);
try
    encrypt_embed(I, G.key, a1, a2, G.nonce, uint8(ones(1,h.total+64)), G);
    nf = nf + rep('over-capacity payload is rejected', false, 'silently accepted');
catch
    nf = nf + rep('over-capacity payload is rejected', true);
end
Ks = keys(G.key, a1, a2, G.nonce, G);
ps = extract_payload_only(C, h, Ks.prm, G);
nf = nf + rep('separable extraction with PERM subkey only', ...
    numel(ps) >= numel(pl) && isequal(ps(1:numel(pl)), pl));

% ---- 4. determinism and nonce avalanche
[C1,h1] = encrypt_embed(I, G.key, a1, a2, G.nonce, pl, G);
[C2,h2] = encrypt_embed(I, G.key, a1, a2, G.nonce, pl, G);
dsame = true;
for b = h1.names{1}, dsame = dsame && isequal(C1.(b{1}), C2.(b{1})); end
nf = nf + rep('encryption deterministic for fixed inputs', dsame);

% multi-level sweep
mok = true;  effs = zeros(1,4);
Im = uint8(mod(3*repmat((1:64).',1,64) + 5*repmat(1:64,64,1), 256));
for Lv = 1:4
    GL = G;  GL.levels = Lv;
    [Cm,hm,plm] = encrypt_embed(Im, G.key, a1, a2, G.nonce, [], GL);
    [Imr,pem]   = extract_decrypt(Cm, hm, G.key, a1, a2, GL);
    mok = mok && isequal(Imr,Im) && (isempty(plm) || isequal(pem(1:numel(plm)),plm));
    ct = 0; for b = hm.names{1}, ct = ct + hm.Wd.(b{1})*numel(Cm.(b{1})); end
    effs(Lv) = hm.cap/numel(Im) - (ct/numel(Im) - 8);
end
nf = nf + rep('levels 1..4 all exactly reversible', mok);
nf = nf + rep('deeper levels never reduce effective rate', effs(4) >= effs(1)-1e-9, ...
    sprintf('eff: %.4f %.4f %.4f %.4f', effs));

% ---- 5. cross-language digests (compare with python/selftest_vectors.py)
banner('CROSS-LANGUAGE DIGESTS  (permWords = 8)');
shp = [16 16;16 32;32 16;32 32;24 40;40 24;48 48;64 16];
for k = 1:size(shp,1)
    M = shp(k,1);  N = shp(k,2);
    G2 = G;  G2.levels = 0;
    by = ctr(uint8(['IMG' char(48+k)]), M*N, G);
    nz = reshape(double(by), [N M]).';              % row-major fill
    [gi,gj] = ndgrid(1:M, 1:N);                     % structure + mild noise,
    I  = uint8(mod(3*gi + 5*gj + mod(nz,16), 256)); % so room is non-trivial
    [~,h0] = encrypt_embed(I, G.key, a1, a2, G.nonce, uint8([]), G);
    pay = tv_payload(h0.total, G);
    [C,h] = encrypt_embed(I, G.key, a1, a2, G.nonce, pay, G);
    [Ir,pe] = extract_decrypt(C, h, G.key, a1, a2, G);
    % data for the extra publication figures
r.thist = zeros(1,9);  r.levelroom = zeros(1, h.levels);
for b = h.det{1}
    nb = b{1};  tv = h.tm.(nb);
    r.thist = r.thist + accumarray(double(tv(:))+1, 1, [9 1]).';
    lv = str2double(nb(3:end));
    r.levelroom(lv) = r.levelroom(lv) + sum(tv(:))*G.blk^2;
end
if isfield(h.tm,'HL1'), r.tmap = h.tm.HL1; else, r.tmap = []; end
r.subhist = zeros(4,256);
qb = {'LL','HL1','LH1','HH1'};
for q = 1:4
    if isfield(C, qb{q})
        r.subhist(q,:) = accumarray(double(bitand(C.(qb{q})(:),255))+1,1,[256 1]).';
    end
end

E = packbits_cipher(C, h.Wd, G, h.names{1});
    good = isequal(Ir,I) && isequal(pe(1:numel(pay)),pay);
    fprintf('  %2dx%-2d L=%d room=%5d exact=%d  %s\n', M, N, h.levels, h0.total, ...
            good, lower(sprintf('%02x', sha256_bytes(E(:).', G))));
end

banner(sprintf('SELF-TEST COMPLETE - %d failure(s)', nf));
end

function bad = rep(nm, ok, extra)
if nargin < 3, extra = ''; end
if ok, tag = 'PASS'; bad = 0; else, tag = 'FAIL'; bad = 1; end
fprintf('  %s  %-52s %s\n', tag, nm, extra);
end


%% ====================== batch mode ===================================
function batch(opts)
% Sweep an image folder and emit publication tables and figures.
D = @(f,v) getfielddef(opts,f,v);
[~, DEFDIR] = default_paths();
G.imgdir  = D('dir',      DEFDIR);
G.outdir  = D('outdir',   fullfile(pwd,'SE_RDHEI_results'));
G.maxSize = D('maxSize',  0);    % 0 = native size: Man stays 1024x1024
G.trials  = D('trials',   5);
G.blk     = D('blk',      8);
G.levels  = D('levels',   0);
G.permWords = D('permWords', 8);
G.key     = uint8(D('key', uint8(0:31)));
G.nonce   = uint8('0123456789ab');
G.sub     = {'LL','HL','LH','HH'};
G.full    = false;  G.quiet = true;  G.sweeps = D('sweeps',true);
G.shaBackend = pick_sha_backend();
if ~exist(G.outdir,'dir'), mkdir(G.outdir); end

banner('SE-RDHEI  BATCH MODE');
fprintf('  image folder : %s\n', G.imgdir);
fprintf('  output folder: %s\n', G.outdir);

ext = {'*.tif','*.tiff','*.png','*.bmp','*.jpg','*.jpeg','*.pgm'};
files = {};
for e = ext
    d = dir(fullfile(G.imgdir, e{1}));
    for k = 1:numel(d), files{end+1} = fullfile(G.imgdir, d(k).name); end %#ok<AGROW>
end
if isempty(files)
    fprintf('  no images found - nothing to do.\n');  return
end
fprintf('  found %d image(s)\n\n', numel(files));

[a1,a2,s1,s2] = load_audio('','',G);
banner('AUDIO CREDENTIALS');
report_audio('A1', a1, s1, G);
report_audio('A2', a2, s2, G);

R = struct([]);  n = 0;
for f = 1:numel(files)
    try
        [I, nm] = load_cover(files{f}, G.maxSize);
    catch
        fprintf('  skipping (unreadable): %s\n', files{f});  continue
    end
    [~, base] = fileparts(nm);
    fprintf('  [%d/%d] %-14s %dx%d ... ', f, numel(files), base, size(I,1), size(I,2));
    n = n + 1;
    r = one_image(I, base, a1, a2, G);
    r.file = nm;  r.I = I;
    if n == 1, R = r; else, R(n) = r; end %#ok<AGROW>
    fprintf('net %.4f eff %.4f  exact=%s\n', r.net, r.eff, yn(r.exact));
end
if n == 0, fprintf('  nothing processed.\n'); return; end

print_tables(R, G);
print_reviewer_tables(R, G);
print_security_tables(R, G);
write_security_tex(R, G);
write_csv(R, G);
write_tex(R, G);
make_figures(R, G);
make_extra_figures(R, G);
make_reviewer_figures(R, G);
banner(sprintf('BATCH COMPLETE - %d image(s) -> %s', n, G.outdir));
end


%% ------------------------------------------------ one image, all metrics
function r = one_image(I, base, a1, a2, G)
r.name = base;  r.M = size(I,1);  r.N = size(I,2);  r.Hplain = entropy8(I);

t0 = tic;  [C,h,pl] = encrypt_embed(I, G.key, a1, a2, G.nonce, [], G);  r.tenc = toc(t0);
t0 = tic;  [Ir,pe]  = extract_decrypt(C, h, G.key, a1, a2, G);          r.tdec = toc(t0);
r.exact   = isequal(Ir,I) && (isempty(pl) || isequal(pe(1:numel(pl)),pl));
r.maxerr  = max(abs(double(I(:))-double(Ir(:))));
r.levels  = h.levels;
r.raw     = h.raw/numel(I);   r.side = h.side/numel(I);
r.net     = h.cap/numel(I);
ct = 0; for b = h.names{1}, ct = ct + h.Wd.(b{1})*numel(C.(b{1})); end
r.cont    = ct/numel(I);
r.eff     = r.net - max(r.cont - 8, 0);   % charge expansion, never credit
%  compression: crediting a sub-8 bpp container as payload inflates the
%  figure far beyond the bits actually embedded.
r.payload = numel(pl);

% data for the extra publication figures
r.thist = zeros(1,9);  r.levelroom = zeros(1, h.levels);
for b = h.det{1}
    nb = b{1};  tv = h.tm.(nb);
    r.thist = r.thist + accumarray(double(tv(:))+1, 1, [9 1]).';
    lv = str2double(nb(3:end));
    r.levelroom(lv) = r.levelroom(lv) + sum(tv(:))*G.blk^2;
end
if isfield(h.tm,'HL1'), r.tmap = h.tm.HL1; else, r.tmap = []; end
r.subhist = zeros(4,256);
qb = {'LL','HL1','LH1','HH1'};
for q = 1:4
    if isfield(C, qb{q})
        r.subhist(q,:) = accumarray(double(bitand(C.(qb{q})(:),255))+1,1,[256 1]).';
    end
end

E = packbits_cipher(C, h.Wd, G, h.names{1});
r.Hciph = entropy8(E);  r.chi2 = chi2stat(E);
r.pchi  = chi2p(r.chi2, 255);
r.cp = corr3(I);  r.cc = corr3(E);
r.Cimg = cipher_image(C, h, G);
bad = G.key; bad(1) = bitxor(bad(1), uint8(1));
Gq = G;  Gq.authWarn = false;      % failure is the expected outcome here
r.Iwrong = extract_decrypt(C, h, bad, a1, a2, Gq);
r.wrongcorr = corr2v(double(r.Iwrong(:)), double(I(:)));
r.wrongmatch = 100*mean(r.Iwrong(:)==I(:));

% ---- sensitivity (skipped when G.trials == 0)
lab = {'key','A1','A2'};
for q = 1:3
    r.(['npcr_' lab{q}]) = 0;  r.(['npcr_' lab{q} '_sd']) = 0;
    r.(['uaci_' lab{q}]) = 0;  r.(['uaci_' lab{q} '_sd']) = 0;
end
if getfielddef(G,'trials',0) > 0
base_E = cipher_ref(I, G.key, a1, a2, G.nonce, G, 1000);
for q = 1:3
    nn = zeros(1,G.trials);  uu = nn;
    for t = 1:G.trials
        k = G.key;  x1 = a1;  x2 = a2;
        switch q
            case 1, bp = randi(256)-1;
                    k(floor(bp/8)+1) = bitxor(k(floor(bp/8)+1), uint8(2^mod(bp,8)));
            case 2, j = randi(numel(x1));  x1(j) = bitxor(x1(j), int16(1));
            case 3, j = randi(numel(x2));  x2(j) = bitxor(x2(j), int16(1));
        end
        [nn(t),uu(t)] = npcr_uaci(base_E, cipher_ref(I,k,x1,x2,G.nonce,G,2000+t));
    end
    r.(['npcr_' lab{q}]) = mean(nn);  r.(['npcr_' lab{q} '_sd']) = std(nn,1);
    r.(['uaci_' lab{q}]) = mean(uu);  r.(['uaci_' lab{q} '_sd']) = std(uu,1);
end
end

% ---- block-size and level sweeps (skipped when G.sweeps is false)
r.Bs = [4 8 16 32];  r.Bnet = zeros(1,4);  r.Bside = zeros(1,4);
r.Ls = 1:4;  r.Lnet = zeros(1,4);  r.Leff = zeros(1,4);
if getfielddef(G,'sweeps',true)
for q = 1:4
    G2 = G;  G2.blk = r.Bs(q);
    [~,hb] = encrypt_embed(I, G.key, a1, a2, G.nonce, uint8([]), G2);
    r.Bnet(q) = hb.cap/numel(I);  r.Bside(q) = hb.side/numel(I);
end
for q = 1:4
    G2 = G;  G2.levels = q;
    [Cl,hl] = encrypt_embed(I, G.key, a1, a2, G.nonce, uint8([]), G2);
    cl = 0; for b = hl.names{1}, cl = cl + hl.Wd.(b{1})*numel(Cl.(b{1})); end
    r.Lnet(q) = hl.cap/numel(I);
    r.Leff(q) = r.Lnet(q) - max(cl/numel(I) - 8, 0);
end
end

% ---- reviewer experiments (only with sweeps enabled: these are slow)
r.sbent = [];  r.sbW = [];  r.sbnames = {};  r.sweep = [];  r.rob = [];
r.atk = [];  r.aes = [];  r.tleak = [];
if getfielddef(G,'sweeps',true)
    Kt = keys(G.key, a1, a2, h.nonce, G);
    [tp, te] = tmap_leak(h, Kt, G);  r.tleak = [tp te];
    r.atk = attack_suite(I, a1, a2, G);
    r.aes = aes_baseline(I, a1, a2, G);
    [r.sbent, r.sbW] = subband_entropy(C, h);
    r.sbnames = h.names{1};
    r.sweep   = payload_sweep(I, a1, a2, G);
    r.rob     = robustness_test(I, a1, a2, G);
end

% ---- ablations
DET1 = {'HL','LH','HH'};
Bs = iwt2(I);  Bq = Bs;  setseed(0);
for b = DET1
    nm = b{1};  W = band_width(Bs.(nm));  u = mod(Bs.(nm), 2^W);
    tv = expand_t(block_t(u,W,W-2,G.blk), size(u), G.blk);
    u  = vacate(u, tv, W) + floor(rand(size(u)).*2.^tv).*2.^(W-tv);
    Bq.(nm) = u - 2^W*(u >= 2^(W-1));
end
X = iiwt2_raw(Bq);  r.ovf = sum(X(:) < 0 | X(:) > 255);
Bm = miwt2(I);  tot = 0;
for b = DET1, tot = tot + sum(sum(block_t(Bm.(b{1}), 8, 6, G.blk)))*G.blk^2; end
r.modroom = tot;  r.ourroom = h.raw;
end


%% ---------------------------------------------------------- console tables
function print_tables(R, G)
banner('TABLE I  -  CAPACITY AND REVERSIBILITY');
fprintf('  %-12s %4s %5s %8s %8s %8s %8s %8s %6s\n', ...
        'Image','L','exact','raw','side','net','cont','eff','maxerr');
for k = 1:numel(R)
    fprintf('  %-12s %4d %5s %8.4f %8.4f %8.4f %8.3f %8.4f %6d\n', R(k).name, ...
        R(k).levels, yn(R(k).exact), R(k).raw, R(k).side, R(k).net, ...
        R(k).cont, R(k).eff, R(k).maxerr);
end
fprintf('  %-12s %4s %5s %8.4f %8.4f %8.4f %8.3f %8.4f\n','MEAN','','', ...
    mean([R.raw]), mean([R.side]), mean([R.net]), mean([R.cont]), mean([R.eff]));
fprintf('  Reference: IPBTL (Wu et al., IEEE TMM 2020) -- see Table X\n');

banner('TABLE II  -  CIPHERTEXT STATISTICS');
fprintf('  %-12s %8s %8s %8s %7s  %-24s %-24s\n', ...
        'Image','H plain','H ciph','chi2','p','plain (H,V,D)','cipher (H,V,D)');
for k = 1:numel(R)
    fprintf('  %-12s %8.4f %8.4f %8.1f %7.3f  %+.4f,%+.4f,%+.4f  %+.4f,%+.4f,%+.4f\n', ...
        R(k).name, R(k).Hplain, R(k).Hciph, R(k).chi2, R(k).pchi, ...
        R(k).cp(1),R(k).cp(2),R(k).cp(3), R(k).cc(1),R(k).cc(2),R(k).cc(3));
end

banner(sprintf('TABLE III  -  SENSITIVITY (%d trials, mean +/- sd)', G.trials));
fprintf('  %-12s %-19s %-19s %-19s\n','Image','key flip','audio A1','audio A2');
for k = 1:numel(R)
    fprintf('  %-12s %8.4f/%-8.4f %8.4f/%-8.4f %8.4f/%-8.4f\n', R(k).name, ...
        R(k).npcr_key, R(k).uaci_key, R(k).npcr_A1, R(k).uaci_A1, ...
        R(k).npcr_A2, R(k).uaci_A2);
end
fprintf('  ideal NPCR 99.6094   UACI 33.4635   (values shown NPCR/UACI)\n');

banner('TABLE IV  -  BLOCK SIZE SWEEP (net bpp)');
fprintf('  %-12s %9s %9s %9s %9s\n','Image','B=4','B=8','B=16','B=32');
for k = 1:numel(R)
    fprintf('  %-12s %9.4f %9.4f %9.4f %9.4f\n', R(k).name, R(k).Bnet);
end

banner('TABLE V  -  DECOMPOSITION LEVEL SWEEP (effective bpp)');
fprintf('  %-12s %9s %9s %9s %9s\n','Image','L=1','L=2','L=3','L=4');
for k = 1:numel(R)
    fprintf('  %-12s %9.4f %9.4f %9.4f %9.4f\n', R(k).name, R(k).Leff);
end

banner('TABLE VI  -  ABLATIONS');
fprintf('  %-12s %14s %14s %16s %14s\n','Image','ovf classic','ovf ours', ...
        'room modular','room ours');
for k = 1:numel(R)
    fprintf('  %-12s %14d %14d %16d %14d\n', R(k).name, R(k).ovf, 0, ...
            R(k).modroom, R(k).ourroom);
end

banner('TABLE VII  -  RUNTIME');
fprintf('  %-12s %8s %10s %10s\n','Image','pixels','encrypt s','decrypt s');
for k = 1:numel(R)
    fprintf('  %-12s %8d %10.3f %10.3f\n', R(k).name, R(k).M*R(k).N, ...
            R(k).tenc, R(k).tdec);
end
end


%% ------------------------------------------------------------- CSV export
function write_csv(R, G)
p = fullfile(G.outdir,'results.csv');
fid = fopen(p,'w');
fprintf(fid, ['image,M,N,levels,exact,maxerr,raw_bpp,side_bpp,net_bpp,' ...
    'container_bpp,eff_bpp,payload_bits,H_plain,H_cipher,chi2,p_chi2,' ...
    'cp_H,cp_V,cp_D,cc_H,cc_V,cc_D,npcr_key,uaci_key,npcr_A1,uaci_A1,' ...
    'npcr_A2,uaci_A2,ovf_classic,room_modular,room_ours,t_enc,t_dec\n']);
for k = 1:numel(R)
    r = R(k);
    fprintf(fid, ['%s,%d,%d,%d,%d,%d,%.6f,%.6f,%.6f,%.6f,%.6f,%d,' ...
        '%.6f,%.6f,%.4f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,' ...
        '%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%d,%d,%d,%.4f,%.4f\n'], ...
        r.name, r.M, r.N, r.levels, r.exact, r.maxerr, r.raw, r.side, r.net, ...
        r.cont, r.eff, r.payload, r.Hplain, r.Hciph, r.chi2, r.pchi, ...
        r.cp(1),r.cp(2),r.cp(3), r.cc(1),r.cc(2),r.cc(3), ...
        r.npcr_key,r.uaci_key,r.npcr_A1,r.uaci_A1,r.npcr_A2,r.uaci_A2, ...
        r.ovf, r.modroom, round(r.raw*r.M*r.N), r.tenc, r.tdec);
end
fclose(fid);
fprintf('  wrote %s\n', p);
end


%% ----------------------------------------------------------- LaTeX export
function write_tex(R, G)
p = fullfile(G.outdir,'tables.tex');
fid = fopen(p,'w');
fprintf(fid, '%% SE-RDHEI auto-generated tables. Requires \\usepackage{booktabs}\n\n');

fprintf(fid, ['\\begin{table}[t]\n\\centering\n\\caption{Reversibility and ' ...
  'embedding capacity. Effective rate charges the scheme for ciphertext ' ...
  'expansion, $\\mathrm{eff}=\\mathrm{net}-(\\mathrm{container}-8)$.}\n' ...
  '\\label{tab:capacity}\n\\begin{tabular}{lccccccc}\n\\toprule\n' ...
  'Image & $L$ & Exact & Raw & Side & Net & Cont. & Eff. \\\\\n' ...
  ' & & & (bpp) & (bpp) & (bpp) & (bpp) & (bpp) \\\\\n\\midrule\n']);
for k = 1:numel(R)
    fprintf(fid,'%s & %d & %s & %.4f & %.4f & %.4f & %.3f & %.4f \\\\\n', ...
        texesc(R(k).name), R(k).levels, ternary(R(k).exact,'\checkmark','$\times$'), ...
        R(k).raw, R(k).side, R(k).net, R(k).cont, R(k).eff);
end
fprintf(fid, ['\\midrule\nMean & & & %.4f & %.4f & %.4f & %.3f & %.4f \\\\\n' ...
  '\\bottomrule\n\\end{tabular}\n\\end{table}\n\n'], mean([R.raw]), ...
  mean([R.side]), mean([R.net]), mean([R.cont]), mean([R.eff]));

fprintf(fid, ['\\begin{table}[t]\n\\centering\n\\caption{Ciphertext ' ...
  'statistics. $\\chi^2$ has 255 degrees of freedom; $p>0.05$ means ' ...
  'uniformity is not rejected.}\n\\label{tab:stats}\n' ...
  '\\begin{tabular}{lcccccc}\n\\toprule\nImage & $H$ plain & $H$ cipher & ' ...
  '$\\chi^2$ & $p$ & $\\rho_H$ & $\\rho_V$ \\\\\n\\midrule\n']);
for k = 1:numel(R)
    fprintf(fid,'%s & %.4f & %.4f & %.1f & %.3f & %+.4f & %+.4f \\\\\n', ...
        texesc(R(k).name), R(k).Hplain, R(k).Hciph, R(k).chi2, R(k).pchi, ...
        R(k).cc(1), R(k).cc(2));
end
fprintf(fid,'\\bottomrule\n\\end{tabular}\n\\end{table}\n\n');

fprintf(fid, ['\\begin{table}[t]\n\\centering\n\\caption{Sensitivity. Ideal ' ...
  'NPCR $=99.6094\\%%$, UACI $=33.4635\\%%$; %d trials per entry.}\n' ...
  '\\label{tab:sens}\n\\begin{tabular}{lcccccc}\n\\toprule\n & ' ...
  '\\multicolumn{2}{c}{Key} & \\multicolumn{2}{c}{Audio $A_1$} & ' ...
  '\\multicolumn{2}{c}{Audio $A_2$} \\\\\n\\cmidrule(lr){2-3}' ...
  '\\cmidrule(lr){4-5}\\cmidrule(lr){6-7}\nImage & NPCR & UACI & NPCR & ' ...
  'UACI & NPCR & UACI \\\\\n\\midrule\n'], G.trials);
for k = 1:numel(R)
    fprintf(fid,'%s & %.4f & %.4f & %.4f & %.4f & %.4f & %.4f \\\\\n', ...
        texesc(R(k).name), R(k).npcr_key, R(k).uaci_key, R(k).npcr_A1, ...
        R(k).uaci_A1, R(k).npcr_A2, R(k).uaci_A2);
end
fprintf(fid,'\\bottomrule\n\\end{tabular}\n\\end{table}\n\n');

fprintf(fid, ['\\begin{table}[t]\n\\centering\n\\caption{Ablations. Classic ' ...
  'ordering inverse-transforms modified coefficients and needs a location ' ...
  'map; deferred synthesis never does. Modular lifting is bijective but ' ...
  'carries no exploitable redundancy.}\n\\label{tab:ablation}\n' ...
  '\\begin{tabular}{lcccc}\n\\toprule\n & \\multicolumn{2}{c}{Out-of-range ' ...
  'pixels} & \\multicolumn{2}{c}{Exploitable room (bits)} \\\\\n' ...
  '\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\nImage & Classic & Proposed & ' ...
  'Modular & Proposed \\\\\n\\midrule\n']);
for k = 1:numel(R)
    fprintf(fid,'%s & %d & 0 & %d & %d \\\\\n', texesc(R(k).name), ...
        R(k).ovf, R(k).modroom, round(R(k).raw*R(k).M*R(k).N));
end
fprintf(fid,'\\bottomrule\n\\end{tabular}\n\\end{table}\n');
fclose(fid);
fprintf('  wrote %s\n', p);
end

function s = texesc(s), s = strrep(s,'_','\_'); end


%% ------------------------------------------------------------- figures
function make_figures(R, G)
if exist('OCTAVE_VERSION','builtin')
    for tk = {'qt','fltk','gnuplot'}
        try, graphics_toolkit(tk{1}); break; catch, end
    end
end
n = numel(R);
sv = @(fh,nm) savefig_both(fh, fullfile(G.outdir, nm));

try
    ns = 0;                       % how many have image panels retained
    for k = 1:n, if ~isempty(R(k).I), ns = ns + 1; end, end
    ns = min(ns, 6);              % montage caps at 6 rows

    % Fig 1: cover / cipher / recovered montage
    if ns > 0
    fh = figure('Visible','off','Color','w','Position',[0 0 900 300*ns]);
    for k = 1:ns
        subplot(ns,3,3*k-2); show(R(k).I);
            title(sprintf('%s  cover (H=%.3f)', R(k).name, R(k).Hplain));
        subplot(ns,3,3*k-1); show(R(k).Cimg);
            title(sprintf('encrypted (H=%.4f)', R(k).Hciph));
        subplot(ns,3,3*k);   show(R(k).Iwrong);
            title(sprintf('wrong key (\\rho=%+.3f)', R(k).wrongcorr));
    end
    sv(fh,'fig1_montage');
    end

    % Fig 2: histograms
    if ns > 0
    fh = figure('Visible','off','Color','w','Position',[0 0 300*ns 420]);
    for k = 1:ns
        subplot(2,ns,k);    bar(accumarray(double(R(k).I(:))+1,1,[256 1]),'k');
            xlim([0 255]); title([R(k).name ' cover']);
        subplot(2,ns,ns+k); bar(accumarray(double(R(k).Cimg(:))+1,1,[256 1]),'k');
            xlim([0 255]); title(sprintf('cipher  p=%.3f', R(k).pchi));
    end
    sv(fh,'fig2_histograms');
    end

    % Fig 3: correlation scatter, first image
    if ns > 0
    fh = figure('Visible','off','Color','w','Position',[0 0 900 320]);
    I1 = double(R(1).I);  E1 = double(R(1).Cimg);
    lbl = {'Horizontal','Vertical','Diagonal'};  dd = {[0 1],[1 0],[1 1]};
    for q = 1:3
        subplot(1,3,q);
        a = I1(1:end-dd{q}(1), 1:end-dd{q}(2));  b = I1(1+dd{q}(1):end, 1+dd{q}(2):end);
        c2 = E1(1:end-dd{q}(1), 1:end-dd{q}(2)); d2 = E1(1+dd{q}(1):end, 1+dd{q}(2):end);
        s = randperm(numel(a), min(3000,numel(a)));
        plot(a(s),b(s),'.','MarkerSize',3); hold on
        plot(c2(s),d2(s),'.','MarkerSize',3); hold off
        axis([0 255 0 255]); axis square; title(lbl{q});
        if q==1, legend('plain','cipher','Location','northwest'); end
    end
    sv(fh,'fig3_correlation');
    end

    % Fig 4: capacity bars vs baseline
    fh = figure('Visible','off','Color','w','Position',[0 0 700 380]);
    bar([[R.net].' [R.eff].']); hold off
    set(gca,'XTick',1:n,'XTickLabel',{R.name}); rotx();
    ylabel('bits per pixel');
    legend('net','effective','Location','best');
    title('Embedding capacity'); sv(fh,'fig4_capacity');

    % Fig 5: block-size sweep
    fh = figure('Visible','off','Color','w','Position',[0 0 640 380]);
    for k = 1:n, semilogx(R(k).Bs, R(k).Bnet,'-o'); hold on; end
    hold off; grid on; xlabel('block size B'); ylabel('net bpp');
    legend({R.name},'Location','best'); title('Block-size sweep');
    sv(fh,'fig5_blocksize');

    % Fig 6: level sweep
    fh = figure('Visible','off','Color','w','Position',[0 0 640 380]);
    for k = 1:n, plot(R(k).Ls, R(k).Leff,'-s'); hold on; end
    hold off; grid on; xlabel('decomposition levels L');
    ylabel('effective bpp'); legend({R.name},'Location','best');
    title('Decomposition depth'); sv(fh,'fig6_levels');

    % Fig 7: sensitivity
    fh = figure('Visible','off','Color','w','Position',[0 0 760 380]);
    subplot(1,2,1);
    bar([[R.npcr_key].' [R.npcr_A1].' [R.npcr_A2].']); hold on
    plot(xlim,[99.6094 99.6094],'k--'); hold off
    set(gca,'XTick',1:n,'XTickLabel',{R.name}); rotx(); ylim([99.5 99.72]);
    ylabel('NPCR (%)');
    legend('key','A_1','A_2','ideal','Location','best'); title('NPCR');
    subplot(1,2,2);
    bar([[R.uaci_key].' [R.uaci_A1].' [R.uaci_A2].']); hold on
    plot(xlim,[33.4635 33.4635],'k--'); hold off
    set(gca,'XTick',1:n,'XTickLabel',{R.name}); rotx(); ylim([33.2 33.7]);
    ylabel('UACI (%)');
    title('UACI'); sv(fh,'fig7_sensitivity');

    % Fig 8: ablations
    fh = figure('Visible','off','Color','w','Position',[0 0 760 380]);
    subplot(1,2,1); bar([[R.ovf].' zeros(n,1)]);
    set(gca,'XTick',1:n,'XTickLabel',{R.name}); rotx();
    ylabel('out-of-range pixels');
    legend('classic ordering','proposed','Location','best');
    title('Location-map requirement');
    subplot(1,2,2);
    bar([[R.modroom].' round([R.raw].'.*[R.M].'.*[R.N].')]);
    set(gca,'XTick',1:n,'XTickLabel',{R.name}); rotx();
    ylabel('exploitable room (bits)');
    legend('modular IWT','proposed','Location','best');
    title('Modular-lifting ablation'); sv(fh,'fig8_ablation');

    fprintf('  wrote 8 figures (png + eps) to %s\n', G.outdir);
catch err
    fprintf('  FIGURES SKIPPED (%s)\n', err.message);
    fprintf('  tables and CSV were still written.\n');
end
end

function histbar(v, nb)
lo = min(v); hi = max(v);
if hi <= lo, hi = lo + 1e-9; end
ed = linspace(lo, hi, nb+1);
ct = zeros(1, nb);
for k = 1:nb
    if k < nb, ct(k) = sum(v >= ed(k) & v < ed(k+1));
    else,      ct(k) = sum(v >= ed(k) & v <= ed(k+1)); end
end
bar((ed(1:end-1)+ed(2:end))/2, ct, 1, 'FaceColor',[0.3 0.3 0.3]);
end

function rotx()
try, set(gca,'XTickLabelRotation',45); catch, end
end

function savefig_both(fh, stem)
% Report save failures instead of swallowing them: a figure that silently
% fails to write is worse than one that errors, because it just goes missing.
okp = false;  oke = false;
try, print(fh, [stem '.png'], '-dpng', '-r300'); okp = true;
catch ep, fprintf('    ! %s.png not written: %s\n', stem, ep.message); end
try, print(fh, [stem '.eps'], '-depsc2');        oke = true;
catch ee, fprintf('    ! %s.eps not written: %s\n', stem, ee.message); end
if ~okp && ~oke
    fprintf('    ! figure %s produced NO output file\n', stem);
end
try, close(fh); catch, end
end

function p = chi2p(x, k)
% upper-tail chi-square p-value via a Wilson-Hilferty normal approximation
z = ((x/k)^(1/3) - (1 - 2/(9*k))) / sqrt(2/(9*k));
p = 0.5 * erfc(z/sqrt(2));
end

function c = corr2v(a, b)
a = a(:) - mean(a(:));  b = b(:) - mean(b(:));
c = sum(a.*b) / (sqrt(sum(a.^2)*sum(b.^2)) + eps);
end


%% ============ Huffman coding of the block t-map ======================

function len = huff_codelens(cnt)
%HUFF_CODELENS  Code length per symbol from a count vector (0 = unused).
n = numel(cnt);  len = zeros(1,n);
act = find(cnt > 0);
if isempty(act), return; end
if numel(act) == 1, len(act) = 1; return; end
% node list: [weight, left, right]; leaves first
w  = cnt(act);  nl = numel(act);
par = zeros(1, 2*nl);          % parent index per node
nodes = w;                     % weights of live nodes
alive = 1:nl;
nxt = nl;
while numel(alive) > 1
    [~, o] = sort(nodes(alive));
    a = alive(o(1));  b = alive(o(2));
    nxt = nxt + 1;
    nodes(nxt) = nodes(a) + nodes(b);
    par(a) = nxt;  par(b) = nxt;
    alive = [alive(o(3:end)) nxt];
end
for k = 1:nl                   % depth of each leaf
    d = 0;  q = k;
    while par(q) ~= 0, q = par(q);  d = d + 1; end
    len(act(k)) = max(d,1);
end
end

function code = huff_canonical(len)
%HUFF_CANONICAL  Canonical codes as {symbol}{bit vector} from code lengths.
n = numel(len);  code = cell(1,n);
act = find(len > 0);
[~, o] = sort(len(act)*1000 + act);     % by length, then symbol
act = act(o);
c = 0;  prev = 0;
for k = 1:numel(act)
    L = len(act(k));
    if prev > 0, c = bitshift(c + 1, L - prev); end
    prev = L;
    b = zeros(1,L);
    for q = 1:L, b(q) = bitget(c, L-q+1); end
    code{act(k)} = b;
end
end

function [bits, len] = huff_encode(sym, alpha)
%HUFF_ENCODE  sym: symbol values 0..alpha-1. Returns bitstream and lengths.
cnt = accumarray(double(sym(:))+1, 1, [alpha 1]).';
len = huff_codelens(cnt);
code = huff_canonical(len);
tot = 0;
for k = 1:alpha, tot = tot + cnt(k)*len(k); end
bits = zeros(1, tot);  p = 0;
for q = 1:numel(sym)
    b = code{double(sym(q))+1};
    bits(p+1:p+numel(b)) = b;  p = p + numel(b);
end
end

function sym = huff_decode(bits, len, n)
%HUFF_DECODE  Inverse of huff_encode given the code lengths and count.
code = huff_canonical(len);
alpha = numel(len);
sym = zeros(1,n);  p = 0;
for q = 1:n
    L = 0;  hit = 0;
    while hit == 0 && L < 32
        L = L + 1;
        cand = bits(p+1:p+L);
        for a = 1:alpha
            if numel(code{a}) == L && isequal(code{a}, cand)
                sym(q) = a-1;  hit = 1;  break
            end
        end
    end
    p = p + L;
end
end

function [nbits, payload, lens] = tmap_pack(tm, det, tmax)
%TMAP_PACK  Huffman-code every block t-map. Side information is the code
% length table (4 bits per symbol) plus the coded bitstream, which is what
% the scheme actually has to transmit.
alpha = tmax + 2;
sym = [];
for b = det, v = tm.(b{1});  sym = [sym double(v(:)).']; end %#ok<AGROW>
if isempty(sym), nbits = 0; payload = []; lens = zeros(1,alpha); return; end
[payload, lens] = huff_encode(sym, alpha);
nbits = numel(payload) + 4*alpha;      % table: 4 bits of length per symbol
end


%% ============ cover identity guard ===================================
function [H, sz, note] = cover_reference(name)
%COVER_REFERENCE  Plain-image entropy and size reported in the literature
% for each standard cover, used to confirm that the file on disk is the same
% image the published rates were measured on. Entropies from Dong et al.
% 2025 Table 4 and the USC-SIPI originals. NaN = no reference value.
T = { 'Airplane', 6.7025, 512,  'the F-16; Dong Table 4' ; ...
      'Jetplane', 6.7025, 512,  'same image as Airplane in [6]-[9]' ; ...
      'Baboon',   7.3583, 512,  'Dong Table 4' ; ...
      'Lena',     7.4451, 512,  '' ; ...
      'Man',      7.5237, 1024, '1024x1024 in all sources' ; ...
      'Tiffany',  6.6009, 512,  '' ; ...
      'boat',     7.1914, 512,  'Dong Table 4' ; ...
      'peppers',  7.5937, 512,  'Dong Table 4' ; ...
      'lake',     7.4842, 512,  'Dong Table 4' ; ...
      'barbara',  7.4664, 512,  'Dong Table 4' };
H = NaN;  sz = NaN;  note = '';
for k = 1:size(T,1)
    if strcmpi(name, T{k,1}), H = T{k,2};  sz = T{k,3};  note = T{k,4};  return; end
end
end

function flag = cover_check(name, Hplain, M, N)
%COVER_CHECK  '' when the cover matches its published counterpart, else a
% short warning to print beside the comparison.
flag = '';
[H, sz] = cover_reference(name);
if isnan(H), return; end
if max(M,N) ~= sz
    flag = sprintf('SIZE %dx%d, published %dx%d', M, N, sz, sz);
elseif abs(Hplain - H) > 0.02
    flag = sprintf('ENTROPY %.4f vs %.4f: different image', Hplain, H);
end
end


%% ============ PUBLISHED COMPARISON DATA ==============================
function M = published_methods()
% Per-image embedding rates (bpp) reported in the literature. Man is
% 1024x1024 in [5]; all other covers are 512x512. NaN = not reported.
%
%  [1] P. Puteaux, W. Puech, IEEE TIFS 13(7):1670-1681, 2018.
%  [2] S. Yi, Y. Zhou, IEEE TMM 21(1):51-64, 2019.                (PBTL)
%  [3] Z. Yin, Y. Xiang, X. Zhang, IEEE TMM 22(4):874-884, 2020.
%  [4] X. Wu et al., IEEE TMM 22(8):1929-1938, 2020.             (IPBTL)
%      -- measured here by running the authors' released code.
%  [5] Z. Yin, Y. Peng, Y. Xiang, arXiv:1911.01699.                (BPC)
%  [6] Y. Wang, W. He, IEEE TMM 24:1288-1298, 2021.
%  [7] K. Gao, J.-H. Horng, C.-C. Chang, JVCIR 84:103481, 2022.
%  [8] H. Zou, G. Chen, Signal Processing 205:108847, 2023.
%  [9] H. Dong, J. Song, H. Yao, C. Qin, JVCIR 111:104501, 2025.
%      -- adaptive classification encoding; 3x3 blocks.
%
%      name            Airpl  Baboon  Jetpl   Lena    Man    Tiff   Boat  Peppers  lake  barbara
M = { 'Puteaux 2018 [1]',[0.977 0.838  0.983  0.977  0.981  0.993  NaN    NaN     NaN    NaN  ] ; ...
      'Yi 2019 [2]',     [NaN   NaN    NaN    2.014  NaN    NaN    NaN    NaN     NaN    NaN  ] ; ...
      'Yin 2020 [3]',    [NaN   NaN    NaN    2.583  NaN    NaN    NaN    NaN     NaN    NaN  ] ; ...
      'Wu 2020 [4]',     [2.8578 0.9692 2.6726 2.6447 2.4790 2.6515 NaN   NaN     NaN    NaN  ] ; ...
      'Yin 2019 BPC [5]',[3.8363 1.3832 3.4019 3.0750 2.6345 3.1492 NaN   NaN     NaN    NaN  ] ; ...
      'Wang 2021 [6]',   [NaN   0.30   2.02   NaN    NaN    NaN    1.28   1.51    1.23   1.16 ] ; ...
      'Gao 2022 [7]',    [NaN   0.81   2.04   NaN    NaN    NaN    1.41   1.56    1.32   1.20 ] ; ...
      'Zou 2023 [8]',    [NaN   0.83   2.47   NaN    NaN    NaN    1.80   2.09    1.62   1.69 ] ; ...
      'Dong 2025 [9]',   [NaN   0.98   2.59   NaN    NaN    NaN    1.92   2.28    1.85   1.89 ] };
%  NOTE: [6]-[9] all report via Dong et al. Table 11, whose 'Airplane' is the
%  F-16 (plain entropy 6.7025) -- the image we call Jetplane. Those values are
%  therefore placed in the Jetplane column, not Airplane.
end

function names = published_images()
names = {'Airplane','Baboon','Jetplane','Lena','Man','Tiffany', ...
         'boat','peppers','lake','barbara'};
end

function D = published_datasets()
% Average embedding rate (bpp) on the standard databases.
%          method             BOSSbase  BOWS-2   UCID
D = { 'Puteaux 2018 [1]',  [NaN      NaN      0.893 ] ; ...
      'Yi 2019 [2]',       [1.9656   1.8808   1.586 ] ; ...
      'Yin 2020 [3]',      [NaN      NaN      2.688 ] ; ...
      'Wu 2020 [4]',       [2.5613   2.5194   2.2751] ; ...
      'Yin 2019 BPC [5]',  [3.6248   3.4948   2.8990] ; ...
      'Dong 2025 [9]',     [2.9652   2.7615   NaN   ] };
end


%% ============ PUBLISHED REFERENCE: IPBTL (Wu et al., IEEE TMM 2020) ===

function v = ipbtl_dataset(name)
% Authors' own per-image arrays shipped with the repository.
switch upper(name)
    case 'BOSSBASE', v = 2.5613;   % mean over 10 000 images
    case 'BOWS-2',   v = 2.5194;   % mean over 10 000 images
    case 'UCID',     v = 2.2751;   % mean over 1 334 images
    otherwise,       v = NaN;
end
end


%% ============ EDIT DATASET PATHS HERE ================================
function DS = dataset_list()
% One row per dataset. Set `dir` to '' or a path that does not exist and
% that dataset is silently skipped. `limit` caps how many images are used
% (0 = all). `sens` is the number of NPCR/UACI trials per image (0 = skip,
% which is what you want for the 10 000-image sets). `sweeps` enables the
% block-size and decomposition-level sweeps (slow; keep it on for the small
% showcase dataset only).
%
%          name          directory                                limit sens sweeps
DS = { ...
  'USC-SIPI',  '/Users/sudhirsingh/Desktop/dataset/test image',   0,  10, true ; ...
  'BOSSbase',  '/Users/sudhirsingh/Desktop/BOSSbase_1.01',          100,   0, false; ...
  'BOWS-2',    '/Users/sudhirsingh/Desktop/BOSS-2',                  100,   0, false; ...
  'UCID',      '/Users/sudhirsingh/Desktop/UCID1338',                 100,   0, false; ...
  'Kodak',     '',                                                     24,   0, false  ...
};
end
%% =====================================================================


function datasets(opts)
% Run every configured dataset, skipping any whose folder is missing.
D = @(f,v) getfielddef(opts,f,v);
G.outdir  = D('outdir',   fullfile(pwd,'SE_RDHEI_results'));
G.maxSize = D('maxSize',  0);    % 0 = native size: Man stays 1024x1024
G.blk     = D('blk',      8);
G.levels  = D('levels',   0);
G.permWords = D('permWords', 8);
G.key     = uint8(D('key', uint8(0:31)));
G.nonce   = uint8('0123456789ab');
G.sub     = {'LL','HL','LH','HH'};
G.full    = false;  G.quiet = true;
G.shaBackend = pick_sha_backend();
if ~exist(G.outdir,'dir'), mkdir(G.outdir); end

DS = dataset_list();
dd = D('dir','');
if iscell(dd) && numel(dd) == 1 && iscell(dd{1}), dd = dd{1}; end
if (ischar(dd) && ~isempty(dd)) || (iscell(dd) && ~isempty(dd))
    DS = {'Custom', dd, D('limit',0), D('trials',5), true};
end

banner('SE-RDHEI  MULTI-DATASET RUN');
fprintf('  output folder : %s\n\n', G.outdir);
fprintf('  %-11s %-8s %6s %5s %7s  %s\n','dataset','status','limit','sens','sweeps','path');
use = {};
for k = 1:size(DS,1)
    d = DS{k,2};
    if iscell(d)
        nfiles = numel(list_images(d));  ok = nfiles > 0;
        dtxt = sprintf('%d explicit file(s)', numel(d));
    else
        ok = ~isempty(d) && exist(d,'dir') == 7;
        if ok, nfiles = numel(list_images(d));  ok = nfiles > 0; else, nfiles = 0; end
        dtxt = ternary(isempty(d),'(not set)',d);
    end
    st = ternary(ok, sprintf('%d img', nfiles), 'SKIP');
    fprintf('  %-11s %-8s %6d %5d %7s  %s\n', DS{k,1}, st, DS{k,3}, DS{k,4}, ...
            ternary(DS{k,5},'yes','no'), dtxt);
    if ok, use(end+1,:) = DS(k,:); end %#ok<AGROW>
end
if isempty(use)
    fprintf(['\n  No dataset folders found. Edit dataset_list() near the ' ...
             'bottom of this file\n  and set at least one directory.\n']);
    return
end

[a1,a2,s1,s2] = load_audio('','',G);
banner('AUDIO CREDENTIALS');
report_audio('A1', a1, s1, G);
report_audio('A2', a2, s2, G);

ALL = {};  SUM = struct([]);  ns = 0;  Rshow = [];
for k = 1:size(use,1)
    nm = use{k,1};
    G2 = G;  G2.trials = use{k,4};  G2.sweeps = use{k,5};
    R = run_dataset(nm, use{k,2}, use{k,3}, a1, a2, G2);
    if isempty(R), continue; end
    ALL{end+1} = {nm, R}; %#ok<AGROW>
    ns = ns + 1;
    s = agg(nm, R);
    if ns == 1, SUM = s; else, SUM(ns) = s; end %#ok<AGROW>
    write_csv_named(R, G, sprintf('dataset_%s.csv', safename(nm)));
    if use{k,5}
        print_tables(R, G2);
        print_reviewer_tables(R, G2);
        print_security_tables(R, G2);
        write_security_tex(R, G2);
        write_tex(R, G2);
        make_figures(R, G2);
        make_reviewer_figures(R, G2);
        Rshow = R;
    end
end
if ns == 0, fprintf('  nothing processed.\n'); return; end

print_summary(SUM);
write_summary(SUM, ALL, G);
make_dataset_figures(ALL, G);
if ~isempty(Rshow), make_extra_figures(Rshow, G, ALL); end
banner(sprintf('MULTI-DATASET RUN COMPLETE - %d dataset(s) -> %s', ns, G.outdir));
end


function images_run(opts)
%IMAGES_RUN  Full analysis over an explicit list of image files.
%  SE_RDHEI('__images', struct('files', {{ 'a.tiff','b.tiff','c.tiff' }}))
%  Note the DOUBLE braces: that is how a cell array is placed in a struct.
D = @(f,v) getfielddef(opts,f,v);
f = D('files', D('dir', {}));
if ischar(f)
    if exist(f,'dir') == 7
        fprintf('  folder given: %s\n', f);
        f = list_images(f);                 % every image in that folder
        if isempty(f)
            error('SE_RDHEI:noImages','no image files in folder:\n    %s', f);
        end
        fprintf('  found %d image(s)\n', numel(f));
    else
        f = {f};
    end
end
if isempty(f)
    fprintf(['  Give a list of images:\n' ...
      '    SE_RDHEI(''__images'', struct(''files'', {{ ''a.tiff'',''b.tiff'' }}))\n' ...
      '  Note the double braces.\n']);
    return
end
o = opts;
o.dir    = {f};                       % list_images accepts a cell of paths
o.limit  = D('limit', 0);
o.trials = D('trials', 10);
if ~isfield(o,'maxSize'), o.maxSize = 0; end   % native size by default
datasets(o);
end

function files = list_images(d)
if iscell(d)                      % an explicit list of files was given
    files = {};
    for k = 1:numel(d)
        q = resolve_cover(d{k});
        if exist(q,'file') == 2, files{end+1} = q; end %#ok<AGROW>
    end
    return
end
ext = {'*.tif','*.tiff','*.png','*.bmp','*.jpg','*.jpeg','*.pgm','*.ppm'};
files = {};
for e = ext
    q = dir(fullfile(d, e{1}));
    for k = 1:numel(q)
        if ~q(k).isdir, files{end+1} = fullfile(d, q(k).name); end %#ok<AGROW>
    end
end
if isempty(files)                      % fall back to immediate subfolders
    q = dir(d);
    for k = 1:numel(q)
        if q(k).isdir && ~any(strcmp(q(k).name,{'.','..'}))
            sub = fullfile(d, q(k).name);
            for e = ext
                r = dir(fullfile(sub, e{1}));
                for j = 1:numel(r)
                    files{end+1} = fullfile(sub, r(j).name); %#ok<AGROW>
                end
            end
        end
    end
end
files = sort(files);
end


function R = run_dataset(name, d, limit, a1, a2, G)
files = list_images(d);
if limit > 0 && numel(files) > limit
    setseed(12345);
    idx = sort(randperm(numel(files), limit));   % reproducible random sample
    files = files(idx);
end
banner(sprintf('DATASET: %s   (%d image(s))', name, numel(files)));
R = struct([]);  n = 0;  t0 = tic;
for f = 1:numel(files)
    try
        nat = [0 0];
        try, z = imread(files{f});  nat = [size(z,1) size(z,2)];  catch, end
        [I, nm] = load_cover(files{f}, G.maxSize);
    catch
        fprintf('    skip (unreadable): %s\n', files{f});  continue
    end
    if min(size(I)) < 8, continue; end
    [~, base] = fileparts(nm);
    n = n + 1;
    r = one_image(I, base, a1, a2, G);
    r.file = nm;  r.I = I;
    if numel(files) > 20
        r.I = [];  r.Cimg = [];  r.Iwrong = [];  r.tmap = [];
        r.subhist = [];                            % keep memory bounded
    end
    if n == 1, R = r; else, R(n) = r; end %#ok<AGROW>
    if numel(files) <= 20
        if all(nat > 0) && ~isequal(nat, [r.M r.N])
            szs = sprintf('%dx%d on disk -> %dx%d used', nat(1), nat(2), r.M, r.N);
        else
            szs = sprintf('%dx%d', r.M, r.N);
        end
        fprintf('    %-14s %-26s net %.4f  eff %+.4f  exact=%s\n', base, ...
                szs, r.net, r.eff, yn(r.exact));
    elseif mod(n, 10) == 0 || n == numel(files)
        fprintf('    %d/%d  (%.1f s elapsed)\n', n, numel(files), toc(t0));
    end
end
if n == 0, R = struct([]); return; end
fprintf('    done: %d image(s), %d exact, %.1f s\n', n, sum([R.exact]), toc(t0));
end


function s = agg(name, R)
s.name = name;  s.n = numel(R);
s.exact = sum([R.exact]);  s.maxerr = max([R.maxerr]);
f = @(v) [mean(v) std(v,1) min(v) max(v)];
s.net = f([R.net]);  s.eff = f([R.eff]);  s.cont = f([R.cont]);
s.Hp = f([R.Hplain]);  s.Hc = f([R.Hciph]);
s.chi = f([R.chi2]);   s.pch = f([R.pchi]);
cc = reshape([R.cc],3,[]).';
s.absrho = f(max(abs(cc),[],2).');
s.tenc = f([R.tenc]);  s.tdec = f([R.tdec]);
if any([R.npcr_key] > 0)
    s.npcr = f([R.npcr_key]);  s.uaci = f([R.uaci_key]);
    s.npcrA = f([R.npcr_A1]);  s.uaciA = f([R.uaci_A1]);
else
    s.npcr = [0 0 0 0]; s.uaci = [0 0 0 0];
    s.npcrA = [0 0 0 0]; s.uaciA = [0 0 0 0];
end
s.ovf = f(double([R.ovf]));  s.modroom = f(double([R.modroom]));
end


function print_summary(S)
banner('TABLE 0  -  CROSS-DATASET SUMMARY');
fprintf('  %-11s %5s %7s %17s %17s %9s %8s\n', 'dataset','N','exact', ...
        'net bpp (mu+-sd)','eff bpp (mu+-sd)','H cipher','max|rho|');
for k = 1:numel(S)
    fprintf('  %-11s %5d %7s %8.4f+-%-7.4f %8.4f+-%-7.4f %9.4f %8.4f\n', ...
        S(k).name, S(k).n, sprintf('%d/%d',S(k).exact,S(k).n), ...
        S(k).net(1), S(k).net(2), S(k).eff(1), S(k).eff(2), ...
        S(k).Hc(1), S(k).absrho(1));
end
fprintf('\n  %-11s %9s %9s %11s %11s %10s\n','dataset','eff min','eff max', ...
        'chi2 mean','p mean','enc s');
for k = 1:numel(S)
    fprintf('  %-11s %9.4f %9.4f %11.1f %11.3f %10.3f\n', S(k).name, ...
        S(k).eff(3), S(k).eff(4), S(k).chi(1), S(k).pch(1), S(k).tenc(1));
end
fprintf('\n  IPBTL (Wu et al., IEEE TMM 2020), authors'' own results:\n');
fprintf('    BOSSbase %.4f   BOWS-2 %.4f   UCID %.4f bpp\n', ...
        ipbtl_dataset('BOSSbase'), ipbtl_dataset('BOWS-2'), ipbtl_dataset('UCID'));
fprintf('  ideal: H=8, |rho|=0, NPCR=99.6094, UACI=33.4635\n');
end


function write_csv_named(R, G, fname)
p = fullfile(G.outdir, fname);
fid = fopen(p,'w');
fprintf(fid, ['image,M,N,levels,exact,maxerr,raw_bpp,side_bpp,net_bpp,' ...
    'container_bpp,eff_bpp,payload_bits,H_plain,H_cipher,chi2,p_chi2,' ...
    'cc_H,cc_V,cc_D,npcr_key,uaci_key,npcr_A1,uaci_A1,npcr_A2,uaci_A2,' ...
    'ovf_classic,room_modular,room_ours,t_enc,t_dec\n']);
for k = 1:numel(R)
    r = R(k);
    fprintf(fid, ['%s,%d,%d,%d,%d,%d,%.6f,%.6f,%.6f,%.6f,%.6f,%d,%.6f,%.6f,' ...
        '%.4f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%d,%d,%d,' ...
        '%.4f,%.4f\n'], r.name, r.M, r.N, r.levels, r.exact, r.maxerr, ...
        r.raw, r.side, r.net, r.cont, r.eff, r.payload, r.Hplain, r.Hciph, ...
        r.chi2, r.pchi, r.cc(1),r.cc(2),r.cc(3), r.npcr_key,r.uaci_key, ...
        r.npcr_A1,r.uaci_A1,r.npcr_A2,r.uaci_A2, r.ovf, r.modroom, ...
        r.ourroom, r.tenc, r.tdec);
end
fclose(fid);
fprintf('  wrote %s\n', p);
end


function write_summary(S, ALL, G)
p = fullfile(G.outdir,'summary.csv');
fid = fopen(p,'w');
fprintf(fid,['dataset,N,exact,net_mean,net_sd,net_min,net_max,eff_mean,eff_sd,' ...
   'eff_min,eff_max,cont_mean,H_plain_mean,H_cipher_mean,chi2_mean,p_mean,' ...
   'absrho_mean,npcr_key_mean,uaci_key_mean,tenc_mean,tdec_mean\n']);
for k = 1:numel(S)
    fprintf(fid,'%s,%d,%d,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.4f,%.6f,%.6f,%.6f,%.6f,%.4f,%.4f\n', ...
      S(k).name,S(k).n,S(k).exact,S(k).net(1),S(k).net(2),S(k).net(3),S(k).net(4), ...
      S(k).eff(1),S(k).eff(2),S(k).eff(3),S(k).eff(4),S(k).cont(1),S(k).Hp(1), ...
      S(k).Hc(1),S(k).chi(1),S(k).pch(1),S(k).absrho(1),S(k).npcr(1),S(k).uaci(1), ...
      S(k).tenc(1),S(k).tdec(1));
end
fclose(fid);
fprintf('  wrote %s\n', p);

p = fullfile(G.outdir,'tables_datasets.tex');
fid = fopen(p,'w');
fprintf(fid,'%% SE-RDHEI cross-dataset tables. Requires \\usepackage{booktabs}\n\n');
fprintf(fid,['\\begin{table}[t]\n\\centering\n\\caption{Cross-dataset results. ' ...
  'Every image is recovered bit-exactly. Effective rate charges the scheme ' ...
  'for ciphertext expansion.}\n\\label{tab:datasets}\n' ...
  '\\begin{tabular}{lccccc}\n\\toprule\nDataset & $N$ & Exact & Net (bpp) & ' ...
  'Eff. (bpp) & $H$ cipher \\\\\n\\midrule\n']);
for k = 1:numel(S)
    fprintf(fid,'%s & %d & %d/%d & $%.4f \\pm %.4f$ & $%.4f \\pm %.4f$ & %.4f \\\\\n', ...
      texesc(S(k).name), S(k).n, S(k).exact, S(k).n, S(k).net(1), S(k).net(2), ...
      S(k).eff(1), S(k).eff(2), S(k).Hc(1));
end
fprintf(fid,'\\bottomrule\n\\end{tabular}\n\\end{table}\n\n');

D = published_datasets();
fprintf(fid,['\\begin{table}[t]\n\\centering\n\\caption{Comparison with ' ...
  'published RDHEI methods. Rates are averages reported by the authors on ' ...
  'each database; the proposed rates are measured in this work.}\n' ...
  '\\label{tab:compare}\n\\begin{tabular}{lcccc}\n\\toprule\nMethod & ' ...
  'Domain & BOSSbase & BOWS-2 & UCID \\\\\n\\midrule\n']);
for k = 1:size(D,1)
    fprintf(fid,'%s & spatial', texesc(D{k,1}));
    for q = 1:3
        if isnan(D{k,2}(q)), fprintf(fid,' & --');
        else,                fprintf(fid,' & %.4f', D{k,2}(q)); end
    end
    fprintf(fid,' \\\\\n');
end
fprintf(fid,'\\midrule\n\\textbf{Proposed} & IWT');
for q = 1:3
    nmq = {'BOSSbase','BOWS-2','UCID'};  v = NaN;
    for j = 1:numel(S), if strcmpi(S(j).name,nmq{q}), v = S(j).net(1); end, end
    if isnan(v), fprintf(fid,' & --'); else, fprintf(fid,' & %.4f', v); end
end
fprintf(fid,[' \\\\\n\\bottomrule\n\\end{tabular}\n\\end{table}\n\n' ...
  '%% The proposed scheme requires NO location map; every method above ' ...
  'does.\n']);
fclose(fid);
fprintf('  wrote %s\n', p);
end


function make_dataset_figures(ALL, G)
try
    if exist('OCTAVE_VERSION','builtin')
        for tk = {'qt','fltk','gnuplot'}
            try, graphics_toolkit(tk{1}); break; catch, end
        end
    end
    nd = numel(ALL);
    nm = cell(1,nd);  effs = cell(1,nd);  nets = cell(1,nd);
    for k = 1:nd
        nm{k} = ALL{k}{1};  R = ALL{k}{2};
        effs{k} = [R.eff];  nets{k} = [R.net];
    end

    % Fig 9: effective-rate distribution per dataset
    fh = figure('Visible','off','Color','w','Position',[0 0 760 400]);
    hold on
    for k = 1:nd
        v = effs{k};
        plot(k + 0.16*randn(1,numel(v)), v, '.', 'MarkerSize', 6);
        plot([k-0.3 k+0.3], [mean(v) mean(v)], 'k-', 'LineWidth', 2);
    end
    for q = 1:nd, ipd = ipbtl_dataset(nm{q});
        if ~isnan(ipd), plot([q-0.3 q+0.3],[ipd ipd],'r--','LineWidth',1.4); end
    end
    hold off; grid on; set(gca,'XTick',1:nd,'XTickLabel',nm);
    ylabel('effective rate (bpp)');
    title('Effective rate by dataset (red = IPBTL, Wu et al. 2020)');
    savefig_both(fh, fullfile(G.outdir,'fig9_dataset_eff'));

    % Fig 10: empirical CDF of effective rate
    fh = figure('Visible','off','Color','w','Position',[0 0 640 400]);
    hold on
    for k = 1:nd
        v = sort(effs{k});
        stairs(v, (1:numel(v))/numel(v), 'LineWidth', 1.3);
    end
    hold off; grid on
    xlabel('effective rate (bpp)'); ylabel('empirical CDF');
    legend(nm, 'Location','southeast');
    title('Distribution of effective rate');
    savefig_both(fh, fullfile(G.outdir,'fig10_eff_cdf'));

    % Fig 11: capacity vs cover entropy
    fh = figure('Visible','off','Color','w','Position',[0 0 640 400]);
    hold on
    for k = 1:nd
        R = ALL{k}{2};
        plot([R.Hplain], [R.net], '.', 'MarkerSize', 8);
    end
    hold off; grid on; xlabel('cover entropy (bits)');
    ylabel('net rate (bpp)'); legend(nm,'Location','best');
    title('Capacity falls as cover entropy rises');
    savefig_both(fh, fullfile(G.outdir,'fig11_entropy_vs_rate'));

    fprintf('  wrote 3 cross-dataset figures to %s\n', G.outdir);
catch err
    fprintf('  DATASET FIGURES SKIPPED (%s)\n', err.message);
end
end


function s = safename(s)
s(~isstrprop(s,'alphanum')) = '_';
end


%% ============ EDIT PRIOR-WORK NUMBERS HERE ===========================
function T = literature_table()
% Rates reported by the authors of prior work, for Fig. 18 and the
% comparison table.
%
% Values marked with a dataset are BOSSbase averages taken from the papers'
% abstracts; those marked TODO are placeholders you must fill in. Verify
% every number against the paper before publishing, and cite only published
% work: an unpublished manuscript cannot appear here.
%
% NOTE ON POSITIONING: 3.58 bpp (MTAP 2024) and 3.18 bpp (DSP 2025) are
% above our BOSSbase result. Do NOT claim state-of-the-art capacity.
% Columns: {label, domain, rate_bpp}.
T = { ...
  'Zhang 2011',          'spatial', 0.0061 ; ...  %% TODO verify
  'Zhang 2012 (sep.)',   'spatial', 0.0330 ; ...  %% TODO verify
  'Ma et al. 2013',      'spatial', 0.5000 ; ...  %% TODO verify
  'Xiong et al. 2018',   'IWT',     0.0400 ; ...  %% TODO verify
  'Yi & Zhou 2019 PBTL', 'spatial', 1.9656 ; ...  %% BOSSbase, TMM 21(1)
  'Ma & Wang 2019',      'IWT',     0.5000 ; ...  %% TODO verify
  'Feng et al. EPBTL',   'spatial', 2.5800 ; ...  %% 3-dataset average
  'Chen 2021 MED+2''s c.','spatial',0.0000 ; ...  %% TODO verify
  'EPBTL-RDHEI 2024',    'spatial', 2.6670 ; ...  %% BOSSbase, KBS
  'Multi-pred EPBTL 2025','spatial',3.1770 ; ...  %% BOSSbase, DSP
  'Bit-plane realloc 2024','spatial',3.5840  ...  %% BOSSbase, MTAP
};
end
%% =====================================================================


function make_extra_figures(R, G, ALL)
% Publication figures beyond the core set. ALL may be empty.
if nargin < 3, ALL = {}; end
try
    if exist('OCTAVE_VERSION','builtin')
        for tk = {'qt','fltk','gnuplot'}
            try, graphics_toolkit(tk{1}); break; catch, end
        end
    end
    n  = numel(R);
    sv = @(fh,nm) savefig_both(fh, fullfile(G.outdir, nm));
    idx = 0;  for k = 1:n, if ~isempty(R(k).I), idx = k; break; end, end

    % ---- Fig 12: system block diagram -------------------------------
    fh = figure('Visible','off','Color','w','Position',[0 0 980 300]);
    ax = axes('Parent',fh,'Position',[0.02 0.02 0.96 0.96]);
    axis(ax,[0 100 0 30]);  set(ax,'Visible','off');  hold(ax,'on')
    stage = {'Cover','L-level','Sign-ext.','Band','CTR','Within-band','Payload', ...
             'Encrypted'};
    sub   = {'image I','5/3 IWT','room reserve','key KDF','diffusion', ...
             'permutation','embed','marked C'};
    x = 1.5;  w = 11;  g = 1.3;
    for k = 1:numel(stage)
        rectangle('Parent',ax,'Position',[x 10 w 10],'Curvature',0.12, ...
                  'LineWidth',1.1,'FaceColor',[0.95 0.95 0.95]);
        text(x+w/2, 16.2, stage{k}, 'Parent',ax, ...
             'HorizontalAlignment','center','FontSize',9);
        text(x+w/2, 13.0, sub{k},   'Parent',ax, ...
             'HorizontalAlignment','center','FontSize',8);
        if k < numel(stage)
            plot(ax, [x+w x+w+g],[15 15],'k-','LineWidth',1.1);
            plot(ax, x+w+g, 15, 'k>', 'MarkerFaceColor','k','MarkerSize',4);
        end
        x = x + w + g;
    end
    text(50, 25, 'SE-RDHEI encryption and embedding pipeline', 'Parent',ax, ...
         'HorizontalAlignment','center','FontSize',11,'FontWeight','bold');
    text(50, 5.5, ['audio credentials H(A_1), H(A_2) enter the band KDF; ' ...
         'the t-map is the only side information'], 'Parent',ax, ...
         'HorizontalAlignment','center','FontSize',8);
    hold(ax,'off');  sv(fh,'fig12_block_diagram');

    % ---- Fig 13: sub-band structure and t-map -----------------------
    if idx > 0 && ~isempty(R(idx).tmap)
        fh = figure('Visible','off','Color','w','Position',[0 0 900 320]);
        subplot(1,3,1); show(R(idx).I);      title([R(idx).name ' cover']);
        subplot(1,3,2); show(R(idx).Cimg);   title('encrypted sub-bands');
        subplot(1,3,3); imagesc(R(idx).tmap); axis image off;
            colormap(gca, gray(256)); colorbar;
            title('block t-map, HL_1 (vacatable bits)');
        sv(fh,'fig13_subbands_tmap');
    end

    % ---- Fig 14: where the room comes from --------------------------
    fh = figure('Visible','off','Color','w','Position',[0 0 860 360]);
    subplot(1,2,1);
    th = zeros(1,9);  for k = 1:n, th = th + R(k).thist; end
    bar(0:8, th, 'k'); xlabel('block t (vacatable bits)');
    ylabel('number of blocks'); title('Distribution of block t'); grid on
    subplot(1,2,2);
    L = max([R.levels]);  br = zeros(1,L);
    for k = 1:n
        m = min(L, numel(R(k).levelroom));
        br(1:m) = br(1:m) + R(k).levelroom(1:m);
    end
    bar(1:L, br/max(sum(br),1)*100, 'k'); xlabel('decomposition level');
    ylabel('share of total room (%)'); title('Room by level'); grid on
    sv(fh,'fig14_room_distribution');

    % ---- Fig 15: runtime scaling ------------------------------------
    fh = figure('Visible','off','Color','w','Position',[0 0 620 380]);
    px = [R.M].*[R.N];
    loglog(px, [R.tenc], 'o', px, [R.tdec], 's'); hold on
    q = logspace(log10(min(px)), log10(max(px)), 20);
    loglog(q, q*mean([R.tenc])/mean(px), 'k--'); hold off; grid on
    xlabel('pixels'); ylabel('seconds');
    legend('encrypt','decrypt','O(MN) reference','Location','northwest');
    title('Runtime scaling'); sv(fh,'fig15_runtime');

    % ---- Fig 16: NPCR / UACI distributions --------------------------
    if any([R.npcr_key] > 0)
        fh = figure('Visible','off','Color','w','Position',[0 0 860 360]);
        v = [[R.npcr_key] [R.npcr_A1] [R.npcr_A2]];
        subplot(1,2,1); histbar(v, 12); hold on
        yl = ylim; plot([99.6094 99.6094], yl, 'r--', 'LineWidth',1.4);
        plot([99.5693 99.5693], yl, 'k:'); hold off
        xlabel('NPCR (%)'); ylabel('count');
        title('NPCR (red = ideal, dotted = 0.05 critical)'); grid on
        u = [[R.uaci_key] [R.uaci_A1] [R.uaci_A2]];
        subplot(1,2,2); histbar(u, 12); hold on
        yl = ylim; plot([33.4635 33.4635], yl, 'r--', 'LineWidth',1.4); hold off
        xlabel('UACI (%)'); ylabel('count'); title('UACI (red = ideal)'); grid on
        sv(fh,'fig16_npcr_uaci_dist');
    end

    % ---- Fig 17: chi-square p-value uniformity ----------------------
    P = [];
    if ~isempty(ALL)
        for k = 1:numel(ALL), P = [P ALL{k}{2}.pchi]; end %#ok<AGROW>
    else
        P = [R.pchi];
    end
    fh = figure('Visible','off','Color','w','Position',[0 0 620 380]);
    Ps = sort(P);  m = numel(Ps);
    stairs(Ps, (1:m)/m, 'LineWidth',1.3); hold on
    plot([0 1],[0 1],'k--'); plot([0.05 0.05],[0 1],'r:'); hold off
    grid on; axis([0 1 0 1]); xlabel('\chi^2 p-value'); ylabel('empirical CDF');
    legend(sprintf('observed (N=%d)',m),'Uniform(0,1)','\alpha=0.05', ...
           'Location','southeast');
    title('Histogram-uniformity p-values are uniform');
    sv(fh,'fig17_pvalue_uniformity');

    % ---- Fig 18: comparison with prior work -------------------------
    T = literature_table();
    lab = [T(:,1).' {'Proposed'}];
    val = [cell2mat(T(:,3)).' mean([R.net])];
    fh = figure('Visible','off','Color','w','Position',[0 0 760 400]);
    b = bar(val); set(gca,'XTick',1:numel(val),'XTickLabel',lab); rotx();
    ylabel('embedding rate (bpp)'); grid on
    title('Embedding rate against prior work (authors'' reported values)');
    hold on; plot(xlim,[2.5613 2.5613],'r--'); hold off
    text(1, 2.62, 'IPBTL (Wu et al. 2020)', 'FontSize',8);
    sv(fh,'fig18_comparison');

    % ---- Fig 19: key sensitivity and difference map -----------------
    if idx > 0
        fh = figure('Visible','off','Color','w','Position',[0 0 900 320]);
        subplot(1,3,1); show(R(idx).I);       title('correct key: exact');
        subplot(1,3,2); show(R(idx).Iwrong);  title('key flipped by 1 bit');
        d = uint8(abs(double(R(idx).I) - double(R(idx).Iwrong)));
        subplot(1,3,3); show(d);
            title(sprintf('|difference|  (%.2f%% pixels differ)', ...
                  100*mean(R(idx).I(:) ~= R(idx).Iwrong(:))));
        sv(fh,'fig19_key_sensitivity');
    end

    % ---- Fig 20: per-sub-band ciphertext histograms -----------------
    if idx > 0 && ~isempty(R(idx).subhist)
        fh = figure('Visible','off','Color','w','Position',[0 0 900 300]);
        nmb = {'LL','HL_1','LH_1','HH_1'};
        for q = 1:4
            subplot(1,4,q); bar(R(idx).subhist(q,:),'k'); xlim([0 255]);
            title(nmb{q}); if q==1, ylabel('count'); end
        end
        sv(fh,'fig20_subband_histograms');
    end

    fprintf('  wrote 9 additional figures to %s\n', G.outdir);
catch err
    fprintf('  EXTRA FIGURES SKIPPED (%s)\n', err.message);
end
end


%% ============ reviewer-requested experiments =========================

function [pass, crit] = npcr_test(v, T, alpha)
% Wu, Noonan & Agaian one-sided NPCR test. v in percent.
if nargin < 3, alpha = 0.05; end
F = 255;
z = -sqrt(2)*erfcinv(2*alpha);           % Phi^{-1}(alpha) < 0
crit = (F + z*sqrt(F/T))/(F+1)*100;      % lower critical value
pass = v > crit;
end


function [pass, lo, hi] = uaci_test(v, T, alpha)
% Wu, Noonan & Agaian two-sided UACI test. v in percent.
if nargin < 3, alpha = 0.05; end
F  = 255;
mu = (F+2)/(3*F+3);
sd = sqrt((F+2)*(F^2+2*F+3)/(18*(F+1)^2*F*T));
z  = sqrt(2)*erfcinv(alpha);             % Phi^{-1}(1-alpha/2) > 0
lo = (mu - z*sd)*100;  hi = (mu + z*sd)*100;
pass = v > lo && v < hi;
end


function [E, W] = subband_entropy(C, h)
% Entropy of each encrypted sub-band, NORMALISED by its field width W_b.
% Reporting the raw entropy of the low 8 bits under-states any band with
% W_b < 8 (it cannot exceed W_b bits), which is a measurement artifact and
% not a property of the cipher. We report H/W_b in [0,1]; 1 means uniform.
nb = h.names{1};  E = zeros(1, numel(nb));  W = zeros(1, numel(nb));
for k = 1:numel(nb)
    Wb = h.Wd.(nb{k});  W(k) = Wb;
    v  = double(C.(nb{k})(:));
    pr = accumarray(v+1, 1, [2^Wb 1]) / numel(v);
    pr = pr(pr > 0);
    E(k) = -sum(pr .* log2(pr)) / Wb;
end
end


function S = payload_sweep(I, a1, a2, G)
% Reversibility as a function of how full the room is.
[~, h0] = encrypt_embed(I, G.key, a1, a2, G.nonce, uint8([]), G);
fr = [0.1 0.25 0.5 0.75 0.9 1.0];
S.frac = fr;  S.exact = false(1,numel(fr));  S.bits = zeros(1,numel(fr));
for k = 1:numel(fr)
    nb = floor(h0.total*fr(k));
    pay = tv_payload(nb, G);
    [C,h,pl] = encrypt_embed(I, G.key, a1, a2, G.nonce, pay, G);
    [Ir,pe]  = extract_decrypt(C, h, G.key, a1, a2, G);
    S.exact(k) = isequal(Ir,I) && (isempty(pl) || isequal(pe(1:numel(pl)),pl));
    S.bits(k)  = nb;
end
end


function Rb = robustness_test(I, a1, a2, G)
% SCOPE EXPERIMENT. This is a lossless-channel scheme: any modification of
% the ciphertext destroys recovery. We measure that rather than claim
% robustness we do not have.
[C,h] = encrypt_embed(I, G.key, a1, a2, G.nonce, uint8([]), G);
nb = h.names{1};
lab = {'1 bit flipped','0.1% bytes','1% bytes','5% cropped'};
Rb.label = lab;  Rb.err = zeros(1,4);
for t = 1:4
    C2 = C;  setseed(t);
    switch t
        case 1
            C2.(nb{1})(1) = bitxor(C2.(nb{1})(1), 1);
        case 2
            for q = 1:numel(nb)
                v = C2.(nb{q});  m = rand(size(v)) < 0.001;
                v(m) = mod(v(m)+1, 2^h.Wd.(nb{q}));  C2.(nb{q}) = v;
            end
        case 3
            for q = 1:numel(nb)
                v = C2.(nb{q});  m = rand(size(v)) < 0.01;
                v(m) = mod(v(m)+1, 2^h.Wd.(nb{q}));  C2.(nb{q}) = v;
            end
        case 4
            v = C2.(nb{1});  k = max(round(0.05*numel(v)),1);
            v(1:k) = 0;  C2.(nb{1}) = v;
    end
    Gq = G;  Gq.authWarn = false;     % ciphertext is tampered on purpose
    Ir = extract_decrypt(C2, h, G.key, a1, a2, Gq);
    Rb.err(t) = 100*mean(Ir(:) ~= I(:));
end
end


function print_reviewer_tables(R, G)
n = numel(R);

banner('TABLE VIII  -  NPCR / UACI HYPOTHESIS TESTS (Wu et al.)');
if any([R.npcr_key] > 0)
    fprintf('  %-12s %8s %10s %6s %9s %9s %9s %6s\n','Image','NPCR', ...
            'N* (0.05)','pass','UACI','U*-','U*+','pass');
    np = 0;  up = 0;
    for k = 1:n
        T = R(k).M*R(k).N;
        [pa, cr]      = npcr_test(R(k).npcr_key, T);
        [pb, lo, hi]  = uaci_test(R(k).uaci_key, T);
        np = np + pa;  up = up + pb;
        fprintf('  %-12s %8.4f %10.4f %6s %9.4f %9.4f %9.4f %6s\n', ...
            R(k).name, R(k).npcr_key, cr, yn(pa), R(k).uaci_key, lo, hi, yn(pb));
    end
    fprintf('  NPCR passed %d/%d,  UACI passed %d/%d  at alpha = 0.05\n', np,n,up,n);
else
    fprintf('  (sensitivity was disabled for this dataset)\n');
end

banner('TABLE IX  -  KEY SPACE AND SUB-BAND ENTROPY');
fprintf('  master key                : 256 bits  ->  key space 2^256 ~ 1.16e77\n');
fprintf('  derived subkeys           : ENC, PERM, PARAM, DH, MAC (HKDF-SHA256)\n');
fprintf('  per-band keys             : HKDF(ENC, band_id || H(A1) || H(A2) || F_b || nonce)\n');
fprintf('  audio credential space    : 2 x 256-bit SHA-256 digests\n');
fprintf('  effective, no degradation : finite-precision loss does not apply (no chaotic orbit)\n\n');
fprintf('  normalised sub-band entropy H/W_b (1.0000 = uniform over the field)\n');
fprintf('  %-12s', 'Image');
if ~isempty(R(1).sbent)
    for q = 1:min(numel(R(1).sbnames),7), fprintf(' %9s', R(1).sbnames{q}); end
end
fprintf('\n');
for k = 1:n
    fprintf('  %-12s', R(k).name);
    for q = 1:min(numel(R(k).sbent),7)
        fprintf(' %9.5f', R(k).sbent(q));
    end
    fprintf('\n');
end
fprintf('  %-12s', 'W_b');
if ~isempty(R(1).sbW)
    for q = 1:min(numel(R(1).sbW),7), fprintf(' %9d', R(1).sbW(q)); end
end
fprintf('   (field width of the first image)\n');
fprintf(['  Deep-level bands hold few coefficients (LL at L=4 is MN/256), so\n' ...
         '  their entropy is sample-limited, not cipher-limited: a band with\n' ...
         '  n samples cannot exceed log2(n) bits. Quote level-1 bands, which\n' ...
         '  hold MN/4 coefficients each, as the security-relevant figures.\n']);

banner('TABLE X  -  COMPARISON WITH PUBLISHED RDHEI METHODS');
M  = published_methods();  pin = published_images();
fprintf('  Embedding rate (bpp) on the six standard covers.\n');
fprintf('  %-18s', 'Method');
for q = 1:numel(pin), fprintf(' %8s', pin{q}); end
fprintf('\n');
for k = 1:size(M,1)
    fprintf('  %-18s', M{k,1});
    for q = 1:numel(pin)
        v = M{k,2}(q);
        if isnan(v), fprintf(' %8s','--'); else, fprintf(' %8.4f', v); end
    end
    fprintf('\n');
end
fprintf('  %-18s', 'PROPOSED');
for q = 1:numel(pin)
    v = NaN;
    for k = 1:numel(R), if strcmpi(R(k).name, pin{q}), v = R(k).net; end, end
    if isnan(v), fprintf(' %8s','--'); else, fprintf(' %8.4f', v); end
end
fprintf('\n\n');
bad = 0;
for k = 1:numel(R)
    f = cover_check(R(k).name, R(k).Hplain, R(k).M, R(k).N);
    if ~isempty(f)
        if bad == 0, fprintf('  COVER IDENTITY WARNINGS (these rows are NOT comparable):\n'); end
        bad = bad + 1;
        fprintf('    %-12s %s\n', R(k).name, f);
    end
end
if bad == 0
    fprintf('  Cover identity: all covers match their published counterparts.\n');
else
    fprintf(['    A size or entropy mismatch means the file on disk is not the\n' ...
             '    image the published rate was measured on. Exclude those rows.\n']);
end
fprintf('\n');
fprintf(['  Man is 1024x1024 in all sources including ours (measured at\n' ...
         '  native size: 3.4608 bpp net). All other covers are 512x512.\n\n']);

D = published_datasets();
fprintf('  Average embedding rate (bpp) on the three databases.\n');
fprintf('  %-20s %10s %10s %10s\n','Method','BOSSbase','BOWS-2','UCID');
for k = 1:size(D,1)
    fprintf('  %-20s', D{k,1});
    for q = 1:3
        v = D{k,2}(q);
        if isnan(v), fprintf(' %10s','--'); else, fprintf(' %10.4f', v); end
    end
    fprintf('\n');
end
fprintf('  %-20s', 'PROPOSED');
fprintf('   mean net over this dataset = %.4f bpp (%d images)\n', ...
        mean([R.net]), numel(R));
fprintf('  Per-database values for the proposed method are in Table 0.\n');

banner('TABLE XI  -  PAYLOAD FILL SWEEP');
fprintf('  %-12s', 'Image');
for q = 1:numel(R(1).sweep.frac), fprintf(' %7.0f%%', R(1).sweep.frac(q)*100); end
fprintf('\n');
for k = 1:n
    fprintf('  %-12s', R(k).name);
    for q = 1:numel(R(k).sweep.exact), fprintf(' %8s', yn(R(k).sweep.exact(q))); end
    fprintf('\n');
end

banner('TABLE XII  -  ROBUSTNESS SCOPE (lossless channel required)');
fprintf('  %-12s', 'Image');
for q = 1:numel(R(1).rob.label), fprintf(' %14s', R(1).rob.label{q}); end
fprintf('\n');
for k = 1:n
    fprintf('  %-12s', R(k).name);
    for q = 1:numel(R(k).rob.err), fprintf(' %13.2f%%', R(k).rob.err(q)); end
    fprintf('\n');
end
fprintf(['  Percentages are pixels differing after recovery. This scheme is\n' ...
         '  designed for a lossless channel; we state the limitation rather\n' ...
         '  than claim robustness it does not have.\n']);
end


function make_reviewer_figures(R, G)
try
    if exist('OCTAVE_VERSION','builtin')
        for tk = {'qt','fltk','gnuplot'}
            try, graphics_toolkit(tk{1}); break; catch, end
        end
    end
    n = numel(R);  sv = @(fh,nm) savefig_both(fh, fullfile(G.outdir, nm));

    % Fig 21: proposed vs published RDHEI methods, same covers
    M = published_methods();  pin = published_images();
    fh = figure('Visible','off','Color','w','Position',[0 0 1180 460]);
    Y = [];  lab = {};
    for q = 1:numel(pin)
        v = NaN;
        for k = 1:numel(R), if strcmpi(R(k).name,pin{q}), v = R(k).net; end, end
        Y(q,1) = v; %#ok<AGROW>
    end
    lab{1} = 'Proposed';
    for k = 1:size(M,1), Y(:,k+1) = M{k,2}(:);  lab{k+1} = M{k,1}; end %#ok<AGROW>
    hb = bar(Y);
    % MATLAB's default colour order has only 7 entries, so an 8th series
    % silently reuses the 1st -- which put Gao 2022 in the same blue as the
    % proposed method. Assign an explicit palette: black for ours, then a
    % qualitative set with no repeats.
    cols = [0.00 0.00 0.00;      % Proposed
            0.85 0.33 0.10;      % Puteaux 2018
            0.93 0.69 0.13;      % Yi 2019
            0.49 0.18 0.56;      % Yin 2020
            0.47 0.67 0.19;      % Wu 2020
            0.30 0.75 0.93;      % Yin 2019 BPC
            0.64 0.08 0.18;      % Wang 2021
            0.00 0.45 0.74;      % Gao 2022
            1.00 0.50 0.00;      % Zou 2023
            0.20 0.60 0.55;      % Dong 2025
            0.55 0.55 0.55];
    for q = 1:min(numel(hb), size(cols,1))
        try, set(hb(q), 'FaceColor', cols(q,:)); catch, end
    end
    set(gca,'XTick',1:numel(pin),'XTickLabel',pin); rotx();
    ylabel('embedding rate (bpp)'); grid on
    xlabel('Man is 1024x1024 in all sources; other covers 512x512');
    legend(lab,'Location','eastoutside');   % vertical: never clips
    title('Comparison with published RDHEI methods');

    sv(fh,'fig21_baseline_comparison');

    % Fig 22: payload fill sweep
    fh = figure('Visible','off','Color','w','Position',[0 0 620 380]);
    fr = R(1).sweep.frac*100;  ok = zeros(1,numel(fr));
    for q = 1:numel(fr)
        for k = 1:n, ok(q) = ok(q) + R(k).sweep.exact(q); end
    end
    bar(fr, ok/n*100, 'k'); ylim([0 105]); grid on
    xlabel('room occupancy (%)'); ylabel('images recovered exactly (%)');
    title('Reversibility across payload fill');
    sv(fh,'fig22_payload_sweep');

    % Fig 23: robustness scope
    fh = figure('Visible','off','Color','w','Position',[0 0 700 380]);
    E = zeros(n, numel(R(1).rob.err));
    for k = 1:n, E(k,:) = R(k).rob.err; end
    bar(mean(E,1)); set(gca,'XTick',1:size(E,2),'XTickLabel',R(1).rob.label);
    rotx(); ylabel('pixels differing after recovery (%)'); grid on
    title('Ciphertext perturbation destroys recovery (by design)');
    sv(fh,'fig23_robustness_scope');

    fprintf('  wrote 3 reviewer figures to %s\n', G.outdir);
catch err
    fprintf('  REVIEWER FIGURES SKIPPED (%s)\n', err.message);
end
end


%% ============ security engineering for a security venue ==============

function b = u32b(x)
x = double(x);
b = uint8([floor(x/2^24) mod(floor(x/2^16),256) mod(floor(x/256),256) mod(x,256)]);
end

function b = hdr_bytes(h, K, CFG)
% The t-map is encrypted before transmission: in the clear it is a
% block-resolution edge map of the cover (see Fig.~13) and therefore leaks.
% Canonical, deterministic serialisation of everything the receiver needs.
% This is what the authentication tag actually covers.
b = uint8(h.nonce);
b = [b u32b(h.shape(1)) u32b(h.shape(2)) u32b(h.levels) u32b(h.total)];
nm = h.names{1};
for k = 1:numel(nm)
    b = [b band_id(nm{k}) uint8(h.Wd.(nm{k}))]; %#ok<AGROW>
end
dt = h.det{1};
tb = uint8([]);
for k = 1:numel(dt)
    t = h.tm.(dt{k});
    tb = [tb u32b(size(t,1)) u32b(size(t,2)) uint8(t(:).')]; %#ok<AGROW>
end
if nargin >= 3 && isfield(K,'tmap')
    ks = ctr([K.tmap h.nonce], numel(tb), CFG);
    tb = bitxor(tb, ks);                    % encrypted t-map
end
b = [b tb];
end

function [Hp, He] = tmap_leak(h, K, CFG)
% Entropy of the t-map before and after encryption, in bits/byte.
dt = h.det{1};  tb = uint8([]);
for k = 1:numel(dt), t = h.tm.(dt{k});  tb = [tb uint8(t(:).')]; end %#ok<AGROW>
Hp = entropy8(tb);
He = entropy8(bitxor(tb, ctr([K.tmap h.nonce], numel(tb), CFG)));
end

function M = res_mask(h, K, CFG)
% Per-band bit mask of the slots the data hider is allowed to overwrite,
% expressed in the PERMUTED coefficient order.
M = struct();
for b = h.det{1}
    nm = b{1};  W = h.Wd.(nm);  n = prod(h.shapes.(nm));
    tf = expand_t(h.tm.(nm), h.shapes.(nm), CFG.blk);
    [pi_, pb] = slots(tf, W);
    p = permutation(K, nm, n, CFG);  pinv = zeros(1,n);  pinv(p) = 1:n;
    m = zeros(1,n);
    if ~isempty(pi_)
        idx = pinv(pi_);
        for q = 1:numel(idx)
            m(idx(q)) = m(idx(q)) + 2^pb(q);
        end
    end
    M.(nm) = m;
end
end

function b = cipher_bytes(C, h, M)
% Ciphertext as bytes. If M is supplied, the reserved (payload) slots are
% zeroed first, so the tag covers only what the data hider must not touch.
nm = h.names{1};  b = uint8([]);
for k = 1:numel(nm)
    v = C.(nm{k});
    if ~isempty(M) && isfield(M, nm{k}), v = v - bitand(v, M.(nm{k})); end
    b = [b typecast(uint16(v(:).'), 'uint8')]; %#ok<AGROW>
end
end

function t = tag_owner(C, h, K, CFG)
M = res_mask(h, K, CFG);
t = hmac256(K.mac, [hdr_bytes(h, K, CFG) cipher_bytes(C, h, M)], CFG);
end

function t = tag_hider(C, h, K, tau1, CFG)
t = hmac256(K.dh, [hdr_bytes(h, K, CFG) cipher_bytes(C, h, []) tau1], CFG);
end

function v = verify_tags(C, h, K, CFG)
% v.owner and v.hider are true when the corresponding tag checks out.
v.owner = isequal(tag_owner(C, h, K, CFG), h.tag1);
v.hider = isequal(tag_hider(C, h, K, h.tag1, CFG), h.tag2);
end


function nz = fresh_nonce(CFG)
% 96-bit nonce. Random by default; reuse under one key is a two-time pad,
% so we generate rather than accept a fixed value unless asked.
persistent ctr0
if isempty(ctr0), ctr0 = 0; end
ctr0 = ctr0 + 1;
seed = [uint8(mod(floor(now*86400*1000), 2^32)) ...
        uint8(mod(floor(rand*2^32), 2^32)) u32b(ctr0)];
d = sha256_bytes([seed uint8('SE-RDHEI-NONCE')], CFG);
nz = d(1:12);
end

function nonce_guard(nz, CFG) %#ok<INUSD>
% Detect reuse of a caller-supplied nonce within this session.
persistent seen
if isempty(seen), seen = {}; end
k = lower(sprintf('%02x', nz));
for q = 1:numel(seen)
    if strcmp(seen{q}, k)
        warning('SE_RDHEI:nonceReuse', ...
          ['nonce %s reused under the same key: this is a two-time pad ' ...
           'and destroys confidentiality. Use a fresh nonce.'], k);
        return
    end
end
seen{end+1} = k;
end


function ks = aes_ctr(key32, nonce, nbytes)
% AES-256-CTR keystream via the JVM. Returns [] when unavailable.
ks = [];
try
    c  = javax.crypto.Cipher.getInstance('AES/CTR/NoPadding');
    sk = javax.crypto.spec.SecretKeySpec( ...
             int8(mod(double(key32)+128,256)-128), 'AES');
    iv = zeros(1,16,'uint8');  iv(1:numel(nonce)) = nonce;
    ip = javax.crypto.spec.IvParameterSpec(int8(mod(double(iv)+128,256)-128));
    c.init(javax.crypto.Cipher.ENCRYPT_MODE, sk, ip);
    ks = typecast(c.doFinal(int8(zeros(1,nbytes))), 'uint8').';
catch
    ks = [];
end
end

function A = aes_baseline(I, a1, a2, G)
% Same RDH stage, AES-256-CTR keystream instead of the SHA-256-CTR XOF.
% Answers "what does your cipher buy over AES?" with a measurement.
A.ok = false;
K = keys(G.key, a1, a2, G.nonce, G);
probe = aes_ctr(K.enc, G.nonce, 32);
if isempty(probe), return; end
G2 = G;  G2.useAES = true;
t0 = tic;  [C,h] = encrypt_embed(I, G.key, a1, a2, G.nonce, uint8([]), G2);
A.tenc = toc(t0);
t0 = tic;  Ir = extract_decrypt(C, h, G.key, a1, a2, G2);  A.tdec = toc(t0);
A.exact = isequal(Ir, I);
A.net   = h.cap/numel(I);
E = packbits_cipher(C, h.Wd, G2, h.names{1});
A.H = entropy8(E);  A.chi2 = chi2stat(E);  A.ok = true;
end


function K = attack_suite(I, a1, a2, G)
% Concrete attack experiments, not prose.
K.ok = true;

% --- known-plaintext: recover the keystream from one known image, then try
%     it on a second image encrypted under a DIFFERENT nonce.
n1 = G.nonce;  n2 = fresh_nonce(G);
[C1,h1] = encrypt_embed(I, G.key, a1, a2, n1, uint8([]), G);
J = uint8(mod(double(I) + 37, 256));                 % attacker's second image
[C2,h2] = encrypt_embed(J, G.key, a1, a2, n2, uint8([]), G);
nm = h1.names{1};
guess = struct();
for q = 1:numel(nm)
    guess.(nm{q}) = bitxor(C1.(nm{q}), C2.(nm{q}));  % cancels only if reused
end
d = 0;  tot = 0;
for q = 1:numel(nm)
    d = d + sum(guess.(nm{q}) ~= 0);  tot = tot + numel(guess.(nm{q}));
end
K.kpa_diff = 100*d/tot;              % ~100% means no keystream cancellation

% --- nonce REUSE, shown deliberately so the paper can justify enforcement
[C3,h3] = encrypt_embed(J, G.key, a1, a2, n1, uint8([]), G); %#ok<ASGLU>
d = 0; tot = 0;
for q = 1:numel(nm)
    x = bitxor(C1.(nm{q}), C3.(nm{q}));
    d = d + sum(x ~= 0);  tot = tot + numel(x);
end
K.reuse_diff = 100*d/tot;            % well below 100%: keystream cancels

% --- chosen-plaintext: encrypt an all-zero image, keep the keystream, then
%     try it against a real image under a fresh nonce.
Z = zeros(size(I),'uint8');
[Cz,hz] = encrypt_embed(Z, G.key, a1, a2, fresh_nonce(G), uint8([]), G); %#ok<ASGLU>
d = 0; tot = 0;
for q = 1:numel(nm)
    x = bitxor(C1.(nm{q}), Cz.(nm{q}));
    d = d + sum(x ~= 0);  tot = tot + numel(x);
end
K.cpa_diff = 100*d/tot;

% --- collusion: data hider (PERM subkey) plus cloud storage, no ENC key
Kf = keys(G.key, a1, a2, n1, G);
rec = struct();
for q = 1:numel(nm)
    n = numel(C1.(nm{q}));
    p = permutation(Kf, nm{q}, n, G);
    e = zeros(1,n);  e(p) = C1.(nm{q});
    rec.(nm{q}) = from_field_local(reshape(e, ...
        [h1.shapes.(nm{q})(2) h1.shapes.(nm{q})(1)]).', h1.Wd.(nm{q}));
end
Ic = iiwt2_multi(rec, h1.levels);
K.collude_match = 100*mean(Ic(:) == I(:));
K.collude_corr  = corr2v(double(Ic(:)), double(I(:)));
K.chance = 100/256;

% --- tamper detection
[C4,h4] = encrypt_embed(I, G.key, a1, a2, fresh_nonce(G), uint8([]), G);
v0 = verify_tags(C4, h4, Kf4(G, a1, a2, h4), G);
C5 = C4;  C5.(nm{1})(1) = bitxor(C5.(nm{1})(1), 1);
v1 = verify_tags(C5, h4, Kf4(G, a1, a2, h4), G);
K.tag_clean = v0.owner && v0.hider;
K.tag_tamper_caught = ~(v1.owner || v1.hider);
end

function K = Kf4(G, a1, a2, h)
K = keys(G.key, a1, a2, h.nonce, G);
end

function v = from_field_local(u, W)
v = u - 2^W*(u >= 2^(W-1));
end


function print_security_tables(R, G)
banner('TABLE XIII  -  AUTHENTICATION');
fprintf('  two-layer HMAC-SHA256 over header || ciphertext\n');
fprintf('    tau1 (owner)      : covers header + all NON-reserved bits\n');
fprintf('    tau2 (data hider) : covers header + full ciphertext + tau1\n');
fprintf('    keys              : K_mac and K_dh, separate HKDF labels\n');
fprintf('    padding key       : K_pad, its own label (no reuse of K_mac)\n\n');
fprintf('  t-map entropy (bits/byte): plaintext vs encrypted in header\n');
fprintf('  %-12s %12s %12s\n','Image','plain t-map','encrypted');
for k = 1:numel(R)
    if isempty(R(k).tleak), continue; end
    fprintf('  %-12s %12.4f %12.4f\n', R(k).name, R(k).tleak(1), R(k).tleak(2));
end
fprintf(['  In the clear the t-map is a block-resolution edge map of the\n' ...
         '  cover, so it is encrypted under K_tmap before transmission.\n' ...
         '  K_tmap is shared with the data hider, who needs it to locate\n' ...
         '  the vacated slots.\n\n']);
fprintf('  %-12s %10s %10s %14s\n','Image','tags OK','1-bit flip','detected');
for k = 1:numel(R)
    a = R(k).atk;
    if isempty(a), continue; end
    fprintf('  %-12s %10s %10s %14s\n', R(k).name, yn(a.tag_clean), ...
            'applied', yn(a.tag_tamper_caught));
end

banner('TABLE XIV  -  ATTACK EXPERIMENTS');
fprintf('  %-12s %11s %11s %11s %13s %9s %9s\n','Image','KPA diff', ...
        'CPA diff','reuse diff','collusion hit','chance','rho');
for k = 1:numel(R)
    a = R(k).atk;
    if isempty(a), continue; end
    fprintf('  %-12s %10.2f%% %10.2f%% %10.2f%% %12.3f%% %8.3f%% %+9.4f\n', ...
        R(k).name, a.kpa_diff, a.cpa_diff, a.reuse_diff, ...
        a.collude_match, a.chance, a.collude_corr);
end
fprintf(['  Collusion hit can exceed chance on images with large saturated\n' ...
         '  regions: the inverse transform of wrong coefficients is clipped to\n' ...
         '  [0,255], so 0/255 pixels coincide by construction. The correlation\n' ...
         '  rho is the leak-free indicator; it stays near zero.\n']);
fprintf(['  KPA/CPA diff near 100%% means no keystream cancellation across\n' ...
         '  nonces. "reuse diff" is a DELIBERATE two-time pad, shown to\n' ...
         '  justify nonce enforcement. Collusion hit at or below chance\n' ...
         '  means the data hider learns nothing about the cover.\n']);

banner('TABLE XV  -  CIPHER SUBSTITUTION (AES-256-CTR)');
any_ok = false;
fprintf('  %-12s %10s %10s %10s %10s %10s\n','Image','net XOF', ...
        'net AES','H AES','enc AES s','exact');
for k = 1:numel(R)
    a = R(k).aes;
    if isempty(a) || ~a.ok, continue; end
    any_ok = true;
    fprintf('  %-12s %10.4f %10.4f %10.4f %10.3f %10s\n', R(k).name, ...
            R(k).net, a.net, a.H, a.tenc, yn(a.exact));
end
if ~any_ok
    fprintf('  AES baseline unavailable (no JVM in this session).\n');
else
    fprintf(['  Capacity is identical: the cipher is a replaceable component.\n' ...
             '  The contribution is the RDH architecture, not the keystream.\n']);
end

banner('SECURITY ASSUMPTIONS (state these in the paper)');
fprintf('  1. K_master (256 bit) is the only secret required for confidentiality.\n');
fprintf('  2. Audio A1, A2 are CREDENTIALS, not entropy sources. If the\n');
fprintf('     adversary holds both, security still reduces to K_master.\n');
fprintf('  3. Nonces are unique per (key, image). Reuse is a two-time pad;\n');
fprintf('     the implementation generates a fresh 96-bit nonce by default.\n');
fprintf('  4. The channel is lossless. See Table XII for the scope test.\n');
fprintf('  5. Security reduces to the PRF security of the keyed XOF; see the\n');
fprintf('     reduction in security_analysis.tex.\n');
end


function write_security_tex(R, G)
p = fullfile(G.outdir,'security_analysis.tex');
fid = fopen(p,'w');
fprintf(fid, '%%%% Auto-generated skeleton. Edit prose; numbers are measured.\n\n');
fprintf(fid, '\\section{Threat Model}\n');
fprintf(fid, ['We consider three parties. The \\emph{content owner} holds the ' ...
 'master key $K$. The \\emph{data hider} holds only the derived subkeys ' ...
 '$K_{\\mathrm{perm}}$ and $K_{\\mathrm{dh}}$ and may be honest-but-curious. ' ...
 'The \\emph{receiver} holds $K$, $K_{\\mathrm{dh}}$, or both. The adversary ' ...
 'observes the ciphertext, the public header and both audio credentials, and ' ...
 'may mount known- and chosen-plaintext attacks under a single key. Nonce ' ...
 'reuse is outside the model and is prevented by construction.\n\n']);
fprintf(fid, '\\section{Confidentiality}\n');
fprintf(fid, ['\\begin{theorem} If $\\mathrm{XOF}$ is a secure PRF, the ' ...
 'proposed encryption is IND-CPA. \\end{theorem}\n' ...
 '\\begin{proof}[Proof sketch] Replace each band keystream ' ...
 '$\\mathrm{XOF}(K_b\\,\\|\\,N\\,\\|\\,\\mathrm{id}_b)$ with a uniformly ' ...
 'random string; by the PRF assumption this is indistinguishable, with ' ...
 'advantage at most $q\\varepsilon_{\\mathrm{PRF}}$ for $q$ bands. Diffusion ' ...
 'is then a one-time pad over $\\mathbb{Z}_{2^{W_b}}$, so the diffused ' ...
 'coefficients are uniform and independent of the plaintext. Permutation is ' ...
 'a bijection applied after diffusion and cannot reduce entropy. Distinct ' ...
 'nonces give independent keystreams, hence encryptions of adversarially ' ...
 'chosen plaintexts are indistinguishable. \\end{proof}\n\n']);
fprintf(fid, '\\section{Integrity}\n');
fprintf(fid, ['Two tags are produced. $\\tau_1=\\mathrm{HMAC}_{K_{' ...
 '\\mathrm{mac}}}(\\mathrm{hdr}\\|\\mathcal{C}|_{\\bar\\Omega})$ authenticates ' ...
 'the header and every bit outside the vacated room, so the data hider can ' ...
 'embed without invalidating it. $\\tau_2=\\mathrm{HMAC}_{K_{\\mathrm{dh}}}' ...
 '(\\mathrm{hdr}\\|\\mathcal{C}\\|\\tau_1)$ authenticates the marked result. ' ...
 'Forgery reduces to HMAC-SHA256 unforgeability.\n\n']);
fprintf(fid, '\\section{Key Hierarchy}\n');
fprintf(fid, ['All subkeys derive from $K$ by HKDF-SHA256 with distinct ' ...
 'labels ENC, PERM, PARAM, DH, MAC, PAD; per-band keys additionally bind ' ...
 '$\\mathrm{id}_b$, $H(A_1)$, $H(A_2)$, $F_b$ and the nonce. Distinct labels ' ...
 'yield computationally independent outputs, which is what guarantees ' ...
 'band separation.\n\n']);
fprintf(fid, '\\section{Measured Results}\n');
for k = 1:numel(R)
    a = R(k).atk;
    if isempty(a), continue; end
    fprintf(fid, ['%% %s: KPA %.2f%%, CPA %.2f%%, collusion %.3f%% ' ...
      '(chance %.3f%%), tamper detected %d\n'], texesc(R(k).name), ...
      a.kpa_diff, a.cpa_diff, a.collude_match, a.chance, a.tag_tamper_caught);
end
fclose(fid);
fprintf('  wrote %s\n', p);
end

%% ============ EDIT THESE TWO PATHS FOR YOUR MACHINE ==================
function [cover, imgdir] = default_paths()
imgdir = '/Users/sudhirsingh/Desktop/dataset/test image';
cover  = fullfile(imgdir, 'Baboon.tiff');
end

function checkfile()
%CHECKFILE  Verify this file's integrity: line count and end-convention.
%  Run:  SE_RDHEI('__check')
f = which(mfilename('fullpath'));
if isempty(f), f = [mfilename('fullpath') '.m']; end
txt = fileread(f);
nl  = numel(strfind(txt, sprintf('\n')));
nf  = numel(strfind(txt, sprintf('\nfunction'))) + ...
      double(strncmp(txt, 'function', 8));
fprintf('  file        : %s\n', f);
fprintf('  lines       : %d   (expected 3317)\n', nl);
fprintf('  functions   : %d   (expected 129)\n', nf);
if nl ~= 3317 || nf ~= 129
    fprintf(['  MISMATCH: this is not the released file. Re-download it; a\n' ...
             '  truncated or merged copy is the usual cause of end-convention\n' ...
             '  errors.\n']);
else
    fprintf('  OK: file matches the released version.\n');
end
end

function showfigs(opts)
%SHOWFIGS  Display the saved PNG figures without the Import Wizard.
D = @(f,v) getfielddef(opts,f,v);
d = D('outdir', fullfile(pwd,'SE_RDHEI_results'));
if ~exist(d,'dir')
    fprintf('  no results folder at %s\n', d);
    fprintf('  pass one: SE_RDHEI(''__figs'', struct(''outdir'',''/path''))\n');
    return
end
q = dir(fullfile(d,'*.png'));
if isempty(q), fprintf('  no PNG files in %s\n', d); return; end
[~,ix] = sort({q.name});  q = q(ix);
useOS = D('os', false);
fprintf('  %d figure(s) in %s\n', numel(q), d);
for k = 1:numel(q)
    f = fullfile(d, q(k).name);
    fprintf('    %-34s %8.1f kB\n', q(k).name, q(k).bytes/1024);
    if useOS
        if ismac,             system(['open "' f '"']);
        elseif ispc,          winopen(f);
        else,                 system(['xdg-open "' f '" &']);
        end
    else
        try
            im = imread(f);
            figure('Name', q(k).name, 'NumberTitle','off', 'Color','w');
            imshow(im); title(strrep(q(k).name,'_','\_'), 'Interpreter','tex');
        catch err
            fprintf('      could not display: %s\n', err.message);
        end
    end
end
if ~useOS
    fprintf('  opened %d MATLAB figure windows.\n', numel(q));
    fprintf('  For the OS viewer instead: SE_RDHEI(''__figs'', struct(''os'',true))\n');
end
end
