# 20 — EMA long/flat OOS stress (2022 bear + 2023 chop)

**Stance:** Research. `not_a_forecast: true`. Do not headline PnL. Do not promote to Phase C or live. Does **not** replace Phase A BreakoutV1.

Strategy: `ema_long_flat_v1_12_30` on **BTC-USDT** 1D. Fixed 12/30. Neighbors 10/30 and 15/25 are a sensitivity table only — not a search.

PR #11’s bull-window “interesting” bar is restated below for comparison. **This PR’s decision bar is bear + chop (full span).**

## Decision bar (2022-bear + 2023-chop): **CLEAR**

CLEAR iff 2022-bear (full): after-costs return > buy-and-hold AND max DD ≤ BH DD; AND 2023-chop (full): return ≥ 0 OR (return > BH AND DD ≤ BH DD). not_a_forecast. not live. does not replace Phase A.

| window | EMA return € | BH return € | EMA > BH? | EMA max DD € | BH max DD € | DD ≤ BH? | cleared |
|---|---:|---:|:---:|---:|---:|:---:|:---:|
| 2022-bear | -105.9800 | -129.9965 | yes | 105.98 | 132.48 | yes | yes |
| 2023-chop | 94.6455 | 111.0970 | no | 33.98 | 66.07 | yes | yes |

`not_a_forecast: true`. Still not live / not replacing Phase A.

## Restated: PR #11 interesting bar (bull named windows, holdout)

**NOT CLEARED** — after-costs holdout return > 0 on both 2020-09 and 2023-09 AND max DD < buy-and-hold DD on both. Still not_a_forecast.

| window | holdout return € | > 0? | holdout max DD € | BH max DD € | DD < BH? | cleared |
|---|---:|:---:|---:|---:|:---:|:---:|
| 2020-09 | 189.6711 | yes | 91.99 | 91.99 | no | no |
| 2023-09 | 116.1369 | yes | 41.78 | 42.63 | yes | yes |

Bull-window selection bias still applies to those two rows.

## 2022-bear (BTC-USDT)

MD: research MD BTC-USDT 1D; window 2022-01-01 → 2022-12-31 UTC
Daily bars: full 365 · IS 255 · holdout 110.

| Slice | n_trades | net return € | net return % | max DD € | max DD % | expectancy after costs | time in market | fee drag € | BH return € | BH max DD € |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| full | 6 | -105.9800 | -52.99 | 105.98 | 52.99 | -17.6633 | 0.21 | 0.86 | -129.9965 | 132.48 |
| in-sample 70% | 5 | -85.3194 | -42.66 | 85.32 | 42.66 | -17.0639 | 0.25 | 0.75 | -111.9379 | 120.90 |
| holdout 30% | 1 | -36.0316 | -18.02 | 40.21 | 20.11 | -36.0316 | 0.13 | 0.18 | -41.3364 | 49.57 |

Neighbors (holdout only; **not** a search, not a second candidate):

| fast/slow | holdout net return € | holdout max DD € |
|---|---:|---:|
| 12/30 (this strategy) | -36.0316 | 40.21 |
| 10/30 | -46.2383 | 50.42 |
| 15/25 | -31.8826 | 40.05 |

`not_a_forecast: true`.

## 2022-h1 (BTC-USDT)

MD: research MD BTC-USDT 1D; window 2022-01-01 → 2022-06-30 UTC
Daily bars: full 181 · IS 126 · holdout 55.

| Slice | n_trades | net return € | net return % | max DD € | max DD % | expectancy after costs | time in market | fee drag € | BH return € | BH max DD € |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| full | 3 | -55.8307 | -27.92 | 55.83 | 27.92 | -18.6102 | 0.20 | 0.49 | -118.4432 | 120.54 |
| in-sample 70% | 3 | -55.8307 | -27.92 | 55.83 | 27.92 | -18.6102 | 0.29 | 0.49 | -47.9620 | 55.43 |
| holdout 30% | 0 | 0.0000 | 0.00 | 0.00 | 0.00 | — | 0.00 | 0.00 | -92.9295 | 94.71 |

Neighbors (holdout only; **not** a search, not a second candidate):

| fast/slow | holdout net return € | holdout max DD € |
|---|---:|---:|
| 12/30 (this strategy) | 0.0000 | 0.00 |
| 10/30 | 0.0000 | 0.00 |
| 15/25 | 0.0000 | 0.00 |

`not_a_forecast: true`.

## 2023-chop (BTC-USDT)

MD: research MD BTC-USDT 1D; window 2023-01-01 → 2023-08-31 UTC
Daily bars: full 243 · IS 170 · holdout 73.

| Slice | n_trades | net return € | net return % | max DD € | max DD % | expectancy after costs | time in market | fee drag € | BH return € | BH max DD € |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| full | 3 | 94.6455 | 47.32 | 33.98 | 16.99 | 31.5485 | 0.62 | 0.81 | 111.0970 | 66.07 |
| in-sample 70% | 2 | 100.9314 | 50.47 | 33.98 | 16.99 | 50.4657 | 0.67 | 0.51 | 126.3154 | 66.07 |
| holdout 30% | 1 | -4.1776 | -2.09 | 14.36 | 7.18 | -4.1776 | 0.49 | 0.20 | -9.7090 | 40.08 |

Neighbors (holdout only; **not** a search, not a second candidate):

| fast/slow | holdout net return € | holdout max DD € |
|---|---:|---:|
| 12/30 (this strategy) | -4.1776 | 14.36 |
| 10/30 | -4.9083 | 14.36 |
| 15/25 | -3.9663 | 14.36 |

`not_a_forecast: true`.

## 2020-09 (BTC-USDT)

MD: research MD BTC-USDT 1D; window 2020-09-01 → 2021-03-31 UTC
Daily bars: full 212 · IS 148 · holdout 64.

| Slice | n_trades | net return € | net return % | max DD € | max DD % | expectancy after costs | time in market | fee drag € | BH return € | BH max DD € |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| full | 1 | 718.7329 | 359.37 | 216.89 | 108.45 | -27.1892 | 0.83 | 0.27 | 777.9736 | 231.11 |
| in-sample 70% | 1 | 718.7329 | 359.37 | 164.60 | 82.30 | -27.1892 | 0.76 | 0.27 | 301.4465 | 175.39 |
| holdout 30% | 0 | 189.6711 | 94.84 | 91.99 | 46.00 | — | 1.00 | 0.10 | 189.2815 | 91.99 |

Neighbors (holdout only; **not** a search, not a second candidate):

| fast/slow | holdout net return € | holdout max DD € |
|---|---:|---:|
| 12/30 (this strategy) | 189.6711 | 91.99 |
| 10/30 | 189.6711 | 91.99 |
| 15/25 | 189.6711 | 91.99 |

`not_a_forecast: true`.

## 2023-09 (BTC-USDT)

MD: research MD BTC-USDT 1D; window 2023-09-01 → 2024-03-31 UTC
Daily bars: full 213 · IS 149 · holdout 64.

| Slice | n_trades | net return € | net return % | max DD € | max DD % | expectancy after costs | time in market | fee drag € | BH return € | BH max DD € |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| full | 1 | 275.2385 | 137.62 | 62.80 | 31.40 | 100.6536 | 0.79 | 0.40 | 327.6452 | 69.80 |
| in-sample 70% | 1 | 100.6536 | 50.33 | 44.21 | 22.10 | 100.6536 | 0.74 | 0.25 | 126.8121 | 59.31 |
| holdout 30% | 0 | 116.1369 | 58.07 | 41.78 | 20.89 | — | 0.91 | 0.10 | 122.2585 | 42.63 |

Neighbors (holdout only; **not** a search, not a second candidate):

| fast/slow | holdout net return € | holdout max DD € |
|---|---:|---:|
| 12/30 (this strategy) | 116.1369 | 41.78 |
| 10/30 | 115.3107 | 41.67 |
| 15/25 | 117.5035 | 41.96 |

`not_a_forecast: true`.



## Secondary: DOGE-USDT (same 12/30, not the decision bar)

DOGE 2022-bear: return −46.04 vs BH −119.13 (better) but max DD 168.22 vs BH 164.15 (**not** ≤ BH). 2023-chop: −68.24 vs BH −18.57 (worse) and negative. **NOT CLEAR** on DOGE — secondary only; BTC is this PR's decision asset.

## What this is not

- Not a Phase C recommendation.
- Not a live-trading recommendation.
- Not a replacement for Phase A BreakoutV1.
- Not a PASS/FAIL vs the breakout baseline (different family).
- Neighbor EMA pairs are a sensitivity note, not an optimized winner.

