# 17 — Candidate v2 (stops) vs frozen baseline — Phase D trial #2

**Stance:** Research. `not_a_forecast: true`. Do not headline PnL. Do not promote to Phase C or live from this score. A PASS is a research result on paper holdout, not a go-live signal; a FAIL keeps the frozen baseline.

## Candidate

- Baseline: `baseline` — frozen BreakoutV1 + `config/default.yaml` (no overlay; `atr_stop_mult: 1.5`).
- Candidate: `candidate_v2_stops` — overlay `{"atr_stop_mult": 3.0, "atr_stop_mult_baseline": 1.5, "atr_stop_mult_factor": 2.0}`.
- `atr_stop_mult` → 2.0× the baseline multiplier read from `config/default.yaml` at apply time (with the config as committed: baseline **1.5** → candidate **3.0**; the trial brief fixes the rule as 2.5 if the baseline were already 2.0). The resolved values are stamped in the overlay above. Stop distance = ATR × multiplier, so the initial stop sits twice as far from entry; stop-outs need a 2× larger adverse move.
- Sizing rule is unchanged: notional = min(risk budget ÷ stop fraction, 2× equity leverage cap). Where the risk budget binds, a 2× stop halves the notional at the same € at risk; where the 2× leverage cap binds (small ATR/close), the notional stays at the cap and the € at risk per trade DOUBLES. Which regime dominates is measured in the run note, not assumed.
- Unchanged: lookback 16, ATR period 14, `min_atr_frac: 0.001`, `oneh_filter: stub`, time-stop 16 bars, no daily cap, €200 book, 5% daily kill, 1.5% risk/trade, one position, X-Perp ≤2x. candidate_v1's daily_cap / min_atr are deliberately NOT included (isolate the stop change). No grid search; one candidate, one trial.
- Rationale (phase1/15 loss attribution): stop-outs are the #1 loss driver, fees #2, time-stops a positive offset — widen the stop once and measure on holdout.
- Resolved against this config: `atr_stop_mult` baseline **1.50** → candidate **3.00** (factor 2.0).

## Pass / fail rule (decided up front)

PASS (research only) iff on BOTH 2020-09 and 2023-09: candidate holdout-30% expectancy after costs is strictly greater than baseline (less negative or positive) AND candidate holdout max DD <= baseline holdout max DD × 1.10. A holdout with zero trades has no expectancy and fails closed. Stress is documented, never scored: a less-negative expectancy under 2× fees is never a win — with fewer trades / more kill-days it is kill truncation; with the same trade set it is smaller positions on a poorer equity path (sizing scales with equity). similar (June) and Q4 months are secondary and do not rewrite this rule.

## Verdict: **PASS**

| window | baseline holdout exp. | candidate holdout exp. | strictly greater? | baseline holdout DD | candidate holdout DD | DD change | DD within +10%? | cand. kill-days | cand. daily_cap blocked | window pass |
|---|---:|---:|:---:|---:|---:|---:|:---:|---:|---:|:---:|
| 2020-09 | -0.3066 | -0.0967 | yes | 306.74 | 136.95 | -55.4% | yes | 1 | 0 | **PASS** |
| 2023-09 | -0.2660 | -0.1745 | yes | 112.97 | 76.58 | -32.2% | yes | 4 | 0 | **PASS** |

Both primary windows pass on holdout expectancy and holdout max DD. This is a research PASS on paper; it says nothing about live and does not by itself unlock Phase C. Promoting the candidate into the frozen baseline (`config/default.yaml`) is a separate decision for Atlas/Kaje, not part of this trial.

**Still negative.** Candidate holdout expectancy after costs is below zero on `2020-09`, `2023-09`. PASS here means *loses less than the frozen baseline on holdout*, not *positive expectancy* and not edge.

<!-- run-note:start -->
## Mac run (2026-09-03)

Cached research candles under `data/eval_cache/` (no refetch); similar-regime window from the existing replay summary. Wall-clock ≈ 4.6 min per 6-month window, ≈ 1 min for the nine Q4 months, ≈ 1 s for `similar`, per profile, eight jobs in parallel.

**Baseline reproducibility (measured, not assumed).** The `baseline` profile re-run here is identical — every field, all twelve samples including `similar` — to the trial #1 baseline run, which itself matched a fresh run of pristine `origin/main` on the same cache. The new profile code did not move the frozen baseline.

**What PASS means here.** Both primary holdouts are still negative (−0.0967 and −0.1745 €/trade): the candidate loses less than the frozen baseline, it does not make money. The improvement is not uniform across slices: on 2020-09 the in-sample and full slices are slightly *worse* than baseline (IS −0.2967 vs −0.2847; full −0.2072 vs −0.2032) while the holdout is much better; on 2023-09 all three slices improve. Trade counts barely change (holdout 212→199 and 228→212) — this is a stop change, not a filter — while the win rate rises (20.3%→33.7% and 31.1%→40.1%) because fewer trades are stopped out before the time-stop / opposite-breakout exit.

**Sizing regime, measured (`scripts/measure_sizing_regime.py`, full samples, would-place decisions).** Notional = min(risk budget ÷ stop fraction, 2× equity). The 2× leverage cap bound **39%** (2020-09) and **61%** (2023-09) of baseline decisions, but only **8%** and **24%** of the candidate's. So the candidate did **not** trade half the size: mean notional went 80.2 → 65.6 € (2020-09) and 93.8 → 98.1 € (2023-09), while the mean € at risk per trade roughly **doubled** (0.62 → 0.94 € and 0.47 → 0.92 €) — cap-bound baseline trades risked less than the 1.5% budget, and the wider stop lets most candidate trades reach it. Fee drag follows notional and trade count: down on 2020-09 (54.1 → 41.9 € full), flat on 2023-09 (68.9 → 67.0 €). Kill-days collapse (52 → 7 and 38 → 9 full-sample) because fewer trades are stopped out per UTC day. Max DD is lower on both holdouts (−55%, −32%); this document does not decompose why. None of this is edge; it is how the fixed sizing rule reacts to a wider stop. Under 2× fees the candidate's less-negative rows are kill truncation (kill-days 7 → 17 and 9 → 14) — flagged below, not a win.

**Decision boundary.** PASS is a research result on paper holdout. `config/default.yaml` is unchanged in this PR; whether `atr_stop_mult: 3.0` becomes the new frozen baseline is Atlas/Kaje's call, and Phase C / live are separate gates untouched by this trial. The mean € at risk per trade roughly doubling is a fact for that decision, not a footnote.
<!-- run-note:end -->

## Primary windows (pass rule)

Research MD DOGE-USDT (not OMS DOGE-USD). Holdout 30% is the scored slice.

### 2020-09

MD: research MD DOGE-USDT (not OMS DOGE-USD); window 2020-09-01 → 2021-03-31 UTC
Bars: full 20352 · IS 14246 · holdout 6106.

| metric | baseline holdout | candidate holdout | Δ holdout | baseline IS | candidate IS | baseline full | candidate full |
|---|---:|---:|---:|---:|---:|---:|---:|
| n_trades | 212 | 199 | -13 | 462 | 439 | 675 | 639 |
| n_would_place | 212 | 199 | -13 | 463 | 440 | 675 | 639 |
| n_kill_days | 23 | 1 | -22 | 29 | 6 | 52 | 7 |
| n_blocked_daily_cap | 0 | 0 | +0 | 0 | 0 | 0 | 0 |
| expectancy after costs (€/trade) | -0.3066 | -0.0967 | +0.2098 | -0.2847 | -0.2967 | -0.2032 | -0.2072 |
| max DD (€) | 306.74 | 136.95 | -169.79 | 182.85 | 170.66 | 192.07 | 176.50 |
| fee drag (€) | 39.23 | 23.71 | -15.52 | 50.54 | 38.01 | 54.13 | 41.91 |
| win rate (secondary) | 20.3% | 33.7% | +13.4% | 22.7% | 30.8% | 22.1% | 31.8% |

Stress (full sample, same engine path):

| profile | stress | n_trades full→stress | kill-days full→stress | expectancy full→stress (€/trade) | max DD stress (€) | fee drag full→stress (€) | fee/trade ratio | confound |
|---|---|---:|---:|---:|---:|---:|---:|---|
| baseline | 2× fees | 675→667 | 52→60 | -0.2032→-0.1685 | 196.10 | 54.13→83.71 | 1.56 | **kill-truncation: less-negative expectancy is NOT a win** |
| baseline | 1-bar entry delay | 675→670 | 52→45 | -0.2032→-0.2040 | 192.15 | 54.13→54.19 | — | trade set differs by construction |
| baseline | 10% missed entries | 675→633 | 52→45 | -0.2032→-0.2320 | 192.88 | 54.13→45.94 | — | trade set differs by construction |
| candidate | 2× fees | 639→635 | 7→17 | -0.2072→-0.1819 | 186.55 | 41.91→69.93 | 1.68 | **kill-truncation: less-negative expectancy is NOT a win** |
| candidate | 1-bar entry delay | 639→622 | 7→9 | -0.2072→-0.2120 | 176.53 | 41.91→42.14 | — | trade set differs by construction |
| candidate | 10% missed entries | 639→594 | 7→6 | -0.2072→-0.2190 | 172.95 | 41.91→40.73 | — | trade set differs by construction |

`not_a_forecast: true`.

### 2023-09

MD: research MD DOGE-USDT (not OMS DOGE-USD); window 2023-09-01 → 2024-03-31 UTC
Bars: full 20448 · IS 14313 · holdout 6135.

| metric | baseline holdout | candidate holdout | Δ holdout | baseline IS | candidate IS | baseline full | candidate full |
|---|---:|---:|---:|---:|---:|---:|---:|
| n_trades | 228 | 212 | -16 | 505 | 470 | 734 | 683 |
| n_would_place | 228 | 212 | -16 | 505 | 470 | 734 | 683 |
| n_kill_days | 12 | 4 | -8 | 26 | 5 | 38 | 9 |
| n_blocked_daily_cap | 0 | 0 | +0 | 0 | 0 | 0 | 0 |
| expectancy after costs (€/trade) | -0.2660 | -0.1745 | +0.0915 | -0.2264 | -0.2114 | -0.1647 | -0.1571 |
| max DD (€) | 112.97 | 76.58 | -36.39 | 181.26 | 166.52 | 190.62 | 179.46 |
| fee drag (€) | 41.92 | 32.06 | -9.86 | 64.44 | 60.61 | 68.87 | 66.98 |
| win rate (secondary) | 31.1% | 40.1% | +9.0% | 27.7% | 37.0% | 28.7% | 37.9% |

Stress (full sample, same engine path):

| profile | stress | n_trades full→stress | kill-days full→stress | expectancy full→stress (€/trade) | max DD stress (€) | fee drag full→stress (€) | fee/trade ratio | confound |
|---|---|---:|---:|---:|---:|---:|---:|---|
| baseline | 2× fees | 734→710 | 38→51 | -0.1647→-0.1350 | 197.30 | 68.87→101.21 | 1.52 | **kill-truncation: less-negative expectancy is NOT a win** |
| baseline | 1-bar entry delay | 734→729 | 38→31 | -0.1647→-0.1692 | 192.83 | 68.87→68.87 | — | trade set differs by construction |
| baseline | 10% missed entries | 734→690 | 38→31 | -0.1647→-0.1726 | 189.08 | 68.87→69.03 | — | trade set differs by construction |
| candidate | 2× fees | 683→682 | 9→14 | -0.1571→-0.1289 | 193.73 | 66.98→101.37 | 1.52 | **kill-truncation: less-negative expectancy is NOT a win** |
| candidate | 1-bar entry delay | 683→663 | 9→9 | -0.1571→-0.1531 | 178.15 | 66.98→70.62 | — | trade set differs by construction |
| candidate | 10% missed entries | 683→642 | 9→11 | -0.1571→-0.1713 | 178.94 | 66.98→63.75 | — | trade set differs by construction |

`not_a_forecast: true`.

## Secondary: similar-regime June (small n)

Similar-regime window, DOGE-USD spot + X-Perp MD 310404. Small sample; informational only.

### similar

MD: DOGE-USD + xperp MD 310404 (similar-regime June)
Bars: full 672 · IS 470 · holdout 202.

| metric | baseline holdout | candidate holdout | Δ holdout | baseline IS | candidate IS | baseline full | candidate full |
|---|---:|---:|---:|---:|---:|---:|---:|
| n_trades | 7 | 6 | -1 | 15 | 14 | 23 | 21 |
| n_would_place | 8 | 7 | -1 | 16 | 15 | 24 | 22 |
| n_kill_days | 0 | 0 | +0 | 0 | 0 | 0 | 0 |
| n_blocked_daily_cap | 0 | 0 | +0 | 0 | 0 | 0 | 0 |
| expectancy after costs (€/trade) | -0.6045 | 1.0555 | +1.6600 | 0.3436 | 0.1124 | 0.0198 | 0.3569 |
| max DD (€) | 10.14 | 9.96 | -0.18 | 21.46 | 20.17 | 21.46 | 21.64 |
| fee drag (€) | 2.92 | 2.09 | -0.83 | 6.11 | 5.46 | 9.21 | 7.68 |
| win rate (secondary) | 28.6% | 50.0% | +21.4% | 46.7% | 50.0% | 39.1% | 47.6% |

Stress (full sample, same engine path):

| profile | stress | n_trades full→stress | kill-days full→stress | expectancy full→stress (€/trade) | max DD stress (€) | fee drag full→stress (€) | fee/trade ratio | confound |
|---|---|---:|---:|---:|---:|---:|---:|---|
| baseline | 2× fees | 23→22 | 0→1 | 0.0198→-0.1499 | 32.28 | 9.21→17.10 | 1.94 | kill-truncation (trade set differs) |
| baseline | 1-bar entry delay | 23→22 | 0→1 | 0.0198→-0.4693 | 24.43 | 9.21→8.41 | — | trade set differs by construction |
| baseline | 10% missed entries | 23→23 | 0→0 | 0.0198→-0.0988 | 23.68 | 9.21→9.15 | — |  |
| candidate | 2× fees | 21→21 | 0→0 | 0.3569→0.3424 | 28.51 | 7.68→15.09 | 1.96 |  |
| candidate | 1-bar entry delay | 21→21 | 0→0 | 0.3569→0.0403 | 21.41 | 7.68→7.34 | — |  |
| candidate | 10% missed entries | 21→20 | 0→0 | 0.3569→0.5012 | 20.17 | 7.68→7.32 | — | trade set differs by construction |

`not_a_forecast: true`.

## Seasonal check: Q4 months (secondary — does not rewrite the pass rule)

Oct/Nov/Dec 2020/2023/2024 on DOGE-USDT. Holdout 30% per month. Informational: same season as the coming months, not a similar-regime match.

| month | baseline holdout exp. | candidate holdout exp. | Δ | baseline holdout DD | candidate holdout DD | baseline kill-days (holdout) | candidate kill-days (holdout) | candidate daily_cap blocked (full) | candidate n_trades (full) vs baseline |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2020-10 | -0.0103 | -0.4748 | -0.4645 | 33.39 | 31.55 | 0 | 1 | 0 | 88 vs 93 |
| 2020-11 | -0.3508 | -0.1678 | +0.1830 | 25.84 | 13.73 | 2 | 0 | 0 | 87 vs 98 |
| 2020-12 | -1.2134 | -0.2979 | +0.9156 | 72.37 | 37.80 | 6 | 0 | 0 | 95 vs 100 |
| 2023-10 | -1.0208 | -0.5424 | +0.4784 | 65.23 | 41.56 | 3 | 1 | 0 | 93 vs 102 |
| 2023-11 | -0.5472 | -0.1442 | +0.4030 | 31.14 | 18.41 | 1 | 0 | 0 | 96 vs 95 |
| 2023-12 | -1.1539 | -0.5562 | +0.5977 | 52.22 | 24.85 | 4 | 0 | 0 | 105 vs 114 |
| 2024-10 | -0.5864 | -0.5202 | +0.0662 | 43.11 | 36.59 | 2 | 0 | 0 | 104 vs 113 |
| 2024-11 | -1.0048 | -0.6409 | +0.3638 | 45.70 | 23.85 | 1 | 0 | 0 | 97 vs 103 |
| 2024-12 | -1.3462 | -1.0718 | +0.2744 | 46.79 | 31.04 | 2 | 0 | 0 | 99 vs 98 |

Candidate holdout expectancy is less negative than baseline in 8 of 9 Q4 months. Secondary information only; it does not change the verdict above.

## How to read the 2× fees stress (kill truncation and equity-path sizing)

2× fees does not change signals, so any difference in n_trades or n_kill_days between the full run and the 2× run comes from the equity path: higher fees drain the book faster, the 5% daily kill trips earlier, positions are flattened and the rest of that UTC day is blocked. Fewer, earlier-killed trades can make expectancy per trade read LESS negative under 2× fees while the book is simply dying sooner. A second mechanism needs no truncation: sizing scales with equity (risk budget = 1.5% of equity), so a poorer equity path under 2× fees means smaller positions and smaller € losses per trade — the same trade set reads less negative in €/trade. Read 2× fees on a comparable basis: fee drag per trade should be ≈2× the base (fee_per_trade_ratio), and total fee drag € should be worse or equal unless truncation removed trades. Fees cannot improve a strategy: never read a less-negative 2× expectancy as a win.

Flagged rows in this run:

- `2020-09` / baseline: 2× fees reads -0.1685 vs -0.2032 base (less negative) with n_trades 675→667 and kill-days 52→60. Fee rate doubled (fee/trade ratio 1.56; below 2.0 because positions shrink on the poorer equity path); the 'improvement' is the kill flattening/truncating the trade set. **Not a win.**
- `2020-09` / candidate: 2× fees reads -0.1819 vs -0.2072 base (less negative) with n_trades 639→635 and kill-days 7→17. Fee rate doubled (fee/trade ratio 1.68; below 2.0 because positions shrink on the poorer equity path); the 'improvement' is the kill flattening/truncating the trade set. **Not a win.**
- `2023-09` / baseline: 2× fees reads -0.1350 vs -0.1647 base (less negative) with n_trades 734→710 and kill-days 38→51. Fee rate doubled (fee/trade ratio 1.52; below 2.0 because positions shrink on the poorer equity path); the 'improvement' is the kill flattening/truncating the trade set. **Not a win.**
- `2023-09` / candidate: 2× fees reads -0.1289 vs -0.1571 base (less negative) with n_trades 683→682 and kill-days 9→14. Fee rate doubled (fee/trade ratio 1.52; below 2.0 because positions shrink on the poorer equity path); the 'improvement' is the kill flattening/truncating the trade set. **Not a win.**
- `similar` / baseline: 2× fees trade set differs (n_trades 23→22, kill-days 0→1); expectancy 0.0198→-0.1499 is not on a comparable basis.
- `2020-10` / baseline: 2× fees reads -0.6333 vs -0.6717 base (less negative) with n_trades 93→93 and kill-days 0→1. Fee rate doubled (fee/trade ratio 1.85; below 2.0 because positions shrink on the poorer equity path); the 'improvement' is the kill flattening/truncating the trade set. **Not a win.**
- `2020-10` / candidate: 2× fees reads -0.8349 vs -0.8790 base (less negative) with n_trades 88→86 and kill-days 2→5. Fee rate doubled (fee/trade ratio 1.90; below 2.0 because positions shrink on the poorer equity path); the 'improvement' is the kill flattening/truncating the trade set. **Not a win.**
- `2020-11` / baseline: 2× fees reads -0.4915 vs -0.5331 base (less negative) with n_trades 98→98 and kill-days 5→6. Fee rate doubled (fee/trade ratio 1.86; below 2.0 because positions shrink on the poorer equity path); the 'improvement' is the kill flattening/truncating the trade set. **Not a win.**
- `2020-11` / candidate: 2× fees trade set differs (n_trades 87→86, kill-days 2→7); expectancy -0.4334→-0.4792 is not on a comparable basis.
- `2020-12` / baseline: 2× fees reads -0.2916 vs -0.3779 base (less negative) with n_trades 100→99 and kill-days 10→11. Fee rate doubled (fee/trade ratio 1.89; below 2.0 because positions shrink on the poorer equity path); the 'improvement' is the kill flattening/truncating the trade set. **Not a win.**
- `2023-10` / baseline: 2× fees reads -0.4245 vs -0.4839 base (less negative) with n_trades 102→101 and kill-days 3→5. Fee rate doubled (fee/trade ratio 1.84; below 2.0 because positions shrink on the poorer equity path); the 'improvement' is the kill flattening/truncating the trade set. **Not a win.**
- `2023-10` / candidate: 2× fees reads -0.3544 vs -0.3927 base (less negative) with n_trades 93→93 and kill-days 1→2. Fee rate doubled (fee/trade ratio 1.86; below 2.0 because positions shrink on the poorer equity path); the 'improvement' is the kill flattening/truncating the trade set. **Not a win.**
- `2023-11` / baseline: 2× fees trade set differs (n_trades 95→94, kill-days 6→8); expectancy -0.3845→-0.3964 is not on a comparable basis.
- `2023-11` / candidate: 2× fees reads -0.2555 vs -0.2631 base (less negative) with n_trades 96→96 and kill-days 1→2. Fee rate doubled (fee/trade ratio 1.91; below 2.0 because positions shrink on the poorer equity path); the 'improvement' is the kill flattening/truncating the trade set. **Not a win.**
- `2023-12` / baseline: 2× fees reads -0.2724 vs -0.3281 base (less negative) with n_trades 114→105 and kill-days 10→12. Fee rate doubled (fee/trade ratio 1.84; below 2.0 because positions shrink on the poorer equity path); the 'improvement' is the kill flattening/truncating the trade set. **Not a win.**
- `2023-12` / candidate: 2× fees reads -0.2944 vs -0.3224 base (less negative) with the same n_trades (105) and kill-day count (2) — a count-based check — and total fee drag 20.54→39.01. Sizing scales with equity, so the poorer equity path under 2× fees shrinks positions and € losses per trade. **Not a win.**
- `2024-10` / baseline: 2× fees trade set differs (n_trades 113→111, kill-days 4→9); expectancy -0.4769→-0.4983 is not on a comparable basis.
- `2024-10` / candidate: 2× fees reads -0.3679 vs -0.3796 base (less negative) with the same n_trades (104) and kill-day count (0) — a count-based check — and total fee drag 15.36→29.43. Sizing scales with equity, so the poorer equity path under 2× fees shrinks positions and € losses per trade. **Not a win.**
- `2024-11` / baseline: 2× fees reads -0.2912 vs -0.3521 base (less negative) with n_trades 103→102 and kill-days 6→8. Fee rate doubled (fee/trade ratio 1.94; below 2.0 because positions shrink on the poorer equity path); the 'improvement' is the kill flattening/truncating the trade set. **Not a win.**
- `2024-11` / candidate: 2× fees reads -0.2924 vs -0.3035 base (less negative) with the same n_trades (97) and kill-day count (0) — a count-based check — and total fee drag 9.07→17.73. Sizing scales with equity, so the poorer equity path under 2× fees shrinks positions and € losses per trade. **Not a win.**
- `2024-12` / baseline: 2× fees trade set differs (n_trades 98→96, kill-days 8→10); expectancy -0.6571→-0.7117 is not on a comparable basis.
- `2024-12` / candidate: 2× fees reads -0.4429 vs -0.4561 base (less negative) with the same n_trades (99) and kill-day count (0) — a count-based check — and total fee drag 11.58→22.41. Sizing scales with equity, so the poorer equity path under 2× fees shrinks positions and € losses per trade. **Not a win.**

## Reproduce

```bash
source .venv/bin/activate
python scripts/run_paper_eval.py --samples similar,2020-09,2023-09 --profile baseline --write-md ''
python scripts/run_paper_eval.py --samples similar,2020-09,2023-09 --profile candidate_v2_stops
python scripts/run_paper_eval.py --samples q4 --profile baseline --write-md ''   # secondary
python scripts/run_paper_eval.py --samples q4 --profile candidate_v2_stops                 # secondary
python scripts/compare_eval_profiles.py --candidate candidate_v2_stops --write-md phase1/17-candidate-v2-stops.md
```

JSON under gitignored `data/reports/` (`profiles/<profile>/eval_*.json`, `compare_*.json`). Cached research candles under `data/eval_cache/` are reused; nothing is refetched unless missing. Re-running the last command on the existing file carries over its H1 and the run-note section between the `run-note` markers, so it regenerates this document as committed.

## What this is not

- Not a Phase C recommendation.
- Not a live-trading recommendation.
- Not a claim that the locked breakout, with or without this overlay, has edge.
- Not a proposal for a follow-up candidate or a parameter sweep.

