# 16 — Candidate v1 (filters) vs frozen baseline — Phase D trial #1

**Stance:** Research. `not_a_forecast: true`. Do not headline PnL. Do not promote to Phase C or live from this score. A PASS is a research result on paper holdout, not a go-live signal; a FAIL keeps the frozen baseline.

## Candidate

- Baseline: `baseline` — frozen BreakoutV1 + `config/default.yaml` (no overlay; `min_atr_frac: 0.001`, no daily cap).
- Candidate: `candidate_v1_filters` — overlay `{"max_would_place_per_utc_day": 1, "min_atr_frac": 0.005}`.
- `max_would_place_per_utc_day: 1` → the first would-place decision of a UTC day is allowed; further same-day signals are blocked with `blocked_reason: daily_cap` (checked after kill / one-position, before sizing; counted at decision time even if the fill is later missed).
- `min_atr_frac: 0.005` → 15m ATR/close below 0.5% is untradeable (baseline 0.1%). Not a fade; ranging stays off.
- Unchanged: `oneh_filter: stub`, lookback 16, ATR period 14, ATR stop 1.5×, time-stop 16 bars, €200 book, 5% daily kill, 1.5% risk/trade, one position, X-Perp ≤2x. No grid search; one candidate, one trial.

## Pass / fail rule (decided up front)

PASS (research only) iff on BOTH 2020-09 and 2023-09: candidate holdout-30% expectancy after costs is strictly greater than baseline (less negative or positive) AND candidate holdout max DD <= baseline holdout max DD × 1.10. A holdout with zero trades has no expectancy and fails closed. Stress is documented, never scored: a less-negative expectancy under 2× fees is never a win — with fewer trades / more kill-days it is kill truncation; with the same trade set it is smaller positions on a poorer equity path (sizing scales with equity). similar (June) and Q4 months are secondary and do not rewrite this rule.

## Verdict: **FAIL**

| window | baseline holdout exp. | candidate holdout exp. | strictly greater? | baseline holdout DD | candidate holdout DD | DD change | DD within +10%? | cand. kill-days | cand. daily_cap blocked | window pass |
|---|---:|---:|:---:|---:|---:|---:|:---:|---:|---:|:---:|
| 2020-09 | -0.3066 | 0.0380 | yes | 306.74 | 150.54 | -50.9% | yes | 0 | 289 | **PASS** |
| 2023-09 | -0.2660 | -0.3400 | no | 112.97 | 29.78 | -73.6% | yes | 0 | 241 | **FAIL** |

At least one primary window fails the rule. **FAIL** — keep the frozen baseline. No candidate_v2 is proposed in this trial.

## Mac run (2026-09-03)

Cached research candles under `data/eval_cache/` (no refetch); similar-regime window from the existing replay summary. Wall-clock ≈ 4 min per 6-month window, ≈ 10 s per Q4 month, per profile.

**Baseline reproducibility (measured, not assumed).** The `baseline` profile reproduces the committed 13/14 JSON exactly — every field — for 2020-09, 2023-09 and all nine Q4 months, and reproduces a fresh run of pristine `origin/main` on the same cache exactly for every sample including `similar`. So the profile plumbing did not move the frozen baseline. The `similar` figures do differ from the 25-trade full-sample row in `13-paper-eval.md`: that row came from the first, uncached run, whose fetched 1h series carried a 48h pre-window pad; the cached path resamples 1h from the window only, so the first ~13 hours have no 1h context (`oneh_missing`) and the full/IS slices lose two early trades (holdout is identical). Pre-existing on main, not introduced here; both profiles use the same cached path so the similar comparison is apples-to-apples, and similar is secondary regardless.

**Mechanical note.** The candidate never trips the 5% daily kill (0 kill-days on every sample): with one would-place per UTC day at 1.5% risk, a single stop-out costs ≈1.5% of equity plus costs, far from the 5% threshold unless a gap blows through the stop. That is a consequence of the cap, not evidence of edge — and it is exactly why the candidate's stress rows cannot show kill truncation while the baseline's can.

## Primary windows (pass rule)

Research MD DOGE-USDT (not OMS DOGE-USD). Holdout 30% is the scored slice.

### 2020-09

MD: research MD DOGE-USDT (not OMS DOGE-USD); window 2020-09-01 → 2021-03-31 UTC
Bars: full 20352 · IS 14246 · holdout 6106.

| metric | baseline holdout | candidate holdout | Δ holdout | baseline IS | candidate IS | baseline full | candidate full |
|---|---:|---:|---:|---:|---:|---:|---:|
| n_trades | 212 | 62 | -150 | 462 | 102 | 675 | 163 |
| n_would_place | 212 | 62 | -150 | 463 | 102 | 675 | 163 |
| n_kill_days | 23 | 0 | -23 | 29 | 0 | 52 | 0 |
| n_blocked_daily_cap | 0 | 289 | +289 | 0 | 384 | 0 | 680 |
| expectancy after costs (€/trade) | -0.3066 | 0.0380 | +0.3446 | -0.2847 | -0.9584 | -0.2032 | -0.5844 |
| max DD (€) | 306.74 | 150.54 | -156.20 | 182.85 | 130.57 | 192.07 | 133.58 |
| fee drag (€) | 39.23 | 15.52 | -23.71 | 50.54 | 19.27 | 54.13 | 25.75 |
| win rate (secondary) | 20.3% | 17.7% | -2.5% | 22.7% | 16.7% | 22.1% | 17.2% |

Stress (full sample, same engine path):

| profile | stress | n_trades full→stress | kill-days full→stress | expectancy full→stress (€/trade) | max DD stress (€) | fee drag full→stress (€) | fee/trade ratio | confound |
|---|---|---:|---:|---:|---:|---:|---:|---|
| baseline | 2× fees | 675→667 | 52→60 | -0.2032→-0.1685 | 196.10 | 54.13→83.71 | 1.56 | **kill-truncation: less-negative expectancy is NOT a win** |
| baseline | 1-bar entry delay | 675→670 | 52→45 | -0.2032→-0.2040 | 192.15 | 54.13→54.19 | — | trade set differs by construction |
| baseline | 10% missed entries | 675→633 | 52→45 | -0.2032→-0.2320 | 192.88 | 54.13→45.94 | — | trade set differs by construction |
| candidate | 2× fees | 163→163 | 0→0 | -0.5844→-0.5377 | 145.78 | 25.75→47.47 | 1.84 | **equity-path sizing: less-negative expectancy is NOT a win** |
| candidate | 1-bar entry delay | 163→163 | 0→1 | -0.5844→-0.4819 | 115.23 | 25.75→26.60 | — | trade set differs by construction |
| candidate | 10% missed entries | 163→149 | 0→0 | -0.5844→-0.5747 | 123.44 | 25.75→25.25 | — | trade set differs by construction |

`not_a_forecast: true`.

### 2023-09

MD: research MD DOGE-USDT (not OMS DOGE-USD); window 2023-09-01 → 2024-03-31 UTC
Bars: full 20448 · IS 14313 · holdout 6135.

| metric | baseline holdout | candidate holdout | Δ holdout | baseline IS | candidate IS | baseline full | candidate full |
|---|---:|---:|---:|---:|---:|---:|---:|
| n_trades | 228 | 43 | -185 | 505 | 85 | 734 | 128 |
| n_would_place | 228 | 43 | -185 | 505 | 85 | 734 | 128 |
| n_kill_days | 12 | 0 | -12 | 26 | 0 | 38 | 0 |
| n_blocked_daily_cap | 0 | 241 | +241 | 0 | 249 | 0 | 490 |
| expectancy after costs (€/trade) | -0.2660 | -0.3400 | -0.0740 | -0.2264 | -0.7103 | -0.1647 | -0.5407 |
| max DD (€) | 112.97 | 29.78 | -83.19 | 181.26 | 99.17 | 190.62 | 99.17 |
| fee drag (€) | 41.92 | 9.16 | -32.75 | 64.44 | 18.84 | 68.87 | 24.38 |
| win rate (secondary) | 31.1% | 32.6% | +1.4% | 27.7% | 24.7% | 28.7% | 27.3% |

Stress (full sample, same engine path):

| profile | stress | n_trades full→stress | kill-days full→stress | expectancy full→stress (€/trade) | max DD stress (€) | fee drag full→stress (€) | fee/trade ratio | confound |
|---|---|---:|---:|---:|---:|---:|---:|---|
| baseline | 2× fees | 734→710 | 38→51 | -0.1647→-0.1350 | 197.30 | 68.87→101.21 | 1.52 | **kill-truncation: less-negative expectancy is NOT a win** |
| baseline | 1-bar entry delay | 734→729 | 38→31 | -0.1647→-0.1692 | 192.83 | 68.87→68.87 | — | trade set differs by construction |
| baseline | 10% missed entries | 734→690 | 38→31 | -0.1647→-0.1726 | 189.08 | 68.87→69.03 | — | trade set differs by construction |
| candidate | 2× fees | 128→128 | 0→0 | -0.5407→-0.5206 | 112.30 | 24.38→44.95 | 1.84 | **equity-path sizing: less-negative expectancy is NOT a win** |
| candidate | 1-bar entry delay | 128→128 | 0→2 | -0.5407→-0.7135 | 114.70 | 24.38→23.05 | — | trade set differs by construction |
| candidate | 10% missed entries | 128→115 | 0→0 | -0.5407→-0.5021 | 88.39 | 24.38→23.29 | — | trade set differs by construction |

`not_a_forecast: true`.

## Secondary: similar-regime June (small n)

Similar-regime window, DOGE-USD spot + X-Perp MD 310404. Small sample; informational only.

### similar

MD: DOGE-USD + xperp MD 310404 (similar-regime June)
Bars: full 672 · IS 470 · holdout 202.

| metric | baseline holdout | candidate holdout | Δ holdout | baseline IS | candidate IS | baseline full | candidate full |
|---|---:|---:|---:|---:|---:|---:|---:|
| n_trades | 7 | 2 | -5 | 15 | 1 | 23 | 3 |
| n_would_place | 8 | 2 | -6 | 16 | 1 | 24 | 3 |
| n_kill_days | 0 | 0 | +0 | 0 | 0 | 0 | 0 |
| n_blocked_daily_cap | 0 | 0 | +0 | 0 | 0 | 0 | 0 |
| expectancy after costs (€/trade) | -0.6045 | -2.1716 | -1.5671 | 0.3436 | -3.6768 | 0.0198 | -2.6446 |
| max DD (€) | 10.14 | 5.10 | -5.04 | 21.46 | 3.97 | 21.46 | 8.97 |
| fee drag (€) | 2.92 | 0.76 | -2.16 | 6.11 | 0.29 | 9.21 | 1.03 |
| win rate (secondary) | 28.6% | 0.0% | -28.6% | 46.7% | 0.0% | 39.1% | 0.0% |

Stress (full sample, same engine path):

| profile | stress | n_trades full→stress | kill-days full→stress | expectancy full→stress (€/trade) | max DD stress (€) | fee drag full→stress (€) | fee/trade ratio | confound |
|---|---|---:|---:|---:|---:|---:|---:|---|
| baseline | 2× fees | 23→22 | 0→1 | 0.0198→-0.1499 | 32.28 | 9.21→17.10 | 1.94 | kill-truncation (trade set differs) |
| baseline | 1-bar entry delay | 23→22 | 0→1 | 0.0198→-0.4693 | 24.43 | 9.21→8.41 | — | trade set differs by construction |
| baseline | 10% missed entries | 23→23 | 0→0 | 0.0198→-0.0988 | 23.68 | 9.21→9.15 | — |  |
| candidate | 2× fees | 3→3 | 0→0 | -2.6446→-2.6410 | 9.99 | 1.03→2.06 | 2.00 | **equity-path sizing: less-negative expectancy is NOT a win** |
| candidate | 1-bar entry delay | 3→3 | 0→0 | -2.6446→-2.3875 | 8.19 | 1.03→1.03 | — |  |
| candidate | 10% missed entries | 3→3 | 0→0 | -2.6446→-2.6446 | 8.97 | 1.03→1.03 | — |  |

`not_a_forecast: true`.

## Seasonal check: Q4 months (secondary — does not rewrite the pass rule)

Oct/Nov/Dec 2020/2023/2024 on DOGE-USDT. Holdout 30% per month. Informational: same season as the coming months, not a similar-regime match.

| month | baseline holdout exp. | candidate holdout exp. | Δ | baseline holdout DD | candidate holdout DD | baseline kill-days (holdout) | candidate kill-days (holdout) | candidate daily_cap blocked (full) | candidate n_trades (full) vs baseline |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2020-10 | -0.0103 | -1.6360 | -1.6257 | 33.39 | 14.56 | 0 | 0 | 6 | 9 vs 93 |
| 2020-11 | -0.3508 | -1.4377 | -1.0869 | 25.84 | 16.96 | 2 | 0 | 69 | 21 vs 98 |
| 2020-12 | -1.2134 | -2.0987 | -0.8852 | 72.37 | 27.03 | 6 | 0 | 126 | 27 vs 100 |
| 2023-10 | -1.0208 | -1.0560 | -0.0352 | 65.23 | 16.41 | 3 | 0 | 21 | 9 vs 102 |
| 2023-11 | -0.5472 | -1.3141 | -0.7669 | 31.14 | 20.10 | 1 | 0 | 84 | 26 vs 95 |
| 2023-12 | -1.1539 | -2.2827 | -1.1288 | 52.22 | 17.10 | 4 | 0 | 90 | 26 vs 114 |
| 2024-10 | -0.5864 | 0.3568 | +0.9432 | 43.11 | 11.45 | 2 | 0 | 112 | 30 vs 113 |
| 2024-11 | -1.0048 | -0.6472 | +0.3576 | 45.70 | 18.56 | 1 | 0 | 160 | 30 vs 103 |
| 2024-12 | -1.3462 | -2.2920 | -0.9458 | 46.79 | 23.44 | 2 | 0 | 151 | 31 vs 98 |

Candidate holdout expectancy is less negative than baseline in 2 of 9 Q4 months. Secondary information only; it does not change the verdict above.

## How to read the 2× fees stress (kill truncation and equity-path sizing)

2× fees does not change signals, so any difference in n_trades or n_kill_days between the full run and the 2× run comes from the equity path: higher fees drain the book faster, the 5% daily kill trips earlier, positions are flattened and the rest of that UTC day is blocked. Fewer, earlier-killed trades can make expectancy per trade read LESS negative under 2× fees while the book is simply dying sooner. A second mechanism needs no truncation: sizing scales with equity (risk budget = 1.5% of equity), so a poorer equity path under 2× fees means smaller positions and smaller € losses per trade — the same trade set reads less negative in €/trade. Read 2× fees on a comparable basis: fee drag per trade should be ≈2× the base (fee_per_trade_ratio), and total fee drag € should be worse or equal unless truncation removed trades. Fees cannot improve a strategy: never read a less-negative 2× expectancy as a win.

Flagged rows in this run:

- `2020-09` / baseline: 2× fees reads -0.1685 vs -0.2032 base (less negative) with n_trades 675→667 and kill-days 52→60. Fee rate doubled (fee/trade ratio 1.56; below 2.0 because positions shrink on the poorer equity path); the 'improvement' is the kill flattening/truncating the trade set. **Not a win.**
- `2020-09` / candidate: 2× fees reads -0.5377 vs -0.5844 base (less negative) with the SAME trade set (n_trades 163, kill-days 0) and total fee drag 25.75→47.47. Sizing scales with equity, so the poorer equity path under 2× fees shrinks positions and € losses per trade. **Not a win.**
- `2023-09` / baseline: 2× fees reads -0.1350 vs -0.1647 base (less negative) with n_trades 734→710 and kill-days 38→51. Fee rate doubled (fee/trade ratio 1.52; below 2.0 because positions shrink on the poorer equity path); the 'improvement' is the kill flattening/truncating the trade set. **Not a win.**
- `2023-09` / candidate: 2× fees reads -0.5206 vs -0.5407 base (less negative) with the SAME trade set (n_trades 128, kill-days 0) and total fee drag 24.38→44.95. Sizing scales with equity, so the poorer equity path under 2× fees shrinks positions and € losses per trade. **Not a win.**
- `similar` / baseline: 2× fees trade set differs (n_trades 23→22, kill-days 0→1); expectancy 0.0198→-0.1499 is not on a comparable basis.
- `similar` / candidate: 2× fees reads -2.6410 vs -2.6446 base (less negative) with the SAME trade set (n_trades 3, kill-days 0) and total fee drag 1.03→2.06. Sizing scales with equity, so the poorer equity path under 2× fees shrinks positions and € losses per trade. **Not a win.**
- `2020-10` / baseline: 2× fees reads -0.6333 vs -0.6717 base (less negative) with n_trades 93→93 and kill-days 0→1. Fee rate doubled (fee/trade ratio 1.85; below 2.0 because positions shrink on the poorer equity path); the 'improvement' is the kill flattening/truncating the trade set. **Not a win.**
- `2020-10` / candidate: 2× fees reads -1.5812 vs -1.5897 base (less negative) with the SAME trade set (n_trades 9, kill-days 0) and total fee drag 2.71→5.39. Sizing scales with equity, so the poorer equity path under 2× fees shrinks positions and € losses per trade. **Not a win.**
- `2020-11` / baseline: 2× fees reads -0.4915 vs -0.5331 base (less negative) with n_trades 98→98 and kill-days 5→6. Fee rate doubled (fee/trade ratio 1.86; below 2.0 because positions shrink on the poorer equity path); the 'improvement' is the kill flattening/truncating the trade set. **Not a win.**
- `2020-11` / candidate: 2× fees reads -1.0870 vs -1.1049 base (less negative) with the SAME trade set (n_trades 21, kill-days 0) and total fee drag 5.41→10.68. Sizing scales with equity, so the poorer equity path under 2× fees shrinks positions and € losses per trade. **Not a win.**
- `2020-12` / baseline: 2× fees reads -0.2916 vs -0.3779 base (less negative) with n_trades 100→99 and kill-days 10→11. Fee rate doubled (fee/trade ratio 1.89; below 2.0 because positions shrink on the poorer equity path); the 'improvement' is the kill flattening/truncating the trade set. **Not a win.**
- `2020-12` / candidate: 2× fees reads -1.9141 vs -1.9429 base (less negative) with the SAME trade set (n_trades 27, kill-days 0) and total fee drag 5.56→10.95. Sizing scales with equity, so the poorer equity path under 2× fees shrinks positions and € losses per trade. **Not a win.**
- `2023-10` / baseline: 2× fees reads -0.4245 vs -0.4839 base (less negative) with n_trades 102→101 and kill-days 3→5. Fee rate doubled (fee/trade ratio 1.84; below 2.0 because positions shrink on the poorer equity path); the 'improvement' is the kill flattening/truncating the trade set. **Not a win.**
- `2023-10` / candidate: 2× fees reads -1.3075 vs -1.3128 base (less negative) with the SAME trade set (n_trades 9, kill-days 0) and total fee drag 2.54→5.04. Sizing scales with equity, so the poorer equity path under 2× fees shrinks positions and € losses per trade. **Not a win.**
- `2023-11` / baseline: 2× fees trade set differs (n_trades 95→94, kill-days 6→8); expectancy -0.3845→-0.3964 is not on a comparable basis.
- `2023-11` / candidate: 2× fees reads -1.4144 vs -1.4402 base (less negative) with the SAME trade set (n_trades 26, kill-days 0) and total fee drag 7.27→14.26. Sizing scales with equity, so the poorer equity path under 2× fees shrinks positions and € losses per trade. **Not a win.**
- `2023-12` / baseline: 2× fees reads -0.2724 vs -0.3281 base (less negative) with n_trades 114→105 and kill-days 10→12. Fee rate doubled (fee/trade ratio 1.84; below 2.0 because positions shrink on the poorer equity path); the 'improvement' is the kill flattening/truncating the trade set. **Not a win.**
- `2023-12` / candidate: 2× fees reads -1.4067 vs -1.4419 base (less negative) with the SAME trade set (n_trades 26, kill-days 0) and total fee drag 7.43→14.58. Sizing scales with equity, so the poorer equity path under 2× fees shrinks positions and € losses per trade. **Not a win.**
- `2024-10` / baseline: 2× fees trade set differs (n_trades 113→111, kill-days 4→9); expectancy -0.4769→-0.4983 is not on a comparable basis.
- `2024-11` / baseline: 2× fees reads -0.2912 vs -0.3521 base (less negative) with n_trades 103→102 and kill-days 6→8. Fee rate doubled (fee/trade ratio 1.94; below 2.0 because positions shrink on the poorer equity path); the 'improvement' is the kill flattening/truncating the trade set. **Not a win.**
- `2024-11` / candidate: 2× fees reads 0.1513 vs 0.1465 base (less negative) with the SAME trade set (n_trades 30, kill-days 0) and total fee drag 6.11→12.04. Sizing scales with equity, so the poorer equity path under 2× fees shrinks positions and € losses per trade. **Not a win.**
- `2024-12` / baseline: 2× fees trade set differs (n_trades 98→96, kill-days 8→10); expectancy -0.6571→-0.7117 is not on a comparable basis.
- `2024-12` / candidate: 2× fees reads -1.6070 vs -1.6343 base (less negative) with the SAME trade set (n_trades 31, kill-days 0) and total fee drag 7.14→14.00. Sizing scales with equity, so the poorer equity path under 2× fees shrinks positions and € losses per trade. **Not a win.**

## Reproduce

```bash
source .venv/bin/activate
python scripts/run_paper_eval.py --samples similar,2020-09,2023-09 --profile baseline --write-md ''
python scripts/run_paper_eval.py --samples similar,2020-09,2023-09 --profile candidate_v1_filters
python scripts/run_paper_eval.py --samples q4 --profile baseline --write-md ''   # secondary
python scripts/run_paper_eval.py --samples q4 --profile candidate_v1_filters                 # secondary
python scripts/compare_eval_profiles.py --candidate candidate_v1_filters --write-md phase1/16-candidate-v1.md
```

JSON under gitignored `data/reports/` (`profiles/<profile>/eval_*.json`, `compare_*.json`). Cached research candles under `data/eval_cache/` are reused; nothing is refetched unless missing.

## What this is not

- Not a Phase C recommendation.
- Not a live-trading recommendation.
- Not a claim that the locked breakout, with or without these filters, has edge.
- Not a candidate_v2 proposal.

