# 19 — EMA long/flat (daily) — parallel research strategy

**Stance:** Research. `not_a_forecast: true`. Do not headline PnL. Do not promote to Phase C or live. Does **not** replace Phase A BreakoutV1. Do **not** claim PASS against the breakout baseline (different family).

Strategy: `ema_long_flat_v1_12_30` — 1D closed bars, long iff EMA(12) > EMA(30), otherwise **flat**. Never short. Signal at close, fill next open. Paper book €200, 1× leverage, fee+slip from existing PaperSettings.

**Bull-window selection bias:** primary named windows 2020-09 and 2023-09 are the same spans used for breakout research and include historically strong crypto bull legs. A long-only rule is advantaged here. That is not a forecast of the coming months.

## Dual-window “interesting” bar: **NOT CLEARED**

after-costs holdout return > 0 on both 2020-09 and 2023-09 AND max DD < buy-and-hold DD on both. Still not_a_forecast.

| window | holdout return € | > 0? | holdout max DD € | BH max DD € | DD < BH? | cleared |
|---|---:|:---:|---:|---:|:---:|:---:|
| 2020-09 | 189.6711 | yes | 91.99 | 91.99 | no | no |
| 2023-09 | 116.1369 | yes | 41.78 | 42.63 | yes | yes |

`not_a_forecast: true`. Named-window ≠ future.

Holdout **n_trades = 0** on the primary BTC slices means the slice started already in a long regime (EMA from pad + prior bars) and did not flatten before the slice ended — return is marked equity, not a closed round-trip. 2020-09 holdout DD equals buy-and-hold DD because time-in-market was 100%. Strict `<` vs BH DD therefore fails. **NOT CLEARED.** This is not a PASS vs breakout.

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

## 2020-10 (BTC-USDT)

MD: research MD BTC-USDT 1D; window 2020-10-01 → 2020-10-31 UTC
Daily bars: full 31 · IS 21 · holdout 10.

| Slice | n_trades | net return € | net return % | max DD € | max DD % | expectancy after costs | time in market | fee drag € | BH return € | BH max DD € |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| full | 0 | 40.9872 | 20.49 | 7.04 | 3.52 | — | 0.71 | 0.10 | 54.9714 | 7.45 |
| in-sample 70% | 0 | 40.9872 | 20.49 | 4.01 | 2.01 | — | 0.57 | 0.10 | 40.5084 | 4.25 |
| holdout 30% | 0 | 11.8020 | 5.90 | 6.19 | 3.09 | — | 1.00 | 0.10 | 11.5903 | 6.19 |

Neighbors (holdout only; **not** a search, not a second candidate):

| fast/slow | holdout net return € | holdout max DD € |
|---|---:|---:|
| 12/30 (this strategy) | 11.8020 | 6.19 |
| 10/30 | 11.8020 | 6.19 |
| 15/25 | 11.8020 | 6.19 |

`not_a_forecast: true`.

## 2020-11 (BTC-USDT)

MD: research MD BTC-USDT 1D; window 2020-11-01 → 2020-11-30 UTC
Daily bars: full 30 · IS 21 · holdout 9.

| Slice | n_trades | net return € | net return % | max DD € | max DD % | expectancy after costs | time in market | fee drag € | BH return € | BH max DD € |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| full | 0 | 81.2011 | 40.60 | 41.54 | 20.77 | — | 1.00 | 0.10 | 80.9200 | 41.54 |
| in-sample 70% | 0 | 81.2011 | 40.60 | 6.20 | 3.10 | — | 1.00 | 0.10 | 66.1669 | 6.20 |
| holdout 30% | 0 | 10.8839 | 5.44 | 31.15 | 15.58 | — | 1.00 | 0.10 | 10.6730 | 31.15 |

Neighbors (holdout only; **not** a search, not a second candidate):

| fast/slow | holdout net return € | holdout max DD € |
|---|---:|---:|
| 12/30 (this strategy) | 10.8839 | 31.15 |
| 10/30 | 10.8839 | 31.15 |
| 15/25 | 10.8839 | 31.15 |

`not_a_forecast: true`.

## 2020-12 (BTC-USDT)

MD: research MD BTC-USDT 1D; window 2020-12-01 → 2020-12-31 UTC
Daily bars: full 31 · IS 21 · holdout 10.

| Slice | n_trades | net return € | net return % | max DD € | max DD % | expectancy after costs | time in market | fee drag € | BH return € | BH max DD € |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| full | 0 | 102.6703 | 51.34 | 14.89 | 7.45 | — | 1.00 | 0.10 | 102.3677 | 14.89 |
| in-sample 70% | 0 | 102.6703 | 51.34 | 14.89 | 7.45 | — | 1.00 | 0.10 | 41.8469 | 14.89 |
| holdout 30% | 0 | 49.7990 | 24.90 | 6.37 | 3.18 | — | 1.00 | 0.10 | 49.5492 | 6.37 |

Neighbors (holdout only; **not** a search, not a second candidate):

| fast/slow | holdout net return € | holdout max DD € |
|---|---:|---:|
| 12/30 (this strategy) | 49.7990 | 6.37 |
| 10/30 | 49.7990 | 6.37 |
| 15/25 | 49.7990 | 6.37 |

`not_a_forecast: true`.

## 2023-10 (BTC-USDT)

MD: research MD BTC-USDT 1D; window 2023-10-01 → 2023-10-31 UTC
Daily bars: full 31 · IS 21 · holdout 10.

| Slice | n_trades | net return € | net return % | max DD € | max DD % | expectancy after costs | time in market | fee drag € | BH return € | BH max DD € |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| full | 0 | 52.3380 | 26.17 | 9.94 | 4.97 | — | 1.00 | 0.10 | 52.0857 | 9.94 |
| in-sample 70% | 0 | 52.3380 | 26.17 | 9.94 | 4.97 | — | 1.00 | 0.10 | 19.2648 | 9.94 |
| holdout 30% | 0 | 29.7074 | 14.85 | 5.63 | 2.82 | — | 1.00 | 0.10 | 29.4778 | 5.63 |

Neighbors (holdout only; **not** a search, not a second candidate):

| fast/slow | holdout net return € | holdout max DD € |
|---|---:|---:|
| 12/30 (this strategy) | 29.7074 | 5.63 |
| 10/30 | 29.7074 | 5.63 |
| 15/25 | 29.7074 | 5.63 |

`not_a_forecast: true`.

## 2023-11 (BTC-USDT)

MD: research MD BTC-USDT 1D; window 2023-11-01 → 2023-11-30 UTC
Daily bars: full 30 · IS 21 · holdout 9.

| Slice | n_trades | net return € | net return % | max DD € | max DD % | expectancy after costs | time in market | fee drag € | BH return € | BH max DD € |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| full | 0 | 23.8184 | 11.91 | 8.55 | 4.28 | — | 1.00 | 0.10 | 23.5946 | 8.55 |
| in-sample 70% | 0 | 23.8184 | 11.91 | 6.48 | 3.24 | — | 1.00 | 0.10 | 12.3408 | 6.48 |
| holdout 30% | 0 | 10.3893 | 5.19 | 8.04 | 4.02 | — | 1.00 | 0.10 | 10.1790 | 8.04 |

Neighbors (holdout only; **not** a search, not a second candidate):

| fast/slow | holdout net return € | holdout max DD € |
|---|---:|---:|
| 12/30 (this strategy) | 10.3893 | 8.04 |
| 10/30 | 10.3893 | 8.04 |
| 15/25 | 10.3893 | 8.04 |

`not_a_forecast: true`.

## 2023-12 (BTC-USDT)

MD: research MD BTC-USDT 1D; window 2023-12-01 → 2023-12-31 UTC
Daily bars: full 31 · IS 21 · holdout 10.

| Slice | n_trades | net return € | net return % | max DD € | max DD % | expectancy after costs | time in market | fee drag € | BH return € | BH max DD € |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| full | 0 | 22.5262 | 11.26 | 14.46 | 7.23 | — | 1.00 | 0.10 | 22.3037 | 14.46 |
| in-sample 70% | 0 | 22.5262 | 11.26 | 14.46 | 7.23 | — | 1.00 | 0.10 | 26.9205 | 14.46 |
| holdout 30% | 0 | -4.2648 | -2.13 | 6.82 | 3.41 | — | 1.00 | 0.10 | -4.4605 | 6.82 |

Neighbors (holdout only; **not** a search, not a second candidate):

| fast/slow | holdout net return € | holdout max DD € |
|---|---:|---:|
| 12/30 (this strategy) | -4.2648 | 6.82 |
| 10/30 | -4.2648 | 6.82 |
| 15/25 | -4.2648 | 6.82 |

`not_a_forecast: true`.

## 2024-10 (BTC-USDT)

MD: research MD BTC-USDT 1D; window 2024-10-01 → 2024-10-31 UTC
Daily bars: full 31 · IS 21 · holdout 10.

| Slice | n_trades | net return € | net return % | max DD € | max DD % | expectancy after costs | time in market | fee drag € | BH return € | BH max DD € |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| full | 0 | 21.3703 | 10.69 | 9.59 | 4.80 | — | 1.00 | 0.10 | 21.1490 | 9.59 |
| in-sample 70% | 0 | 21.3703 | 10.69 | 9.13 | 4.57 | — | 1.00 | 0.10 | 14.4324 | 9.13 |
| holdout 30% | 0 | 6.0581 | 3.03 | 8.93 | 4.47 | — | 1.00 | 0.10 | 5.8521 | 8.93 |

Neighbors (holdout only; **not** a search, not a second candidate):

| fast/slow | holdout net return € | holdout max DD € |
|---|---:|---:|
| 12/30 (this strategy) | 6.0581 | 8.93 |
| 10/30 | 6.0581 | 8.93 |
| 15/25 | 6.0581 | 8.93 |

`not_a_forecast: true`.

## 2024-11 (BTC-USDT)

MD: research MD BTC-USDT 1D; window 2024-11-01 → 2024-11-30 UTC
Daily bars: full 30 · IS 21 · holdout 9.

| Slice | n_trades | net return € | net return % | max DD € | max DD % | expectancy after costs | time in market | fee drag € | BH return € | BH max DD € |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| full | 0 | 79.3785 | 39.69 | 16.80 | 8.40 | — | 1.00 | 0.10 | 79.0992 | 16.80 |
| in-sample 70% | 0 | 79.3785 | 39.69 | 13.16 | 6.58 | — | 1.00 | 0.10 | 83.7622 | 13.16 |
| holdout 30% | 0 | -3.4783 | -1.74 | 12.01 | 6.01 | — | 1.00 | 0.10 | -3.6748 | 12.01 |

Neighbors (holdout only; **not** a search, not a second candidate):

| fast/slow | holdout net return € | holdout max DD € |
|---|---:|---:|
| 12/30 (this strategy) | -3.4783 | 12.01 |
| 10/30 | -3.4783 | 12.01 |
| 15/25 | -3.4783 | 12.01 |

`not_a_forecast: true`.

## 2024-12 (BTC-USDT)

MD: research MD BTC-USDT 1D; window 2024-12-01 → 2024-12-31 UTC
Daily bars: full 31 · IS 21 · holdout 10.

| Slice | n_trades | net return € | net return % | max DD € | max DD % | expectancy after costs | time in market | fee drag € | BH return € | BH max DD € |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| full | 1 | -10.4934 | -5.25 | 29.74 | 14.87 | -10.4934 | 0.94 | 0.19 | -5.7205 | 29.54 |
| in-sample 70% | 0 | -5.5261 | -2.76 | 22.86 | 11.43 | — | 1.00 | 0.10 | -3.8115 | 22.86 |
| holdout 30% | 1 | -7.1977 | -3.60 | 13.62 | 6.81 | -7.1977 | 0.80 | 0.20 | -2.3418 | 13.43 |

Neighbors (holdout only; **not** a search, not a second candidate):

| fast/slow | holdout net return € | holdout max DD € |
|---|---:|---:|
| 12/30 (this strategy) | -7.1977 | 13.62 |
| 10/30 | -7.1977 | 13.62 |
| 15/25 | -7.1977 | 13.62 |

`not_a_forecast: true`.


## Secondary asset: DOGE-USDT (same rule)

Same 12/30 long/flat. Secondary. Bull-window bias still applies. `not_a_forecast`.

## 2020-09 (DOGE-USDT)

MD: research MD DOGE-USDT 1D; window 2020-09-01 → 2021-03-31 UTC
Daily bars: full 212 · IS 148 · holdout 64.

| Slice | n_trades | net return € | net return % | max DD € | max DD % | expectancy after costs | time in market | fee drag € | BH return € | BH max DD € |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| full | 0 | 4245.7487 | 2122.87 | 2693.94 | 1346.97 | — | 0.67 | 0.10 | 3459.9564 | 2220.00 |
| in-sample 70% | 0 | 4245.7487 | 2122.87 | 371.91 | 185.96 | — | 0.53 | 0.10 | 269.4306 | 306.48 |
| holdout 30% | 0 | 1357.7594 | 678.88 | 943.94 | 471.97 | — | 1.00 | 0.10 | 1356.2019 | 943.94 |

Neighbors (holdout only; **not** a search, not a second candidate):

| fast/slow | holdout net return € | holdout max DD € |
|---|---:|---:|
| 12/30 (this strategy) | 1357.7594 | 943.94 |
| 10/30 | 1357.7594 | 943.94 |
| 15/25 | 1357.7594 | 943.94 |

`not_a_forecast: true`.

## 2023-09 (DOGE-USDT)

MD: research MD DOGE-USDT 1D; window 2023-09-01 → 2024-03-31 UTC
Daily bars: full 213 · IS 149 · holdout 64.

| Slice | n_trades | net return € | net return % | max DD € | max DD % | expectancy after costs | time in market | fee drag € | BH return € | BH max DD € |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| full | 1 | 397.7909 | 198.90 | 126.00 | 63.00 | 55.4399 | 0.55 | 0.36 | 427.2257 | 132.34 |
| in-sample 70% | 1 | 55.4399 | 27.72 | 56.81 | 28.40 | 55.4399 | 0.48 | 0.23 | 50.6258 | 74.83 |
| holdout 30% | 0 | 268.0482 | 134.02 | 98.66 | 49.33 | — | 0.72 | 0.10 | 299.5902 | 105.41 |

Neighbors (holdout only; **not** a search, not a second candidate):

| fast/slow | holdout net return € | holdout max DD € |
|---|---:|---:|
| 12/30 (this strategy) | 268.0482 | 98.66 |
| 10/30 | 278.7995 | 100.92 |
| 15/25 | 268.0482 | 98.66 |

`not_a_forecast: true`.

## What this is not

- Not a Phase C recommendation.
- Not a live-trading recommendation.
- Not a replacement for Phase A BreakoutV1.
- Not a PASS/FAIL vs the breakout baseline (different family).
- Neighbor EMA pairs are a sensitivity note, not an optimized winner.

