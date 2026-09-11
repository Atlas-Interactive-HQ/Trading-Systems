# 91 — rise_panel_accounting_v2 OLD vs V2 re-score

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** DOGE ≤€20 **HALTED**. Soft PASS ≠ arm. **This audit does not promote.**
**Accounting:** `rise_panel_accounting_v2` (additive; historical keys preserved).
**Audit:** [`90`](./90-evaluation-integrity-audit.md).

Gate `rise_panel_accounting_v2` was locked **before** this re-score. It is **not** a rewrite of `soft_promote_v1`. Do not create green by changing the gate after seeing results.

---

## Gate (LOCKED before score)

`rise_panel_accounting_v2` PASS iff:

1. `median(n_terminal_trips) ≥ 1`
2. `count(expectancy_terminal_adjusted_eur > 0) ≥ 5/7`
3. `sum(terminal_liquidation_net_eur) > 0`

`n_terminal_trips` = completed realized round-trips **plus** 1 if a forced window close.

`soft_promote_v1` is still computed on the original keys for comparison. Soft PASS ≠ arm. V2 PASS ≠ promote.

---

## Required v2 fields (additive)

`realized_net_eur` · `unrealized_net_eur` · `terminal_exit_cost_estimate_eur` · `terminal_liquidation_net_eur` · `completed_round_trips` · `open_position_at_end` · `expectancy_completed_eur` · `expectancy_terminal_adjusted_eur` · `forced_window_close` · `n_terminal_trips`

Synthetic terminal liquidation: last **in-window** close, same sell slippage + fee as a normal exit (`PaperSettings` 5+5 bps). Signals unchanged.

---

## Unchanged strategies re-scored

| Key | Role | Sleeve | Bar |
|-----|------|-------:|-----|
| Core C0 EMA12/30 | baseline | €140 | 1D |
| Mid #71 BreakoutV1+EMA12/21 | frozen primary | €40 | 4H |
| Mid M1 ADX>20 | robustness comparator only | €40 | 4H |
| Scalp #83 Dual Thrust | S0 | €20 | 1H |
| Scalp S1 Dual Thrust+RVOL>1 | provisional DEV | €20 | 1H |
| Core C1 Donchian 40/20 | audit/reference only | €140 | 1D |
| Core C2 Donchian+EMA50/200 | audit/reference only | €140 | 1D |

New artifacts: `results/accounting_v2/` (do **not** overwrite historical `data/reports/rise_panel_v1_*.json` or phase1/54–89 tables).

---

## Measured OLD vs V2 table

**Status:** pending a measured run of `scripts/run_rise_panel_accounting_v2_eval.py`.

This file is overwritten by that script with **real** window rows. Until the script succeeds against OKX EEA `history-candles`, treat every numeric cell below as **absent** — do not invent fills.

If the run fails (no network / empty candles): leave this section as `insufficient_data` and stop. Do not promote.

---

## Honesty / invalidation

- Soft PASS ≠ arm. V2 PASS ≠ promote. This audit does **not** promote anyone.
- R1–R7 remain DEV/eliminate-only. Next Mid score = unseen SHADOW only.
- Do not change `rise_panel_accounting_v2` after seeing these numbers.
- Historical `soft_promote_v1` artifacts are **not** rewritten.
- CORE-R1 and SCALP-R2 are **not** in this table (lock only; see [`93`](./93-frozen-mid-scalp-candidates.md) / [`94`](./94-core-r1-lock.md)).

`not_a_forecast: true`. `place_orders: false`.
