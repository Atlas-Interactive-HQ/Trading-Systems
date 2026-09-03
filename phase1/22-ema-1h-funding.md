# 22 — EMA 1H long/flat + perpetual funding

**Stance:** Research. `not_a_forecast: true`. Do not headline PnL. Do not promote to Phase C or live. Does **not** replace Phase A BreakoutV1. Daily EMA observer (`phase1/21`) is **unchanged**.

Strategy: `ema_long_flat_v1_12_30` on **BTC-USDT-SWAP** **1H**. Long iff EMA(12) > EMA(30), else **flat**. Never short. Signal at close, fill next open. Paper book €200, **1×**.

## Instrument and funding source

- MD: public OKX EEA `history-candles` `BTC-USDT-SWAP` `1H` (fail closed if empty).
- Funding: `/api/v5/public/funding-rate-history` unsigned.
- Formula: long cashflow = `-qty * bar_open * realizedRate` (pay if rate>0). Only while long.
- Prints fetched: 277 (2026-06-03 08:00 UTC → 2026-09-03 08:00 UTC).
- OKX documents ~3 months of funding-rate-history. Named 2020/2022/2023 windows typically have zero overlap — flag funding_incomplete and score fee-only. Do not invent rates.
- Q4 calendar months are optional (`--windows q4`); not required for these CLEAR bars.

## Bull holdouts (2020-09 & 2023-09): **CLEAR**

CLEAR iff after-costs holdout return > 0 on both 2020-09 and 2023-09. After-costs includes funding when complete; fee-only when funding_incomplete.

| window | holdout after-costs € | fee-only € | with observed funding € | incomplete? | > 0? | cleared |
|---|---:|---:|---:|:---:|:---:|:---:|
| 2020-09 | 95.6046 | 95.6046 | 95.6046 | yes | yes | yes |
| 2023-09 | 35.8732 | 35.8732 | 35.8732 | yes | yes | yes |

## OOS (2022-bear + 2023-chop, full span): **CLEAR**

CLEAR iff 2022-bear (full): after-costs return > buy-and-hold AND max DD ≤ BH DD; AND 2023-chop (full): return ≥ 0 OR (return > BH AND DD ≤ BH DD). After-costs includes funding when complete; fee-only when funding_incomplete. not_a_forecast. not live. does not replace Phase A.

| window | after-costs € | fee-only € | with funding € | BH € | EMA > BH? | EMA max DD € | BH max DD € | DD ≤ BH? | incomplete? | cleared |
|---|---:|---:|---:|---:|:---:|---:|---:|:---:|:---:|:---:|
| 2022-bear | -113.9893 | -113.9893 | -113.9893 | -128.5423 | yes | 117.51 | 139.73 | yes | yes | yes |
| 2023-chop | 14.4119 | 14.4119 | 14.4119 | 112.9509 | no | 106.48 | 72.81 | no | yes | yes |

`not_a_forecast: true`. Daily observer unchanged. Still not live.

## 2020-09 (BTC-USDT-SWAP 1H)

MD: research MD BTC-USDT-SWAP 1H; window 2020-09-01 → 2021-03-31 UTC
1H bars: full 5088 · IS 3561 · holdout 1527.

| Slice | n_trades | after-costs € | fee-only € | with funding € | funding drag € | incomplete? | max DD € | time in market | BH after-costs € |
|---|---:|---:|---:|---:|---:|:---:|---:|---:|---:|
| full | 77 | 387.0878 | 387.0878 | 387.0878 | 0.0000 | yes | 107.64 | 0.63 | 807.6684 |
| in-sample 70% | 52 | 197.2114 | 197.2114 | 197.2114 | 0.0000 | yes | 97.87 | 0.62 | 334.1055 |
| holdout 30% | 25 | 95.6046 | 95.6046 | 95.6046 | 0.0000 | yes | 54.20 | 0.64 | 176.6916 |

`not_a_forecast: true`.

## 2023-09 (BTC-USDT-SWAP 1H)

MD: research MD BTC-USDT-SWAP 1H; window 2023-09-01 → 2024-03-31 UTC
1H bars: full 5112 · IS 3578 · holdout 1534.

| Slice | n_trades | after-costs € | fee-only € | with funding € | funding drag € | incomplete? | max DD € | time in market | BH after-costs € |
|---|---:|---:|---:|---:|---:|:---:|---:|---:|---:|
| full | 85 | 109.1135 | 109.1135 | 109.1135 | 0.0000 | yes | 51.87 | 0.61 | 348.8210 |
| in-sample 70% | 56 | 243.7174 | 243.7174 | 243.7174 | 0.0000 | yes | 37.48 | 0.57 | 123.8609 |
| holdout 30% | 29 | 35.8732 | 35.8732 | 35.8732 | 0.0000 | yes | 39.58 | 0.69 | 138.2461 |

`not_a_forecast: true`.

## 2022-bear (BTC-USDT-SWAP 1H)

MD: research MD BTC-USDT-SWAP 1H; window 2022-01-01 → 2022-12-31 UTC
1H bars: full 8760 · IS 6132 · holdout 2628.

| Slice | n_trades | after-costs € | fee-only € | with funding € | funding drag € | incomplete? | max DD € | time in market | BH after-costs € |
|---|---:|---:|---:|---:|---:|:---:|---:|---:|---:|
| full | 141 | -113.9893 | -113.9893 | -113.9893 | 0.0000 | yes | 117.51 | 0.45 | -128.5423 |
| in-sample 70% | 97 | -119.2431 | -119.2431 | -119.2431 | 0.0000 | yes | 108.63 | 0.45 | -102.7079 |
| holdout 30% | 44 | -43.7066 | -43.7066 | -43.7066 | 0.0000 | yes | 46.33 | 0.46 | -53.4003 |

`not_a_forecast: true`.

## 2023-chop (BTC-USDT-SWAP 1H)

MD: research MD BTC-USDT-SWAP 1H; window 2023-01-01 → 2023-08-31 UTC
1H bars: full 5832 · IS 4082 · holdout 1750.

| Slice | n_trades | after-costs € | fee-only € | with funding € | funding drag € | incomplete? | max DD € | time in market | BH after-costs € |
|---|---:|---:|---:|---:|---:|:---:|---:|---:|---:|
| full | 102 | 14.4119 | 14.4119 | 14.4119 | 0.0000 | yes | 106.48 | 0.51 | 112.9509 |
| in-sample 70% | 64 | 40.3219 | 40.3219 | 40.3219 | 0.0000 | yes | 82.95 | 0.55 | 124.5704 |
| holdout 30% | 38 | -28.1233 | -28.1233 | -28.1233 | 0.0000 | yes | 60.34 | 0.42 | -7.5459 |

`not_a_forecast: true`.

## What this is not

- Not a Phase C recommendation.
- Not a live-trading recommendation.
- Not a replacement for Phase A BreakoutV1 / DOGE demo.
- Not a change to the daily EMA paper observer.
- Missing funding prints are **not** filled with 0 or a default — they flag `funding_incomplete`.

