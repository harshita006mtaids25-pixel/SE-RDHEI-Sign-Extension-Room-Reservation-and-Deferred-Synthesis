# SE-RDHEI results

Generated 2026-11-20 07:51:00 on x86_64, Python 3.13.18.  Key bytes 0..31, nonce "0123456789ab", B = 2, 10 sensitivity trials.  Credentials A1/A2: deterministic synthetic clips (SE_RDHEI.m fallback).

## 0. Validation against the recorded MATLAB run (key-independent quantities, at its block size B = 4)

| cover | capacity row | B sweep | L sweep | room (ablation) | t-map entropy |
|---|---|---|---|---|---|
| Airplane | match | match | match | match | match |
| Baboon | match | match | match | match | match |
| Jetplane | match | match | match | match | match |
| Lena | match | match | match | match | match |
| Man | match | match | match | match | match |
| Tiffany | match | match | match | match | match |
| barbara | match | match | match | match | match |
| boat | match | match | match | match | match |
| goldhill | match | match | match | match | match |
| lake | match | match | match | match | match |
| livingroom | match | match | match | match | match |
| peppers | match | match | match | match | match |

All key-independent values reproduce the recorded run on the same cover files. A difference means the uploaded file is not the file used in the MATLAB run.

## 1. Capacity and reversibility (Table 3, Fig. 5)

| image | L | exact | raw | side | net | container | eff |
|---|---|---|---|---|---|---|---|
| Airplane | 4 | YES | 4.8758 | 0.5755 | 4.3004 | 8.355 | 3.9449 |
| Baboon | 4 | YES | 2.8275 | 0.5916 | 2.2358 | 8.477 | 1.7593 |
| Jetplane | 4 | YES | 4.6838 | 0.6285 | 4.0553 | 8.438 | 3.6178 |
| Lena | 4 | YES | 3.6776 | 0.5915 | 3.0861 | 7.652 | 3.0861 |
| Man | 4 | YES | 4.8057 | 0.5917 | 4.2140 | 9.254 | 2.9601 |
| Tiffany | 4 | YES | 4.8584 | 0.6784 | 4.1801 | 8.762 | 3.4183 |
| barbara | 4 | YES | 3.7914 | 0.6521 | 3.1393 | 8.148 | 2.9908 |
| boat | 4 | YES | 3.5610 | 0.5953 | 2.9656 | 8.113 | 2.8524 |
| goldhill | 4 | YES | 3.3497 | 0.5832 | 2.7666 | 7.824 | 2.7666 |
| lake | 4 | YES | 3.1745 | 0.6403 | 2.5342 | 7.938 | 2.5342 |
| livingroom | 4 | YES | 3.7325 | 0.5840 | 3.1485 | 8.246 | 2.9024 |
| peppers | 4 | YES | 3.8763 | 0.5752 | 3.3011 | 8.188 | 3.1136 |
| MEAN |  |  | 3.9345 | 0.6073 | 3.3272 | 8.283 | 2.9955 |

## 2. Per-dataset rates (Table 4, Figs. 5-6)

| dataset | N | sizes | exact | net mean | net sd | net min | net max | eff mean | eff sd | H cipher | mean max|rho| | chi2 rejections |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BOSSbase | 500 | 512x512 | 500/500 | 3.7831 | 0.7334 | 1.4771 | 6.3209 | 3.5022 | 0.7815 | 7.9993 | 0.0025 | 19/500 |
| UCID | 500 | 384x512 512x384 | 500/500 | 3.6068 | 0.6512 | 1.6217 | 5.6596 | 3.0336 | 0.7557 | 7.9991 | 0.0028 | 36/500 |
| USC-SIPI | 12 | 1024x1024 512x512 | 12/12 | 3.3272 | 0.6697 | 2.2358 | 4.3004 | 2.9955 | 0.5255 | 7.9994 | 0.0022 | 0/12 |

## 3. Ciphertext statistics (Table 7, Figs. 9-10)

| image | H plain | H cipher | chi2 | p | plain H,V,D | cipher H,V,D |
|---|---|---|---|---|---|---|
| Airplane | 4.0045 | 7.9993 | 280.0 | 0.135 | +0.9463, +0.9459, +0.8962 | +0.0029, +0.0011, +0.0011 |
| Baboon | 7.3583 | 7.9995 | 207.6 | 0.987 | +0.8665, +0.7587, +0.7262 | -0.0027, +0.0014, +0.0008 |
| Jetplane | 6.7025 | 7.9992 | 287.5 | 0.079 | +0.9663, +0.9641, +0.9370 | +0.0012, -0.0026, -0.0019 |
| Lena | 7.4451 | 7.9993 | 242.5 | 0.703 | +0.9719, +0.9850, +0.9593 | +0.0004, +0.0003, +0.0016 |
| Man | 7.5237 | 7.9999 | 239.1 | 0.755 | +0.9774, +0.9813, +0.9671 | -0.0006, -0.0013, -0.0009 |
| Tiffany | 6.6009 | 7.9994 | 236.2 | 0.795 | +0.9382, +0.9403, +0.8929 | -0.0018, -0.0018, -0.0001 |
| barbara | 7.4664 | 7.9994 | 215.2 | 0.967 | +0.8597, +0.9591, +0.8418 | -0.0018, +0.0002, -0.0027 |
| boat | 7.1914 | 7.9993 | 242.7 | 0.7 | +0.9381, +0.9713, +0.9222 | -0.0021, -0.0010, +0.0004 |
| goldhill | 7.4778 | 7.9993 | 244.8 | 0.665 | +0.9714, +0.9745, +0.9532 | +0.0013, -0.0032, -0.0002 |
| lake | 7.4845 | 7.9992 | 271.1 | 0.233 | +0.9751, +0.9715, +0.9578 | +0.0002, +0.0014, -0.0001 |
| livingroom | 7.2952 | 7.9994 | 235.7 | 0.802 | +0.9462, +0.9528, +0.9116 | -0.0014, -0.0007, -0.0014 |
| peppers | 7.5925 | 7.9994 | 228.4 | 0.883 | +0.9767, +0.9791, +0.9638 | -0.0030, +0.0001, -0.0019 |

## 4. Key and credential sensitivity, Wu-Noonan-Agaian tests at alpha = 0.05 (Fig. 11)

Key: one bit of the master key K of the specified construction flipped, encrypted images compared. A1/A2: credentials of the base construction.
| image | NPCR key | sd | N* | pass | UACI key | sd | U*- | U*+ | pass | NPCR/UACI A1 | NPCR/UACI A2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Airplane | 99.6106 | 0.0171 | 99.5898 | YES | 33.4472 | 0.0401 | 33.3749 | 33.5522 | YES | 87.3483 / 7.0830 | 87.3119 / 7.0695 |
| Baboon | 99.6057 | 0.0125 | 99.5899 | YES | 33.4551 | 0.0496 | 33.3755 | 33.5515 | YES | 96.4737 / 15.7953 | 96.4747 / 15.7747 |
| Jetplane | 99.6111 | 0.0137 | 99.5899 | YES | 33.4771 | 0.0351 | 33.3753 | 33.5517 | YES | 87.9069 / 9.2731 | 87.9109 / 9.2683 |
| Lena | 99.6071 | 0.0100 | 99.5889 | YES | 33.4801 | 0.0477 | 33.3709 | 33.5562 | YES | 92.3305 / 14.1383 | 92.3211 / 14.1349 |
| Man | 99.6080 | 0.0044 | 99.6001 | YES | 33.4787 | 0.0195 | 33.4214 | 33.5057 | YES | 90.3507 / 18.0625 | 90.3484 / 18.0590 |
| Tiffany | 99.6075 | 0.0107 | 99.5902 | YES | 33.4842 | 0.0399 | 33.3770 | 33.5501 | YES | 87.6013 / 9.7341 | 87.4998 / 9.7215 |
| barbara | 99.6086 | 0.0081 | 99.5895 | YES | 33.4750 | 0.0609 | 33.3738 | 33.5533 | YES | 92.1771 / 14.6098 | 92.1996 / 14.6129 |
| boat | 99.6117 | 0.0127 | 99.5895 | YES | 33.4726 | 0.0377 | 33.3736 | 33.5535 | YES | 93.9017 / 14.4155 | 93.8695 / 14.4152 |
| goldhill | 99.6084 | 0.0092 | 99.5891 | YES | 33.4849 | 0.0300 | 33.3719 | 33.5551 | YES | 94.2339 / 9.7591 | 94.2078 / 9.7582 |
| lake | 99.6118 | 0.0140 | 99.5893 | YES | 33.4560 | 0.0469 | 33.3726 | 33.5545 | YES | 94.3788 / 12.7890 | 94.3620 / 12.7899 |
| livingroom | 99.6102 | 0.0129 | 99.5896 | YES | 33.4856 | 0.0434 | 33.3743 | 33.5528 | YES | 93.4920 / 8.2807 | 93.5173 / 8.2848 |
| peppers | 99.6089 | 0.0096 | 99.5896 | YES | 33.4732 | 0.0511 | 33.3740 | 33.5531 | YES | 92.8534 / 6.5381 | 92.8363 / 6.5441 |

NPCR mean 99.6091 (range 99.6057 to 99.6118), UACI mean 33.4725 (range 33.4472 to 33.4856); NPCR passed 12/12, UACI passed 12/12.

## 4b. Plaintext sensitivity, one pixel +-1 (specified construction)

| image | NPCR fresh nonce | UACI fresh nonce | passed N/U | NPCR same nonce | UACI same nonce |
|---|---|---|---|---|---|
| Airplane | 99.6071 | 33.4571 | 10/10, 10/10 | 0.00226 | 0.000114 |
| Baboon | 99.6096 | 33.4541 | 10/10, 9/10 | 0.00284 | 0.000325 |
| Jetplane | 99.6125 | 33.4671 | 10/10, 9/10 | 0.00181 | 0.000134 |
| Lena | 99.6063 | 33.4983 | 10/10, 10/10 | 0.00171 | 0.000149 |
| Man | 99.6113 | 33.4723 | 10/10, 9/10 | 0.00058 | 0.000072 |
| Tiffany | 99.6111 | 33.4288 | 10/10, 7/10 | 0.00195 | 0.000209 |
| barbara | 99.6161 | 33.4618 | 10/10, 10/10 | 0.00311 | 0.000307 |
| boat | 99.6122 | 33.4666 | 10/10, 10/10 | 0.00158 | 0.000202 |
| goldhill | 99.6039 | 33.4836 | 9/10, 10/10 | 0.00254 | 0.000163 |
| lake | 99.6092 | 33.4718 | 8/10, 10/10 | 0.00119 | 0.000074 |
| livingroom | 99.6161 | 33.4879 | 10/10, 9/10 | 0.00241 | 0.000260 |
| peppers | 99.6067 | 33.4861 | 10/10, 10/10 | 0.00127 | 0.000031 |

## 4c. Key sensitivity on marked images (same K_H and payload)

| image | NPCR | UACI | passed N/U |
|---|---|---|---|
| Airplane | 99.5580 | 33.3558 | 1, 5 |
| Baboon | 99.6078 | 33.3957 | 8, 7 |
| Jetplane | 99.5833 | 33.3557 | 3, 4 |
| Lena | 99.5962 | 33.4074 | 8, 9 |
| Man | 99.5981 | 33.4318 | 3, 7 |
| Tiffany | 99.5744 | 33.3474 | 1, 4 |
| barbara | 99.5908 | 33.3841 | 4, 5 |
| boat | 99.5943 | 33.3552 | 8, 4 |
| goldhill | 99.5914 | 33.3564 | 5, 4 |
| lake | 99.6040 | 33.3466 | 10, 1 |
| livingroom | 99.6008 | 33.3804 | 9, 5 |
| peppers | 99.5889 | 33.3179 | 4, 1 |

## 5. Block-size sweep, net bpp (Fig. 7)

| image | B=2 | B=4 | B=8 | B=16 | B=32 |
|---|---|---|---|---|---|
| Airplane | 4.3004 | 3.9959 | 3.4414 | 2.6961 | 1.8218 |
| Baboon | 2.2358 | 2.0229 | 1.6450 | 1.2230 | 0.7756 |
| Jetplane | 4.0553 | 3.8017 | 3.2982 | 2.6744 | 1.9584 |
| Lena | 3.0861 | 2.8325 | 2.3721 | 1.8399 | 1.2519 |
| Man | 4.2140 | 3.9383 | 3.4608 | 2.9264 | 2.3082 |
| Tiffany | 4.1801 | 3.9610 | 3.4403 | 2.7217 | 1.8685 |
| barbara | 3.1393 | 2.9663 | 2.5167 | 1.9656 | 1.3767 |
| boat | 2.9656 | 2.6750 | 2.1857 | 1.6666 | 1.2011 |
| goldhill | 2.7666 | 2.5024 | 2.0547 | 1.5624 | 1.1153 |
| lake | 2.5342 | 2.2989 | 1.8128 | 1.2715 | 0.7366 |
| livingroom | 3.1485 | 2.8408 | 2.3079 | 1.7203 | 1.1231 |
| peppers | 3.3011 | 3.0140 | 2.4847 | 1.8456 | 1.1545 |

## 6. Decomposition-level sweep, effective bpp (Fig. 7)

| image | L=1 | L=2 | L=3 | L=4 |
|---|---|---|---|---|
| Airplane | 2.7994 | 3.6843 | 3.8950 | 3.9449 |
| Baboon | 1.1937 | 1.6312 | 1.7336 | 1.7593 |
| Jetplane | 2.6911 | 3.3713 | 3.5716 | 3.6178 |
| Lena | 2.2291 | 2.9269 | 3.0580 | 3.0861 |
| Man | 1.9069 | 2.7431 | 2.9381 | 2.9601 |
| Tiffany | 2.1972 | 3.1514 | 3.3708 | 3.4183 |
| barbara | 2.1346 | 2.8088 | 2.9609 | 2.9908 |
| boat | 1.7778 | 2.6275 | 2.8110 | 2.8524 |
| goldhill | 2.1150 | 2.6467 | 2.7407 | 2.7666 |
| lake | 1.8318 | 2.3880 | 2.5108 | 2.5342 |
| livingroom | 1.8533 | 2.6714 | 2.8741 | 2.9024 |
| peppers | 2.1804 | 2.8629 | 3.0693 | 3.1136 |

## 7. Ablations (Table 6, Fig. 8)

| image | overflow, classic order | overflow, ours | room, modular lifting | room, ours |
|---|---|---|---|---|
| Airplane | 58656 | 0 | 56416 | 1278172 |
| Baboon | 51844 | 0 | 38464 | 741200 |
| Jetplane | 70810 | 0 | 90092 | 1227828 |
| Lena | 12638 | 0 | 80104 | 964048 |
| Man | 450357 | 0 | 243400 | 5039180 |
| Tiffany | 128980 | 0 | 56872 | 1273604 |
| barbara | 53384 | 0 | 87360 | 993880 |
| boat | 47494 | 0 | 56628 | 933488 |
| goldhill | 24169 | 0 | 68764 | 878112 |
| lake | 36893 | 0 | 44184 | 832180 |
| livingroom | 22964 | 0 | 94064 | 978448 |
| peppers | 30209 | 0 | 52092 | 1016152 |

## 8. Runtime (Section 6.6), this machine

| image | pixels | encrypt s | decrypt s |
|---|---|---|---|
| Airplane | 262144 | 0.215 | 0.163 |
| Baboon | 262144 | 0.235 | 0.205 |
| Jetplane | 262144 | 0.215 | 0.138 |
| Lena | 262144 | 0.332 | 0.227 |
| Man | 1048576 | 1.001 | 0.666 |
| Tiffany | 262144 | 0.209 | 0.166 |
| barbara | 262144 | 0.332 | 0.137 |
| boat | 262144 | 0.197 | 0.134 |
| goldhill | 262144 | 0.189 | 0.136 |
| lake | 262144 | 0.193 | 0.133 |
| livingroom | 262144 | 0.213 | 0.186 |
| peppers | 262144 | 0.2 | 0.143 |

512x512 mean: encrypt 0.230 s, decrypt 0.161 s.

## 9. t-map leakage and wrong-key recovery (Section 7)

| image | t-map entropy plain | encrypted | pixels equal to cover after 1-bit wrong key (%) |
|---|---|---|---|
| Airplane | 2.2319 | 7.9976 | 0.1102 |
| Baboon | 2.3322 | 7.9974 | 0.2033 |
| Jetplane | 2.4822 | 7.9974 | 0.1225 |
| Lena | 2.3388 | 7.9979 | 0.2163 |
| Man | 2.3092 | 7.9991 | 1.6221 |
| Tiffany | 2.6686 | 7.9976 | 0.2113 |
| barbara | 2.5678 | 7.9973 | 0.2602 |
| boat | 2.3291 | 7.9974 | 0.1545 |
| goldhill | 2.2871 | 7.9973 | 0.2293 |
| lake | 2.5200 | 7.9974 | 0.1961 |
| livingroom | 2.2721 | 7.9974 | 0.2480 |
| peppers | 2.2471 | 7.9975 | 0.1972 |

## 10. Credential ablation (Section 7.6)

Mean ciphertext entropy over 12 covers: with credentials 7.99939, with the credential terms removed 7.99937.

## 7b. Ablation at full depth L, same reservation and payload as the scheme (three payloads)

| image | L | classic ordering: px out of range (min..max) | deferred | modular room | proposed room |
|---|---|---|---|---|---|
| Airplane | 4 | 108209..109078 | 0 | 61776 | 1278172 |
| Baboon | 4 | 109257..109575 | 0 | 43508 | 741200 |
| Jetplane | 4 | 126981..127169 | 0 | 96712 | 1227828 |
| Lena | 4 | 82367..83240 | 0 | 85096 | 964048 |
| Man | 4 | 595241..596571 | 0 | 262020 | 5039180 |
| Tiffany | 4 | 138003..138484 | 0 | 62776 | 1273604 |
| barbara | 4 | 100171..100565 | 0 | 92384 | 993880 |
| boat | 4 | 109345..109512 | 0 | 61560 | 933488 |
| goldhill | 4 | 81749..82127 | 0 | 73752 | 878112 |
| lake | 4 | 115747..116105 | 0 | 49932 | 832180 |
| livingroom | 4 | 108799..109588 | 0 | 98924 | 978448 |
| peppers | 4 | 114718..114838 | 0 | 57404 | 1016152 |

## 14b. Specified construction end to end on every image (AES-256-CTR, full payload)

Stored header and tags minus the Huffman t-map cost R_t (bits): BOSSbase/BOSSbase_1.01/1012.pgm 830, BOSSbase/BOSSbase_1.01/102.pgm 824, BOSSbase/BOSSbase_1.01/1032.pgm 825, BOSSbase/BOSSbase_1.01/106.pgm 826, BOSSbase/BOSSbase_1.01/1077.pgm 825, BOSSbase/BOSSbase_1.01/1107.pgm 828, BOSSbase/BOSSbase_1.01/1109.pgm 827, BOSSbase/BOSSbase_1.01/1134.pgm 826, BOSSbase/BOSSbase_1.01/1184.pgm 826, BOSSbase/BOSSbase_1.01/1198.pgm 831, BOSSbase/BOSSbase_1.01/1202.pgm 824, BOSSbase/BOSSbase_1.01/1221.pgm 826, BOSSbase/BOSSbase_1.01/1222.pgm 825, BOSSbase/BOSSbase_1.01/1223.pgm 826, BOSSbase/BOSSbase_1.01/1242.pgm 830, BOSSbase/BOSSbase_1.01/1262.pgm 830, BOSSbase/BOSSbase_1.01/1267.pgm 827, BOSSbase/BOSSbase_1.01/1284.pgm 826, BOSSbase/BOSSbase_1.01/1285.pgm 828, BOSSbase/BOSSbase_1.01/1291.pgm 826, BOSSbase/BOSSbase_1.01/1297.pgm 827, BOSSbase/BOSSbase_1.01/1323.pgm 824, BOSSbase/BOSSbase_1.01/1330.pgm 828, BOSSbase/BOSSbase_1.01/1334.pgm 826, BOSSbase/BOSSbase_1.01/1379.pgm 828, BOSSbase/BOSSbase_1.01/1388.pgm 824, BOSSbase/BOSSbase_1.01/142.pgm 825, BOSSbase/BOSSbase_1.01/1506.pgm 826, BOSSbase/BOSSbase_1.01/1517.pgm 829, BOSSbase/BOSSbase_1.01/1518.pgm 830, BOSSbase/BOSSbase_1.01/1580.pgm 831, BOSSbase/BOSSbase_1.01/159.pgm 830, BOSSbase/BOSSbase_1.01/1603.pgm 824, BOSSbase/BOSSbase_1.01/1653.pgm 828, BOSSbase/BOSSbase_1.01/1674.pgm 825, BOSSbase/BOSSbase_1.01/1678.pgm 829, BOSSbase/BOSSbase_1.01/1680.pgm 831, BOSSbase/BOSSbase_1.01/1685.pgm 825, BOSSbase/BOSSbase_1.01/1697.pgm 830, BOSSbase/BOSSbase_1.01/1705.pgm 827, BOSSbase/BOSSbase_1.01/1732.pgm 825, BOSSbase/BOSSbase_1.01/1747.pgm 825, BOSSbase/BOSSbase_1.01/1785.pgm 826, BOSSbase/BOSSbase_1.01/1806.pgm 828, BOSSbase/BOSSbase_1.01/1807.pgm 825, BOSSbase/BOSSbase_1.01/1841.pgm 830, BOSSbase/BOSSbase_1.01/187.pgm 828, BOSSbase/BOSSbase_1.01/1886.pgm 826, BOSSbase/BOSSbase_1.01/1889.pgm 829, BOSSbase/BOSSbase_1.01/1894.pgm 824, BOSSbase/BOSSbase_1.01/191.pgm 825, BOSSbase/BOSSbase_1.01/1911.pgm 826, BOSSbase/BOSSbase_1.01/1944.pgm 827, BOSSbase/BOSSbase_1.01/2.pgm 826, BOSSbase/BOSSbase_1.01/2009.pgm 830, BOSSbase/BOSSbase_1.01/2031.pgm 827, BOSSbase/BOSSbase_1.01/2056.pgm 825, BOSSbase/BOSSbase_1.01/2064.pgm 829, BOSSbase/BOSSbase_1.01/2068.pgm 826, BOSSbase/BOSSbase_1.01/2069.pgm 824, BOSSbase/BOSSbase_1.01/2120.pgm 828, BOSSbase/BOSSbase_1.01/2124.pgm 828, BOSSbase/BOSSbase_1.01/2131.pgm 826, BOSSbase/BOSSbase_1.01/2164.pgm 827, BOSSbase/BOSSbase_1.01/2174.pgm 829, BOSSbase/BOSSbase_1.01/2182.pgm 831, BOSSbase/BOSSbase_1.01/2202.pgm 828, BOSSbase/BOSSbase_1.01/224.pgm 828, BOSSbase/BOSSbase_1.01/2251.pgm 829, BOSSbase/BOSSbase_1.01/2266.pgm 828, BOSSbase/BOSSbase_1.01/2289.pgm 831, BOSSbase/BOSSbase_1.01/2336.pgm 828, BOSSbase/BOSSbase_1.01/2347.pgm 829, BOSSbase/BOSSbase_1.01/237.pgm 824, BOSSbase/BOSSbase_1.01/2378.pgm 831, BOSSbase/BOSSbase_1.01/2390.pgm 824, BOSSbase/BOSSbase_1.01/2417.pgm 829, BOSSbase/BOSSbase_1.01/2418.pgm 831, BOSSbase/BOSSbase_1.01/2433.pgm 831, BOSSbase/BOSSbase_1.01/2487.pgm 827, BOSSbase/BOSSbase_1.01/250.pgm 825, BOSSbase/BOSSbase_1.01/2510.pgm 830, BOSSbase/BOSSbase_1.01/2516.pgm 827, BOSSbase/BOSSbase_1.01/2528.pgm 827, BOSSbase/BOSSbase_1.01/2557.pgm 825, BOSSbase/BOSSbase_1.01/2582.pgm 824, BOSSbase/BOSSbase_1.01/2586.pgm 830, BOSSbase/BOSSbase_1.01/2598.pgm 830, BOSSbase/BOSSbase_1.01/2620.pgm 824, BOSSbase/BOSSbase_1.01/2629.pgm 827, BOSSbase/BOSSbase_1.01/2639.pgm 831, BOSSbase/BOSSbase_1.01/2649.pgm 829, BOSSbase/BOSSbase_1.01/2659.pgm 827, BOSSbase/BOSSbase_1.01/2678.pgm 830, BOSSbase/BOSSbase_1.01/2778.pgm 826, BOSSbase/BOSSbase_1.01/280.pgm 830, BOSSbase/BOSSbase_1.01/2809.pgm 828, BOSSbase/BOSSbase_1.01/2819.pgm 824, BOSSbase/BOSSbase_1.01/2833.pgm 829, BOSSbase/BOSSbase_1.01/2838.pgm 826, BOSSbase/BOSSbase_1.01/2839.pgm 830, BOSSbase/BOSSbase_1.01/2891.pgm 831, BOSSbase/BOSSbase_1.01/2896.pgm 824, BOSSbase/BOSSbase_1.01/2906.pgm 828, BOSSbase/BOSSbase_1.01/2941.pgm 830, BOSSbase/BOSSbase_1.01/2965.pgm 825, BOSSbase/BOSSbase_1.01/2998.pgm 828, BOSSbase/BOSSbase_1.01/3028.pgm 829, BOSSbase/BOSSbase_1.01/3033.pgm 827, BOSSbase/BOSSbase_1.01/3038.pgm 828, BOSSbase/BOSSbase_1.01/3082.pgm 830, BOSSbase/BOSSbase_1.01/3104.pgm 825, BOSSbase/BOSSbase_1.01/3110.pgm 831, BOSSbase/BOSSbase_1.01/3125.pgm 831, BOSSbase/BOSSbase_1.01/3131.pgm 830, BOSSbase/BOSSbase_1.01/3133.pgm 830, BOSSbase/BOSSbase_1.01/3136.pgm 824, BOSSbase/BOSSbase_1.01/3137.pgm 827, BOSSbase/BOSSbase_1.01/3219.pgm 827, BOSSbase/BOSSbase_1.01/322.pgm 824, BOSSbase/BOSSbase_1.01/3241.pgm 828, BOSSbase/BOSSbase_1.01/3254.pgm 829, BOSSbase/BOSSbase_1.01/3288.pgm 831, BOSSbase/BOSSbase_1.01/3323.pgm 830, BOSSbase/BOSSbase_1.01/3344.pgm 825, BOSSbase/BOSSbase_1.01/3347.pgm 829, BOSSbase/BOSSbase_1.01/3352.pgm 824, BOSSbase/BOSSbase_1.01/3354.pgm 825, BOSSbase/BOSSbase_1.01/3383.pgm 829, BOSSbase/BOSSbase_1.01/3417.pgm 830, BOSSbase/BOSSbase_1.01/3419.pgm 829, BOSSbase/BOSSbase_1.01/3428.pgm 827, BOSSbase/BOSSbase_1.01/3444.pgm 831, BOSSbase/BOSSbase_1.01/3446.pgm 826, BOSSbase/BOSSbase_1.01/3447.pgm 824, BOSSbase/BOSSbase_1.01/345.pgm 828, BOSSbase/BOSSbase_1.01/3462.pgm 828, BOSSbase/BOSSbase_1.01/3484.pgm 829, BOSSbase/BOSSbase_1.01/3494.pgm 831, BOSSbase/BOSSbase_1.01/3516.pgm 827, BOSSbase/BOSSbase_1.01/3538.pgm 826, BOSSbase/BOSSbase_1.01/3553.pgm 830, BOSSbase/BOSSbase_1.01/3570.pgm 830, BOSSbase/BOSSbase_1.01/3579.pgm 826, BOSSbase/BOSSbase_1.01/3586.pgm 828, BOSSbase/BOSSbase_1.01/3589.pgm 828, BOSSbase/BOSSbase_1.01/3627.pgm 830, BOSSbase/BOSSbase_1.01/3628.pgm 824, BOSSbase/BOSSbase_1.01/3640.pgm 826, BOSSbase/BOSSbase_1.01/3648.pgm 831, BOSSbase/BOSSbase_1.01/3666.pgm 831, BOSSbase/BOSSbase_1.01/3704.pgm 830, BOSSbase/BOSSbase_1.01/3724.pgm 831, BOSSbase/BOSSbase_1.01/3750.pgm 828, BOSSbase/BOSSbase_1.01/3751.pgm 827, BOSSbase/BOSSbase_1.01/3780.pgm 825, BOSSbase/BOSSbase_1.01/3782.pgm 828, BOSSbase/BOSSbase_1.01/3794.pgm 829, BOSSbase/BOSSbase_1.01/3806.pgm 824, BOSSbase/BOSSbase_1.01/3809.pgm 830, BOSSbase/BOSSbase_1.01/3810.pgm 828, BOSSbase/BOSSbase_1.01/3826.pgm 827, BOSSbase/BOSSbase_1.01/3839.pgm 827, BOSSbase/BOSSbase_1.01/3857.pgm 831, BOSSbase/BOSSbase_1.01/3905.pgm 830, BOSSbase/BOSSbase_1.01/3922.pgm 828, BOSSbase/BOSSbase_1.01/3923.pgm 824, BOSSbase/BOSSbase_1.01/3940.pgm 825, BOSSbase/BOSSbase_1.01/3949.pgm 828, BOSSbase/BOSSbase_1.01/3958.pgm 829, BOSSbase/BOSSbase_1.01/3968.pgm 829, BOSSbase/BOSSbase_1.01/3970.pgm 827, BOSSbase/BOSSbase_1.01/4022.pgm 827, BOSSbase/BOSSbase_1.01/4035.pgm 829, BOSSbase/BOSSbase_1.01/4057.pgm 827, BOSSbase/BOSSbase_1.01/4099.pgm 830, BOSSbase/BOSSbase_1.01/4103.pgm 826, BOSSbase/BOSSbase_1.01/4107.pgm 831, BOSSbase/BOSSbase_1.01/4111.pgm 831, BOSSbase/BOSSbase_1.01/4123.pgm 828, BOSSbase/BOSSbase_1.01/4130.pgm 824, BOSSbase/BOSSbase_1.01/4137.pgm 831, BOSSbase/BOSSbase_1.01/4154.pgm 830, BOSSbase/BOSSbase_1.01/4168.pgm 826, BOSSbase/BOSSbase_1.01/417.pgm 830, BOSSbase/BOSSbase_1.01/4171.pgm 830, BOSSbase/BOSSbase_1.01/421.pgm 831, BOSSbase/BOSSbase_1.01/4214.pgm 826, BOSSbase/BOSSbase_1.01/4216.pgm 824, BOSSbase/BOSSbase_1.01/4229.pgm 831, BOSSbase/BOSSbase_1.01/4233.pgm 831, BOSSbase/BOSSbase_1.01/4239.pgm 824, BOSSbase/BOSSbase_1.01/4277.pgm 825, BOSSbase/BOSSbase_1.01/4282.pgm 826, BOSSbase/BOSSbase_1.01/4295.pgm 830, BOSSbase/BOSSbase_1.01/4307.pgm 825, BOSSbase/BOSSbase_1.01/4517.pgm 827, BOSSbase/BOSSbase_1.01/4519.pgm 828, BOSSbase/BOSSbase_1.01/4535.pgm 830, BOSSbase/BOSSbase_1.01/4550.pgm 824, BOSSbase/BOSSbase_1.01/4580.pgm 825, BOSSbase/BOSSbase_1.01/4583.pgm 828, BOSSbase/BOSSbase_1.01/460.pgm 827, BOSSbase/BOSSbase_1.01/4602.pgm 831, BOSSbase/BOSSbase_1.01/4603.pgm 831, BOSSbase/BOSSbase_1.01/4613.pgm 824, BOSSbase/BOSSbase_1.01/4630.pgm 830, BOSSbase/BOSSbase_1.01/4639.pgm 827, BOSSbase/BOSSbase_1.01/4690.pgm 828, BOSSbase/BOSSbase_1.01/4696.pgm 827, BOSSbase/BOSSbase_1.01/47.pgm 825, BOSSbase/BOSSbase_1.01/4717.pgm 829, BOSSbase/BOSSbase_1.01/4728.pgm 824, BOSSbase/BOSSbase_1.01/4734.pgm 827, BOSSbase/BOSSbase_1.01/4742.pgm 830, BOSSbase/BOSSbase_1.01/4768.pgm 827, BOSSbase/BOSSbase_1.01/4823.pgm 831, BOSSbase/BOSSbase_1.01/4845.pgm 826, BOSSbase/BOSSbase_1.01/4846.pgm 830, BOSSbase/BOSSbase_1.01/4872.pgm 826, BOSSbase/BOSSbase_1.01/4894.pgm 828, BOSSbase/BOSSbase_1.01/4907.pgm 829, BOSSbase/BOSSbase_1.01/4947.pgm 831, BOSSbase/BOSSbase_1.01/4985.pgm 831, BOSSbase/BOSSbase_1.01/4986.pgm 829, BOSSbase/BOSSbase_1.01/4988.pgm 831, BOSSbase/BOSSbase_1.01/4996.pgm 828, BOSSbase/BOSSbase_1.01/5000.pgm 830, BOSSbase/BOSSbase_1.01/5012.pgm 824, BOSSbase/BOSSbase_1.01/5056.pgm 829, BOSSbase/BOSSbase_1.01/5062.pgm 826, BOSSbase/BOSSbase_1.01/508.pgm 830, BOSSbase/BOSSbase_1.01/5104.pgm 824, BOSSbase/BOSSbase_1.01/5107.pgm 826, BOSSbase/BOSSbase_1.01/5111.pgm 825, BOSSbase/BOSSbase_1.01/5117.pgm 825, BOSSbase/BOSSbase_1.01/5119.pgm 825, BOSSbase/BOSSbase_1.01/5122.pgm 827, BOSSbase/BOSSbase_1.01/5124.pgm 825, BOSSbase/BOSSbase_1.01/5139.pgm 825, BOSSbase/BOSSbase_1.01/5151.pgm 829, BOSSbase/BOSSbase_1.01/5215.pgm 824, BOSSbase/BOSSbase_1.01/5227.pgm 828, BOSSbase/BOSSbase_1.01/5237.pgm 830, BOSSbase/BOSSbase_1.01/5253.pgm 825, BOSSbase/BOSSbase_1.01/5254.pgm 827, BOSSbase/BOSSbase_1.01/5277.pgm 824, BOSSbase/BOSSbase_1.01/5329.pgm 824, BOSSbase/BOSSbase_1.01/5357.pgm 829, BOSSbase/BOSSbase_1.01/5372.pgm 831, BOSSbase/BOSSbase_1.01/5400.pgm 830, BOSSbase/BOSSbase_1.01/5409.pgm 827, BOSSbase/BOSSbase_1.01/5416.pgm 826, BOSSbase/BOSSbase_1.01/5437.pgm 826, BOSSbase/BOSSbase_1.01/5447.pgm 827, BOSSbase/BOSSbase_1.01/5496.pgm 824, BOSSbase/BOSSbase_1.01/5513.pgm 830, BOSSbase/BOSSbase_1.01/5519.pgm 825, BOSSbase/BOSSbase_1.01/5521.pgm 828, BOSSbase/BOSSbase_1.01/5532.pgm 830, BOSSbase/BOSSbase_1.01/5550.pgm 827, BOSSbase/BOSSbase_1.01/5582.pgm 826, BOSSbase/BOSSbase_1.01/5621.pgm 827, BOSSbase/BOSSbase_1.01/5658.pgm 826, BOSSbase/BOSSbase_1.01/566.pgm 826, BOSSbase/BOSSbase_1.01/5662.pgm 828, BOSSbase/BOSSbase_1.01/5737.pgm 829, BOSSbase/BOSSbase_1.01/5756.pgm 830, BOSSbase/BOSSbase_1.01/5762.pgm 827, BOSSbase/BOSSbase_1.01/5765.pgm 830, BOSSbase/BOSSbase_1.01/5832.pgm 827, BOSSbase/BOSSbase_1.01/5840.pgm 829, BOSSbase/BOSSbase_1.01/5847.pgm 831, BOSSbase/BOSSbase_1.01/5852.pgm 826, BOSSbase/BOSSbase_1.01/586.pgm 830, BOSSbase/BOSSbase_1.01/5886.pgm 829, BOSSbase/BOSSbase_1.01/5899.pgm 831, BOSSbase/BOSSbase_1.01/5901.pgm 827, BOSSbase/BOSSbase_1.01/5910.pgm 829, BOSSbase/BOSSbase_1.01/5919.pgm 830, BOSSbase/BOSSbase_1.01/5922.pgm 826, BOSSbase/BOSSbase_1.01/5924.pgm 827, BOSSbase/BOSSbase_1.01/594.pgm 824, BOSSbase/BOSSbase_1.01/5954.pgm 830, BOSSbase/BOSSbase_1.01/5975.pgm 824, BOSSbase/BOSSbase_1.01/5985.pgm 828, BOSSbase/BOSSbase_1.01/5992.pgm 828, BOSSbase/BOSSbase_1.01/6005.pgm 826, BOSSbase/BOSSbase_1.01/6027.pgm 825, BOSSbase/BOSSbase_1.01/6078.pgm 827, BOSSbase/BOSSbase_1.01/6082.pgm 825, BOSSbase/BOSSbase_1.01/6090.pgm 826, BOSSbase/BOSSbase_1.01/6106.pgm 831, BOSSbase/BOSSbase_1.01/6113.pgm 828, BOSSbase/BOSSbase_1.01/6125.pgm 827, BOSSbase/BOSSbase_1.01/6133.pgm 829, BOSSbase/BOSSbase_1.01/6149.pgm 828, BOSSbase/BOSSbase_1.01/6167.pgm 828, BOSSbase/BOSSbase_1.01/6169.pgm 826, BOSSbase/BOSSbase_1.01/6178.pgm 830, BOSSbase/BOSSbase_1.01/6193.pgm 826, BOSSbase/BOSSbase_1.01/6221.pgm 825, BOSSbase/BOSSbase_1.01/623.pgm 829, BOSSbase/BOSSbase_1.01/6234.pgm 826, BOSSbase/BOSSbase_1.01/6253.pgm 825, BOSSbase/BOSSbase_1.01/6257.pgm 824, BOSSbase/BOSSbase_1.01/6258.pgm 830, BOSSbase/BOSSbase_1.01/626.pgm 824, BOSSbase/BOSSbase_1.01/6302.pgm 830, BOSSbase/BOSSbase_1.01/6319.pgm 824, BOSSbase/BOSSbase_1.01/6321.pgm 825, BOSSbase/BOSSbase_1.01/6369.pgm 828, BOSSbase/BOSSbase_1.01/6375.pgm 831, BOSSbase/BOSSbase_1.01/6392.pgm 831, BOSSbase/BOSSbase_1.01/6409.pgm 825, BOSSbase/BOSSbase_1.01/6410.pgm 828, BOSSbase/BOSSbase_1.01/645.pgm 828, BOSSbase/BOSSbase_1.01/6459.pgm 824, BOSSbase/BOSSbase_1.01/6471.pgm 829, BOSSbase/BOSSbase_1.01/6494.pgm 824, BOSSbase/BOSSbase_1.01/6504.pgm 826, BOSSbase/BOSSbase_1.01/6527.pgm 827, BOSSbase/BOSSbase_1.01/6560.pgm 824, BOSSbase/BOSSbase_1.01/6571.pgm 827, BOSSbase/BOSSbase_1.01/6580.pgm 826, BOSSbase/BOSSbase_1.01/6590.pgm 826, BOSSbase/BOSSbase_1.01/6627.pgm 829, BOSSbase/BOSSbase_1.01/6696.pgm 830, BOSSbase/BOSSbase_1.01/6703.pgm 830, BOSSbase/BOSSbase_1.01/6704.pgm 826, BOSSbase/BOSSbase_1.01/6711.pgm 824, BOSSbase/BOSSbase_1.01/6716.pgm 824, BOSSbase/BOSSbase_1.01/6736.pgm 830, BOSSbase/BOSSbase_1.01/6751.pgm 826, BOSSbase/BOSSbase_1.01/6772.pgm 827, BOSSbase/BOSSbase_1.01/6781.pgm 831, BOSSbase/BOSSbase_1.01/6795.pgm 824, BOSSbase/BOSSbase_1.01/680.pgm 827, BOSSbase/BOSSbase_1.01/6810.pgm 826, BOSSbase/BOSSbase_1.01/682.pgm 825, BOSSbase/BOSSbase_1.01/6841.pgm 829, BOSSbase/BOSSbase_1.01/6843.pgm 828, BOSSbase/BOSSbase_1.01/6850.pgm 824, BOSSbase/BOSSbase_1.01/6857.pgm 831, BOSSbase/BOSSbase_1.01/6889.pgm 830, BOSSbase/BOSSbase_1.01/6892.pgm 827, BOSSbase/BOSSbase_1.01/6896.pgm 827, BOSSbase/BOSSbase_1.01/6968.pgm 827, BOSSbase/BOSSbase_1.01/700.pgm 826, BOSSbase/BOSSbase_1.01/7029.pgm 827, BOSSbase/BOSSbase_1.01/7045.pgm 825, BOSSbase/BOSSbase_1.01/7060.pgm 824, BOSSbase/BOSSbase_1.01/7078.pgm 828, BOSSbase/BOSSbase_1.01/7093.pgm 826, BOSSbase/BOSSbase_1.01/7103.pgm 830, BOSSbase/BOSSbase_1.01/7119.pgm 831, BOSSbase/BOSSbase_1.01/7124.pgm 828, BOSSbase/BOSSbase_1.01/7126.pgm 830, BOSSbase/BOSSbase_1.01/714.pgm 825, BOSSbase/BOSSbase_1.01/7174.pgm 826, BOSSbase/BOSSbase_1.01/7216.pgm 829, BOSSbase/BOSSbase_1.01/7229.pgm 824, BOSSbase/BOSSbase_1.01/7237.pgm 831, BOSSbase/BOSSbase_1.01/7246.pgm 829, BOSSbase/BOSSbase_1.01/7296.pgm 828, BOSSbase/BOSSbase_1.01/7308.pgm 826, BOSSbase/BOSSbase_1.01/7314.pgm 827, BOSSbase/BOSSbase_1.01/7330.pgm 828, BOSSbase/BOSSbase_1.01/737.pgm 826, BOSSbase/BOSSbase_1.01/738.pgm 831, BOSSbase/BOSSbase_1.01/7391.pgm 824, BOSSbase/BOSSbase_1.01/740.pgm 830, BOSSbase/BOSSbase_1.01/7403.pgm 824, BOSSbase/BOSSbase_1.01/7430.pgm 831, BOSSbase/BOSSbase_1.01/7434.pgm 829, BOSSbase/BOSSbase_1.01/7437.pgm 830, BOSSbase/BOSSbase_1.01/7453.pgm 825, BOSSbase/BOSSbase_1.01/7509.pgm 827, BOSSbase/BOSSbase_1.01/7517.pgm 829, BOSSbase/BOSSbase_1.01/7547.pgm 828, BOSSbase/BOSSbase_1.01/7568.pgm 825, BOSSbase/BOSSbase_1.01/7618.pgm 829, BOSSbase/BOSSbase_1.01/7636.pgm 825, BOSSbase/BOSSbase_1.01/7693.pgm 829, BOSSbase/BOSSbase_1.01/77.pgm 824, BOSSbase/BOSSbase_1.01/770.pgm 829, BOSSbase/BOSSbase_1.01/7711.pgm 831, BOSSbase/BOSSbase_1.01/772.pgm 830, BOSSbase/BOSSbase_1.01/7726.pgm 831, BOSSbase/BOSSbase_1.01/7766.pgm 830, BOSSbase/BOSSbase_1.01/7819.pgm 828, BOSSbase/BOSSbase_1.01/7846.pgm 827, BOSSbase/BOSSbase_1.01/7864.pgm 826, BOSSbase/BOSSbase_1.01/7866.pgm 830, BOSSbase/BOSSbase_1.01/7867.pgm 831, BOSSbase/BOSSbase_1.01/787.pgm 825, BOSSbase/BOSSbase_1.01/7873.pgm 830, BOSSbase/BOSSbase_1.01/788.pgm 829, BOSSbase/BOSSbase_1.01/7888.pgm 826, BOSSbase/BOSSbase_1.01/7898.pgm 825, BOSSbase/BOSSbase_1.01/79.pgm 826, BOSSbase/BOSSbase_1.01/7902.pgm 824, BOSSbase/BOSSbase_1.01/791.pgm 831, BOSSbase/BOSSbase_1.01/7975.pgm 825, BOSSbase/BOSSbase_1.01/7978.pgm 826, BOSSbase/BOSSbase_1.01/8059.pgm 824, BOSSbase/BOSSbase_1.01/8083.pgm 824, BOSSbase/BOSSbase_1.01/8107.pgm 824, BOSSbase/BOSSbase_1.01/8111.pgm 828, BOSSbase/BOSSbase_1.01/8131.pgm 830, BOSSbase/BOSSbase_1.01/8161.pgm 828, BOSSbase/BOSSbase_1.01/8164.pgm 830, BOSSbase/BOSSbase_1.01/8195.pgm 828, BOSSbase/BOSSbase_1.01/8198.pgm 824, BOSSbase/BOSSbase_1.01/8282.pgm 825, BOSSbase/BOSSbase_1.01/833.pgm 827, BOSSbase/BOSSbase_1.01/8350.pgm 828, BOSSbase/BOSSbase_1.01/8357.pgm 828, BOSSbase/BOSSbase_1.01/84.pgm 827, BOSSbase/BOSSbase_1.01/8401.pgm 830, BOSSbase/BOSSbase_1.01/8408.pgm 831, BOSSbase/BOSSbase_1.01/8493.pgm 827, BOSSbase/BOSSbase_1.01/8516.pgm 826, BOSSbase/BOSSbase_1.01/8526.pgm 827, BOSSbase/BOSSbase_1.01/8539.pgm 830, BOSSbase/BOSSbase_1.01/8550.pgm 830, BOSSbase/BOSSbase_1.01/8557.pgm 825, BOSSbase/BOSSbase_1.01/8560.pgm 830, BOSSbase/BOSSbase_1.01/8566.pgm 824, BOSSbase/BOSSbase_1.01/860.pgm 826, BOSSbase/BOSSbase_1.01/8651.pgm 828, BOSSbase/BOSSbase_1.01/8686.pgm 825, BOSSbase/BOSSbase_1.01/8699.pgm 825, BOSSbase/BOSSbase_1.01/8714.pgm 828, BOSSbase/BOSSbase_1.01/8726.pgm 828, BOSSbase/BOSSbase_1.01/8746.pgm 830, BOSSbase/BOSSbase_1.01/8749.pgm 828, BOSSbase/BOSSbase_1.01/8755.pgm 827, BOSSbase/BOSSbase_1.01/8756.pgm 831, BOSSbase/BOSSbase_1.01/8760.pgm 831, BOSSbase/BOSSbase_1.01/8785.pgm 824, BOSSbase/BOSSbase_1.01/8818.pgm 825, BOSSbase/BOSSbase_1.01/884.pgm 829, BOSSbase/BOSSbase_1.01/885.pgm 829, BOSSbase/BOSSbase_1.01/8883.pgm 828, BOSSbase/BOSSbase_1.01/895.pgm 831, BOSSbase/BOSSbase_1.01/8991.pgm 826, BOSSbase/BOSSbase_1.01/900.pgm 830, BOSSbase/BOSSbase_1.01/9001.pgm 826, BOSSbase/BOSSbase_1.01/9042.pgm 831, BOSSbase/BOSSbase_1.01/9047.pgm 825, BOSSbase/BOSSbase_1.01/9055.pgm 831, BOSSbase/BOSSbase_1.01/9058.pgm 825, BOSSbase/BOSSbase_1.01/9065.pgm 829, BOSSbase/BOSSbase_1.01/9110.pgm 829, BOSSbase/BOSSbase_1.01/9113.pgm 824, BOSSbase/BOSSbase_1.01/9123.pgm 827, BOSSbase/BOSSbase_1.01/9131.pgm 824, BOSSbase/BOSSbase_1.01/9149.pgm 830, BOSSbase/BOSSbase_1.01/9154.pgm 825, BOSSbase/BOSSbase_1.01/9210.pgm 828, BOSSbase/BOSSbase_1.01/9213.pgm 831, BOSSbase/BOSSbase_1.01/9217.pgm 826, BOSSbase/BOSSbase_1.01/9228.pgm 828, BOSSbase/BOSSbase_1.01/923.pgm 831, BOSSbase/BOSSbase_1.01/9236.pgm 828, BOSSbase/BOSSbase_1.01/9263.pgm 830, BOSSbase/BOSSbase_1.01/9270.pgm 824, BOSSbase/BOSSbase_1.01/9272.pgm 825, BOSSbase/BOSSbase_1.01/9285.pgm 831, BOSSbase/BOSSbase_1.01/9299.pgm 828, BOSSbase/BOSSbase_1.01/93.pgm 830, BOSSbase/BOSSbase_1.01/9320.pgm 824, BOSSbase/BOSSbase_1.01/9343.pgm 824, BOSSbase/BOSSbase_1.01/9400.pgm 831, BOSSbase/BOSSbase_1.01/9419.pgm 824, BOSSbase/BOSSbase_1.01/9488.pgm 825, BOSSbase/BOSSbase_1.01/950.pgm 826, BOSSbase/BOSSbase_1.01/9513.pgm 828, BOSSbase/BOSSbase_1.01/9514.pgm 829, BOSSbase/BOSSbase_1.01/9542.pgm 831, BOSSbase/BOSSbase_1.01/9579.pgm 829, BOSSbase/BOSSbase_1.01/9636.pgm 825, BOSSbase/BOSSbase_1.01/9641.pgm 826, BOSSbase/BOSSbase_1.01/9666.pgm 830, BOSSbase/BOSSbase_1.01/9678.pgm 829, BOSSbase/BOSSbase_1.01/9699.pgm 826, BOSSbase/BOSSbase_1.01/9704.pgm 828, BOSSbase/BOSSbase_1.01/9709.pgm 828, BOSSbase/BOSSbase_1.01/972.pgm 827, BOSSbase/BOSSbase_1.01/9737.pgm 825, BOSSbase/BOSSbase_1.01/9742.pgm 829, BOSSbase/BOSSbase_1.01/9761.pgm 825, BOSSbase/BOSSbase_1.01/9861.pgm 831, BOSSbase/BOSSbase_1.01/9868.pgm 828, BOSSbase/BOSSbase_1.01/9871.pgm 830, BOSSbase/BOSSbase_1.01/9929.pgm 829, BOSSbase/BOSSbase_1.01/9945.pgm 826, BOSSbase/BOSSbase_1.01/998.pgm 828, BOSSbase/BOSSbase_1.01/9989.pgm 830, UCID/UCID1338/10.tif 824, UCID/UCID1338/100.tif 829, UCID/UCID1338/1000.tif 826, UCID/UCID1338/1005.tif 831, UCID/UCID1338/1008.tif 831, UCID/UCID1338/1009.tif 829, UCID/UCID1338/1015.tif 825, UCID/UCID1338/1018.tif 824, UCID/UCID1338/1019.tif 824, UCID/UCID1338/1021.tif 830, UCID/UCID1338/1022.tif 825, UCID/UCID1338/1026.tif 827, UCID/UCID1338/1027.tif 826, UCID/UCID1338/1028.tif 824, UCID/UCID1338/103.tif 831, UCID/UCID1338/1031.tif 831, UCID/UCID1338/1032.tif 824, UCID/UCID1338/1038.tif 830, UCID/UCID1338/1043.tif 826, UCID/UCID1338/1047.tif 826, UCID/UCID1338/105.tif 824, UCID/UCID1338/1051.tif 827, UCID/UCID1338/1059.tif 830, UCID/UCID1338/1062.tif 831, UCID/UCID1338/1063.tif 824, UCID/UCID1338/1064.tif 827, UCID/UCID1338/107.tif 825, UCID/UCID1338/1070.tif 827, UCID/UCID1338/1074.tif 831, UCID/UCID1338/1076.tif 825, UCID/UCID1338/1077.tif 827, UCID/UCID1338/1079.tif 830, UCID/UCID1338/108.tif 828, UCID/UCID1338/1082.tif 829, UCID/UCID1338/1085.tif 826, UCID/UCID1338/1086.tif 831, UCID/UCID1338/1087.tif 831, UCID/UCID1338/109.tif 827, UCID/UCID1338/1090.tif 830, UCID/UCID1338/1092.tif 824, UCID/UCID1338/1100.tif 831, UCID/UCID1338/1109.tif 829, UCID/UCID1338/1113.tif 827, UCID/UCID1338/1120.tif 828, UCID/UCID1338/1121.tif 829, UCID/UCID1338/1123.tif 827, UCID/UCID1338/1124.tif 830, UCID/UCID1338/1125.tif 824, UCID/UCID1338/1126.tif 831, UCID/UCID1338/1128.tif 828, UCID/UCID1338/113.tif 827, UCID/UCID1338/1130.tif 826, UCID/UCID1338/1131.tif 830, UCID/UCID1338/1133.tif 829, UCID/UCID1338/1134.tif 829, UCID/UCID1338/1136.tif 829, UCID/UCID1338/114.tif 827, UCID/UCID1338/1140.tif 827, UCID/UCID1338/1142.tif 824, UCID/UCID1338/1149.tif 831, UCID/UCID1338/115.tif 831, UCID/UCID1338/1155.tif 826, UCID/UCID1338/1157.tif 831, UCID/UCID1338/1161.tif 831, UCID/UCID1338/1163.tif 830, UCID/UCID1338/1164.tif 829, UCID/UCID1338/1166.tif 827, UCID/UCID1338/1167.tif 828, UCID/UCID1338/1168.tif 825, UCID/UCID1338/1171.tif 829, UCID/UCID1338/1175.tif 826, UCID/UCID1338/1177.tif 824, UCID/UCID1338/1179.tif 826, UCID/UCID1338/1185.tif 824, UCID/UCID1338/1189.tif 830, UCID/UCID1338/119.tif 828, UCID/UCID1338/1193.tif 831, UCID/UCID1338/1196.tif 831, UCID/UCID1338/1201.tif 831, UCID/UCID1338/1213.tif 828, UCID/UCID1338/1215.tif 828, UCID/UCID1338/1217.tif 824, UCID/UCID1338/1218.tif 828, UCID/UCID1338/1219.tif 829, UCID/UCID1338/1222.tif 824, UCID/UCID1338/1223.tif 825, UCID/UCID1338/1228.tif 831, UCID/UCID1338/1229.tif 827, UCID/UCID1338/1231.tif 829, UCID/UCID1338/1232.tif 826, UCID/UCID1338/1236.tif 827, UCID/UCID1338/1238.tif 826, UCID/UCID1338/124.tif 830, UCID/UCID1338/1240.tif 827, UCID/UCID1338/1241.tif 830, UCID/UCID1338/1244.tif 824, UCID/UCID1338/1249.tif 825, UCID/UCID1338/125.tif 830, UCID/UCID1338/1250.tif 831, UCID/UCID1338/1251.tif 828, UCID/UCID1338/1259.tif 829, UCID/UCID1338/1261.tif 829, UCID/UCID1338/1262.tif 826, UCID/UCID1338/1264.tif 829, UCID/UCID1338/1265.tif 831, UCID/UCID1338/1266.tif 828, UCID/UCID1338/1267.tif 829, UCID/UCID1338/1268.tif 826, UCID/UCID1338/1269.tif 826, UCID/UCID1338/1270.tif 827, UCID/UCID1338/1272.tif 830, UCID/UCID1338/1275.tif 828, UCID/UCID1338/1276.tif 831, UCID/UCID1338/1277.tif 825, UCID/UCID1338/1280.tif 826, UCID/UCID1338/1281.tif 826, UCID/UCID1338/1283.tif 828, UCID/UCID1338/1286.tif 825, UCID/UCID1338/1288.tif 828, UCID/UCID1338/1291.tif 830, UCID/UCID1338/1298.tif 828, UCID/UCID1338/1302.tif 830, UCID/UCID1338/1303.tif 826, UCID/UCID1338/1305.tif 831, UCID/UCID1338/1306.tif 831, UCID/UCID1338/1307.tif 825, UCID/UCID1338/1308.tif 829, UCID/UCID1338/131.tif 830, UCID/UCID1338/1311.tif 829, UCID/UCID1338/1313.tif 829, UCID/UCID1338/1314.tif 831, UCID/UCID1338/1318.tif 825, UCID/UCID1338/1319.tif 828, UCID/UCID1338/132.tif 827, UCID/UCID1338/1321.tif 824, UCID/UCID1338/1324.tif 827, UCID/UCID1338/1326.tif 831, UCID/UCID1338/1329.tif 829, UCID/UCID1338/133.tif 829, UCID/UCID1338/1333.tif 831, UCID/UCID1338/1336.tif 826, UCID/UCID1338/135.tif 826, UCID/UCID1338/136.tif 824, UCID/UCID1338/139.tif 831, UCID/UCID1338/14.tif 827, UCID/UCID1338/142.tif 824, UCID/UCID1338/145.tif 827, UCID/UCID1338/146.tif 824, UCID/UCID1338/149.tif 829, UCID/UCID1338/15.tif 829, UCID/UCID1338/150.tif 831, UCID/UCID1338/151.tif 830, UCID/UCID1338/154.tif 829, UCID/UCID1338/155.tif 827, UCID/UCID1338/156.tif 826, UCID/UCID1338/162.tif 825, UCID/UCID1338/163.tif 831, UCID/UCID1338/166.tif 827, UCID/UCID1338/167.tif 824, UCID/UCID1338/169.tif 825, UCID/UCID1338/171.tif 826, UCID/UCID1338/172.tif 830, UCID/UCID1338/173.tif 826, UCID/UCID1338/175.tif 825, UCID/UCID1338/178.tif 826, UCID/UCID1338/18.tif 826, UCID/UCID1338/181.tif 831, UCID/UCID1338/190.tif 829, UCID/UCID1338/191.tif 831, UCID/UCID1338/195.tif 828, UCID/UCID1338/197.tif 825, UCID/UCID1338/200.tif 824, UCID/UCID1338/206.tif 825, UCID/UCID1338/207.tif 824, UCID/UCID1338/208.tif 825, UCID/UCID1338/21.tif 827, UCID/UCID1338/215.tif 828, UCID/UCID1338/22.tif 831, UCID/UCID1338/220.tif 831, UCID/UCID1338/224.tif 824, UCID/UCID1338/227.tif 830, UCID/UCID1338/229.tif 826, UCID/UCID1338/233.tif 824, UCID/UCID1338/234.tif 827, UCID/UCID1338/238.tif 829, UCID/UCID1338/24.tif 825, UCID/UCID1338/241.tif 831, UCID/UCID1338/242.tif 829, UCID/UCID1338/245.tif 830, UCID/UCID1338/246.tif 830, UCID/UCID1338/247.tif 826, UCID/UCID1338/25.tif 827, UCID/UCID1338/252.tif 825, UCID/UCID1338/254.tif 824, UCID/UCID1338/255.tif 831, UCID/UCID1338/256.tif 826, UCID/UCID1338/257.tif 826, UCID/UCID1338/258.tif 828, UCID/UCID1338/26.tif 828, UCID/UCID1338/260.tif 824, UCID/UCID1338/262.tif 826, UCID/UCID1338/264.tif 828, UCID/UCID1338/269.tif 830, UCID/UCID1338/272.tif 827, UCID/UCID1338/273.tif 826, UCID/UCID1338/279.tif 829, UCID/UCID1338/280.tif 830, UCID/UCID1338/282.tif 827, UCID/UCID1338/283.tif 826, UCID/UCID1338/285.tif 825, UCID/UCID1338/287.tif 827, UCID/UCID1338/288.tif 828, UCID/UCID1338/289.tif 826, UCID/UCID1338/294.tif 828, UCID/UCID1338/295.tif 826, UCID/UCID1338/297.tif 831, UCID/UCID1338/299.tif 827, UCID/UCID1338/300.tif 827, UCID/UCID1338/302.tif 830, UCID/UCID1338/306.tif 824, UCID/UCID1338/308.tif 825, UCID/UCID1338/31.tif 831, UCID/UCID1338/312.tif 826, UCID/UCID1338/318.tif 826, UCID/UCID1338/32.tif 827, UCID/UCID1338/320.tif 827, UCID/UCID1338/321.tif 827, UCID/UCID1338/323.tif 825, UCID/UCID1338/329.tif 825, UCID/UCID1338/33.tif 829, UCID/UCID1338/332.tif 824, UCID/UCID1338/333.tif 829, UCID/UCID1338/342.tif 830, UCID/UCID1338/343.tif 824, UCID/UCID1338/346.tif 830, UCID/UCID1338/347.tif 831, UCID/UCID1338/348.tif 830, UCID/UCID1338/354.tif 826, UCID/UCID1338/357.tif 830, UCID/UCID1338/358.tif 831, UCID/UCID1338/362.tif 825, UCID/UCID1338/368.tif 825, UCID/UCID1338/369.tif 824, UCID/UCID1338/37.tif 827, UCID/UCID1338/370.tif 831, UCID/UCID1338/371.tif 826, UCID/UCID1338/372.tif 829, UCID/UCID1338/373.tif 826, UCID/UCID1338/378.tif 827, UCID/UCID1338/380.tif 829, UCID/UCID1338/385.tif 826, UCID/UCID1338/387.tif 827, UCID/UCID1338/391.tif 825, UCID/UCID1338/392.tif 827, UCID/UCID1338/395.tif 825, UCID/UCID1338/396.tif 826, UCID/UCID1338/398.tif 826, UCID/UCID1338/399.tif 827, UCID/UCID1338/40.tif 829, UCID/UCID1338/400.tif 829, UCID/UCID1338/402.tif 831, UCID/UCID1338/405.tif 828, UCID/UCID1338/409.tif 829, UCID/UCID1338/41.tif 825, UCID/UCID1338/42.tif 828, UCID/UCID1338/424.tif 827, UCID/UCID1338/426.tif 827, UCID/UCID1338/427.tif 827, UCID/UCID1338/429.tif 831, UCID/UCID1338/430.tif 829, UCID/UCID1338/434.tif 831, UCID/UCID1338/435.tif 825, UCID/UCID1338/437.tif 830, UCID/UCID1338/439.tif 827, UCID/UCID1338/440.tif 827, UCID/UCID1338/441.tif 831, UCID/UCID1338/442.tif 825, UCID/UCID1338/443.tif 826, UCID/UCID1338/445.tif 828, UCID/UCID1338/446.tif 825, UCID/UCID1338/447.tif 830, UCID/UCID1338/454.tif 831, UCID/UCID1338/455.tif 826, UCID/UCID1338/462.tif 827, UCID/UCID1338/463.tif 824, UCID/UCID1338/464.tif 826, UCID/UCID1338/47.tif 828, UCID/UCID1338/477.tif 825, UCID/UCID1338/479.tif 827, UCID/UCID1338/48.tif 829, UCID/UCID1338/480.tif 827, UCID/UCID1338/484.tif 828, UCID/UCID1338/488.tif 829, UCID/UCID1338/489.tif 831, UCID/UCID1338/492.tif 831, UCID/UCID1338/493.tif 831, UCID/UCID1338/500.tif 827, UCID/UCID1338/503.tif 827, UCID/UCID1338/507.tif 828, UCID/UCID1338/509.tif 830, UCID/UCID1338/510.tif 828, UCID/UCID1338/511.tif 825, UCID/UCID1338/516.tif 824, UCID/UCID1338/517.tif 831, UCID/UCID1338/52.tif 826, UCID/UCID1338/521.tif 829, UCID/UCID1338/522.tif 828, UCID/UCID1338/523.tif 826, UCID/UCID1338/526.tif 825, UCID/UCID1338/527.tif 828, UCID/UCID1338/529.tif 828, UCID/UCID1338/530.tif 831, UCID/UCID1338/532.tif 825, UCID/UCID1338/534.tif 828, UCID/UCID1338/536.tif 825, UCID/UCID1338/542.tif 829, UCID/UCID1338/547.tif 826, UCID/UCID1338/548.tif 829, UCID/UCID1338/552.tif 827, UCID/UCID1338/553.tif 830, UCID/UCID1338/555.tif 826, UCID/UCID1338/556.tif 824, UCID/UCID1338/567.tif 825, UCID/UCID1338/57.tif 828, UCID/UCID1338/571.tif 824, UCID/UCID1338/572.tif 824, UCID/UCID1338/575.tif 825, UCID/UCID1338/577.tif 826, UCID/UCID1338/579.tif 825, UCID/UCID1338/582.tif 827, UCID/UCID1338/584.tif 827, UCID/UCID1338/585.tif 828, UCID/UCID1338/587.tif 828, UCID/UCID1338/59.tif 830, UCID/UCID1338/590.tif 830, UCID/UCID1338/597.tif 831, UCID/UCID1338/599.tif 824, UCID/UCID1338/60.tif 831, UCID/UCID1338/600.tif 827, UCID/UCID1338/607.tif 831, UCID/UCID1338/609.tif 824, UCID/UCID1338/61.tif 829, UCID/UCID1338/610.tif 826, UCID/UCID1338/612.tif 829, UCID/UCID1338/614.tif 826, UCID/UCID1338/629.tif 824, UCID/UCID1338/634.tif 826, UCID/UCID1338/635.tif 830, UCID/UCID1338/637.tif 827, UCID/UCID1338/639.tif 831, UCID/UCID1338/64.tif 829, UCID/UCID1338/641.tif 824, UCID/UCID1338/642.tif 827, UCID/UCID1338/643.tif 831, UCID/UCID1338/645.tif 830, UCID/UCID1338/648.tif 826, UCID/UCID1338/65.tif 830, UCID/UCID1338/650.tif 828, UCID/UCID1338/652.tif 827, UCID/UCID1338/659.tif 826, UCID/UCID1338/660.tif 827, UCID/UCID1338/662.tif 826, UCID/UCID1338/665.tif 829, UCID/UCID1338/668.tif 825, UCID/UCID1338/672.tif 830, UCID/UCID1338/673.tif 831, UCID/UCID1338/675.tif 824, UCID/UCID1338/677.tif 825, UCID/UCID1338/678.tif 828, UCID/UCID1338/68.tif 827, UCID/UCID1338/689.tif 829, UCID/UCID1338/691.tif 829, UCID/UCID1338/693.tif 828, UCID/UCID1338/695.tif 831, UCID/UCID1338/698.tif 826, UCID/UCID1338/701.tif 831, UCID/UCID1338/703.tif 825, UCID/UCID1338/704.tif 830, UCID/UCID1338/71.tif 827, UCID/UCID1338/711.tif 824, UCID/UCID1338/712.tif 826, UCID/UCID1338/715.tif 830, UCID/UCID1338/716.tif 830, UCID/UCID1338/717.tif 824, UCID/UCID1338/722.tif 826, UCID/UCID1338/723.tif 830, UCID/UCID1338/724.tif 824, UCID/UCID1338/726.tif 831, UCID/UCID1338/732.tif 827, UCID/UCID1338/736.tif 824, UCID/UCID1338/739.tif 829, UCID/UCID1338/74.tif 827, UCID/UCID1338/741.tif 824, UCID/UCID1338/742.tif 829, UCID/UCID1338/743.tif 824, UCID/UCID1338/747.tif 826, UCID/UCID1338/750.tif 825, UCID/UCID1338/751.tif 829, UCID/UCID1338/757.tif 825, UCID/UCID1338/760.tif 827, UCID/UCID1338/761.tif 830, UCID/UCID1338/762.tif 830, UCID/UCID1338/766.tif 827, UCID/UCID1338/768.tif 828, UCID/UCID1338/769.tif 824, UCID/UCID1338/772.tif 826, UCID/UCID1338/773.tif 825, UCID/UCID1338/774.tif 830, UCID/UCID1338/775.tif 828, UCID/UCID1338/777.tif 825, UCID/UCID1338/784.tif 824, UCID/UCID1338/788.tif 825, UCID/UCID1338/79.tif 828, UCID/UCID1338/790.tif 831, UCID/UCID1338/791.tif 828, UCID/UCID1338/796.tif 829, UCID/UCID1338/798.tif 829, UCID/UCID1338/799.tif 824, UCID/UCID1338/80.tif 831, UCID/UCID1338/801.tif 825, UCID/UCID1338/806.tif 826, UCID/UCID1338/807.tif 830, UCID/UCID1338/809.tif 825, UCID/UCID1338/812.tif 830, UCID/UCID1338/816.tif 825, UCID/UCID1338/817.tif 831, UCID/UCID1338/819.tif 824, UCID/UCID1338/820.tif 826, UCID/UCID1338/825.tif 831, UCID/UCID1338/830.tif 824, UCID/UCID1338/831.tif 830, UCID/UCID1338/835.tif 831, UCID/UCID1338/838.tif 831, UCID/UCID1338/842.tif 826, UCID/UCID1338/843.tif 825, UCID/UCID1338/845.tif 828, UCID/UCID1338/847.tif 826, UCID/UCID1338/848.tif 830, UCID/UCID1338/849.tif 828, UCID/UCID1338/850.tif 828, UCID/UCID1338/851.tif 824, UCID/UCID1338/857.tif 825, UCID/UCID1338/858.tif 825, UCID/UCID1338/86.tif 826, UCID/UCID1338/861.tif 829, UCID/UCID1338/863.tif 827, UCID/UCID1338/87.tif 830, UCID/UCID1338/871.tif 826, UCID/UCID1338/874.tif 826, UCID/UCID1338/878.tif 831, UCID/UCID1338/88.tif 830, UCID/UCID1338/883.tif 825, UCID/UCID1338/885.tif 827, UCID/UCID1338/888.tif 826, UCID/UCID1338/89.tif 824, UCID/UCID1338/893.tif 827, UCID/UCID1338/894.tif 829, UCID/UCID1338/897.tif 824, UCID/UCID1338/9.tif 826, UCID/UCID1338/900.tif 825, UCID/UCID1338/901.tif 831, UCID/UCID1338/902.tif 825, UCID/UCID1338/906.tif 825, UCID/UCID1338/907.tif 825, UCID/UCID1338/91.tif 826, UCID/UCID1338/910.tif 826, UCID/UCID1338/916.tif 826, UCID/UCID1338/919.tif 828, UCID/UCID1338/92.tif 827, UCID/UCID1338/925.tif 829, UCID/UCID1338/929.tif 830, UCID/UCID1338/93.tif 824, UCID/UCID1338/930.tif 827, UCID/UCID1338/931.tif 827, UCID/UCID1338/941.tif 828, UCID/UCID1338/942.tif 824, UCID/UCID1338/947.tif 829, UCID/UCID1338/949.tif 830, UCID/UCID1338/950.tif 825, UCID/UCID1338/951.tif 831, UCID/UCID1338/952.tif 827, UCID/UCID1338/956.tif 831, UCID/UCID1338/958.tif 830, UCID/UCID1338/959.tif 827, UCID/UCID1338/96.tif 830, UCID/UCID1338/963.tif 824, UCID/UCID1338/965.tif 828, UCID/UCID1338/969.tif 824, UCID/UCID1338/971.tif 824, UCID/UCID1338/979.tif 828, UCID/UCID1338/980.tif 830, UCID/UCID1338/983.tif 828, UCID/UCID1338/984.tif 826, UCID/UCID1338/986.tif 828, UCID/UCID1338/988.tif 831, UCID/UCID1338/992.tif 830, UCID/UCID1338/994.tif 829, UCID/UCID1338/996.tif 829, UCID/UCID1338/998.tif 831, UCID/UCID1338/999.tif 829, Airplane 825, Baboon 825, Jetplane 829, Lena 824, Man 831, Tiffany 828, barbara 828, boat 824, goldhill 829, lake 826, livingroom 825, peppers 824

| dataset | images | payload exact | cover exact | room = base room | mean s |
|---|---|---|---|---|---|
| BOSSbase | 500 | 500 | 500 | 500 | 0.67 |
| UCID | 500 | 500 | 500 | 500 | 0.51 |
| USC-SIPI | 12 | 12 | 12 | 12 | 0.75 |

## 11. Block-minimum efficiency (Table 8)

| image | sum t (bpp) | room (bpp) | eta | eta B=2 | eta B=4 | eta B=8 | oracle net |
|---|---|---|---|---|---|---|---|
| Airplane | 5.6561 | 4.8758 | 0.862 | 0.862 | 0.732 | 0.615 | 4.0656 |
| Baboon | 4.0206 | 2.8275 | 0.703 | 0.703 | 0.537 | 0.417 | 1.4494 |
| Jetplane | 5.4868 | 4.6838 | 0.854 | 0.854 | 0.722 | 0.609 | 3.6440 |
| Lena | 4.5835 | 3.6776 | 0.802 | 0.802 | 0.649 | 0.525 | 2.6385 |
| Man | 5.8524 | 4.8057 | 0.821 | 0.821 | 0.697 | 0.597 | 3.7059 |
| Tiffany | 5.7409 | 4.8584 | 0.846 | 0.846 | 0.719 | 0.607 | 3.8143 |
| barbara | 4.6853 | 3.7914 | 0.809 | 0.809 | 0.666 | 0.545 | 2.4365 |
| boat | 4.6037 | 3.5610 | 0.774 | 0.774 | 0.612 | 0.482 | 2.4079 |
| goldhill | 4.3913 | 3.3497 | 0.763 | 0.763 | 0.602 | 0.476 | 2.2246 |
| lake | 4.2624 | 3.1745 | 0.745 | 0.745 | 0.574 | 0.433 | 1.9642 |
| livingroom | 4.7807 | 3.7325 | 0.781 | 0.781 | 0.623 | 0.490 | 2.5606 |
| peppers | 4.8831 | 3.8763 | 0.794 | 0.794 | 0.645 | 0.516 | 2.8229 |

## 12. Leakage-reduced descriptor (Proposition 1)

| image | room | payload exact | cover exact | t-map length same | rho spatial | rho permuted |
|---|---|---|---|---|---|---|
| Airplane | 4.8758 | True | True | True | 0.408, 0.384, 0.298 | 0.002, -0.005, -0.004 |
| Baboon | 2.8275 | True | True | True | 0.570, 0.681, 0.583 | 0.000, -0.010, 0.001 |
| Jetplane | 4.6838 | True | True | True | 0.625, 0.636, 0.493 | -0.001, 0.004, -0.001 |
| Lena | 3.6776 | True | True | True | 0.536, 0.468, 0.361 | 0.001, 0.004, -0.009 |
| Man | 4.8057 | True | True | True | 0.439, 0.426, 0.285 | 0.001, 0.003, 0.003 |
| Tiffany | 4.8584 | True | True | True | 0.589, 0.501, 0.517 | 0.005, 0.008, 0.001 |
| barbara | 3.7914 | True | True | True | 0.803, 0.687, 0.688 | -0.000, 0.011, -0.001 |
| boat | 3.5610 | True | True | True | 0.500, 0.425, 0.289 | -0.001, -0.001, -0.004 |
| goldhill | 3.3497 | True | True | True | 0.505, 0.523, 0.341 | 0.004, -0.000, -0.001 |
| lake | 3.1745 | True | True | True | 0.591, 0.603, 0.451 | -0.000, -0.006, -0.000 |
| livingroom | 3.7325 | True | True | True | 0.528, 0.503, 0.280 | 0.009, 0.008, 0.010 |
| peppers | 3.8763 | True | True | True | 0.405, 0.415, 0.231 | 0.001, -0.003, -0.001 |

## 13. Statistics under 20 independent keys per cover (base construction)

H cipher 7.99912 to 7.99988; chi-square rejections 13 of 240 at alpha = 0.05 (expected 12.0); max |rho| 0.0060.

## 14. Specified construction (Section 4.6, Algorithm 3)

Self-tests: HKDF RFC 5869 True, AES SP 800-38A True.

| image | room bpp | raw (base) | payload exact | cover exact | seconds |
|---|---|---|---|---|---|
| Airplane | 4.8758 | 4.8758 | True | True | 0.6 |
| Baboon | 2.8275 | 2.8275 | True | True | 0.6 |
| Jetplane | 4.6838 | 4.6838 | True | True | 0.6 |
| Lena | 3.6776 | 3.6776 | True | True | 1.0 |
| Man | 4.8057 | 4.8057 | True | True | 2.4 |
| Tiffany | 4.8584 | 4.8584 | True | True | 0.6 |
| barbara | 3.7914 | 3.7914 | True | True | 0.6 |
| boat | 3.5610 | 3.5610 | True | True | 0.5 |
| goldhill | 3.3497 | 3.3497 | True | True | 0.6 |
| lake | 3.1745 | 3.1745 | True | True | 0.6 |
| livingroom | 3.7325 | 3.7325 | True | True | 0.6 |
| peppers | 3.8763 | 3.8763 | True | True | 0.9 |

| tampering | tau2 accepts | tau1 accepts | cover exact if accepted | identical on all covers |
|---|---|---|---|---|
| hider_rewrites_reserved | True | True | True | True |
| outsider_flips_reserved_bit | False | True | True | True |
| outsider_flips_nonreserved_bit | False | False | None | True |
| header_tmap_byte | False | False | None | True |
| header_payload_length | False | True | True | True |

AES-256-CTR, 20 keys per cover: H cipher 7.99910 to 7.99989; chi-square rejections 14 of 240 (expected 12.0); max |rho| 0.0072.

## 15. Matched comparison with reimplemented BPC (Table 5)

| cover | published BPC net | reimplemented | room deviation % |
|---|---|---|---|
| Airplane | 3.8363 | 3.8877 | +1.34 |
| Baboon | 1.3832 | 1.4364 | +3.85 |
| Man | 2.6345 | 2.6687 | +1.30 |

| cover | BPC net | overflow px | bs | Lfix | proposed net | proposed eff |
|---|---|---|---|---|---|---|
| Airplane | 3.8877 | 5 | 3 | 2 | 4.3004 | 3.9449 |
| Baboon | 1.4364 | 3 | 4 | 5 | 2.2358 | 1.7593 |
| Jetplane | 3.4750 | 1 | 4 | 5 | 4.0553 | 3.6178 |
| Lena | 3.1270 | 0 | 3 | 4 | 3.0861 | 3.0861 |
| Man | 2.6687 | 125 | 3 | 4 | 4.2140 | 2.9601 |
| Tiffany | 3.2028 | 5 | 3 | 4 | 4.1801 | 3.4183 |
| barbara | 2.6323 | 0 | 3 | 7 | 3.1393 | 2.9908 |
| boat | 2.5102 | 7 | 4 | 5 | 2.9656 | 2.8524 |
| goldhill | 2.7131 | 0 | 3 | 4 | 2.7666 | 2.7666 |
| lake | 2.2416 | 0 | 4 | 6 | 2.5342 | 2.5342 |
| livingroom | 2.7640 | 1 | 3 | 4 | 3.1485 | 2.9024 |
| peppers | 2.7011 | 0 | 3 | 4 | 3.3011 | 3.1136 |

## 16. Matched comparison on the database samples

| dataset | N | BPC net | BPC sd | proposed net | proposed eff | net wins | eff wins |
|---|---|---|---|---|---|---|---|
| BOSSbase | 500 | 3.6241 | 1.0355 | 3.7831 | 3.5022 | 346 | 283 |
| UCID | 500 | 2.9363 | 0.9006 | 3.6068 | 3.0336 | 451 | 395 |

## 17. Identical-image comparison with Xiao et al. (2024), reimplemented (t = 8)

| dataset | N | ABCS net | ABCS sd | proposed net | proposed eff | net wins | eff wins |
|---|---|---|---|---|---|---|---|
| BOSSbase | 500 | 3.8621 | 1.0262 | 3.7831 | 3.5022 | 283 | 80 |
| UCID | 500 | 3.1571 | 0.8798 | 3.6068 | 3.0336 | 410 | 121 |
| USC-SIPI | 12 | 3.0477 | 0.7350 | 3.3272 | 2.9955 | 9 | 6 |

| cover | ABCS net | T | proposed net | proposed eff |
|---|---|---|---|---|
| Airplane | 4.8630 | 27 | 4.3004 | 3.9449 |
| Baboon | 1.6269 | 93 | 2.2358 | 1.7593 |
| Jetplane | 3.6461 | 46 | 4.0553 | 3.6178 |
| Lena | 3.3146 | 47 | 3.0861 | 3.0861 |
| Man | 2.9319 | 44 | 4.2140 | 2.9601 |
| Tiffany | 3.4489 | 38 | 4.1801 | 3.4183 |
| barbara | 2.6575 | 30 | 3.1393 | 2.9908 |
| boat | 2.7395 | 62 | 2.9656 | 2.8524 |
| goldhill | 2.9472 | 58 | 2.7666 | 2.7666 |
| lake | 2.5127 | 63 | 2.5342 | 2.5342 |
| livingroom | 2.9347 | 63 | 3.1485 | 2.9024 |
| peppers | 2.9499 | 50 | 3.3011 | 3.1136 |

## Files processed

- BOSSbase: 500 images
- UCID: 500 images
- USC-SIPI: 12 images
