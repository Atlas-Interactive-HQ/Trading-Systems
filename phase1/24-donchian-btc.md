# 24 — BTC daily Donchian confirm (parallel paper research)

**Stance:** Research. `not_a_forecast: true`. Do not headline PnL. Do **not** promote CLEAR bars. Do not promote to Phase C or live. Does **not** replace Phase A BreakoutV1 or the EMA 12/30 observer. `config/default.yaml` breakout params are unchanged.

Strategy: `donchian_long_flat_v1_20_10` on **BTC-USDT** **1D**. Long iff **closed close > prior 20-day high** (exclusive lookback). Exit/flat iff **closed close < prior 10-day low**. Never short. Signal at close, fill next open. Paper book €200, **1×**, fee+slip from existing PaperSettings.

## Relationship to BreakoutV1 (15m DOGE)

Phase A `BreakoutV1` is **15m Donchian long *and* short** on DOGE, with ATR stop, time-stop, and a 1h stub filter. This trial is **daily, BTC-USDT, long/flat only**, entry only on a confirmed close above the prior 20-day high — not an aggressive mid-range buy, not L+S. Same Donchian primitive (`donchian_prior`), different TF/universe/state machine.

**Bull-window selection bias:** 2020-09 and 2023-09 include historically strong crypto bull legs. A long-only confirm rule is advantaged here. That is not a forecast.

## Dual-window “interesting” bar (docs only): **NOT CLEARED**

after-costs holdout return > 0 on both 2020-09 and 2023-09 AND max DD < buy-and-hold DD on both. Still not_a_forecast.

**Do not promote.** Documentation only. not_a_forecast.

| window | holdout return € | > 0? | holdout max DD € | BH max DD € | DD < BH? | cleared |
|---|---:|:---:|---:|---:|:---:|:---:|
| 2020-09 | 44.1164 | yes | 134.56 | 91.99 | no | no |
| 2023-09 | 81.3934 | yes | 37.97 | 42.63 | yes | yes |

## OOS (2022-bear + 2023-chop, full span, docs only): **CLEAR**

CLEAR iff 2022-bear (full): after-costs return > buy-and-hold AND max DD ≤ BH DD; AND 2023-chop (full): return ≥ 0 OR (return > BH AND DD ≤ BH DD). not_a_forecast. not live. does not replace Phase A.

**Do not promote.** Documentation only. not_a_forecast. not live.

| window | Donchian return € | BH return € | > BH? | max DD € | BH max DD € | DD ≤ BH? | cleared |
|---|---:|---:|:---:|---:|---:|:---:|:---:|
| 2022-bear | -69.6622 | -129.9965 | yes | 74.56 | 132.48 | yes | yes |
| 2023-chop | 43.8506 | 111.0970 | no | 68.62 | 66.07 | no | yes |

`not_a_forecast: true`. EMA observer and Phase A DOGE untouched.

## 2020-09 (BTC-USDT 1D)

MD: research MD BTC-USDT 1D Donchian confirm; window 2020-09-01 → 2021-03-31 UTC
Daily bars: full 212 · IS 148 · holdout 64.

| Slice | n_trades | net return € | expectancy after costs | max DD € | time in market | fee drag € | BH return € | BH max DD € |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| full | 3 | 375.3154 | 125.1051 | 317.12 | 0.73 | 1.24 | 777.9736 | 231.11 |
| in-sample 70% | 1 | 718.3483 | -23.1238 | 164.53 | 0.75 | 0.28 | 301.4465 | 175.39 |
| holdout 30% | 2 | 44.1164 | 22.0582 | 134.56 | 0.69 | 0.51 | 189.2815 | 91.99 |

`not_a_forecast: true`.

## 2023-09 (BTC-USDT 1D)

MD: research MD BTC-USDT 1D Donchian confirm; window 2023-09-01 → 2024-03-31 UTC
Daily bars: full 213 · IS 149 · holdout 64.

| Slice | n_trades | net return € | expectancy after costs | max DD € | time in market | fee drag € | BH return € | BH max DD € |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| full | 3 | 154.5799 | 51.5266 | 47.85 | 0.64 | 0.72 | 327.6452 | 69.80 |
| in-sample 70% | 2 | 52.0172 | 26.0086 | 37.06 | 0.65 | 0.42 | 126.8121 | 59.31 |
| holdout 30% | 1 | 81.3934 | 81.3934 | 37.97 | 0.62 | 0.24 | 122.2585 | 42.63 |

`not_a_forecast: true`.

## 2022-bear (BTC-USDT 1D)

MD: research MD BTC-USDT 1D Donchian confirm; window 2022-01-01 → 2022-12-31 UTC
Daily bars: full 365 · IS 255 · holdout 110.

| Slice | n_trades | net return € | expectancy after costs | max DD € | time in market | fee drag € | BH return € | BH max DD € |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| full | 5 | -69.6622 | -12.0266 | 74.56 | 0.29 | 0.92 | -129.9965 | 132.48 |
| in-sample 70% | 3 | -70.0222 | -8.7437 | 47.09 | 0.27 | 0.63 | -111.9379 | 120.90 |
| holdout 30% | 2 | -40.7378 | -14.5468 | 40.75 | 0.35 | 0.45 | -41.3364 | 49.57 |

`not_a_forecast: true`.

## 2023-chop (BTC-USDT 1D)

MD: research MD BTC-USDT 1D Donchian confirm; window 2023-01-01 → 2023-08-31 UTC
Daily bars: full 243 · IS 170 · holdout 73.

| Slice | n_trades | net return € | expectancy after costs | max DD € | time in market | fee drag € | BH return € | BH max DD € |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| full | 4 | 43.8506 | 10.9626 | 68.62 | 0.52 | 0.97 | 111.0970 | 66.07 |
| in-sample 70% | 3 | 50.7263 | 16.9088 | 68.62 | 0.55 | 0.72 | 126.3154 | 66.07 |
| holdout 30% | 1 | -5.4846 | -5.4846 | 14.56 | 0.45 | 0.20 | -9.7090 | 40.08 |

`not_a_forecast: true`.

## What this is not

- Not a Phase C recommendation.
- Not a live-trading recommendation.
- Not a replacement for Phase A BreakoutV1 / DOGE 15m.
- Not a replacement for the EMA 12/30 daily observer.
- Not a default strategy in `config/default.yaml`.
- CLEAR-style bars here are documentation only — do not promote.

