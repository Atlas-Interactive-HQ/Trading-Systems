# 15 — Loss attribution + bull-gate counterfactual

**Stance:** Research. `not_a_forecast: true`. Do not headline PnL. Do not promote to Phase C or live. Not a candidate_v1 implementation (Claude owns that lane).

Primary score remains **expectancy after costs** = (price PnL − entry/exit fees) / n_trades. Existing eval reports price PnL / n as “expectancy after costs” and fee drag as a separate line; this file uses the net figure and keeps fee drag as its own driver.

**Bull gate (one, no grid):** `bull_1h_sma20_rising`. 1h SMA(20) of closes strictly greater than SMA(20) on the prior 1h bar (rising MA). Fail-closed if fewer than 21 closed 1h bars. Allow = long AND rising 1h SMA20. Fail-closed blocks. Counterfactual is on the **same journal path** (no re-sequence of one-position / kill).

Named-window / similar-regime / Q4 ≠ future performance. BreakoutV1 lookback/stops were not retuned.

## Mac run (2026-09-03) — what hurts

All 12 samples walked on cached public MD (no invented bars). `not_a_forecast: true`.

**Top 3 loss drivers (stable across samples):**

1. **Stop-outs** — largest negative € on every sample (e.g. 2020-09: 446 stops, −344 € after costs; 2023-09: 440 stops, −297 €). This is the hole.
2. **Fee drag** — second everywhere (turnover). 2020-09 −54 €, 2023-09 −69 €, Q4 months ~18–36 € each. Overlaps the exit buckets (fees sit on every round-trip).
3. **Kill-flatten** — small third on the long windows (23 kills, ~−7 € each on 2020-09 / 2023-09). Zero or a few euros on most Q4 months.

**Not a loss driver:** time-stops. They are the offsetting bucket (positive after-cost net on every sample: 2020-09 +161 €, 2023-09 +114 €). The book is not dying because of the 16-bar time stop; stop-outs plus fees eat those time-stop gains.

Adverse-first-bar is a diagnostic overlap (many stops are already losing on the entry 15m bar), not a fifth independent ledger.

## Bull-gate verdict (do not ship as candidate_v2 from this)

Gate = long only when 1h SMA(20) is rising. Same fills, no re-sequence.

| Window (pass-rule) | allow n / exp | block n / exp | allow holdout n / exp |
|---|---:|---:|---:|
| 2020-09 | 257 / −0.299 | 418 / −0.274 | 68 / −0.070 |
| 2023-09 | 273 / −0.267 | 461 / −0.254 | 90 / −0.054 |

Allow is **not** better than block on the named holdouts. A couple of Q4 full windows look less-red or even green in-sample (2020-12, 2024-11) and then the holdout is ugly again. That is not a forecast and not enough to hand this gate to Claude for candidate_v2.

**Explicit: not a live recommendation. Not Phase C.**

## Cross-sample (full window)

| Sample | n | expectancy after costs | fee drag (€) | stop n / € | time-stop n / € | kill-flatten n / € | gate allow n / exp | gate block n / exp |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| similar | 23 | -0.3721 | 9.0142 | 13 / -25.6411 | 10 / 17.0833 | 0 / 0.0000 | 6 / -0.5579 | 17 / -0.3065 |
| 2020-09 | 675 | -0.2834 | 54.1307 | 446 / -344.1142 | 204 / 161.4995 | 23 / -7.5689 | 257 / -0.2993 | 418 / -0.2736 |
| 2023-09 | 734 | -0.2586 | 68.8717 | 440 / -297.0726 | 270 / 114.4381 | 23 / -6.5960 | 273 / -0.2671 | 461 / -0.2535 |
| 2020-10 | 93 | -0.9484 | 25.7323 | 63 / -108.3032 | 29 / 21.2086 | 0 / 0.0000 | 36 / -0.7658 | 57 / -1.0637 |
| 2020-11 | 98 | -0.7860 | 24.7869 | 68 / -153.4615 | 29 / 78.3152 | 1 / -1.8819 | 50 / -0.8272 | 48 / -0.7431 |
| 2020-12 | 100 | -0.6154 | 23.7518 | 66 / -195.6606 | 30 / 142.2752 | 3 / -4.9935 | 43 / 0.3421 | 57 / -1.3378 |
| 2023-10 | 102 | -0.7987 | 32.1119 | 64 / -116.7506 | 37 / 35.8381 | 1 / -0.5557 | 38 / -0.7667 | 64 / -0.8177 |
| 2023-11 | 95 | -0.6546 | 25.6504 | 52 / -139.8076 | 42 / 78.5648 | 1 / -0.9398 | 42 / -0.5522 | 53 / -0.7356 |
| 2023-12 | 114 | -0.6435 | 35.9609 | 64 / -183.3828 | 41 / 126.3833 | 8 / -13.6933 | 41 / -0.7008 | 73 / -0.6114 |
| 2024-10 | 113 | -0.7110 | 26.4565 | 61 / -157.5302 | 49 / 82.3933 | 3 / -5.2068 | 41 / -0.3413 | 72 / -0.9215 |
| 2024-11 | 103 | -0.5290 | 18.2250 | 64 / -204.3367 | 37 / 152.9973 | 2 / -3.1503 | 51 / 0.2984 | 52 / -1.3406 |
| 2024-12 | 98 | -0.8603 | 19.9129 | 57 / -154.7321 | 38 / 76.0437 | 3 / -5.6205 | 34 / -1.2798 | 64 / -0.6374 |

`not_a_forecast: true`.

## similar

MD: DOGE-USD + xperp MD 310404 (similar-regime June)
Bars: full 672 · IS 470 · holdout 202.

### What hurts (drivers)

| Driver | n | price PnL (€) | € contribution | overlaps |
|---|---:|---:|---:|---|
| stop_out | 13 | -20.5414 | -25.6411 | no |
| time_stop | 10 | 20.9978 | 17.0833 | no |
| kill_flatten | 0 | 0.0000 | 0.0000 | no |
| other_exit | 0 | 0.0000 | 0.0000 | no |
| fee_drag | 23 | — | -9.0142 | yes |
| adverse_first_bar | 16 | -11.8649 | -11.8649 | yes |

Top loss drivers (most negative €, fee_drag included, adverse-first-bar excluded from rank): stop_out (-25.6411), fee_drag (-9.0142).

### Slices

| Slice | n | n_long | n_short | expectancy after costs | fee drag (€) | net PnL (€) |
|---|---:|---:|---:|---:|---:|---:|
| full | 23 | 10 | 13 | -0.3721 | 9.0142 | -8.5578 |
| in-sample 70% | 16 | 7 | 9 | -0.1035 | 6.3095 | -1.6568 |
| holdout 30% | 7 | 3 | 4 | -0.9859 | 2.7047 | -6.9010 |

### Bull-gate counterfactual (same fills)

| Bucket | n | n_long | n_short | expectancy after costs | fee drag (€) |
|---|---:|---:|---:|---:|---:|
| allow (long ∩ bull) | 6 | 6 | 0 | -0.5579 | 2.3783 |
| block | 17 | 4 | 13 | -0.3065 | 6.6359 |
| allow holdout | 2 | 2 | 0 | -2.6773 | 0.7926 |
| block holdout | 5 | 1 | 4 | -0.3093 | 1.9120 |

Side × regime cells (diagnostic, not a second gate):

| Cell | n | expectancy after costs |
|---|---:|---:|
| long_bull | 6 | -0.5579 |
| long_not_bull | 3 | -0.4920 |
| short_bull | 4 | -0.5044 |
| short_not_bull | 9 | -0.1678 |
| fail_closed | 1 | -0.2069 |

`not_a_forecast: true`.

## 2020-09

MD: research MD DOGE-USDT (not OMS DOGE-USD); window 2020-09-01 → 2021-03-31 UTC
Bars: full 20352 · IS 14246 · holdout 6106.

### What hurts (drivers)

| Driver | n | price PnL (€) | € contribution | overlaps |
|---|---:|---:|---:|---|
| stop_out | 446 | -307.6686 | -344.1142 | no |
| time_stop | 204 | 178.1365 | 161.4995 | no |
| kill_flatten | 23 | -6.6689 | -7.5689 | no |
| other_exit | 2 | -0.9353 | -1.0833 | no |
| fee_drag | 675 | — | -54.1307 | yes |
| adverse_first_bar | 428 | -125.9843 | -125.9843 | yes |

Top loss drivers (most negative €, fee_drag included, adverse-first-bar excluded from rank): stop_out (-344.1142), fee_drag (-54.1307), kill_flatten (-7.5689).

### Slices

| Slice | n | n_long | n_short | expectancy after costs | fee drag (€) | net PnL (€) |
|---|---:|---:|---:|---:|---:|---:|
| full | 675 | 376 | 299 | -0.2834 | 54.1307 | -191.2669 |
| in-sample 70% | 463 | 269 | 194 | -0.3939 | 50.5504 | -182.3759 |
| holdout 30% | 212 | 107 | 105 | -0.0419 | 3.5803 | -8.8910 |

### Bull-gate counterfactual (same fills)

| Bucket | n | n_long | n_short | expectancy after costs | fee drag (€) |
|---|---:|---:|---:|---:|---:|
| allow (long ∩ bull) | 257 | 257 | 0 | -0.2993 | 19.2552 |
| block | 418 | 119 | 299 | -0.2736 | 34.8754 |
| allow holdout | 68 | 68 | 0 | -0.0699 | 1.0653 |
| block holdout | 144 | 39 | 105 | -0.0287 | 2.5150 |

Side × regime cells (diagnostic, not a second gate):

| Cell | n | expectancy after costs |
|---|---:|---:|
| long_bull | 257 | -0.2993 |
| long_not_bull | 118 | -0.3022 |
| short_bull | 97 | -0.1887 |
| short_not_bull | 201 | -0.2661 |
| fail_closed | 2 | -3.4491 |

`not_a_forecast: true`.

## 2023-09

MD: research MD DOGE-USDT (not OMS DOGE-USD); window 2023-09-01 → 2024-03-31 UTC
Bars: full 20448 · IS 14313 · holdout 6135.

### What hurts (drivers)

| Driver | n | price PnL (€) | € contribution | overlaps |
|---|---:|---:|---:|---|
| stop_out | 440 | -252.9313 | -297.0726 | no |
| time_stop | 270 | 137.8439 | 114.4381 | no |
| kill_flatten | 23 | -5.3506 | -6.5960 | no |
| other_exit | 1 | -0.4780 | -0.5572 | no |
| fee_drag | 734 | — | -68.8717 | yes |
| adverse_first_bar | 454 | -108.0531 | -108.0531 | yes |

Top loss drivers (most negative €, fee_drag included, adverse-first-bar excluded from rank): stop_out (-297.0726), fee_drag (-68.8717), kill_flatten (-6.5960).

### Slices

| Slice | n | n_long | n_short | expectancy after costs | fee drag (€) | net PnL (€) |
|---|---:|---:|---:|---:|---:|---:|
| full | 734 | 427 | 307 | -0.2586 | 68.8717 | -189.7877 |
| in-sample 70% | 505 | 298 | 207 | -0.3540 | 64.4363 | -178.7629 |
| holdout 30% | 229 | 129 | 100 | -0.0481 | 4.4354 | -11.0249 |

### Bull-gate counterfactual (same fills)

| Bucket | n | n_long | n_short | expectancy after costs | fee drag (€) |
|---|---:|---:|---:|---:|---:|
| allow (long ∩ bull) | 273 | 273 | 0 | -0.2671 | 24.1926 |
| block | 461 | 154 | 307 | -0.2535 | 44.6791 |
| allow holdout | 90 | 90 | 0 | -0.0538 | 1.5628 |
| block holdout | 139 | 39 | 100 | -0.0445 | 2.8727 |

Side × regime cells (diagnostic, not a second gate):

| Cell | n | expectancy after costs |
|---|---:|---:|
| long_bull | 273 | -0.2671 |
| long_not_bull | 153 | -0.1543 |
| short_bull | 111 | -0.2838 |
| short_not_bull | 194 | -0.2675 |
| fail_closed | 3 | -3.2861 |

`not_a_forecast: true`.

## 2020-10

MD: research MD DOGE-USDT (not OMS DOGE-USD); window 2020-10-01 → 2020-10-31 UTC
Bars: full 2976 · IS 2083 · holdout 893.

### What hurts (drivers)

| Driver | n | price PnL (€) | € contribution | overlaps |
|---|---:|---:|---:|---|
| stop_out | 63 | -90.4671 | -108.3032 | no |
| time_stop | 29 | 28.8667 | 21.2086 | no |
| kill_flatten | 0 | 0.0000 | 0.0000 | no |
| other_exit | 1 | -0.8669 | -1.1050 | no |
| fee_drag | 93 | — | -25.7323 | yes |
| adverse_first_bar | 64 | -39.5935 | -39.5935 | yes |

Top loss drivers (most negative €, fee_drag included, adverse-first-bar excluded from rank): stop_out (-108.3032), fee_drag (-25.7323), other_exit (-1.1050).

### Slices

| Slice | n | n_long | n_short | expectancy after costs | fee drag (€) | net PnL (€) |
|---|---:|---:|---:|---:|---:|---:|
| full | 93 | 54 | 39 | -0.9484 | 25.7323 | -88.1996 |
| in-sample 70% | 60 | 34 | 26 | -1.3287 | 18.5091 | -79.7231 |
| holdout 30% | 33 | 20 | 13 | -0.2569 | 7.2232 | -8.4765 |

### Bull-gate counterfactual (same fills)

| Bucket | n | n_long | n_short | expectancy after costs | fee drag (€) |
|---|---:|---:|---:|---:|---:|
| allow (long ∩ bull) | 36 | 36 | 0 | -0.7658 | 9.9330 |
| block | 57 | 18 | 39 | -1.0637 | 15.7994 |
| allow holdout | 11 | 11 | 0 | -0.2354 | 2.5061 |
| block holdout | 22 | 9 | 13 | -0.2676 | 4.7171 |

Side × regime cells (diagnostic, not a second gate):

| Cell | n | expectancy after costs |
|---|---:|---:|
| long_bull | 36 | -0.7658 |
| long_not_bull | 18 | -1.3826 |
| short_bull | 15 | -1.0588 |
| short_not_bull | 23 | -0.6965 |
| fail_closed | 1 | -3.8395 |

`not_a_forecast: true`.

## 2020-11

MD: research MD DOGE-USDT (not OMS DOGE-USD); window 2020-11-01 → 2020-11-30 UTC
Bars: full 2880 · IS 2015 · holdout 865.

### What hurts (drivers)

| Driver | n | price PnL (€) | € contribution | overlaps |
|---|---:|---:|---:|---|
| stop_out | 68 | -135.5406 | -153.4615 | no |
| time_stop | 29 | 84.9910 | 78.3152 | no |
| kill_flatten | 1 | -1.6917 | -1.8819 | no |
| other_exit | 0 | 0.0000 | 0.0000 | no |
| fee_drag | 98 | — | -24.7869 | yes |
| adverse_first_bar | 61 | -62.0340 | -62.0340 | yes |

Top loss drivers (most negative €, fee_drag included, adverse-first-bar excluded from rank): stop_out (-153.4615), fee_drag (-24.7869), kill_flatten (-1.8819).

### Slices

| Slice | n | n_long | n_short | expectancy after costs | fee drag (€) | net PnL (€) |
|---|---:|---:|---:|---:|---:|---:|
| full | 98 | 62 | 36 | -0.7860 | 24.7869 | -77.0281 |
| in-sample 70% | 65 | 42 | 23 | -0.9642 | 20.1667 | -62.6702 |
| holdout 30% | 33 | 20 | 13 | -0.4351 | 4.6201 | -14.3579 |

### Bull-gate counterfactual (same fills)

| Bucket | n | n_long | n_short | expectancy after costs | fee drag (€) |
|---|---:|---:|---:|---:|---:|
| allow (long ∩ bull) | 50 | 50 | 0 | -0.8272 | 12.2997 |
| block | 48 | 12 | 36 | -0.7431 | 12.4871 |
| allow holdout | 17 | 17 | 0 | -0.8675 | 2.6879 |
| block holdout | 16 | 3 | 13 | 0.0244 | 1.9322 |

Side × regime cells (diagnostic, not a second gate):

| Cell | n | expectancy after costs |
|---|---:|---:|
| long_bull | 50 | -0.8272 |
| long_not_bull | 12 | -0.2891 |
| short_bull | 13 | -1.3985 |
| short_not_bull | 23 | -0.6096 |
| fail_closed | 0 | — |

`not_a_forecast: true`.

## 2020-12

MD: research MD DOGE-USDT (not OMS DOGE-USD); window 2020-12-01 → 2020-12-31 UTC
Bars: full 2976 · IS 2083 · holdout 893.

### What hurts (drivers)

| Driver | n | price PnL (€) | € contribution | overlaps |
|---|---:|---:|---:|---|
| stop_out | 66 | -180.1677 | -195.6606 | no |
| time_stop | 30 | 149.9604 | 142.2752 | no |
| kill_flatten | 3 | -4.5888 | -4.9935 | no |
| other_exit | 1 | -2.9952 | -3.1643 | no |
| fee_drag | 100 | — | -23.7518 | yes |
| adverse_first_bar | 59 | -59.9931 | -59.9931 | yes |

Top loss drivers (most negative €, fee_drag included, adverse-first-bar excluded from rank): stop_out (-195.6606), fee_drag (-23.7518), kill_flatten (-4.9935).

### Slices

| Slice | n | n_long | n_short | expectancy after costs | fee drag (€) | net PnL (€) |
|---|---:|---:|---:|---:|---:|---:|
| full | 100 | 58 | 42 | -0.6154 | 23.7518 | -61.5432 |
| in-sample 70% | 67 | 39 | 28 | -0.2812 | 17.7494 | -18.8420 |
| holdout 30% | 33 | 19 | 14 | -1.2940 | 6.0024 | -42.7012 |

### Bull-gate counterfactual (same fills)

| Bucket | n | n_long | n_short | expectancy after costs | fee drag (€) |
|---|---:|---:|---:|---:|---:|
| allow (long ∩ bull) | 43 | 43 | 0 | 0.3421 | 10.3130 |
| block | 57 | 15 | 42 | -1.3378 | 13.4388 |
| allow holdout | 16 | 16 | 0 | -1.4344 | 3.2328 |
| block holdout | 17 | 3 | 14 | -1.1618 | 2.7696 |

Side × regime cells (diagnostic, not a second gate):

| Cell | n | expectancy after costs |
|---|---:|---:|
| long_bull | 43 | 0.3421 |
| long_not_bull | 15 | -2.0669 |
| short_bull | 8 | -1.3948 |
| short_not_bull | 33 | -0.9277 |
| fail_closed | 1 | -3.4780 |

`not_a_forecast: true`.

## 2023-10

MD: research MD DOGE-USDT (not OMS DOGE-USD); window 2023-10-01 → 2023-10-31 UTC
Bars: full 2976 · IS 2083 · holdout 893.

### What hurts (drivers)

| Driver | n | price PnL (€) | € contribution | overlaps |
|---|---:|---:|---:|---|
| stop_out | 64 | -96.9279 | -116.7506 | no |
| time_stop | 37 | 48.0014 | 35.8381 | no |
| kill_flatten | 1 | -0.4299 | -0.5557 | no |
| other_exit | 0 | 0.0000 | 0.0000 | no |
| fee_drag | 102 | — | -32.1119 | yes |
| adverse_first_bar | 71 | -45.9009 | -45.9009 | yes |

Top loss drivers (most negative €, fee_drag included, adverse-first-bar excluded from rank): stop_out (-116.7506), fee_drag (-32.1119), kill_flatten (-0.5557).

### Slices

| Slice | n | n_long | n_short | expectancy after costs | fee drag (€) | net PnL (€) |
|---|---:|---:|---:|---:|---:|---:|
| full | 102 | 61 | 41 | -0.7987 | 32.1119 | -81.4682 |
| in-sample 70% | 67 | 36 | 31 | -0.6710 | 23.6165 | -44.9595 |
| holdout 30% | 35 | 25 | 10 | -1.0431 | 8.4954 | -36.5087 |

### Bull-gate counterfactual (same fills)

| Bucket | n | n_long | n_short | expectancy after costs | fee drag (€) |
|---|---:|---:|---:|---:|---:|
| allow (long ∩ bull) | 38 | 38 | 0 | -0.7667 | 11.1129 |
| block | 64 | 23 | 41 | -0.8177 | 20.9990 |
| allow holdout | 17 | 17 | 0 | -0.9606 | 3.9337 |
| block holdout | 18 | 8 | 10 | -1.1211 | 4.5617 |

Side × regime cells (diagnostic, not a second gate):

| Cell | n | expectancy after costs |
|---|---:|---:|
| long_bull | 38 | -0.7667 |
| long_not_bull | 23 | -0.8529 |
| short_bull | 12 | -0.6186 |
| short_not_bull | 28 | -0.8448 |
| fail_closed | 1 | -1.6395 |

`not_a_forecast: true`.

## 2023-11

MD: research MD DOGE-USDT (not OMS DOGE-USD); window 2023-11-01 → 2023-11-30 UTC
Bars: full 2880 · IS 2015 · holdout 865.

### What hurts (drivers)

| Driver | n | price PnL (€) | € contribution | overlaps |
|---|---:|---:|---:|---|
| stop_out | 52 | -125.2089 | -139.8076 | no |
| time_stop | 42 | 89.3631 | 78.5648 | no |
| kill_flatten | 1 | -0.6864 | -0.9398 | no |
| other_exit | 0 | 0.0000 | 0.0000 | no |
| fee_drag | 95 | — | -25.6504 | yes |
| adverse_first_bar | 54 | -42.1379 | -42.1379 | yes |

Top loss drivers (most negative €, fee_drag included, adverse-first-bar excluded from rank): stop_out (-139.8076), fee_drag (-25.6504), kill_flatten (-0.9398).

### Slices

| Slice | n | n_long | n_short | expectancy after costs | fee drag (€) | net PnL (€) |
|---|---:|---:|---:|---:|---:|---:|
| full | 95 | 63 | 32 | -0.6546 | 25.6504 | -62.1826 |
| in-sample 70% | 69 | 46 | 23 | -0.7064 | 18.6641 | -48.7433 |
| holdout 30% | 26 | 17 | 9 | -0.5169 | 6.9863 | -13.4393 |

### Bull-gate counterfactual (same fills)

| Bucket | n | n_long | n_short | expectancy after costs | fee drag (€) |
|---|---:|---:|---:|---:|---:|
| allow (long ∩ bull) | 42 | 42 | 0 | -0.5522 | 11.2570 |
| block | 53 | 21 | 32 | -0.7356 | 14.3934 |
| allow holdout | 13 | 13 | 0 | -0.6306 | 3.4600 |
| block holdout | 13 | 4 | 9 | -0.4032 | 3.5263 |

Side × regime cells (diagnostic, not a second gate):

| Cell | n | expectancy after costs |
|---|---:|---:|
| long_bull | 42 | -0.5522 |
| long_not_bull | 19 | 0.0689 |
| short_bull | 16 | -1.4986 |
| short_not_bull | 16 | -0.7533 |
| fail_closed | 2 | -2.1334 |

`not_a_forecast: true`.

## 2023-12

MD: research MD DOGE-USDT (not OMS DOGE-USD); window 2023-12-01 → 2023-12-31 UTC
Bars: full 2976 · IS 2083 · holdout 893.

### What hurts (drivers)

| Driver | n | price PnL (€) | € contribution | overlaps |
|---|---:|---:|---:|---|
| stop_out | 64 | -163.3927 | -183.3828 | no |
| time_stop | 41 | 139.4796 | 126.3833 | no |
| kill_flatten | 8 | -11.1981 | -13.6933 | no |
| other_exit | 1 | -2.2903 | -2.6696 | no |
| fee_drag | 114 | — | -35.9609 | yes |
| adverse_first_bar | 65 | -74.6745 | -74.6745 | yes |

Top loss drivers (most negative €, fee_drag included, adverse-first-bar excluded from rank): stop_out (-183.3828), fee_drag (-35.9609), kill_flatten (-13.6933).

### Slices

| Slice | n | n_long | n_short | expectancy after costs | fee drag (€) | net PnL (€) |
|---|---:|---:|---:|---:|---:|---:|
| full | 114 | 69 | 45 | -0.6435 | 35.9609 | -73.3624 |
| in-sample 70% | 79 | 47 | 32 | -0.3622 | 25.8216 | -28.6155 |
| holdout 30% | 35 | 22 | 13 | -1.2785 | 10.1393 | -44.7469 |

### Bull-gate counterfactual (same fills)

| Bucket | n | n_long | n_short | expectancy after costs | fee drag (€) |
|---|---:|---:|---:|---:|---:|
| allow (long ∩ bull) | 41 | 41 | 0 | -0.7008 | 12.9697 |
| block | 73 | 28 | 45 | -0.6114 | 22.9912 |
| allow holdout | 13 | 13 | 0 | -1.5063 | 3.9050 |
| block holdout | 22 | 9 | 13 | -1.1439 | 6.2343 |

Side × regime cells (diagnostic, not a second gate):

| Cell | n | expectancy after costs |
|---|---:|---:|
| long_bull | 41 | -0.7008 |
| long_not_bull | 28 | -0.9521 |
| short_bull | 18 | 0.1717 |
| short_not_bull | 26 | -0.6939 |
| fail_closed | 1 | -3.0210 |

`not_a_forecast: true`.

## 2024-10

MD: research MD DOGE-USDT (not OMS DOGE-USD); window 2024-10-01 → 2024-10-31 UTC
Bars: full 2976 · IS 2083 · holdout 893.

### What hurts (drivers)

| Driver | n | price PnL (€) | € contribution | overlaps |
|---|---:|---:|---:|---|
| stop_out | 61 | -142.7592 | -157.5302 | no |
| time_stop | 49 | 93.3666 | 82.3933 | no |
| kill_flatten | 3 | -4.4946 | -5.2068 | no |
| other_exit | 0 | 0.0000 | 0.0000 | no |
| fee_drag | 113 | — | -26.4565 | yes |
| adverse_first_bar | 71 | -60.1173 | -60.1173 | yes |

Top loss drivers (most negative €, fee_drag included, adverse-first-bar excluded from rank): stop_out (-157.5302), fee_drag (-26.4565), kill_flatten (-5.2068).

### Slices

| Slice | n | n_long | n_short | expectancy after costs | fee drag (€) | net PnL (€) |
|---|---:|---:|---:|---:|---:|---:|
| full | 113 | 60 | 53 | -0.7110 | 26.4565 | -80.3437 |
| in-sample 70% | 77 | 41 | 36 | -0.7459 | 20.2018 | -57.4342 |
| holdout 30% | 36 | 19 | 17 | -0.6364 | 6.2548 | -22.9095 |

### Bull-gate counterfactual (same fills)

| Bucket | n | n_long | n_short | expectancy after costs | fee drag (€) |
|---|---:|---:|---:|---:|---:|
| allow (long ∩ bull) | 41 | 41 | 0 | -0.3413 | 9.5293 |
| block | 72 | 19 | 53 | -0.9215 | 16.9272 |
| allow holdout | 13 | 13 | 0 | -0.1078 | 2.2033 |
| block holdout | 23 | 6 | 17 | -0.9351 | 4.0515 |

Side × regime cells (diagnostic, not a second gate):

| Cell | n | expectancy after costs |
|---|---:|---:|
| long_bull | 41 | -0.3413 |
| long_not_bull | 19 | -0.4540 |
| short_bull | 19 | -1.1263 |
| short_not_bull | 33 | -1.4128 |
| fail_closed | 1 | 10.2958 |

`not_a_forecast: true`.

## 2024-11

MD: research MD DOGE-USDT (not OMS DOGE-USD); window 2024-11-01 → 2024-11-30 UTC
Bars: full 2880 · IS 2015 · holdout 865.

### What hurts (drivers)

| Driver | n | price PnL (€) | € contribution | overlaps |
|---|---:|---:|---:|---|
| stop_out | 64 | -193.3169 | -204.3367 | no |
| time_stop | 37 | 159.9370 | 152.9973 | no |
| kill_flatten | 2 | -2.8849 | -3.1503 | no |
| other_exit | 0 | 0.0000 | 0.0000 | no |
| fee_drag | 103 | — | -18.2250 | yes |
| adverse_first_bar | 63 | -72.1505 | -72.1505 | yes |

Top loss drivers (most negative €, fee_drag included, adverse-first-bar excluded from rank): stop_out (-204.3367), fee_drag (-18.2250), kill_flatten (-3.1503).

### Slices

| Slice | n | n_long | n_short | expectancy after costs | fee drag (€) | net PnL (€) |
|---|---:|---:|---:|---:|---:|---:|
| full | 103 | 64 | 39 | -0.5290 | 18.2250 | -54.4898 |
| in-sample 70% | 73 | 45 | 28 | -0.3009 | 12.5336 | -21.9654 |
| holdout 30% | 30 | 19 | 11 | -1.0841 | 5.6914 | -32.5244 |

### Bull-gate counterfactual (same fills)

| Bucket | n | n_long | n_short | expectancy after costs | fee drag (€) |
|---|---:|---:|---:|---:|---:|
| allow (long ∩ bull) | 51 | 51 | 0 | 0.2984 | 8.6693 |
| block | 52 | 13 | 39 | -1.3406 | 9.5557 |
| allow holdout | 15 | 15 | 0 | -0.8281 | 2.8982 |
| block holdout | 15 | 4 | 11 | -1.3401 | 2.7932 |

Side × regime cells (diagnostic, not a second gate):

| Cell | n | expectancy after costs |
|---|---:|---:|
| long_bull | 51 | 0.2984 |
| long_not_bull | 12 | -1.9010 |
| short_bull | 15 | -1.8565 |
| short_not_bull | 23 | -0.5405 |
| fail_closed | 2 | -3.3096 |

`not_a_forecast: true`.

## 2024-12

MD: research MD DOGE-USDT (not OMS DOGE-USD); window 2024-12-01 → 2024-12-31 UTC
Bars: full 2976 · IS 2083 · holdout 893.

### What hurts (drivers)

| Driver | n | price PnL (€) | € contribution | overlaps |
|---|---:|---:|---:|---|
| stop_out | 57 | -142.5685 | -154.7321 | no |
| time_stop | 38 | 83.1578 | 76.0437 | no |
| kill_flatten | 3 | -4.9853 | -5.6205 | no |
| other_exit | 0 | 0.0000 | 0.0000 | no |
| fee_drag | 98 | — | -19.9129 | yes |
| adverse_first_bar | 63 | -73.0014 | -73.0014 | yes |

Top loss drivers (most negative €, fee_drag included, adverse-first-bar excluded from rank): stop_out (-154.7321), fee_drag (-19.9129), kill_flatten (-5.6205).

### Slices

| Slice | n | n_long | n_short | expectancy after costs | fee drag (€) | net PnL (€) |
|---|---:|---:|---:|---:|---:|---:|
| full | 98 | 52 | 46 | -0.8603 | 19.9129 | -84.3089 |
| in-sample 70% | 72 | 37 | 35 | -0.7202 | 14.3177 | -51.8510 |
| holdout 30% | 26 | 15 | 11 | -1.2484 | 5.5952 | -32.4579 |

### Bull-gate counterfactual (same fills)

| Bucket | n | n_long | n_short | expectancy after costs | fee drag (€) |
|---|---:|---:|---:|---:|---:|
| allow (long ∩ bull) | 34 | 34 | 0 | -1.2798 | 7.6394 |
| block | 64 | 18 | 46 | -0.6374 | 12.2736 |
| allow holdout | 13 | 13 | 0 | -0.9517 | 2.9471 |
| block holdout | 13 | 2 | 11 | -1.5450 | 2.6481 |

Side × regime cells (diagnostic, not a second gate):

| Cell | n | expectancy after costs |
|---|---:|---:|
| long_bull | 34 | -1.2798 |
| long_not_bull | 17 | -1.0958 |
| short_bull | 15 | -0.1809 |
| short_not_bull | 30 | -0.5634 |
| fail_closed | 2 | -1.2753 |

`not_a_forecast: true`.

## What NOT to do next

- Do not treat allow-bucket expectancy as a live edge or a Phase C gate.
- Do not retune Donchian lookback, ATR stop, or time-stop to chase these numbers.
- Do not grid-search N on the 1h SMA in this lane.
- Do not silently rewrite the 2020-09 / 2023-09 holdout pass rule.
- Hand this bull gate to Atlas/Claude for **candidate_v2 only if** holdout allow expectancy is better than baseline holdout **and** n_trades is not a handful. Otherwise keep it as a documented hypothesis.
- Claude’s `candidate_v1_filters` (daily_cap / min_atr_frac) is a separate implementation lane — do not merge this gate into that PR from here.

## What this is not

- Not a Phase C recommendation.
- Not a live-trading recommendation.
- Not a claim that the locked breakout has edge in bull markets.

