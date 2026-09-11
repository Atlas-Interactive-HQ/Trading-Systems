# 97 — CORE-R1 FIRST SCORE: DOGE **1D EMA12/30 + ATR14×3.0 trail** (€140)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** DOGE ≤€20 **HALTED**. Soft PASS ≠ Core-arm. **This score does not promote.**
**Accounting:** `rise_panel_accounting_v2` (evaluator-v2 / terminal liquidation + completed expectancy). Gate locked in [`91`](./91-rise-panel-accounting-v2.md) **before** this score — do not rewrite it after seeing results.
**Lock (already on main):** [`94`](./94-core-r1-lock.md) — `rise_panel_v1_core_r1_doge_ema12_30_atr14_trail3_1d_eur140`.
**Panel:** [`54`](./54-rise-panel-v1.md) — same locked R1–R7 (DO NOT change).
**Compare:** Core C0 EMA12/30 `rise_panel_v1_core_doge_ema12_30_1d_eur140`.
**Donchian:** **STOPPED** (C2 soft FAIL [`89`](./89-rise-panel-core-c2-donchian40-20-ema50-200-1d.md)). CORE-R1 is **not** a Donchian continuation. **No** ATR multiplier / EMA period grind.
**R1–R7:** DEV/eliminate-only — **no promote**. Do **not** start SCALP-R2.
**Branch:** `research/vnext-core-r1-ema-atr-trail`. Base: `main` after PR #85 (`phase1/94-core-r1-lock.md`).

---

## Gate (LOCKED — same as #91; do not change after seeing results)

`rise_panel_accounting_v2`: median_terminal_trips≥1 AND ≥5/7 expectancy_terminal_adjusted>0 AND panel_terminal_liquidation_net>0.
OLD `soft_promote_v1` is reported for honesty, **not** rewritten.

Gate note: INTENTIONAL labeled accounting gate — NOT a silent rewrite of soft_promote_v1. Panel comparison uses synthetic terminal liquidation (same sell slip+fee as a normal exit) at the last in-window close. completed_round_trips stay realized-only. Soft PASS ≠ arm. Audit does not promote.

**Honesty:** Soft PASS ≠ Core-arm. V2 PASS ≠ promote. A V2 PASS that is forced-window-close dominated is **not** complete-trade edge. Prefer `expectancy_completed_eur` + `completed_round_trips`. Primary question (locked in [`94`](./94-core-r1-lock.md)):

> Does risk-side protection improve **complete-trade** expectancy / drawdown without eliminating Core participation?

---

## A. LOCKED Core C0 baseline (EMA12/30) — re-scored under accounting_v2

**core_c0_id:** `rise_panel_v1_core_doge_ema12_30_1d_eur140`

- Rule: closed-bar **EMA12 > EMA30** → long; else flat. Never short. No ATR trail.
- Bar: DOGE-USDT **1D**. Sleeve: Core **€140**.
- Role: **core_c0_baseline**. Same harness as [`91`](./91-rise-panel-accounting-v2.md).

### C0 per window (OLD vs V2)

| Id | n_trades old | completed | term trips | open? | old net € | term liq € | Δ net € | old exp € | exp completed € | exp term-adj € | max DD € | TIM |
|----|-------------:|----------:|-----------:|:-----:|----------:|-----------:|--------:|----------:|----------------:|---------------:|---------:|----:|
| R1 | 0 | 0 | 1 | yes | 100.9579 | 100.7170 | -0.2409 | — | — | 100.7170 | 53.4298 | 0.5714 |
| R2 | 2 | 2 | 3 | yes | -16.6090 | -16.7324 | -0.1234 | -7.4986 | -7.4986 | -5.5775 | 69.2569 | 0.4022 |
| R3 | 1 | 1 | 2 | yes | 82.0222 | 81.8002 | -0.2220 | -10.5166 | -10.5166 | 40.9001 | 43.1498 | 0.3146 |
| R4 | 0 | 0 | 1 | yes | 35.3467 | 35.1714 | -0.1753 | — | — | 35.1714 | 14.4543 | 0.4111 |
| R5 | 1 | 1 | 2 | yes | 83.1141 | 82.8910 | -0.2230 | 1.5895 | 1.5895 | 41.4455 | 32.5003 | 0.5333 |
| R6 | 1 | 1 | 2 | yes | 16.7226 | 16.5659 | -0.1567 | 26.3396 | 26.3396 | 8.2830 | 87.9988 | 0.6154 |
| R7 | 0 | 0 | 1 | yes | 62.4439 | 62.2415 | -0.2024 | — | — | 62.2415 | 34.5043 | 0.4944 |

**Panel summary (Core C0 EMA12/30):**

| Panel | OLD (`soft_promote_v1` inputs) | V2 (terminal liquidation) |
|-------|-------------------------------:|--------------------------:|
| panel net € | 363.9983 | 362.6547 |
| median exp € | -2.9545 | 40.9001 |
| median trips | 1.0 | 2.0 |
| exp>0 / 7 | 2 | 6 |
| gate verdict | FAIL (`soft_promote_v1`) | PASS (`rise_panel_accounting_v2`) |

**Complete-trade (realized only — not a gate):**
- completed trips / window: `[0, 2, 1, 0, 1, 1, 0]` · median **1.0**
- windows with completed exp>0: **2**/7
- median expectancy_completed €: **-2.9545**
- panel realized net €: **2.4154**
- worst DD €: **87.9988**
- median TIM: **0.4944** · sum n_entries: **12**
- forced window closes: **7**/7

`audit_does_not_promote: true`. C0 V2 PASS (if present) is typically **one-interval dominated** (open holds → forced closes) — not complete-trade proof.

`not_a_forecast: true`.

---

## B. LOCKED CORE-R1 family (scored AFTER [`94`](./94-core-r1-lock.md) on main)

**Family:** `ema12_30_atr14_trail3_long_flat_1d`  
**core_r1_id:** `rise_panel_v1_core_r1_doge_ema12_30_atr14_trail3_1d_eur140`  
**Code:** `atlas.strategy.core_doge_ema_atr_trail_1d.CoreR1EmaAtrTrailV1`  
**compare_to:** `rise_panel_v1_core_doge_ema12_30_1d_eur140`  
**Ladder:** `CORE-R1` · sleeve `core` · bar `1D`.

### Rule card (LOCKED — do not rewrite)

- Asset / bar: spot **DOGE-USDT** research MD, decision bar **1D**. Long/flat only.
- Entry: closed **EMA12 > EMA30**. Signal close → next open.
- Normal exit: **EMA12 ≤ EMA30**.
- Protection: SMA-ATR(14) trailing stop, multiplier **3.0**, on causally known **closed** bars only. Trail = peak **close** since entry − 3.0×ATR. Intra-bar stop fills are **not** claimed (same next-open fill model).
- After an ATR stop **while EMA is still bullish**: require a **fresh** EMA12-above-EMA30 transition before re-entry (`need_fresh_cross`).
- Max one position. No pyramid / avg / martingale.
- **No** Donchian. **No** ADX. **No** param sweep. **No** alt ATR multipliers on this score.
- Fill: signal close → next open. Size: full Core sleeve €140 when long.
- Costs: PaperSettings 5+5 bps.

### Why this family

Risk-side overlay on existing Core C0 EMA12/30 — **not** a Donchian continuation (C3/C4 STOPPED). Locked in [`94`](./94-core-r1-lock.md) **before** this first score. A smaller time-in-market is not automatically better; the question is complete-trade expectancy and drawdown **with** participation.

---

## C. Harness

- Script: `scripts/run_rise_panel_core_r1_ema_atr_trail_eval.py`
- Module: `atlas.paper.rise_panel_core_r1_ema_atr_trail_1d_eval`
- Walker / gate: `atlas.paper.rise_panel_accounting_v2_eval.run_candidate_on_panel` (same as `scripts/run_rise_panel_accounting_v2_eval.py` / [`91`](./91-rise-panel-accounting-v2.md))
- Strategy: `atlas.strategy.core_doge_ema_atr_trail_1d`
- Unit tests: `tests/unit/test_rise_panel_core_r1_ema_atr_trail_1d.py` (plus lock tests in `tests/unit/test_core_r1_ema_atr_trail.py`)
- Artifacts: `results/accounting_v2/rise_panel_accounting_v2_core_r1_ema_atr_trail.json` (does **not** overwrite historical `rise_panel_v1_*.json` or [`91`](./91-rise-panel-accounting-v2.md))

---

## D. Results — CORE-R1 on same locked 7

**core_r1_id:** `rise_panel_v1_core_r1_doge_ema12_30_atr14_trail3_1d_eur140`

### R1 per window (OLD vs V2)

| Id | n_trades old | completed | term trips | open? | old net € | term liq € | Δ net € | old exp € | exp completed € | exp term-adj € | max DD € | TIM |
|----|-------------:|----------:|-----------:|:-----:|----------:|-----------:|--------:|----------:|----------------:|---------------:|---------:|----:|
| R1 | 1 | 1 | 1 | no | 23.7925 | 23.7925 | -0.0000 | 23.7925 | 23.7925 | 23.7925 | 51.8583 | 0.3297 |
| R2 | 2 | 2 | 3 | yes | -12.5202 | -12.6476 | -0.1274 | -5.4274 | -5.4274 | -4.2159 | 65.3256 | 0.3696 |
| R3 | 1 | 1 | 2 | yes | 82.0222 | 81.8002 | -0.2220 | -10.5166 | -10.5166 | 40.9001 | 43.1498 | 0.3146 |
| R4 | 0 | 0 | 1 | yes | 35.3467 | 35.1714 | -0.1753 | — | — | 35.1714 | 14.4543 | 0.4111 |
| R5 | 1 | 1 | 2 | yes | 78.8948 | 78.6760 | -0.2188 | -1.0880 | -1.0880 | 39.3380 | 35.1107 | 0.5222 |
| R6 | 1 | 1 | 2 | yes | 20.1238 | 19.9637 | -0.1601 | 29.9495 | 29.9495 | 9.9819 | 84.5976 | 0.5934 |
| R7 | 1 | 1 | 1 | no | -4.2049 | -4.2049 | 0.0000 | -4.2049 | -4.2049 | -4.2049 | 31.8117 | 0.1236 |

**Panel summary (CORE-R1 EMA12/30 + ATR14×3.0 trail):**

| Panel | OLD (`soft_promote_v1` inputs) | V2 (terminal liquidation) |
|-------|-------------------------------:|--------------------------:|
| panel net € | 223.4550 | 222.5514 |
| median exp € | -2.6465 | 23.7925 |
| median trips | 1.0 | 2.0 |
| exp>0 / 7 | 2 | 5 |
| gate verdict | FAIL (`soft_promote_v1`) | PASS (`rise_panel_accounting_v2`) |

**Complete-trade (realized only — not a gate):**
- completed trips / window: `[1, 2, 1, 0, 1, 1, 1]` · median **1.0**
- windows with completed exp>0: **2**/7
- median expectancy_completed €: **-2.6465**
- panel realized net €: **27.0777**
- worst DD €: **84.5976**
- median TIM: **0.3696** · sum n_entries: **12**
- forced window closes: **5**/7

### accounting_v2 verdict (CORE-R1): **PASS** (`rise_panel_accounting_v2`)

- median_terminal_trips=2.0 (ok=True, min>=1)
- exp_term_adj>0: 5/7 (need ≥5; ok=True)
- panel_terminal_net €=222.5514 (ok=True)
- OLD informational `soft_promote_v1`: **FAIL** (median_trades=1.0; exp>0=2/7; panel_net €=223.4550)

### Honesty label vs Core C0 (comparison, **not** a gate): **PASS-and-better-completed-exp**

### Honesty deltas vs Core C0 (CORE-R1 − C0)

| Metric | Core C0 EMA €140 | CORE-R1 ATR trail €140 | Δ |
|--------|-----------------:|-----------------------:|--:|
| OLD panel net € | 363.9983 | 223.4550 | -140.5433 |
| V2 terminal panel net € | 362.6547 | 222.5514 | -140.1033 |
| median completed exp € | -2.9545 | -2.6465 | 0.3081 |
| completed exp>0 / 7 | 2 | 2 | 0 |
| median completed trips | 1.0 | 1.0 | 0.0 |
| V2 term-adj exp>0 / 7 | 6 | 5 | -1 |
| worst DD € | 87.9988 | 84.5976 | -3.4012 |
| median TIM | 0.4944 | 0.3696 | -0.1248 |
| v2 gate | PASS | **PASS** | — |
| OLD soft | FAIL | FAIL | informational |
| honesty | — | **PASS-and-better-completed-exp** | promote=**False** |
| participation eliminated | — | **False** | sum n_entries==0 |
| complete-exp improved | — | **True** | — |
| DD improved (smaller) | — | **True** | — |

---

## E. DEV/eliminate-only · Soft PASS ≠ arm · no promote

accounting_v2 **PASS**. Paper only. **Soft PASS ≠ Core-arm**. Live DOGE ≤€20 **HALTED**. `not_a_forecast: true`. `place_orders: false`.

- **eliminate:** `False` (True iff v2 FAIL — no ATR/EMA grind on FAIL).
- **promote:** `False` (hard). R1–R7 cannot prove general profitability.
- **do_not_start_scalp_r2:** `True`.
- **no_donchian / no_atr_ema_grind:** `True`.

**V2 PASS is still DEV/eliminate-only.** It is **not** a GREEN CANDIDATE, **not** Core-arm, **not** a promote. Next Core score = unseen SHADOW only (not another R1–R7 tip). Do **not** start SCALP-R2 from this PR.

**Do not read V2 PASS / tiny completed-exp Δ as complete-trade edge.** Median completed exp remains **negative** (`complete_exp_still_negative=True`); completed exp>0 is still thin (`completed_exp_gt0_thin=True`). V2 forced window closes: **5**/7. Panel terminal net worse than C0: **True** (ATR trail cut BH-like open holds — expected, not a headline). Participation was **not** eliminated. Soft PASS ≠ Core-arm. No promote.

---

## What this is not

- Not a Donchian N / EMA / ATR-multiplier / TF / cost grind.
- Not C3/C4 and not a rescue of C1/C2 FAIL ([`88`](./88-rise-panel-core-c1-donchian40-20-1d.md) / [`89`](./89-rise-panel-core-c2-donchian40-20-ema50-200-1d.md)).
- Not a rewrite of `rise_panel_accounting_v2` or [`91`](./91-rise-panel-accounting-v2.md).
- Not a change to R1–R7 window dates.
- Not a live / Phase C recommendation. Not `ga live €200`.
- Not Core-arming. Soft PASS ≠ arm. Live ≤€20 HALTED.
- Not SCALP-R2. Not Mid M2–M4 on R1–R7.
- Not a claim that past rise windows forecast the next bull.

`not_a_forecast: true`. `place_orders: false`.
