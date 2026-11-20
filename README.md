# SE-RDHEI

Reversible data hiding in encrypted images by **sign-extension room reservation**
and **deferred synthesis**.

Code for the paper *Reversible data hiding in encrypted images via sign-extension
room reservation and deferred synthesis* (Harshita, Poonam Bansal; submitted to
Computers & Electrical Engineering).

## What is here

| Path | Role |
|---|---|
| `serdhei.py` | **Reference implementation** of the specified construction analysed in the paper (Section 4.6, Algorithm 3, Propositions 1–3): AES-256-CTR, HKDF, nonce-bound block permutations, encrypted Huffman-coded t-map, data hider with its own key. Pure Python + NumPy. |
| `example.py` | End-to-end use of the four roles on one image. |
| `spec_test_vector.py`, `spec_test_vector.json` | Cross-language test vector: fixed keys, nonce, payload and a 64×64 synthetic cover; digests of every intermediate object. |
| `prototype/SE_RDHEI.m` | Earlier MATLAB prototype of the **base construction** (SHA-256 counter-mode stream, optional credentials A1/A2). Not covered by the propositions. Its default block size is `blk = 8`; the paper uses `blk = 2`. |
| `se_full.py` | Python port of the prototype, used by the experiments (reproduces the MATLAB capacity values bit-exactly). |
| `run_all.py` | Driver that produces every number and figure of the paper. |
| `extra_experiments.py`, `spec_experiments.py`, `matched_comparison.py` | Block-minimum efficiency and t-map leakage; specified-construction tests (RFC 5869 / SP 800-38A vectors, tamper tests, 20-key statistics); identical-image comparison. |
| `bpc.py`, `abcs.py`, `abcs_roundtrip.py`, `validate.py` | Validated reimplementations of Yin et al. (bit-plane compression) and Xiao et al. 2024 (adaptive block coding selection), with their validation against the published per-image figures. |
| `colour_experiment.py` | Colour covers: the scheme per RGB channel and after the JPEG 2000 reversible colour transform (`python colour_experiment.py out.json img1.tiff ...`). |
| `mkfigs.py` | Draws the data figures from `data.json`. |
| `colab/SE_RDHEI_results.ipynb` | Self-contained Colab notebook that runs everything (the scripts are embedded). |
| `results/` | Reports and JSON outputs of the runs reported in the paper (block size B = 2; 12 covers, 500 images each of BOSSbase 1.01, BOWS-2 256×256 and UCID; `colour.json` for the six USC-SIPI colour images). |

## Requirements

Python 3.9 or later with `numpy`, `scipy`, `pillow` and `matplotlib`:

```
pip install -r requirements.txt
```

## Quick start

```
python example.py                 # synthetic 512x512 cover
python example.py path/to/image   # any grey or colour image (converted to luminance)
python spec_test_vector.py --check
```

```python
import os, numpy as np, serdhei as S
K, nonce, K_H = os.urandom(32), os.urandom(12), os.urandom(32)   # fresh nonce per image
C, H0, tau1 = S.spec_owner(I, K, nonce)                  # content owner
K_tmap = S.owner_keys(K, nonce)['tmap']                  # the only owner key the hider gets
D = np.random.randint(0, 2, S.hider_room(H0, K_tmap), dtype=np.uint8)
Cm, H, tau2 = S.spec_hider(C, H0, tau1, K_tmap, K_H, D)  # data hider
D2 = S.spec_extract(Cm, H, tau1, tau2, K_tmap, K_H)      # payload receiver
I2 = S.spec_recover(Cm, H, tau1, K)                      # cover receiver
```

`spec_extract` and `spec_recover` return `None` when their tag does not verify.
Image dimensions must be divisible by 2^L (L ≤ 4 is chosen automatically).
The block size defaults to B = 2; set the environment variable `SE_BLOCK` to change it.

## Reproducing the paper

Open `colab/SE_RDHEI_results.ipynb` in Google Colab, upload the image databases
as described in its first cell, and run all cells (about 2–3 hours on a CPU
runtime for 12 covers and 3 × 500 database images). Or locally:

```
python run_all.py --data DATA_DIR --out OUT_DIR --n 500 --trials 10
```

`DATA_DIR` holds one folder per database (`USC-SIPI`, `BOSSbase`, `BOWS-2`, `UCID`).
The report `OUT_DIR/REPORT.md` starts with a check of every key-independent
value against the recorded MATLAB run (`recorded_matlab.json`).
