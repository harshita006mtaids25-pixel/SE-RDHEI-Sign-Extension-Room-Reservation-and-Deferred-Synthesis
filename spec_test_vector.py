"""Reproducible test vector for the specified construction (Section 4.6).

Inputs are fixed and derivable without any image file:
  cover   I[y, x] = (7x + 13y + (x*y mod 31)) mod 256,  64 x 64, uint8
  K       bytes 0x00..0x1f            (owner master key)
  K_H     bytes 0x20..0x3f            (data hider's own key)
  N       bytes 0x40..0x4b            (96-bit nonce)
  D       the first min(4096, |Omega|) bits of SHA-256(b'SE-RDHEI test payload' || <i>_32), i = 0, 1, ...
The optional credentials A1, A2 are disabled (Section 7.6), and the permuted
t-map is carried uncoded, one byte per block, as in the reference code.
Outputs: room, SHA-256 of the serialised ciphertext before and after embedding
and of the owner header, both tags, and the two exactness checks.
Writes spec_test_vector.json next to this file; with --check it compares a
fresh run against the stored vector and exits non-zero on any mismatch.
"""
import hashlib, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import serdhei as S


def cover():
    y, x = np.mgrid[0:64, 0:64]
    return ((7 * x + 13 * y + (x * y) % 31) % 256).astype(np.uint8)


def payload(n):
    out, i = b'', 0
    while len(out) * 8 < n:
        out += hashlib.sha256(b'SE-RDHEI test payload' + i.to_bytes(4, 'big')).digest(); i += 1
    return np.unpackbits(np.frombuffer(out, np.uint8))[:n]


def run():
    I = cover()
    K, KH, N = bytes(range(32)), bytes(range(32, 64)), bytes(range(64, 76))
    C, H0, t1 = S.spec_owner(I.astype(np.int64), K, N)
    kt = S.owner_keys(K, N)['tmap']
    T = S._decrypt_tmap(H0, kt)
    room = int(sum(int(T[b].sum()) * H0['B'] ** 2 for b in T))
    D = payload(min(4096, room))
    Cm, H1, t2 = S.spec_hider(C, H0, t1, kt, KH, D)
    got = S.spec_extract(Cm, H1, t1, t2, kt, KH)
    R = S.spec_recover(Cm, H1, t1, K)
    h = lambda b: hashlib.sha256(b).hexdigest()
    return dict(
        cover_sha256=h(I.tobytes()), room_bits=room, payload_bits=int(D.size),
        C_sha256=h(S._ser_all(C, H0)), H0_sha256=h(S._ser_header(H0)), tau1=t1.hex(),
        Cmarked_sha256=h(S._ser_all(Cm, H1)), H_sha256=h(S._ser_header(H1)), tau2=t2.hex(),
        payload_exact=bool(got is not None and np.array_equal(np.asarray(got)[:D.size], D)),
        cover_exact=bool(R is not None and np.array_equal(np.asarray(R).astype(np.uint8), I)))


if __name__ == '__main__':
    v = run()
    p = os.path.join(HERE, 'spec_test_vector.json')
    if '--check' in sys.argv:
        ref = json.load(open(p))
        bad = [k for k in ref if ref[k] != v[k]]
        print('test vector', 'MATCHES' if not bad else 'DIFFERS in ' + ', '.join(bad))
        sys.exit(1 if bad else 0)
    json.dump(v, open(p, 'w'), indent=1)
    print(json.dumps(v, indent=1))
