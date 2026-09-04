# 27 — EMA 12/30 + Donchian 20/10 confirm (BTC-USDT 1D)

**Stance:** Research. `not_a_forecast: true`. Do not headline PnL. Dual-window interesting must **both** clear or **FAIL**. CLEAR/FAIL bars are **docs only — do not promote**. Do not promote to Phase C or live. Does **not** replace Phase A BreakoutV1, live20, or the EMA 12/30 observer. `config/default.yaml` unchanged.

Strategy: `ema_donchian_confirm_v1_12_30_20_10` on **BTC-USDT** **1D**. Long iff **EMA(12) > EMA(30)** AND **closed close > prior 20-day high** (exclusive lookback). Flat iff **EMA(12) ≤ EMA(30)** OR **closed close < prior 10-day low**. Never short. Hysteresis: once long, stay long between the 10-day low and 20-day high while EMA is still long. Signal at close, fill next open. Paper book €200, **1×**, fee+slip from existing PaperSettings.

## Relationship to EMA 12/30 and Donchian 20/10

Locked weekday observer is still **EMA 12/30 long/flat** under `data/ema/` (PR #13). PR #18 is **Donchian 20/10** long/flat without the EMA filter. This trial is the AND of both entry conditions and the OR of both exit conditions. It does not change either default.

**Bull-window selection bias:** 2020-09 and 2023-09 include historically strong crypto bull legs. A long-only confirm rule is advantaged here. That is not a forecast.

## Dual-window “interesting” bar (docs only): **FAIL**

after-costs holdout return > 0 on both 2020-09 and 2023-09 AND max DD < buy-and-hold DD on both. **Both** windows must clear; otherwise **FAIL**. Still not_a_forecast.

**Do not promote.** Documentation only. not_a_forecast.

| window | holdout return € | > 0? | holdout max DD € | BH max DD € | DD < BH? | cleared |
|---|---:|:---:|---:|---:|:---:|:---:|
| 2020-09 | 44.1164 | yes | 134.56 | 91.99 | no | no |
| 2023-09 | 81.3934 | yes | 37.97 | 42.63 | yes | yes |

## OOS (2022-bear + 2023-chop, full span, docs only): **CLEAR**

CLEAR iff 2022-bear (full): after-costs return > buy-and-hold AND max DD ≤ BH DD; AND 2023-chop (full): return ≥ 0 OR (return > BH AND DD ≤ BH DD). not_a_forecast. not live. does not replace Phase A.

**Do not promote.** Documentation only. not_a_forecast. not live.

| window | combo return € | BH return € | > BH? | max DD € | BH max DD € | DD ≤ BH? | cleared |
|---|---:|---:|:---:|---:|---:|:---:|:---:|
| 2022-bear | -39.5909 | -129.9965 | yes | 55.10 | 132.48 | yes | yes |
| 2023-chop | 22.3975 | 111.0970 | no | 56.16 | 66.07 | yes | yes |

`not_a_forecast: true`. EMA observer, Phase A DOGE, and live20 untouched.

## 2020-09 (BTC-USDT 1D)

MD: research MD BTC-USDT 1D EMA+Donchian confirm; window 2020-09-01 → 2021-03-31 UTC
Daily bars: full 212 · IS 148 · holdout 64.

| Slice | n_trades | net return € | expectancy after costs | max DD € | time in market | fee drag € | BH return € | BH max DD € |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| full | 2 | 450.5289 | 225.2644 | 358.57 | 0.72 | 1.19 | 777.9736 | 231.11 |
| in-sample 70% | 0 | 838.4079 | — | 186.04 | 0.74 | 0.10 | 301.4465 | 175.39 |
| holdout 30% | 2 | 44.1164 | 22.0582 | 134.56 | 0.69 | 0.51 | 189.2815 | 91.99 |

`not_a_forecast: true`.

## 2023-09 (BTC-USDT 1D)

MD: research MD BTC-USDT 1D EMA+Donchian confirm; window 2023-09-01 → 2024-03-31 UTC
Daily bars: full 213 · IS 149 · holdout 64.

| Slice | n_trades | net return € | expectancy after costs | max DD € | time in market | fee drag € | BH return € | BH max DD € |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| full | 3 | 154.5799 | 51.5266 | 47.85 | 0.64 | 0.72 | 327.6452 | 69.80 |
| in-sample 70% | 2 | 52.0172 | 26.0086 | 37.06 | 0.65 | 0.42 | 126.8121 | 59.31 |
| holdout 30% | 1 | 81.3934 | 81.3934 | 37.97 | 0.62 | 0.24 | 122.2585 | 42.63 |

`not_a_forecast: true`.

## 2022-bear (BTC-USDT 1D)

MD: research MD BTC-USDT 1D EMA+Donchian confirm; window 2022-01-01 → 2022-12-31 UTC
Daily bars: full 365 · IS 255 · holdout 110.

| Slice | n_trades | net return € | expectancy after costs | max DD € | time in market | fee drag € | BH return € | BH max DD € |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| full | 3 | -39.5909 | -13.1970 | 55.10 | 0.13 | 0.55 | -129.9965 | 132.48 |
| in-sample 70% | 2 | -28.4115 | -14.2057 | 43.92 | 0.13 | 0.38 | -111.9379 | 120.90 |
| holdout 30% | 1 | -13.0305 | -13.0305 | 17.21 | 0.12 | 0.19 | -41.3364 | 49.57 |

`not_a_forecast: true`.

## 2023-chop (BTC-USDT 1D)

MD: research MD BTC-USDT 1D EMA+Donchian confirm; window 2023-01-01 → 2023-08-31 UTC
Daily bars: full 243 · IS 170 · holdout 73.

| Slice | n_trades | net return € | expectancy after costs | max DD € | time in market | fee drag € | BH return € | BH max DD € |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| full | 4 | 22.3975 | 5.5994 | 56.16 | 0.47 | 0.91 | 111.0970 | 66.07 |
| in-sample 70% | 3 | 28.6683 | 9.5561 | 56.16 | 0.48 | 0.69 | 126.3154 | 66.07 |
| holdout 30% | 1 | -5.4846 | -5.4846 | 14.56 | 0.45 | 0.20 | -9.7090 | 40.08 |

`not_a_forecast: true`.

## How to run

```bash
python scripts/run_ema_donchian_confirm_eval.py --windows 2020-09,2023-09,2022-bear,2023-chop
```

Writes `ema_donchian_{asset}_{win}.json` under `data/reports/` — does **not** overwrite EMA `ema_*`, Donchian `donchian_*`, or 12/21 compare reports.

## What this is not

- Not a Phase C recommendation.
- Not a live-trading recommendation.
- Not a replacement for Phase A BreakoutV1 / DOGE 15m.
- Not a replacement for the EMA 12/30 daily observer.
- Not a live20 change.
- Not a default strategy in `config/default.yaml`.
- Dual-window FAIL or CLEARED, and OOS CLEAR, are documentation only — do not promote.

