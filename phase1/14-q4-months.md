# 14 — Q4 calendar-month samples (Oct/Nov/Dec)

**Stance:** Research. `not_a_forecast: true`. Do not headline PnL. Do not promote to Phase C or live from this score.

Q4 calendar months exist so Phase D can define the system against the same season as the coming months. They are not similar-regime matches and they do not rewrite the named-window holdout pass rule on 2020-09 + 2023-09. Research MD = DOGE-USDT (not OMS DOGE-USD). Empty months are skipped, never faked.

Primary score: **expectancy after costs** on the €200 paper book. Split is chronological 70/30 (cut never searched). Stress uses the same engine path (2× fees, 1-bar entry delay, 10% missed entries seed 20260903).

Named-window / similar-regime ≠ future performance. BreakoutV1 params were not retuned.

Q4 months inform “coming months” definition. They do **not** rewrite the candidate pass rule on named `2020-09` + `2023-09` holdouts.

```bash
python scripts/replay_phase_a_history.py --windows 2020-10,2020-11,2020-12,2023-10,2023-11,2023-12,2024-10,2024-11,2024-12 --venue spot
python scripts/run_paper_eval.py --samples q4 --write-md phase1/14-q4-months.md
```

## Mac run (2026-09-03)

Public EEA `history-candles` on **DOGE-USDT**: all nine months returned complete spans (Oct 2976 15m bars, Nov 2880, Dec 2976). **No skips.** X-Perp was not fetched on this path (named-window rule: skip `…310404`, do not invent bars).

| Id | n_trades | expectancy after costs (€/trade) | max DD (€) | n_kill_days | holdout expectancy | holdout max DD (€) | holdout kill-days |
|----|---:|---:|---:|---:|---:|---:|---:|
| 2020-10 | 93 | -0.6717 | 99.39 | 0 | -0.0103 | 33.39 | 0 |
| 2020-11 | 98 | -0.5331 | 77.03 | 5 | -0.3508 | 25.84 | 2 |
| 2020-12 | 100 | -0.3779 | 90.69 | 10 | -1.2134 | 72.37 | 6 |
| 2023-10 | 102 | -0.4839 | 84.63 | 3 | -1.0208 | 65.23 | 3 |
| 2023-11 | 95 | -0.3845 | 67.01 | 6 | -0.5472 | 31.14 | 1 |
| 2023-12 | 114 | -0.3281 | 99.17 | 10 | -1.1539 | 52.22 | 4 |
| 2024-10 | 113 | -0.4769 | 102.90 | 4 | -0.5864 | 43.11 | 2 |
| 2024-11 | 103 | -0.3521 | 81.23 | 6 | -1.0048 | 45.70 | 1 |
| 2024-12 | 98 | -0.6571 | 95.82 | 8 | -1.3462 | 46.79 | 2 |

`not_a_forecast: true`. JSON under gitignored `data/reports/eval_YYYY-MM.json`.

## 2020-10

MD: research MD DOGE-USDT (not OMS DOGE-USD); window 2020-10-01 → 2020-10-31 UTC
Bars: full 2976 · IS 2083 · holdout 893.

| Slice | n_trades | n_would_place | n_kill_days | expectancy after costs (€/trade) | max DD (€) | fee drag (€) | turnover/book |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 93 | 93 | 0 | -0.6717 | 99.38599188 | 25.73233763 | 257.32 |
| in-sample 70% | 60 | 60 | 0 | -1.0202 | 89.03377452 | 18.50909701 | 185.09 |
| holdout 30% | 32 | 32 | 0 | -0.0103 | 33.38524174 | 11.7383739 | 117.38 |

Win rate (secondary):
- full: 16.1%
- IS: 13.3%
- holdout: 21.9%

Stress (full sample):

| Stress | n_trades | expectancy after costs | max DD (€) | fee drag (€) |
|---|---:|---:|---:|---:|
| 2× fees | 93 | -0.6333 | 114.8970435 | 47.64748705 |
| 1-bar entry delay | 92 | -0.7977 | 104.80714988 | 25.2895319 |
| 10% missed entries | 86 | -0.6292 | 94.07083298 | 24.78431636 |

`not_a_forecast: true`.

## 2020-11

MD: research MD DOGE-USDT (not OMS DOGE-USD); window 2020-11-01 → 2020-11-30 UTC
Bars: full 2880 · IS 2015 · holdout 865.

| Slice | n_trades | n_would_place | n_kill_days | expectancy after costs (€/trade) | max DD (€) | fee drag (€) | turnover/book |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 98 | 98 | 5 | -0.5331 | 77.02813743 | 24.78687029 | 247.87 |
| in-sample 70% | 65 | 65 | 3 | -0.6539 | 64.52261946 | 20.1667484 | 201.67 |
| holdout 30% | 32 | 32 | 2 | -0.3508 | 25.83501672 | 6.63789892 | 66.38 |

Win rate (secondary):
- full: 26.5%
- IS: 24.6%
- holdout: 31.2%

Stress (full sample):

| Stress | n_trades | expectancy after costs | max DD (€) | fee drag (€) |
|---|---:|---:|---:|---:|
| 2× fees | 98 | -0.4915 | 94.37386678 | 46.20607549 |
| 1-bar entry delay | 96 | -0.4768 | 70.79675524 | 24.20094782 |
| 10% missed entries | 94 | -0.4935 | 70.53460127 | 24.15008804 |

`not_a_forecast: true`.

## 2020-12

MD: research MD DOGE-USDT (not OMS DOGE-USD); window 2020-12-01 → 2020-12-31 UTC
Bars: full 2976 · IS 2083 · holdout 893.

| Slice | n_trades | n_would_place | n_kill_days | expectancy after costs (€/trade) | max DD (€) | fee drag (€) | turnover/book |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 100 | 100 | 10 | -0.3779 | 90.69118517 | 23.75178077 | 237.52 |
| in-sample 70% | 67 | 67 | 3 | -0.0163 | 49.38789228 | 17.74936355 | 177.49 |
| holdout 30% | 32 | 32 | 6 | -1.2134 | 72.3707838 | 6.49528496 | 64.95 |

Win rate (secondary):
- full: 22.0%
- IS: 25.4%
- holdout: 15.6%

Stress (full sample):

| Stress | n_trades | expectancy after costs | max DD (€) | fee drag (€) |
|---|---:|---:|---:|---:|
| 2× fees | 99 | -0.2916 | 82.03686423 | 44.42411113 |
| 1-bar entry delay | 99 | -0.2566 | 90.84324395 | 24.92127727 |
| 10% missed entries | 96 | -0.3384 | 87.81612736 | 23.32463728 |

`not_a_forecast: true`.

## 2023-10

MD: research MD DOGE-USDT (not OMS DOGE-USD); window 2023-10-01 → 2023-10-31 UTC
Bars: full 2976 · IS 2083 · holdout 893.

| Slice | n_trades | n_would_place | n_kill_days | expectancy after costs (€/trade) | max DD (€) | fee drag (€) | turnover/book |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 102 | 102 | 3 | -0.4839 | 84.63405967 | 32.11185883 | 321.12 |
| in-sample 70% | 67 | 67 | 0 | -0.3186 | 48.02543532 | 23.6164985 | 236.16 |
| holdout 30% | 34 | 34 | 3 | -1.0208 | 65.23291843 | 10.67760911 | 106.78 |

Win rate (secondary):
- full: 26.5%
- IS: 26.9%
- holdout: 26.5%

Stress (full sample):

| Stress | n_trades | expectancy after costs | max DD (€) | fee drag (€) |
|---|---:|---:|---:|---:|
| 2× fees | 101 | -0.4245 | 103.17561809 | 58.65222201 |
| 1-bar entry delay | 102 | -0.5385 | 89.78293261 | 31.41957778 |
| 10% missed entries | 97 | -0.5197 | 84.48430118 | 30.90639167 |

`not_a_forecast: true`.

## 2023-11

MD: research MD DOGE-USDT (not OMS DOGE-USD); window 2023-11-01 → 2023-11-30 UTC
Bars: full 2880 · IS 2015 · holdout 865.

| Slice | n_trades | n_would_place | n_kill_days | expectancy after costs (€/trade) | max DD (€) | fee drag (€) | turnover/book |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 95 | 95 | 6 | -0.3845 | 67.00601991 | 25.65040343 | 256.50 |
| in-sample 70% | 68 | 69 | 5 | -0.4046 | 49.59889607 | 18.56342857 | 185.63 |
| holdout 30% | 28 | 28 | 1 | -0.5472 | 31.14014989 | 9.69482433 | 96.95 |

Win rate (secondary):
- full: 32.6%
- IS: 33.8%
- holdout: 28.6%

Stress (full sample):

| Stress | n_trades | expectancy after costs | max DD (€) | fee drag (€) |
|---|---:|---:|---:|---:|
| 2× fees | 94 | -0.3964 | 86.05598763 | 46.88500701 |
| 1-bar entry delay | 98 | -0.3973 | 66.37251044 | 26.66260959 |
| 10% missed entries | 93 | -0.4095 | 65.98459598 | 24.83713305 |

`not_a_forecast: true`.

## 2023-12

MD: research MD DOGE-USDT (not OMS DOGE-USD); window 2023-12-01 → 2023-12-31 UTC
Bars: full 2976 · IS 2083 · holdout 893.

| Slice | n_trades | n_would_place | n_kill_days | expectancy after costs (€/trade) | max DD (€) | fee drag (€) | turnover/book |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 114 | 114 | 10 | -0.3281 | 99.16730574 | 35.96092759 | 359.61 |
| in-sample 70% | 78 | 79 | 6 | -0.0095 | 55.96206208 | 25.65118378 | 256.51 |
| holdout 30% | 35 | 35 | 4 | -1.1539 | 52.2181586 | 11.83227003 | 118.32 |

Win rate (secondary):
- full: 28.9%
- IS: 34.6%
- holdout: 17.1%

Stress (full sample):

| Stress | n_trades | expectancy after costs | max DD (€) | fee drag (€) |
|---|---:|---:|---:|---:|
| 2× fees | 105 | -0.2724 | 103.8453586 | 61.05822711 |
| 1-bar entry delay | 114 | -0.2946 | 97.27194717 | 36.36824042 |
| 10% missed entries | 109 | -0.3200 | 98.91884255 | 34.29952806 |

`not_a_forecast: true`.

## 2024-10

MD: research MD DOGE-USDT (not OMS DOGE-USD); window 2024-10-01 → 2024-10-31 UTC
Bars: full 2976 · IS 2083 · holdout 893.

| Slice | n_trades | n_would_place | n_kill_days | expectancy after costs (€/trade) | max DD (€) | fee drag (€) | turnover/book |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 113 | 113 | 4 | -0.4769 | 102.89596086 | 26.45653364 | 264.57 |
| in-sample 70% | 77 | 77 | 2 | -0.4835 | 81.92488659 | 20.20175354 | 202.02 |
| holdout 30% | 35 | 35 | 2 | -0.5864 | 43.11065347 | 8.73497945 | 87.35 |

Win rate (secondary):
- full: 36.3%
- IS: 37.7%
- holdout: 34.3%

Stress (full sample):

| Stress | n_trades | expectancy after costs | max DD (€) | fee drag (€) |
|---|---:|---:|---:|---:|
| 2× fees | 111 | -0.4983 | 121.56915213 | 48.55915126 |
| 1-bar entry delay | 111 | -0.3381 | 84.82411439 | 28.16200865 |
| 10% missed entries | 108 | -0.4705 | 102.91311676 | 25.47358005 |

`not_a_forecast: true`.

## 2024-11

MD: research MD DOGE-USDT (not OMS DOGE-USD); window 2024-11-01 → 2024-11-30 UTC
Bars: full 2880 · IS 2015 · holdout 865.

| Slice | n_trades | n_would_place | n_kill_days | expectancy after costs (€/trade) | max DD (€) | fee drag (€) | turnover/book |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 103 | 103 | 6 | -0.3521 | 81.23144839 | 18.22499601 | 182.25 |
| in-sample 70% | 73 | 73 | 5 | -0.1292 | 48.70708787 | 12.53358457 | 125.34 |
| holdout 30% | 30 | 30 | 1 | -1.0048 | 45.70379621 | 6.39360206 | 63.94 |

Win rate (secondary):
- full: 29.1%
- IS: 31.5%
- holdout: 23.3%

Stress (full sample):

| Stress | n_trades | expectancy after costs | max DD (€) | fee drag (€) |
|---|---:|---:|---:|---:|
| 2× fees | 102 | -0.2912 | 86.7858609 | 35.03921563 |
| 1-bar entry delay | 107 | -0.3778 | 73.31406401 | 17.85246923 |
| 10% missed entries | 97 | -0.4819 | 81.63209217 | 16.61214408 |

`not_a_forecast: true`.

## 2024-12

MD: research MD DOGE-USDT (not OMS DOGE-USD); window 2024-12-01 → 2024-12-31 UTC
Bars: full 2976 · IS 2083 · holdout 893.

| Slice | n_trades | n_would_place | n_kill_days | expectancy after costs (€/trade) | max DD (€) | fee drag (€) | turnover/book |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 98 | 98 | 8 | -0.6571 | 95.82117814 | 19.91292647 | 199.13 |
| in-sample 70% | 72 | 72 | 6 | -0.5213 | 73.5233534 | 14.31773195 | 143.18 |
| holdout 30% | 25 | 25 | 2 | -1.3462 | 46.79420943 | 7.47508302 | 74.75 |

Win rate (secondary):
- full: 34.7%
- IS: 40.3%
- holdout: 20.0%

Stress (full sample):

| Stress | n_trades | expectancy after costs | max DD (€) | fee drag (€) |
|---|---:|---:|---:|---:|
| 2× fees | 96 | -0.7117 | 115.55725541 | 35.91524968 |
| 1-bar entry delay | 100 | -0.5253 | 87.77060811 | 22.16533516 |
| 10% missed entries | 96 | -0.6014 | 88.96530527 | 19.71583148 |

`not_a_forecast: true`.

## What this is not

- Not a Phase C recommendation.
- Not a live-trading recommendation.
- Not a claim that the locked breakout has edge.

