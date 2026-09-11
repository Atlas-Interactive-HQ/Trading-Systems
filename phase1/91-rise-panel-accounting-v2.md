# 91 — rise_panel_accounting_v2 OLD vs V2 re-score

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** DOGE ≤€20 **HALTED**. Soft PASS ≠ arm. **This audit does not promote.**
**Accounting:** `rise_panel_accounting_v2` (additive; historical keys preserved).
**Audit:** [`90`](./90-evaluation-integrity-audit.md).

Gate `rise_panel_accounting_v2` was locked **before** this re-score. It is **not** a rewrite of `soft_promote_v1`. Do not create green by changing the gate after seeing results.

Numbers below are **measured** from `scripts/run_rise_panel_accounting_v2_eval.py` (OKX EEA public `history-candles`, PaperSettings 5+5 bps, next-open fills). OLD `net_return` / `n_trades` / expectancy reproduce the historical phase1 tables.

---

## How to read (do not promote)

- A V2 **PASS** is **not** a GREEN CANDIDATE and **not** a promote.
- Core C0 / C1 can flip FAIL→PASS because a forced window close turns an open hold (`n_trades=0`) into `n_terminal_trips=1` with terminal-MTM expectancy. That is **one-interval dominated**, not complete-trade edge.
- Prefer `expectancy_completed_eur` + `completed_round_trips` when asking whether the strategy actually finished trades.
- Δ net is almost entirely the missing terminal sell fee/slip (~few cents to ~€0.24).
- Mid M1 remains the robustness comparator (more exp>0 windows historically, lower median exp / panel). Not a post-hoc swap for #71.

| Candidate | OLD soft | V2 gate | OLD panel € | V2 term € | OLD exp>0 | V2 exp>0 | forced |
|-----------|:--------:|:-------:|------------:|----------:|----------:|---------:|-------:|
| core_c0_ema12_30 | FAIL | PASS | 363.9983 | 362.6547 | 2 | 6 | 7/7 |
| mid_71_breakout_ema1221 | PASS | PASS | 97.2663 | 97.1317 | 5 | 7 | 3/7 |
| mid_m1_adx | PASS | PASS | 74.6942 | 74.6109 | 6 | 6 | 2/7 |
| scalp_83_dual_thrust | PASS | PASS | 31.1763 | 31.0774 | 6 | 6 | 4/7 |
| scalp_s1_rvol | PASS | PASS | 32.6400 | 32.5631 | 6 | 6 | 3/7 |
| core_c1_donchian40_20 | FAIL | PASS | 208.1348 | 207.2313 | 1 | 6 | 5/7 |
| core_c2_donchian_ema | FAIL | FAIL | 74.4898 | 73.9999 | 1 | 3 | 3/7 |

---

## core_c0_ema12_30 — `rise_panel_v1_core_doge_ema12_30_1d_eur140`

Role: **core_c0_baseline**
Bar 1D · sleeve €140.0 · strategy `ema12_30_long_flat`

| Id | n_trades old | completed | term trips | open? | old net € | term liq € | Δ net € | old exp € | exp completed € | exp term-adj € |
|----|-------------:|----------:|-----------:|:-----:|----------:|-----------:|--------:|----------:|----------------:|---------------:|
| R1 | 0 | 0 | 1 | yes | 100.9579 | 100.7170 | -0.2409 | — | — | 100.7170 |
| R2 | 2 | 2 | 3 | yes | -16.6090 | -16.7324 | -0.1234 | -7.4986 | -7.4986 | -5.5775 |
| R3 | 1 | 1 | 2 | yes | 82.0222 | 81.8002 | -0.2220 | -10.5166 | -10.5166 | 40.9001 |
| R4 | 0 | 0 | 1 | yes | 35.3467 | 35.1714 | -0.1753 | — | — | 35.1714 |
| R5 | 1 | 1 | 2 | yes | 83.1141 | 82.8910 | -0.2230 | 1.5895 | 1.5895 | 41.4455 |
| R6 | 1 | 1 | 2 | yes | 16.7226 | 16.5659 | -0.1567 | 26.3396 | 26.3396 | 8.2830 |
| R7 | 0 | 0 | 1 | yes | 62.4439 | 62.2415 | -0.2024 | — | — | 62.2415 |

| Panel | OLD (`soft_promote_v1` inputs) | V2 (terminal liquidation) |
|-------|-------------------------------:|--------------------------:|
| panel net € | 363.9983 | 362.6547 |
| median exp € | -2.9545 | 40.9001 |
| median trips | 1.0 | 2.0 |
| exp>0 / 7 | 2 | 6 |
| gate verdict | FAIL (`soft_promote_v1`) | PASS (`rise_panel_accounting_v2`) |

Forced window closes: **7**/7. `audit_does_not_promote: true`.

`not_a_forecast: true`.

---

## mid_71_breakout_ema1221 — `rise_panel_v1_mid_doge_breakoutv1_ema1221_long_4h_eur40`

Role: **mid_primary_frozen**
Bar 4H · sleeve €40.0 · strategy `breakout_v1_ema1221_long_regime_4h`

| Id | n_trades old | completed | term trips | open? | old net € | term liq € | Δ net € | old exp € | exp completed € | exp term-adj € |
|----|-------------:|----------:|-----------:|:-----:|----------:|-----------:|--------:|----------:|----------------:|---------------:|
| R1 | 4 | 4 | 4 | no | 23.9590 | 23.9590 | 0.0000 | 5.9898 | 5.9898 | 5.9898 |
| R2 | 7 | 7 | 8 | yes | 6.0916 | 6.0455 | -0.0461 | 0.9778 | 0.9778 | 0.7557 |
| R3 | 6 | 6 | 6 | no | 27.4157 | 27.4157 | 0.0000 | 4.5693 | 4.5693 | 4.5693 |
| R4 | 8 | 8 | 9 | yes | 1.9067 | 1.8648 | -0.0419 | -0.0323 | -0.0323 | 0.2072 |
| R5 | 7 | 7 | 8 | yes | 6.6592 | 6.6125 | -0.0466 | -0.8389 | -0.8389 | 0.8266 |
| R6 | 7 | 7 | 7 | no | 16.1628 | 16.1628 | 0.0000 | 2.3090 | 2.3090 | 2.3090 |
| R7 | 7 | 7 | 7 | no | 15.0714 | 15.0714 | 0.0000 | 2.1531 | 2.1531 | 2.1531 |

| Panel | OLD (`soft_promote_v1` inputs) | V2 (terminal liquidation) |
|-------|-------------------------------:|--------------------------:|
| panel net € | 97.2663 | 97.1317 |
| median exp € | 2.1531 | 2.1531 |
| median trips | 7.0 | 7.0 |
| exp>0 / 7 | 5 | 7 |
| gate verdict | PASS (`soft_promote_v1`) | PASS (`rise_panel_accounting_v2`) |

Forced window closes: **3**/7. `audit_does_not_promote: true`.

`not_a_forecast: true`.

---

## mid_m1_adx — `rise_panel_v1_mid_doge_breakoutv1_ema1221_adx14_gt20_4h_eur40`

Role: **mid_robustness_comparator**
Bar 4H · sleeve €40.0 · strategy `breakout_v1_ema1221_adx14_gt20_4h`

| Id | n_trades old | completed | term trips | open? | old net € | term liq € | Δ net € | old exp € | exp completed € | exp term-adj € |
|----|-------------:|----------:|-----------:|:-----:|----------:|-----------:|--------:|----------:|----------------:|---------------:|
| R1 | 6 | 6 | 6 | no | 5.4678 | 5.4678 | -0.0000 | 0.9113 | 0.9113 | 0.9113 |
| R2 | 4 | 4 | 4 | no | 8.3162 | 8.3162 | -0.0000 | 2.0790 | 2.0790 | 2.0790 |
| R3 | 4 | 4 | 4 | no | 26.1894 | 26.1894 | 0.0000 | 6.5473 | 6.5473 | 6.5473 |
| R4 | 6 | 6 | 7 | yes | 3.4465 | 3.4031 | -0.0434 | 0.6390 | 0.6390 | 0.4862 |
| R5 | 8 | 8 | 9 | yes | -0.1448 | -0.1847 | -0.0398 | -0.9932 | -0.9932 | -0.0205 |
| R6 | 6 | 6 | 6 | no | 29.4295 | 29.4295 | 0.0000 | 4.9049 | 4.9049 | 4.9049 |
| R7 | 9 | 9 | 9 | no | 1.9896 | 1.9896 | -0.0000 | 0.2211 | 0.2211 | 0.2211 |

| Panel | OLD (`soft_promote_v1` inputs) | V2 (terminal liquidation) |
|-------|-------------------------------:|--------------------------:|
| panel net € | 74.6942 | 74.6109 |
| median exp € | 0.9113 | 0.9113 |
| median trips | 6.0 | 6.0 |
| exp>0 / 7 | 6 | 6 |
| gate verdict | PASS (`soft_promote_v1`) | PASS (`rise_panel_accounting_v2`) |

Forced window closes: **2**/7. `audit_does_not_promote: true`.

`not_a_forecast: true`.

---

## scalp_83_dual_thrust — `rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_1h_eur20`

Role: **scalp_s0**
Bar 1H · sleeve €20.0 · strategy `dual_thrust_n20_k0505_long_flat`

| Id | n_trades old | completed | term trips | open? | old net € | term liq € | Δ net € | old exp € | exp completed € | exp term-adj € |
|----|-------------:|----------:|-----------:|:-----:|----------:|-----------:|--------:|----------:|----------------:|---------------:|
| R1 | 16 | 16 | 16 | no | 0.4451 | 0.4451 | 0.0000 | 0.0278 | 0.0278 | 0.0278 |
| R2 | 7 | 7 | 8 | yes | 6.5725 | 6.5459 | -0.0266 | 1.0729 | 1.0729 | 0.8182 |
| R3 | 12 | 12 | 12 | no | 10.1558 | 10.1558 | -0.0000 | 0.8463 | 0.8463 | 0.8463 |
| R4 | 5 | 5 | 6 | yes | -0.6700 | -0.6894 | -0.0193 | -0.2980 | -0.2980 | -0.1149 |
| R5 | 7 | 7 | 8 | yes | 11.0009 | 10.9699 | -0.0310 | 0.4974 | 0.4974 | 1.3712 |
| R6 | 8 | 8 | 8 | no | 1.6690 | 1.6690 | 0.0000 | 0.2086 | 0.2086 | 0.2086 |
| R7 | 10 | 10 | 11 | yes | 2.0031 | 1.9811 | -0.0220 | 0.1958 | 0.1958 | 0.1801 |

| Panel | OLD (`soft_promote_v1` inputs) | V2 (terminal liquidation) |
|-------|-------------------------------:|--------------------------:|
| panel net € | 31.1763 | 31.0774 |
| median exp € | 0.2086 | 0.2086 |
| median trips | 8.0 | 8.0 |
| exp>0 / 7 | 6 | 6 |
| gate verdict | PASS (`soft_promote_v1`) | PASS (`rise_panel_accounting_v2`) |

Forced window closes: **4**/7. `audit_does_not_promote: true`.

`not_a_forecast: true`.

---

## scalp_s1_rvol — `rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_rvol_gt1_1h_eur20`

Role: **scalp_provisional_dev**
Bar 1H · sleeve €20.0 · strategy `dual_thrust_n20_k0505_rvol20_gt1_long_flat`

| Id | n_trades old | completed | term trips | open? | old net € | term liq € | Δ net € | old exp € | exp completed € | exp term-adj € |
|----|-------------:|----------:|-----------:|:-----:|----------:|-----------:|--------:|----------:|----------------:|---------------:|
| R1 | 14 | 14 | 14 | no | 1.9536 | 1.9536 | 0.0000 | 0.1395 | 0.1395 | 0.1395 |
| R2 | 7 | 7 | 8 | yes | 6.5725 | 6.5459 | -0.0266 | 1.0729 | 1.0729 | 0.8182 |
| R3 | 12 | 12 | 12 | no | 10.1558 | 10.1558 | -0.0000 | 0.8463 | 0.8463 | 0.8463 |
| R4 | 5 | 5 | 6 | yes | -0.6700 | -0.6894 | -0.0193 | -0.2980 | -0.2980 | -0.1149 |
| R5 | 7 | 7 | 8 | yes | 11.0009 | 10.9699 | -0.0310 | 0.4974 | 0.4974 | 1.3712 |
| R6 | 8 | 8 | 8 | no | 1.6690 | 1.6690 | 0.0000 | 0.2086 | 0.2086 | 0.2086 |
| R7 | 10 | 10 | 10 | no | 1.9582 | 1.9582 | 0.0000 | 0.1958 | 0.1958 | 0.1958 |

| Panel | OLD (`soft_promote_v1` inputs) | V2 (terminal liquidation) |
|-------|-------------------------------:|--------------------------:|
| panel net € | 32.6400 | 32.5631 |
| median exp € | 0.2086 | 0.2086 |
| median trips | 8.0 | 8.0 |
| exp>0 / 7 | 6 | 6 |
| gate verdict | PASS (`soft_promote_v1`) | PASS (`rise_panel_accounting_v2`) |

Forced window closes: **3**/7. `audit_does_not_promote: true`.

`not_a_forecast: true`.

---

## core_c1_donchian40_20 — `rise_panel_v1_core_doge_donchian40_20_1d_eur140`

Role: **core_c1_audit_reference** · audit/reference only
Bar 1D · sleeve €140.0 · strategy `donchian40_20_long_flat`

| Id | n_trades old | completed | term trips | open? | old net € | term liq € | Δ net € | old exp € | exp completed € | exp term-adj € |
|----|-------------:|----------:|-----------:|:-----:|----------:|-----------:|--------:|----------:|----------------:|---------------:|
| R1 | 0 | 0 | 1 | yes | 41.7391 | 41.5574 | -0.1817 | — | — | 41.5574 |
| R2 | 1 | 1 | 1 | no | -25.4819 | -25.4819 | -0.0000 | -25.4819 | -25.4819 | -25.4819 |
| R3 | 1 | 1 | 2 | yes | 22.9542 | 22.7913 | -0.1629 | -31.1945 | -31.1945 | 11.3956 |
| R4 | 0 | 0 | 1 | yes | 35.3467 | 35.1714 | -0.1753 | — | — | 35.1714 |
| R5 | 1 | 1 | 2 | yes | 54.0712 | 53.8772 | -0.1940 | -1.0880 | -1.0880 | 26.9386 |
| R6 | 1 | 1 | 1 | no | 29.9495 | 29.9495 | 0.0000 | 29.9495 | 29.9495 | 29.9495 |
| R7 | 0 | 0 | 1 | yes | 49.5559 | 49.3664 | -0.1895 | — | — | 49.3664 |

| Panel | OLD (`soft_promote_v1` inputs) | V2 (terminal liquidation) |
|-------|-------------------------------:|--------------------------:|
| panel net € | 208.1348 | 207.2313 |
| median exp € | -13.2850 | 29.9495 |
| median trips | 1.0 | 1.0 |
| exp>0 / 7 | 1 | 6 |
| gate verdict | FAIL (`soft_promote_v1`) | PASS (`rise_panel_accounting_v2`) |

Forced window closes: **5**/7. `audit_does_not_promote: true`.

`not_a_forecast: true`.

---

## core_c2_donchian_ema — `rise_panel_v1_core_doge_donchian40_20_ema50_200_1d_eur140`

Role: **core_c2_audit_reference** · audit/reference only
Bar 1D · sleeve €140.0 · strategy `donchian40_20_ema50_200_regime_1d`

| Id | n_trades old | completed | term trips | open? | old net € | term liq € | Δ net € | old exp € | exp completed € | exp term-adj € |
|----|-------------:|----------:|-----------:|:-----:|----------:|-----------:|--------:|----------:|----------------:|---------------:|
| R1 | 0 | 0 | 1 | yes | 41.7391 | 41.5574 | -0.1817 | — | — | 41.5574 |
| R2 | 1 | 1 | 1 | no | -25.4819 | -25.4819 | -0.0000 | -25.4819 | -25.4819 | -25.4819 |
| R3 | 0 | 0 | 0 | no | 0.0000 | 0.0000 | 0.0000 | — | — | — |
| R4 | 0 | 0 | 0 | no | 0.0000 | 0.0000 | 0.0000 | — | — | — |
| R5 | 1 | 1 | 2 | yes | 40.2338 | 40.0536 | -0.1802 | -10.9926 | -10.9926 | 20.0268 |
| R6 | 1 | 1 | 1 | no | 29.9495 | 29.9495 | 0.0000 | 29.9495 | 29.9495 | 29.9495 |
| R7 | 0 | 0 | 1 | yes | -11.9507 | -12.0788 | -0.1280 | — | — | -12.0788 |

| Panel | OLD (`soft_promote_v1` inputs) | V2 (terminal liquidation) |
|-------|-------------------------------:|--------------------------:|
| panel net € | 74.4898 | 73.9999 |
| median exp € | -10.9926 | 20.0268 |
| median trips | 0.0 | 1.0 |
| exp>0 / 7 | 1 | 3 |
| gate verdict | FAIL (`soft_promote_v1`) | FAIL (`rise_panel_accounting_v2`) |

Forced window closes: **3**/7. `audit_does_not_promote: true`.

`not_a_forecast: true`.

---

## Honesty / invalidation

- Soft PASS ≠ arm. V2 PASS ≠ promote. This audit does **not** promote anyone.
- R1–R7 remain DEV/eliminate-only. Next Mid score = unseen SHADOW only.
- Do not change `rise_panel_accounting_v2` after seeing these numbers.
- Historical `soft_promote_v1` artifacts are **not** rewritten.
- CORE-R1 and SCALP-R2 are **not** in this table (lock only).
- Core C0 V2 PASS (7/7 forced closes) and C1 V2 PASS (5/7 forced) are **not** complete-trade expectancy proofs. C2 remains FAIL on both gates.

`not_a_forecast: true`. `place_orders: false`.
