# 18 — Candidate v3 (combo) vs frozen baseline — Phase D trial #3

**Stance:** Research. `not_a_forecast: true`. Do not headline PnL. Do not promote to Phase C or live from this score. A PASS is a research result on paper holdout, not a go-live signal; a FAIL keeps the frozen baseline.

## Candidate

- Baseline: `baseline` — frozen BreakoutV1 + `config/default.yaml` (no overlay; `atr_stop_mult: 1.5`, no daily cap, `min_atr_frac: 0.001`).
- Candidate: `candidate_v3_combo` — overlay `{"atr_stop_mult": 3.0, "atr_stop_mult_baseline": 1.5, "atr_stop_mult_factor": 2.0, "max_would_place_per_utc_day": 1}`.
- `atr_stop_mult` → same rule as candidate_v2_stops: 2.0× the baseline multiplier read from `config/default.yaml` at apply time (committed config: baseline **1.5** → candidate **3.0**; 2.5 if the baseline were already 2.0). Resolved values are stamped in the overlay above.
- `max_would_place_per_utc_day: 1` → same as candidate_v1_filters: the first would-place of a UTC day is allowed; further same-day signals are blocked with `blocked_reason: daily_cap` (after kill / one-position, before sizing; counted at decision time).
- `min_atr_frac` is **not** overlaid (stays baseline 0.001). Trial #1's quieter-bar filter is deliberately omitted so this pack isolates stop+cap.
- Sizing rule is unchanged. Wider stops can raise € at risk where the 2× leverage cap bound the baseline (v2 finding); cap-bound share is measured, not assumed.
- Unchanged: lookback 16, ATR period 14, `min_atr_frac: 0.001`, `oneh_filter: stub`, time-stop 16 bars, €200 book, 5% daily kill, 1.5% risk/trade, one position, X-Perp ≤2x. No grid search; one candidate, one trial.
- Resolved against this config: `atr_stop_mult` baseline **1.50** → candidate **3.00** (factor 2.0).

## Pass / fail rule (decided up front)

PASS (research only) iff on BOTH 2020-09 and 2023-09: candidate holdout-30% expectancy after costs is strictly greater than baseline (less negative or positive) AND candidate holdout max DD <= baseline holdout max DD × 1.10. A holdout with zero trades has no expectancy and fails closed. Stress is documented, never scored: a less-negative expectancy under 2× fees is never a win — with fewer trades / more kill-days it is kill truncation; with the same trade set it is smaller positions on a poorer equity path (sizing scales with equity). similar (June) and Q4 months are secondary and do not rewrite this rule.

## Verdict: **FAIL**

| window | baseline holdout exp. | candidate holdout exp. | strictly greater? | baseline holdout DD | candidate holdout DD | DD change | DD within +10%? | cand. kill-days | cand. daily_cap blocked | window pass |
|---|---:|---:|:---:|---:|---:|---:|:---:|---:|---:|:---:|
| 2020-09 | -0.3066 | 0.1831 | yes | 306.74 | 91.12 | -70.3% | yes | 0 | 320 | **PASS** |
| 2023-09 | -0.2660 | -0.4885 | no | 112.97 | 46.93 | -58.5% | yes | 0 | 403 | **FAIL** |

At least one primary window fails the rule. **FAIL** — keep the frozen baseline. No candidate_v4 is proposed in this trial.

<!-- run-note:start -->
## Mac run (2026-09-03)

Cached research candles under `data/eval_cache/` (no refetch). `config/default.yaml` is unchanged (`atr_stop_mult: 1.5`, no daily cap, `min_atr_frac: 0.001`).

**Why FAIL.** 2020-09 holdout expectancy is strictly better than baseline (−0.3066 → **+0.1831**) and DD is inside +10% (306.74 → 91.12). 2023-09 holdout expectancy is **worse** (−0.2660 → **−0.4885**) even though DD improved (112.97 → 46.93). The rule requires **both** windows. FAIL — keep the frozen baseline.

**vs candidate_v2_stops (secondary; does not rewrite the pass rule).** Combo does **not** beat v2-only on both named holdouts.

| window | v2 holdout exp. | v3 holdout exp. | v3 strictly greater? | v2 n_trades | v3 n_trades |
|---|---:|---:|:---:|---:|---:|
| 2020-09 | −0.0967 | +0.1831 | yes | 199 | 64 |
| 2023-09 | −0.1745 | −0.4885 | no | 212 | 64 |

**Sizing regime (full sample, would-place).** Cap-bound share: v3 **9.0%** (2020-09) / **26.3%** (2023-09). Mean € at risk 1.82 / 1.68 € (v2 was 0.94 / 0.92). Wider stop plus a surviving book (one trade/day, 0 kill-days) is consistent with v2's finding that € at risk can rise; this is measured, not a reason to PASS.

Daily cap blocked 997 / 1203 would-places on the two long windows (full). 2×-fee rows that look less negative are equity-path sizing (same n_trades, 0 kill-days) — flagged below, **not a win**.
<!-- run-note:end -->

## Primary windows (pass rule)

Research MD DOGE-USDT (not OMS DOGE-USD). Holdout 30% is the scored slice.

### 2020-09

MD: research MD DOGE-USDT (not OMS DOGE-USD); window 2020-09-01 → 2021-03-31 UTC
Bars: full 20352 · IS 14246 · holdout 6106.

| metric | baseline holdout | candidate holdout | Δ holdout | baseline IS | candidate IS | baseline full | candidate full |
|---|---:|---:|---:|---:|---:|---:|---:|
| n_trades | 212 | 64 | -148 | 462 | 148 | 675 | 211 |
| n_would_place | 212 | 64 | -148 | 463 | 148 | 675 | 211 |
| n_kill_days | 23 | 0 | -23 | 29 | 0 | 52 | 0 |
| n_blocked_daily_cap | 0 | 320 | +320 | 0 | 670 | 0 | 997 |
| expectancy after costs (€/trade) | -0.3066 | 0.1831 | +0.4896 | -0.2847 | -0.6235 | -0.2032 | -0.4145 |
| max DD (€) | 306.74 | 91.12 | -215.62 | 182.85 | 114.98 | 192.07 | 114.98 |
| fee drag (€) | 39.23 | 8.73 | -30.51 | 50.54 | 22.21 | 54.13 | 25.89 |
| win rate (secondary) | 20.3% | 26.6% | +6.3% | 22.7% | 24.3% | 22.1% | 24.6% |

Stress (full sample, same engine path):

| profile | stress | n_trades full→stress | kill-days full→stress | expectancy full→stress (€/trade) | max DD stress (€) | fee drag full→stress (€) | fee/trade ratio | confound |
|---|---|---:|---:|---:|---:|---:|---:|---|
| baseline | 2× fees | 675→667 | 52→60 | -0.2032→-0.1685 | 196.10 | 54.13→83.71 | 1.56 | **kill-truncation: less-negative expectancy is NOT a win** |
| baseline | 1-bar entry delay | 675→670 | 52→45 | -0.2032→-0.2040 | 192.15 | 54.13→54.19 | — | trade set differs by construction |
| baseline | 10% missed entries | 675→633 | 52→45 | -0.2032→-0.2320 | 192.88 | 54.13→45.94 | — | trade set differs by construction |
| candidate | 2× fees | 211→211 | 0→0 | -0.4145→-0.3839 | 128.69 | 25.89→47.68 | 1.84 | **equity-path sizing (same trade/kill counts): less-negative expectancy is NOT a win** |
| candidate | 1-bar entry delay | 211→211 | 0→0 | -0.4145→-0.4375 | 119.64 | 25.89→25.23 | — |  |
| candidate | 10% missed entries | 211→191 | 0→0 | -0.4145→-0.4345 | 108.99 | 25.89→24.52 | — | trade set differs by construction |

`not_a_forecast: true`.

### 2023-09

MD: research MD DOGE-USDT (not OMS DOGE-USD); window 2023-09-01 → 2024-03-31 UTC
Bars: full 20448 · IS 14313 · holdout 6135.

| metric | baseline holdout | candidate holdout | Δ holdout | baseline IS | candidate IS | baseline full | candidate full |
|---|---:|---:|---:|---:|---:|---:|---:|
| n_trades | 228 | 64 | -164 | 505 | 149 | 734 | 213 |
| n_would_place | 228 | 64 | -164 | 505 | 149 | 734 | 213 |
| n_kill_days | 12 | 0 | -12 | 26 | 0 | 38 | 0 |
| n_blocked_daily_cap | 0 | 403 | +403 | 0 | 797 | 0 | 1203 |
| expectancy after costs (€/trade) | -0.2660 | -0.4885 | -0.2225 | -0.2264 | -0.4817 | -0.1647 | -0.4152 |
| max DD (€) | 112.97 | 46.93 | -66.04 | 181.26 | 112.58 | 190.62 | 130.78 |
| fee drag (€) | 41.92 | 11.83 | -30.08 | 64.44 | 31.51 | 68.87 | 37.14 |
| win rate (secondary) | 31.1% | 37.5% | +6.4% | 27.7% | 31.5% | 28.7% | 32.9% |

Stress (full sample, same engine path):

| profile | stress | n_trades full→stress | kill-days full→stress | expectancy full→stress (€/trade) | max DD stress (€) | fee drag full→stress (€) | fee/trade ratio | confound |
|---|---|---:|---:|---:|---:|---:|---:|---|
| baseline | 2× fees | 734→710 | 38→51 | -0.1647→-0.1350 | 197.30 | 68.87→101.21 | 1.52 | **kill-truncation: less-negative expectancy is NOT a win** |
| baseline | 1-bar entry delay | 734→729 | 38→31 | -0.1647→-0.1692 | 192.83 | 68.87→68.87 | — | trade set differs by construction |
| baseline | 10% missed entries | 734→690 | 38→31 | -0.1647→-0.1726 | 189.08 | 68.87→69.03 | — | trade set differs by construction |
| candidate | 2× fees | 213→213 | 0→0 | -0.4152→-0.3630 | 148.30 | 37.14→66.43 | 1.79 | **equity-path sizing (same trade/kill counts): less-negative expectancy is NOT a win** |
| candidate | 1-bar entry delay | 213→213 | 0→0 | -0.4152→-0.4186 | 131.46 | 37.14→36.88 | — |  |
| candidate | 10% missed entries | 213→191 | 0→0 | -0.4152→-0.4492 | 125.88 | 37.14→34.42 | — | trade set differs by construction |

`not_a_forecast: true`.

## Secondary: similar-regime June (small n)

Similar-regime window, DOGE-USD spot + X-Perp MD 310404. Small sample; informational only.

### similar

MD: DOGE-USD + xperp MD 310404 (similar-regime June)
Bars: full 672 · IS 470 · holdout 202.

| metric | baseline holdout | candidate holdout | Δ holdout | baseline IS | candidate IS | baseline full | candidate full |
|---|---:|---:|---:|---:|---:|---:|---:|
| n_trades | 7 | 2 | -5 | 15 | 5 | 23 | 7 |
| n_would_place | 8 | 2 | -6 | 16 | 5 | 24 | 7 |
| n_kill_days | 0 | 0 | +0 | 0 | 0 | 0 | 0 |
| n_blocked_daily_cap | 0 | 28 | +28 | 0 | 33 | 0 | 61 |
| expectancy after costs (€/trade) | -0.6045 | -0.4376 | +0.1669 | 0.3436 | -0.0974 | 0.0198 | -0.1931 |
| max DD (€) | 10.14 | 4.10 | -6.03 | 21.46 | 16.26 | 21.46 | 16.26 |
| fee drag (€) | 2.92 | 0.78 | -2.14 | 6.11 | 1.90 | 9.21 | 2.67 |
| win rate (secondary) | 28.6% | 50.0% | +21.4% | 46.7% | 60.0% | 39.1% | 57.1% |

Stress (full sample, same engine path):

| profile | stress | n_trades full→stress | kill-days full→stress | expectancy full→stress (€/trade) | max DD stress (€) | fee drag full→stress (€) | fee/trade ratio | confound |
|---|---|---:|---:|---:|---:|---:|---:|---|
| baseline | 2× fees | 23→22 | 0→1 | 0.0198→-0.1499 | 32.28 | 9.21→17.10 | 1.94 | kill-truncation (trade set differs) |
| baseline | 1-bar entry delay | 23→22 | 0→1 | 0.0198→-0.4693 | 24.43 | 9.21→8.41 | — | trade set differs by construction |
| baseline | 10% missed entries | 23→23 | 0→0 | 0.0198→-0.0988 | 23.68 | 9.21→9.15 | — |  |
| candidate | 2× fees | 7→7 | 0→0 | -0.1931→-0.1942 | 17.91 | 2.67→5.32 | 1.99 |  |
| candidate | 1-bar entry delay | 7→7 | 0→0 | -0.1931→-1.1553 | 15.49 | 2.67→2.61 | — |  |
| candidate | 10% missed entries | 7→7 | 0→0 | -0.1931→-0.1931 | 16.26 | 2.67→2.67 | — |  |

`not_a_forecast: true`.

## Seasonal check: Q4 months (secondary — does not rewrite the pass rule)

Oct/Nov/Dec 2020/2023/2024 on DOGE-USDT. Holdout 30% per month. Informational: same season as the coming months, not a similar-regime match.

| month | baseline holdout exp. | candidate holdout exp. | Δ | baseline holdout DD | candidate holdout DD | baseline kill-days (holdout) | candidate kill-days (holdout) | candidate daily_cap blocked (full) | candidate n_trades (full) vs baseline |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2020-10 | -0.0103 | 0.4863 | +0.4966 | 33.39 | 16.40 | 0 | 0 | 102 | 31 vs 93 |
| 2020-11 | -0.3508 | -0.3523 | -0.0015 | 25.84 | 7.70 | 2 | 0 | 147 | 29 vs 98 |
| 2020-12 | -1.2134 | -0.5984 | +0.6151 | 72.37 | 10.43 | 6 | 0 | 163 | 31 vs 100 |
| 2023-10 | -1.0208 | -0.4017 | +0.6191 | 65.23 | 13.89 | 3 | 0 | 148 | 31 vs 102 |
| 2023-11 | -0.5472 | -1.5836 | -1.0364 | 31.14 | 18.17 | 1 | 0 | 197 | 30 vs 95 |
| 2023-12 | -1.1539 | -1.3378 | -0.1840 | 52.22 | 15.92 | 4 | 0 | 198 | 31 vs 114 |
| 2024-10 | -0.5864 | 0.0417 | +0.6281 | 43.11 | 7.06 | 2 | 0 | 165 | 31 vs 113 |
| 2024-11 | -1.0048 | -0.6932 | +0.3116 | 45.70 | 11.11 | 1 | 0 | 159 | 30 vs 103 |
| 2024-12 | -1.3462 | -2.5118 | -1.1656 | 46.79 | 24.23 | 2 | 0 | 176 | 31 vs 98 |

Candidate holdout expectancy is less negative than baseline in 5 of 9 Q4 months. Secondary information only; it does not change the verdict above.

## How to read the 2× fees stress (kill truncation and equity-path sizing)

2× fees does not change signals, so any difference in n_trades or n_kill_days between the full run and the 2× run comes from the equity path: higher fees drain the book faster, the 5% daily kill trips earlier, positions are flattened and the rest of that UTC day is blocked. Fewer, earlier-killed trades can make expectancy per trade read LESS negative under 2× fees while the book is simply dying sooner. A second mechanism needs no truncation: sizing scales with equity (risk budget = 1.5% of equity), so a poorer equity path under 2× fees means smaller positions and smaller € losses per trade — the same trade set reads less negative in €/trade. Read 2× fees on a comparable basis: fee drag per trade should be ≈2× the base (fee_per_trade_ratio), and total fee drag € should be worse or equal unless truncation removed trades. Fees cannot improve a strategy: never read a less-negative 2× expectancy as a win.

Flagged rows in this run:

- `2020-09` / baseline: 2× fees reads -0.1685 vs -0.2032 base (less negative) with n_trades 675→667 and kill-days 52→60. Fee rate doubled (fee/trade ratio 1.56; below 2.0 because positions shrink on the poorer equity path); the 'improvement' is the kill flattening/truncating the trade set. **Not a win.**
- `2020-09` / candidate: 2× fees reads -0.3839 vs -0.4145 base (less negative) with the same n_trades (211) and kill-day count (0) — a count-based check — and total fee drag 25.89→47.68. Sizing scales with equity, so the poorer equity path under 2× fees shrinks positions and € losses per trade. **Not a win.**
- `2023-09` / baseline: 2× fees reads -0.1350 vs -0.1647 base (less negative) with n_trades 734→710 and kill-days 38→51. Fee rate doubled (fee/trade ratio 1.52; below 2.0 because positions shrink on the poorer equity path); the 'improvement' is the kill flattening/truncating the trade set. **Not a win.**
- `2023-09` / candidate: 2× fees reads -0.3630 vs -0.4152 base (less negative) with the same n_trades (213) and kill-day count (0) — a count-based check — and total fee drag 37.14→66.43. Sizing scales with equity, so the poorer equity path under 2× fees shrinks positions and € losses per trade. **Not a win.**
- `similar` / baseline: 2× fees trade set differs (n_trades 23→22, kill-days 0→1); expectancy 0.0198→-0.1499 is not on a comparable basis.
- `2020-10` / baseline: 2× fees reads -0.6333 vs -0.6717 base (less negative) with n_trades 93→93 and kill-days 0→1. Fee rate doubled (fee/trade ratio 1.85; below 2.0 because positions shrink on the poorer equity path); the 'improvement' is the kill flattening/truncating the trade set. **Not a win.**
- `2020-10` / candidate: 2× fees reads -0.5793 vs -0.5874 base (less negative) with the same n_trades (31) and kill-day count (0) — a count-based check — and total fee drag 9.04→17.68. Sizing scales with equity, so the poorer equity path under 2× fees shrinks positions and € losses per trade. **Not a win.**
- `2020-11` / baseline: 2× fees reads -0.4915 vs -0.5331 base (less negative) with n_trades 98→98 and kill-days 5→6. Fee rate doubled (fee/trade ratio 1.86; below 2.0 because positions shrink on the poorer equity path); the 'improvement' is the kill flattening/truncating the trade set. **Not a win.**
- `2020-11` / candidate: 2× fees reads -0.8429 vs -0.8536 base (less negative) with the same n_trades (29) and kill-day count (0) — a count-based check — and total fee drag 5.97→11.75. Sizing scales with equity, so the poorer equity path under 2× fees shrinks positions and € losses per trade. **Not a win.**
- `2020-12` / baseline: 2× fees reads -0.2916 vs -0.3779 base (less negative) with n_trades 100→99 and kill-days 10→11. Fee rate doubled (fee/trade ratio 1.89; below 2.0 because positions shrink on the poorer equity path); the 'improvement' is the kill flattening/truncating the trade set. **Not a win.**
- `2020-12` / candidate: 2× fees reads -1.1146 vs -1.1251 base (less negative) with the same n_trades (31) and kill-day count (0) — a count-based check — and total fee drag 4.42→8.74. Sizing scales with equity, so the poorer equity path under 2× fees shrinks positions and € losses per trade. **Not a win.**
- `2023-10` / baseline: 2× fees reads -0.4245 vs -0.4839 base (less negative) with n_trades 102→101 and kill-days 3→5. Fee rate doubled (fee/trade ratio 1.84; below 2.0 because positions shrink on the poorer equity path); the 'improvement' is the kill flattening/truncating the trade set. **Not a win.**
- `2023-10` / candidate: 2× fees reads -0.6904 vs -0.7115 base (less negative) with the same n_trades (31) and kill-day count (0) — a count-based check — and total fee drag 9.97→19.44. Sizing scales with equity, so the poorer equity path under 2× fees shrinks positions and € losses per trade. **Not a win.**
- `2023-11` / baseline: 2× fees trade set differs (n_trades 95→94, kill-days 6→8); expectancy -0.3845→-0.3964 is not on a comparable basis.
- `2023-11` / candidate: 2× fees reads -1.0773 vs -1.0925 base (less negative) with the same n_trades (30) and kill-day count (0) — a count-based check — and total fee drag 5.72→11.26. Sizing scales with equity, so the poorer equity path under 2× fees shrinks positions and € losses per trade. **Not a win.**
- `2023-12` / baseline: 2× fees reads -0.2724 vs -0.3281 base (less negative) with n_trades 114→105 and kill-days 10→12. Fee rate doubled (fee/trade ratio 1.84; below 2.0 because positions shrink on the poorer equity path); the 'improvement' is the kill flattening/truncating the trade set. **Not a win.**
- `2023-12` / candidate: 2× fees reads -0.5141 vs -0.5277 base (less negative) with the same n_trades (31) and kill-day count (0) — a count-based check — and total fee drag 6.29→12.40. Sizing scales with equity, so the poorer equity path under 2× fees shrinks positions and € losses per trade. **Not a win.**
- `2024-10` / baseline: 2× fees trade set differs (n_trades 113→111, kill-days 4→9); expectancy -0.4769→-0.4983 is not on a comparable basis.
- `2024-11` / baseline: 2× fees reads -0.2912 vs -0.3521 base (less negative) with n_trades 103→102 and kill-days 6→8. Fee rate doubled (fee/trade ratio 1.94; below 2.0 because positions shrink on the poorer equity path); the 'improvement' is the kill flattening/truncating the trade set. **Not a win.**
- `2024-11` / candidate: 2× fees reads -0.1950 vs -0.1990 base (less negative) with the same n_trades (30) and kill-day count (0) — a count-based check — and total fee drag 2.98→5.92. Sizing scales with equity, so the poorer equity path under 2× fees shrinks positions and € losses per trade. **Not a win.**
- `2024-12` / baseline: 2× fees trade set differs (n_trades 98→96, kill-days 8→10); expectancy -0.6571→-0.7117 is not on a comparable basis.
- `2024-12` / candidate: 2× fees reads -1.3581 vs -1.3728 base (less negative) with the same n_trades (31) and kill-day count (0) — a count-based check — and total fee drag 3.97→7.87. Sizing scales with equity, so the poorer equity path under 2× fees shrinks positions and € losses per trade. **Not a win.**

## Reproduce

```bash
source .venv/bin/activate
python scripts/run_paper_eval.py --samples similar,2020-09,2023-09 --profile baseline --write-md ''
python scripts/run_paper_eval.py --samples similar,2020-09,2023-09 --profile candidate_v3_combo
python scripts/run_paper_eval.py --samples q4 --profile baseline --write-md ''   # secondary
python scripts/run_paper_eval.py --samples q4 --profile candidate_v3_combo                 # secondary
python scripts/compare_eval_profiles.py --candidate candidate_v3_combo --write-md phase1/18-candidate-v3-combo.md
```

JSON under gitignored `data/reports/` (`profiles/<profile>/eval_*.json`, `compare_*.json`). Cached research candles under `data/eval_cache/` are reused; nothing is refetched unless missing. Re-running the last command on the existing file carries over its H1 and the run-note section between the `run-note` markers, so it regenerates this document as committed.

## What this is not

- Not a Phase C recommendation.
- Not a live-trading recommendation.
- Not a claim that the locked breakout, with or without this overlay, has edge.
- Not a candidate_v4 proposal.

