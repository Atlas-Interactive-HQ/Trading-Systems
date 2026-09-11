# 99 — SCALP-R2 FIRST SCORE: Dual Thrust + RVOL + **4H EMA12/21 regime** 1H €20

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** DOGE ≤€20 **HALTED**. Soft PASS ≠ Scalp-arm. **This score does not promote.**
**Accounting:** `rise_panel_accounting_v2` (evaluator-v2 / terminal liquidation + completed expectancy). Gate locked in [`91`](./91-rise-panel-accounting-v2.md) **before** this score — do not rewrite it after seeing results.
**Lock (already on main):** [`93`](./93-frozen-mid-scalp-candidates.md) — `rise_panel_v1_scalp_r2_dual_thrust_4h_ema1221_regime`.
**Panel:** [`54`](./54-rise-panel-v1.md) — same locked R1–R7 (DO NOT change).
**Compare:** Scalp S1 `rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_rvol_gt1_1h_eur20` (and S0 `#83` `rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_1h_eur20` via S1 path).
**Walker:** `walk_long_short` — **not** `walk_long_flat` (would silently drop shorts).
**No** RVOL 1.25/1.5 grind. Not a threshold rescue of S1.
**R1–R7:** DEV/eliminate-only — **no promote**. Soft PASS ≠ arm.
**Branch:** `research/vnext-scalp-r2-dt-4h-regime`. Base: `main` after PR #86. phase1/98 reserved for H0 health; this doc is **99**.

---

## Gate (LOCKED — same as #91; do not change after seeing results)

`rise_panel_accounting_v2`: median_terminal_trips≥1 AND ≥5/7 expectancy_terminal_adjusted>0 AND panel_terminal_liquidation_net>0.
OLD `soft_promote_v1` is reported for honesty, **not** rewritten.

Gate note: INTENTIONAL labeled accounting gate — NOT a silent rewrite of soft_promote_v1. Panel comparison uses synthetic terminal liquidation (same sell slip+fee as a normal exit) at the last in-window close. completed_round_trips stay realized-only. Soft PASS ≠ arm. Audit does not promote.

**Honesty:** Soft PASS ≠ Scalp-arm. V2 PASS ≠ promote. Prefer `expectancy_completed_eur` + `completed_round_trips`. Short entries must be non-zero somewhere if the regime fires shorts — otherwise the walker is not exercising the short path.

---

## A. LOCKED Scalp S1 baseline — re-scored under accounting_v2

**scalp_s1_id:** `rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_rvol_gt1_1h_eur20`

- Rule: 1H Dual Thrust N20 k=0.5 + RVOL20>1, **long/flat only** (S1).
- Walker: `walk_long_flat` (correct for long-only S1).
- Bar: DOGE-USDT **1H**. Sleeve: Scalp **€20**.
- Role: provisional DEV / honesty comparator ([`87`](./87-rise-panel-scalp-s1-rvol-1h.md), [`91`](./91-rise-panel-accounting-v2.md)).

### S1 per window (OLD vs V2)

| Id | n_trades old | completed | term trips | open? | old net € | term liq € | Δ net € | old exp € | exp completed € | exp term-adj € | long ent | short ent | max DD € | TIM |
|----|-------------:|----------:|-----------:|:-----:|----------:|-----------:|--------:|----------:|----------------:|---------------:|---------:|----------:|---------:|----:|
| R1 | 14 | 14 | 14 | no | 1.9536 | 1.9536 | 0.0000 | 0.1395 | 0.1395 | 0.1395 | 14 | 0 | 6.9658 | 0.6178 |
| R2 | 7 | 7 | 8 | yes | 6.5725 | 6.5459 | -0.0266 | 1.0729 | 1.0729 | 0.8182 | 8 | 0 | 7.2502 | 0.5650 |
| R3 | 12 | 12 | 12 | no | 10.1558 | 10.1558 | -0.0000 | 0.8463 | 0.8463 | 0.8463 | 12 | 0 | 13.8215 | 0.4366 |
| R4 | 5 | 5 | 6 | yes | -0.6700 | -0.6894 | -0.0193 | -0.2980 | -0.2980 | -0.1149 | 6 | 0 | 4.0964 | 0.1896 |
| R5 | 7 | 7 | 8 | yes | 11.0009 | 10.9699 | -0.0310 | 0.4974 | 0.4974 | 1.3712 | 8 | 0 | 4.6419 | 0.4954 |
| R6 | 8 | 8 | 8 | no | 1.6690 | 1.6690 | 0.0000 | 0.2086 | 0.2086 | 0.2086 | 8 | 0 | 10.9765 | 0.5924 |
| R7 | 10 | 10 | 10 | no | 1.9582 | 1.9582 | 0.0000 | 0.1958 | 0.1958 | 0.1958 | 10 | 0 | 4.8612 | 0.2894 |

**Panel summary (Scalp S1 RVOL):**

| Panel | OLD (`soft_promote_v1` inputs) | V2 (terminal liquidation) |
|-------|-------------------------------:|--------------------------:|
| panel net € | 32.6400 | 32.5631 |
| median exp € | 0.2086 | 0.2086 |
| median trips | 8.0 | 8.0 |
| exp>0 / 7 | 6 | 6 |
| gate verdict | PASS (`soft_promote_v1`) | PASS (`rise_panel_accounting_v2`) |

**Complete-trade (realized only — not a gate):**
- completed trips / window: `[14, 7, 12, 5, 7, 8, 10]` · median **8.0**
- windows with completed exp>0: **6**/7
- median expectancy_completed €: **0.2086**
- panel realized net €: **25.2387**
- worst DD €: **13.8215**
- median TIM: **0.4954** · sum n_entries: **66** (long **66** / short **0**)
- forced window closes: **3**/7

`audit_does_not_promote: true`.

`not_a_forecast: true`.

---

## B. LOCKED SCALP-R2 family (scored AFTER [`93`](./93-frozen-mid-scalp-candidates.md))

**Family:** `dual_thrust_n20_k0505_rvol_gt1_4h_ema1221_regime_1h`  
**scalp_r2_id:** `rise_panel_v1_scalp_r2_dual_thrust_4h_ema1221_regime`  
**Code:** `atlas.strategy.scalp_doge_dual_thrust_rvol_4h_regime_1h.ScalpDogeDualThrustRvol4hRegime1hV1`  
**compare_to:** `rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_rvol_gt1_1h_eur20`  
**Ladder:** `SCALP-R2` · sleeve `scalp` · decision `1H` · regime `4H`.

### Rule card (LOCKED — do not rewrite)

- Asset / bar: spot **DOGE-USDT** research MD, decision bar **1H**.
- Dual Thrust: N=**20**, k1=k2=**0.5** + RVOL20>**1.0** (unchanged from S1).
- Regime: **4H EMA12/21**.
- LONG: EMA12>EMA21 AND upper DT break AND RVOL>1.0.
- SHORT: EMA12<EMA21 AND lower DT break AND RVOL>1.0.
- Exit: opposite DT boundary OR HTF regime reversal.
- Max one position. No pyramid / avg / martingale.
- Fill: signal close → next open. Size: Scalp €20. Costs: 5+5 bps.
- **Walker:** `atlas.paper.ls_eval.walk_long_short` (signed qty; shorts filled).

---

## C. Harness

- Script: `scripts/run_rise_panel_scalp_r2_4h_regime_1h_eval.py`
- Module: `atlas.paper.rise_panel_scalp_r2_4h_regime_1h_eval`
- Walker: `atlas.paper.ls_eval.walk_long_short`
- Accounting: `rise_panel_accounting_v2` / [`91`](./91-rise-panel-accounting-v2.md)
- Artifacts: `results/accounting_v2/rise_panel_accounting_v2_scalp_r2_*.json`
- Unit tests: `tests/unit/test_walk_long_short.py`, `tests/unit/test_rise_panel_scalp_r2_4h_regime_1h.py`

---

## D. Results — SCALP-R2 on same 7 (accounting_v2)

**scalp_r2_id:** `rise_panel_v1_scalp_r2_dual_thrust_4h_ema1221_regime`

### R2 per window (OLD vs V2)

| Id | n_trades old | completed | term trips | open? | old net € | term liq € | Δ net € | old exp € | exp completed € | exp term-adj € | long ent | short ent | max DD € | TIM |
|----|-------------:|----------:|-----------:|:-----:|----------:|-----------:|--------:|----------:|----------------:|---------------:|---------:|----------:|---------:|----:|
| R1 | 13 | 13 | 13 | no | 1.8233 | 1.8233 | 0.0000 | 0.1403 | 0.1403 | 0.1403 | 8 | 5 | 6.4447 | 0.4049 |
| R2 | 13 | 13 | 14 | yes | -2.5775 | -2.5949 | -0.0174 | -0.1509 | -0.1509 | -0.1853 | 9 | 5 | 12.1415 | 0.5565 |
| R3 | 13 | 13 | 14 | yes | 11.7777 | 11.7446 | -0.0332 | 0.9613 | 0.9613 | 0.8389 | 6 | 8 | 8.3709 | 0.4694 |
| R4 | 10 | 10 | 11 | yes | -3.8510 | -3.8672 | -0.0161 | -0.4536 | -0.4536 | -0.3516 | 5 | 6 | 5.8622 | 0.3301 |
| R5 | 8 | 8 | 9 | yes | 7.4149 | 7.3875 | -0.0274 | 0.0957 | 0.0957 | 0.8208 | 5 | 4 | 4.5029 | 0.3471 |
| R6 | 10 | 10 | 11 | yes | 0.9205 | 0.8999 | -0.0206 | 0.0769 | 0.0769 | 0.0818 | 6 | 5 | 9.6408 | 0.4497 |
| R7 | 13 | 13 | 13 | no | -3.3400 | -3.3400 | -0.0000 | -0.2569 | -0.2569 | -0.2569 | 7 | 6 | 3.9864 | 0.4954 |

**Panel summary (SCALP-R2 4H regime):**

| Panel | OLD (`soft_promote_v1` inputs) | V2 (terminal liquidation) |
|-------|-------------------------------:|--------------------------:|
| panel net € | 12.1679 | 12.0531 |
| median exp € | 0.0769 | 0.0818 |
| median trips | 13.0 | 13.0 |
| exp>0 / 7 | 4 | 4 |
| gate verdict | FAIL (`soft_promote_v1`) | FAIL (`rise_panel_accounting_v2`) |

**Complete-trade (realized only — not a gate):**
- completed trips / window: `[13, 13, 13, 10, 8, 10, 13]` · median **13.0**
- windows with completed exp>0: **4**/7
- median expectancy_completed €: **0.0769**
- panel realized net €: **6.0154**
- worst DD €: **12.1415**
- median TIM: **0.4497** · sum n_entries: **85** (long **46** / short **39**)
- forced window closes: **5**/7

### accounting_v2 verdict (SCALP-R2): **FAIL** (`rise_panel_accounting_v2`)

- median_terminal_trips=13.0 (ok=True)
- exp_terminal_adj>0: 4/7 (need ≥5; ok=False)
- panel_terminal_liquidation_net €=12.0531 (ok=True)

### Honesty label vs Scalp S1: **FAIL**

### Honesty deltas vs Scalp S1 (R2 − S1)

| Metric | Scalp S1 €20 | SCALP-R2 €20 | Δ |
|--------|-------------:|-------------:|--:|
| v2 panel term € | 32.5631 | 12.0531 | -20.5099 |
| old panel net € | 32.6400 | 12.1679 | -20.4721 |
| median exp completed € | 0.2086 | 0.0769 | -0.1317 |
| n completed exp>0 / 7 | 6 | 4 | -2 |
| median completed trips | 8.0 | 13.0 | 5.0 |
| worst DD € | 13.8215 | 12.1415 | -1.6801 |
| median TIM | 0.4954 | 0.4497 | -0.0457 |
| sum short entries (R2) | — | **39** | — |
| sum long entries (R2) | — | **46** | — |
| soft promote (OLD) | PASS | FAIL | — |
| v2 gate | PASS | **FAIL** | — |
| honesty | — | **FAIL** | promote=False |

---

## E. Soft PASS ≠ arm · no promote

accounting_v2 **FAIL**. Paper only. **Soft PASS ≠ Scalp-arm**. Mid/Scalp **HALTED**. Live ≤€20. `not_a_forecast: true`. `place_orders: false`.

- **promote:** `False`
- **dev_eliminate_only:** `True`
- **eliminate:** `True`
- **no_rvol_grind:** `True`
- **walker:** `walk_long_short`

**SCALP-R2 eliminated under accounting_v2.** Archive. Do **not** grind RVOL 1.25/1.5 or k on R1–R7.

---

## F. Integrity / non-goals

- Not a rewrite of `rise_panel_accounting_v2` or [`91`](./91-rise-panel-accounting-v2.md).
- Not scored with `walk_long_flat`.
- Not a RVOL threshold rescue of S1.
- Not Mid M2–M4. Not CORE tip grind. Not phase1/98 (H0 health).
- `config/default.yaml` untouched.

`not_a_forecast: true`. `place_orders: false`.

