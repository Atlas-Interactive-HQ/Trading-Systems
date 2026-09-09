# 31 — EMA 12/30 asymmetric persist-2 entry (BTC-USDT 1D)

**Stance:** Research. `not_a_forecast: true`. Do not headline PnL. **PASS/FAIL: FAIL**. Docs only — **do not promote**. Does **not** replace Phase A, live20, or the EMA 12/30 observer under `data/ema/`. `config/default.yaml` unchanged. No persist=3/4/5 sweeps. No rescue filters.

Strategy: `ema_12_30_persist2_entry_v1` on **BTC-USDT** **1D**. FLAT→LONG only if **EMA(12) > EMA(30)** on this closed bar **and** the prior closed bar (persist=2). LONG→FLAT on first closed bar with **EMA(12) ≤ EMA(30)** (immediate exit). Never short. Signal at close, fill next open. Paper €200, **1×**, same fee+slip as EMA family (`EmaBookSettings`).

Side-by-side baseline: `ema_long_flat_v1_12_30` (locked observer 12/30).

**Bull-window selection bias:** 2020-09 and 2023-09 include historically strong crypto bull legs. A long-only rule is advantaged here. That is not a forecast.

## PASS gate (all locks must hold): **FAIL**

1. 2022-bear full: expectancy > −17.6633 AND net ≥ locked 12/30 AND max DD ≤ 105.98
2. 2023-chop full: expectancy > 31.5485 AND net ≥ locked 12/30 AND max DD ≤ 33.98
3. Both 30% holdouts 2022-bear + 2023-chop: n_trades≥1; expectancy not worse than 12/30; DD not worse
4. Bull full 2020-09 return ≥ 646.86; 2023-09 ≥ 247.71; DD not exceed locked 12/30 DD

Missing/NaN/zero trades on scored OOS holdout = **FAIL**. Secondary: return+DD vs BH (not expectancy vs BH).

**Do not promote.** Observer stays 12/30. not_a_forecast.

| check | ok | detail |
|---|:---:|---|
| 2022-bear-full | yes | exp=-15.4988 net=-92.9929 dd=95.19 |
| 2023-chop-full | no | exp=28.3776 net=85.1328 dd=32.88 |
| oos-holdouts | no | 2022-bear: ok=False n=1.0 exp=-33.7749 dd=40.76 net=—; 2023-chop: ok=False n=1.0 exp=-4.1783 dd=14.36 net=— |
| bull-full | yes | 2020-09: ok=True n=None exp=— dd=211.82 net=697.2408; 2023-09: ok=True n=None exp=— dd=61.11 net=262.4069 |

## Side-by-side full span (persist2 vs locked 12/30)

| window | pair | n_trades | net € | expectancy | max DD € | BH return € | BH max DD € |
|---|---|---:|---:|---:|---:|---:|---:|
| 2020-09 | persist2 | 1 | 697.2408 | -27.1892 | 211.82 | 777.9736 | 231.11 |
| 2020-09 | 12/30 | 1 | 718.7329 | -27.1892 | 216.89 | 777.9736 | 231.11 |
| 2023-09 | persist2 | 1 | 262.4069 | 91.2766 | 61.11 | 327.6452 | 69.80 |
| 2023-09 | 12/30 | 1 | 275.2385 | 100.6536 | 62.80 | 327.6452 | 69.80 |
| 2022-bear | persist2 | 6 | -92.9929 | -15.4988 | 95.19 | -129.9965 | 132.48 |
| 2022-bear | 12/30 | 6 | -105.9800 | -17.6633 | 105.98 | -129.9965 | 132.48 |
| 2023-chop | persist2 | 3 | 85.1328 | 28.3776 | 32.88 | 111.0970 | 66.07 |
| 2023-chop | 12/30 | 3 | 94.6455 | 31.5485 | 33.98 | 111.0970 | 66.07 |

## Side-by-side holdout 30% (persist2 vs locked 12/30)

| window | pair | n_trades | net € | expectancy | max DD € |
|---|---|---:|---:|---:|---:|
| 2020-09 | persist2 | 0 | 189.6711 | — | 91.99 |
| 2020-09 | 12/30 | 0 | 189.6711 | — | 91.99 |
| 2023-09 | persist2 | 0 | 117.5035 | — | 41.96 |
| 2023-09 | 12/30 | 0 | 116.1369 | — | 41.78 |
| 2022-bear | persist2 | 1 | -33.7749 | -33.7749 | 40.76 |
| 2022-bear | 12/30 | 1 | -36.0316 | -36.0316 | 40.21 |
| 2023-chop | persist2 | 1 | -4.1783 | -4.1783 | 14.36 |
| 2023-chop | 12/30 | 1 | -4.1776 | -4.1776 | 14.36 |

`not_a_forecast: true`. EMA observer, Phase A DOGE, and live20 untouched.

## 2020-09 persist2 (BTC-USDT 1D)

MD: research MD BTC-USDT 1D EMA persist-2 entry; window 2020-09-01 → 2021-03-31 UTC
Daily bars: full 212 · IS 148 · holdout 64.

| Slice | n_trades | net return € | expectancy after costs | max DD € | time in market | fee drag € | BH return € | BH max DD € |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| full | 1 | 697.2408 | -27.1892 | 211.82 | 0.83 | 0.27 | 777.9736 | 231.11 |
| in-sample 70% | 1 | 697.2408 | -27.1892 | 160.75 | 0.76 | 0.27 | 301.4465 | 175.39 |
| holdout 30% | 0 | 189.6711 | — | 91.99 | 1.00 | 0.10 | 189.2815 | 91.99 |

`not_a_forecast: true`.

## 2023-09 persist2 (BTC-USDT 1D)

MD: research MD BTC-USDT 1D EMA persist-2 entry; window 2023-09-01 → 2024-03-31 UTC
Daily bars: full 213 · IS 149 · holdout 64.

| Slice | n_trades | net return € | expectancy after costs | max DD € | time in market | fee drag € | BH return € | BH max DD € |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| full | 1 | 262.4069 | 91.2766 | 61.11 | 0.78 | 0.39 | 327.6452 | 69.80 |
| in-sample 70% | 1 | 91.2766 | 91.2766 | 42.83 | 0.73 | 0.25 | 126.8121 | 59.31 |
| holdout 30% | 0 | 117.5035 | — | 41.96 | 0.89 | 0.10 | 122.2585 | 42.63 |

`not_a_forecast: true`.

## 2022-bear persist2 (BTC-USDT 1D)

MD: research MD BTC-USDT 1D EMA persist-2 entry; window 2022-01-01 → 2022-12-31 UTC
Daily bars: full 365 · IS 255 · holdout 110.

| Slice | n_trades | net return € | expectancy after costs | max DD € | time in market | fee drag € | BH return € | BH max DD € |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| full | 6 | -92.9929 | -15.4988 | 95.19 | 0.20 | 0.92 | -129.9965 | 132.48 |
| in-sample 70% | 5 | -71.2504 | -14.2501 | 73.45 | 0.23 | 0.80 | -111.9379 | 120.90 |
| holdout 30% | 1 | -33.7749 | -33.7749 | 40.76 | 0.12 | 0.18 | -41.3364 | 49.57 |

`not_a_forecast: true`.

## 2023-chop persist2 (BTC-USDT 1D)

MD: research MD BTC-USDT 1D EMA persist-2 entry; window 2023-01-01 → 2023-08-31 UTC
Daily bars: full 243 · IS 170 · holdout 73.

| Slice | n_trades | net return € | expectancy after costs | max DD € | time in market | fee drag € | BH return € | BH max DD € |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| full | 3 | 85.1328 | 28.3776 | 32.88 | 0.60 | 0.79 | 111.0970 | 66.07 |
| in-sample 70% | 2 | 91.2166 | 45.6083 | 32.88 | 0.66 | 0.50 | 126.3154 | 66.07 |
| holdout 30% | 1 | -4.1783 | -4.1783 | 14.36 | 0.48 | 0.20 | -9.7090 | 40.08 |

`not_a_forecast: true`.

## How to run

```bash
python scripts/run_ema_persist2_eval.py --windows 2020-09,2023-09,2022-bear,2023-chop
```

Writes `ema_persist2_{asset}_{win}.json` under `data/reports/` — does **not** overwrite `data/ema/` observer journals or `config/default.yaml`.

## What this is not

- Not a Phase C or live recommendation.
- Not a replacement for Phase A or the EMA 12/30 observer.
- Not a live20 change.
- Not a default in `config/default.yaml`.
- Not a persist=3/4/5 sweep or rescue filter.
- PASS/FAIL is documentation only — do not promote.

