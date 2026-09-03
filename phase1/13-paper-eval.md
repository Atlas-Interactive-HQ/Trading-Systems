# 13 — Paper eval (Phase D-lite)

**Stance:** Research. `not_a_forecast: true`. Do not headline PnL. Do not promote to Phase C or live from this score.

Primary score: **expectancy after costs** on the €200 paper book. Split is chronological 70/30 (cut never searched). Stress uses the same engine path (2× fees, 1-bar entry delay, 10% missed entries seed 20260903).

Named-window / similar-regime ≠ future performance. BreakoutV1 params were not retuned.

## similar

MD: DOGE-USD + xperp MD 310404 (similar-regime June)
Bars: full 672 · IS 470 · holdout 202.

| Slice | n_trades | n_would_place | n_kill_days | expectancy after costs (€/trade) | max DD (€) | fee drag (€) | turnover/book |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 25 | 26 | 0 | -0.0943 | 22.06547908 | 9.84987499 | 98.50 |
| in-sample 70% | 17 | 18 | 0 | 0.1326 | 21.22056977 | 6.80979336 | 68.10 |
| holdout 30% | 7 | 8 | 0 | -0.6045 | 10.13963881 | 2.9200993 | 29.20 |

Win rate (secondary):
- full: 36.0%
- IS: 41.2%
- holdout: 28.6%

Stress (full sample):

| Stress | n_trades | expectancy after costs | max DD (€) | fee drag (€) |
|---|---:|---:|---:|---:|
| 2× fees | 24 | -0.2513 | 33.42968396 | 18.32657942 |
| 1-bar entry delay | 24 | -0.5458 | 25.40767332 | 9.04104658 |
| 10% missed entries | 25 | -0.2428 | 25.69354856 | 9.76344475 |

`not_a_forecast: true`.

## 2020-09

MD: research MD DOGE-USDT (not OMS DOGE-USD); window 2020-09-01 → 2021-03-31 UTC
Bars: full 20352 · IS 14246 · holdout 6106.

| Slice | n_trades | n_would_place | n_kill_days | expectancy after costs (€/trade) | max DD (€) | fee drag (€) | turnover/book |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 675 | 675 | 52 | -0.2032 | 192.07140901 | 54.13066365 | 541.31 |
| in-sample 70% | 462 | 463 | 29 | -0.2847 | 182.85422309 | 50.53692136 | 505.37 |
| holdout 30% | 212 | 212 | 23 | -0.3066 | 306.74080576 | 39.2337961 | 392.34 |

Win rate (secondary):
- full: 22.1%
- IS: 22.7%
- holdout: 20.3%

Stress (full sample):

| Stress | n_trades | expectancy after costs | max DD (€) | fee drag (€) |
|---|---:|---:|---:|---:|
| 2× fees | 667 | -0.1685 | 196.10273369 | 83.71266779 |
| 1-bar entry delay | 670 | -0.2040 | 192.151304 | 54.18579815 |
| 10% missed entries | 633 | -0.2320 | 192.87579336 | 45.93910129 |

`not_a_forecast: true`.

## 2023-09

MD: research MD DOGE-USDT (not OMS DOGE-USD); window 2023-09-01 → 2024-03-31 UTC
Bars: full 20448 · IS 14313 · holdout 6135.

| Slice | n_trades | n_would_place | n_kill_days | expectancy after costs (€/trade) | max DD (€) | fee drag (€) | turnover/book |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 734 | 734 | 38 | -0.1647 | 190.61634631 | 68.8717355 | 688.72 |
| in-sample 70% | 505 | 505 | 26 | -0.2264 | 181.26429235 | 64.4362989 | 644.36 |
| holdout 30% | 228 | 228 | 12 | -0.2660 | 112.97147246 | 41.91518732 | 419.15 |

Win rate (secondary):
- full: 28.7%
- IS: 27.7%
- holdout: 31.1%

Stress (full sample):

| Stress | n_trades | expectancy after costs | max DD (€) | fee drag (€) |
|---|---:|---:|---:|---:|
| 2× fees | 710 | -0.1350 | 197.30168722 | 101.20801402 |
| 1-bar entry delay | 729 | -0.1692 | 192.83303494 | 68.87188696 |
| 10% missed entries | 690 | -0.1726 | 189.08060522 | 69.03346324 |

`not_a_forecast: true`.

Q4 calendar months (Oct/Nov/Dec) are a **separate** seasonal-definition set — see [`14-q4-months.md`](./14-q4-months.md). They do not rewrite this holdout table.

Loss drivers + one bull-gate counterfactual: [`15-loss-attribution-bull-gate.md`](./15-loss-attribution-bull-gate.md).

## What this is not

- Not a Phase C recommendation.
- Not a live-trading recommendation.
- Not a claim that the locked breakout has edge.

