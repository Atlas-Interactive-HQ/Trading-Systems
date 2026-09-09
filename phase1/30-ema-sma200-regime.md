# 30 — EMA 12/30 + SMA(200) regime (BTC-USDT 1D)

**Stance:** Research. `not_a_forecast: true`. Do not headline PnL. Dual-window interesting must **both** clear or **FAIL**. CLEAR/FAIL bars are **docs only — do not promote**. Do not promote to Phase C or live. Does **not** replace Phase A, live20, or the EMA 12/30 observer. `config/default.yaml` unchanged.

Strategy: `ema_sma200_regime_v1_12_30_200` on **BTC-USDT** **1D**. Long iff **EMA(12) > EMA(30)** AND **close > SMA(200)**. Else **flat**. Never short. Pad ≥ **220** days before each window. Signal at close, fill next open. Paper €200, **1×**.

**Bull-window selection bias:** 2020-09 and 2023-09 include historically strong crypto bull legs. A long-only rule is advantaged here. That is not a forecast.

## Dual-window “interesting” bar (docs only): **FAIL**

after-costs holdout return > 0 on both 2020-09 and 2023-09 AND max DD < buy-and-hold DD on both. **Both** windows must clear; otherwise **FAIL**. Still not_a_forecast.

**Do not promote.** Documentation only. not_a_forecast.

| window | holdout return € | > 0? | holdout max DD € | BH max DD € | DD < BH? | cleared |
|---|---:|:---:|---:|---:|:---:|:---:|
| 2020-09 | 189.6711 | yes | 91.99 | 91.99 | no | no |
| 2023-09 | 116.1369 | yes | 41.78 | 42.63 | yes | yes |

## OOS (2022-bear + 2023-chop, full span, docs only): **CLEAR**

CLEAR iff 2022-bear (full): after-costs return > buy-and-hold AND max DD ≤ BH DD; AND 2023-chop (full): return ≥ 0 OR (return > BH AND DD ≤ BH DD). not_a_forecast. not live. does not replace Phase A.

**Do not promote.** Documentation only. not_a_forecast. not live.

| window | regime return € | BH return € | > BH? | max DD € | BH max DD € | DD ≤ BH? | cleared |
|---|---:|---:|:---:|---:|---:|:---:|:---:|
| 2022-bear | 0.0000 | -129.9965 | yes | 0.00 | 132.48 | yes | yes |
| 2023-chop | 40.9606 | 111.0970 | no | 27.79 | 66.07 | yes | yes |

`not_a_forecast: true`. EMA observer, Phase A DOGE, and live20 untouched.

## 2020-09 (BTC-USDT 1D)

MD: research MD BTC-USDT 1D EMA+SMA200 regime; window 2020-09-01 → 2021-03-31 UTC
Daily bars: full 212 · IS 148 · holdout 64.

| Slice | n_trades | net return € | expectancy after costs | max DD € | time in market | fee drag € | BH return € | BH max DD € |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| full | 1 | 718.7329 | -27.1892 | 216.89 | 0.83 | 0.27 | 777.9736 | 231.11 |
| in-sample 70% | 1 | 718.7329 | -27.1892 | 164.60 | 0.76 | 0.27 | 301.4465 | 175.39 |
| holdout 30% | 0 | 189.6711 | — | 91.99 | 1.00 | 0.10 | 189.2815 | 91.99 |

`not_a_forecast: true`.

## 2023-09 (BTC-USDT 1D)

MD: research MD BTC-USDT 1D EMA+SMA200 regime; window 2023-09-01 → 2024-03-31 UTC
Daily bars: full 213 · IS 149 · holdout 64.

| Slice | n_trades | net return € | expectancy after costs | max DD € | time in market | fee drag € | BH return € | BH max DD € |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| full | 2 | 247.5942 | 41.5824 | 59.15 | 0.72 | 0.58 | 327.6452 | 69.80 |
| in-sample 70% | 2 | 83.1647 | 41.5824 | 41.64 | 0.64 | 0.44 | 126.8121 | 59.31 |
| holdout 30% | 0 | 116.1369 | — | 41.78 | 0.91 | 0.10 | 122.2585 | 42.63 |

`not_a_forecast: true`.

## 2022-bear (BTC-USDT 1D)

MD: research MD BTC-USDT 1D EMA+SMA200 regime; window 2022-01-01 → 2022-12-31 UTC
Daily bars: full 365 · IS 255 · holdout 110.

| Slice | n_trades | net return € | expectancy after costs | max DD € | time in market | fee drag € | BH return € | BH max DD € |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| full | 0 | 0.0000 | — | 0.00 | 0.00 | 0.00 | -129.9965 | 132.48 |
| in-sample 70% | 0 | 0.0000 | — | 0.00 | 0.00 | 0.00 | -111.9379 | 120.90 |
| holdout 30% | 0 | 0.0000 | — | 0.00 | 0.00 | 0.00 | -41.3364 | 49.57 |

`not_a_forecast: true`.

## 2023-chop (BTC-USDT 1D)

MD: research MD BTC-USDT 1D EMA+SMA200 regime; window 2023-01-01 → 2023-08-31 UTC
Daily bars: full 243 · IS 170 · holdout 73.

| Slice | n_trades | net return € | expectancy after costs | max DD € | time in market | fee drag € | BH return € | BH max DD € |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| full | 3 | 40.9606 | 13.6535 | 27.79 | 0.59 | 0.68 | 111.0970 | 66.07 |
| in-sample 70% | 2 | 46.1011 | 23.0506 | 27.79 | 0.64 | 0.44 | 126.3154 | 66.07 |
| holdout 30% | 1 | -4.1776 | -4.1776 | 14.36 | 0.49 | 0.20 | -9.7090 | 40.08 |

`not_a_forecast: true`.

## How to run

```bash
python scripts/run_ema_sma200_regime_eval.py --windows 2020-09,2023-09,2022-bear,2023-chop
```

Writes `ema_sma200_{asset}_{win}.json` under `data/reports/` — does **not** overwrite EMA `ema_*` observer journals or `config/default.yaml`. Uses separate `ema1d_sma200pad_*` eval cache (pad ≥ 220).

## What this is not

- Not a Phase C or live recommendation.
- Not a replacement for Phase A or the EMA 12/30 observer.
- Not a live20 change.
- Not a default in `config/default.yaml`.
- Dual-window FAIL or CLEARED, and OOS CLEAR, are documentation only — do not promote.

