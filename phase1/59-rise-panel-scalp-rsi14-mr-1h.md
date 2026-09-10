# 59 — rise_panel_v1 Scalp: DOGE **1H RSI(14) mean-reversion** long/flat (€20)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** DOGE ≤€20; no `ga live €200`; no Mid/Scalp arming; no live-raise. Soft PASS ≠ Scalp-arm.
**Panel:** [`54-rise-panel-v1.md`](./54-rise-panel-v1.md) — **same** locked R1–R7 dates (DO NOT change).
**Parent sleeves:** Core €140 / Mid €40 / Scalp €20 ([`38-eur200-three-stream-confirmation.md`](./38-eur200-three-stream-confirmation.md))
**Compare:** provisional Scalp [`55-rise-panel-cascade-compound.md`](./55-rise-panel-cascade-compound.md); Scalp 4H [`57-rise-panel-scalp-improve-4h-ema.md`](./57-rise-panel-scalp-improve-4h-ema.md); Scalp 15m [`58-rise-panel-scalp-improve-15m-ema.md`](./58-rise-panel-scalp-improve-15m-ema.md). **Not** EMA-twin — different indicators.

---

## Soft promote gate (LOCKED — same as #54)

`soft_promote_v1` (INTENTIONAL labeled; NOT a silent rewrite of `core_style_return` A∧B):

1. `median_trades` across the 7 windows **≫ 0** (coded: `median_trades >= 1`)
2. **≥5 / 7** windows with `expectancy_after_costs > 0`
3. **panel net > 0** (sum of after-costs net € across 7)

Costs: PaperSettings **5+5 bps**; fills **next-open**; `place_orders: false`.

---

## A. LOCKED compare targets

**scalp_provisional_id (#55):** `rise_panel_v1_scalp_doge_ema12_30_1h_daily_bull_eur20`  
(soft_promote **FAIL** — provisional stand-in)

- Rule: 1H EMA12/30 long/flat + daily EMA bull entry gate. Never short.
- Bar: DOGE-USDT **1H**. Sleeve: Scalp **€20**.
- #55 snapshot (reported): exp>0 **4**/7 · median_trades=**18** · panel_net≈**€44.70**.

**scalp_4h_id (#57):** `rise_panel_v1_scalp_doge_ema12_30_4h_eur20`  
(soft_promote **PASS** — EMA12/30 long/flat on **4H**)

- #57 snapshot (reported): exp>0 **6**/7 · median_trades=**7** · panel_net≈**€41.81** · median exp≈**€1.05**.

**scalp_15m_id (#58):** `rise_panel_v1_scalp_doge_ema12_30_15m_eur20`  
(soft_promote **FAIL** — EMA12/30 long/flat on **15m**)

- #58 snapshot (reported): exp>0 **1**/7 · median_trades=**161** · panel_net≈**−€32.48**.

### Provisional Scalp per window (re-scored)

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 18 | 0.6561 | 13.0156 | 5.0107 | 0.3528 | 15.3616 | 10.6267 |
| R2 | 12 | -0.0154 | 0.1815 | 3.2508 | 0.2074 | 9.2713 | 17.5480 |
| R3 | 10 | 1.7603 | 17.6026 | 7.8428 | 0.1806 | 12.1697 | 13.4725 |
| R4 | 16 | -0.0063 | 0.7810 | 3.1150 | 0.2527 | 6.1076 | 4.9136 |
| R5 | 21 | -0.1132 | 3.6889 | 7.0512 | 0.2976 | 8.0627 | 6.9305 |
| R6 | 22 | 0.2048 | 4.5066 | 10.2683 | 0.3284 | 7.0466 | 18.0849 |
| R7 | 18 | 0.2558 | 4.9258 | 3.2967 | 0.2977 | 12.7458 | 7.0240 |

**Panel summary (provisional Scalp re-score):**
- windows with exp>0: **4**/7 · net>0: **7**/7
- median expectancy €/trade: **0.2048**
- median_trades: **18.0**
- panel net €: **44.7022**
- worst DD €: **10.2683**
- soft_promote: **FAIL** (`soft_promote_v1`)

---

## B. LOCKED Scalp family (BEFORE scoring)

**ONE family only — NOT grinding RSI period / thresholds / TF / costs.**

**Family:** `rsi14_mr_long_flat_1h`  
**scalp_improve_id:** `rise_panel_v1_scalp_doge_rsi14_mr_1h_eur20`  
**compare_to:** `rise_panel_v1_scalp_doge_ema12_30_1h_daily_bull_eur20`, `rise_panel_v1_scalp_doge_ema12_30_4h_eur20`, `rise_panel_v1_scalp_doge_ema12_30_15m_eur20`
**Different indicators:** RSI(14) mean-reversion (not EMA12/30 twin). Reuse Wilder RSI helper from Mid #43; Scalp locks cross-up / exit≥70 on **1H**.

### Rule card (LOCKED)

- Asset / bar: spot **DOGE-USDT** research MD, decision bar **1H**.
- RSI: Wilder **RSI(14)**.
- **Long:** closed-bar RSI crosses up from ≤30 (prev ≤30 and curr >30). Long only.
- **Flat/exit:** closed-bar RSI ≥70. Never short.
- **No** EMA filter / regime gate.
- Insufficient history → flat.
- Fill: signal close → next open. Size: full Scalp sleeve €20 when long.
- Costs: PaperSettings 5+5 bps.
- **No** Donchian / ATR / EMA rescue knobs this trial. **No** RSI period / threshold / TF / cost grind on FAIL.

### Why this family

Provisional Scalp 1H+daily-bull (#55) soft FAIL (exp>0 4/7). Scalp #57 4H EMA soft PASS; Scalp #58 15m EMA soft FAIL. This trial switches **indicators** (RSI MR, not EMA-twin) on the same locked rise panel / Scalp €20 / 1H bar — testing whether mean-reversion clears soft_promote without inventing EMA knobs.

---

## C. Harness

- Script: `scripts/run_rise_panel_scalp_rsi_mr_1h_eval.py`
- Module: `atlas.paper.rise_panel_scalp_rsi_mr_1h_eval`
- Strategy: `atlas.strategy.scalp_doge_rsi_mr_1h` (reuses `rsi_wilder` from `mid_doge_rsi_mr`)
- Reuse: `walk_long_flat`, `soft_promote_score`, locked `RISE_PANEL_V1` windows, cascade compound (#55 rules) on PASS only; patterns from #57/#58
- Unit tests: `tests/unit/test_rise_panel_scalp_rsi_mr_1h.py`

---

## D. Results — Scalp RSI(14) MR 1H €20 on same 7

**scalp_improve_id:** `rise_panel_v1_scalp_doge_rsi14_mr_1h_eur20`

### Improve per window

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 7 | 0.5128 | 8.6302 | 2.6151 | 0.4316 | 15.3616 | 10.6267 |
| R2 | 6 | -0.3439 | -2.0635 | 6.0136 | 0.3436 | 9.2713 | 17.5480 |
| R3 | 7 | 0.5540 | 2.2107 | 4.8459 | 0.5708 | 12.1697 | 13.4725 |
| R4 | 7 | 0.5936 | 4.1555 | 1.8771 | 0.5600 | 6.1076 | 4.9136 |
| R5 | 7 | 0.7499 | 5.2491 | 2.1435 | 0.3897 | 8.0627 | 6.9305 |
| R6 | 6 | -0.2627 | -1.5981 | 9.0983 | 0.4343 | 7.0466 | 18.0849 |
| R7 | 6 | 0.3300 | 1.6584 | 4.7853 | 0.4250 | 12.7458 | 7.0240 |

**Panel summary (Scalp RSI MR 1H):**
- windows with exp>0: **5**/7 · net>0: **5**/7
- median expectancy €/trade: **0.5128**
- median_trades: **7.0**
- panel net €: **18.2424**
- worst DD €: **9.0983**

### Soft promote (Scalp RSI MR): **PASS** (`soft_promote_v1`)

- median_trades=7.0 (ok=True, min>=1)
- exp>0: 5/7 (need ≥5; ok=True)
- panel_net €=18.2424 (ok=True)
- note: INTENTIONAL labeled gate — NOT a silent rewrite of core_style_return A∧B three-stream board. median_trades≫0 (coded >=1) AND >=5/7 exp>0 AND panel_net>0.

### Honesty deltas vs provisional Scalp #55 (RSI MR − provisional)

| Metric | Provisional 1H €20 | Scalp RSI MR 1H €20 | Δ |
|--------|-------------------:|--------------------:|--:|
| median exp € | 0.2048 | 0.5128 | 0.3080 |
| panel net € | 44.7022 | 18.2424 | -26.4598 |
| median_trades | 18.0 | 7.0 | -11.0 |
| n exp>0 / 7 | 4 | 5 | 1 |
| soft promote | FAIL | **PASS** | — |

### Honesty deltas vs Scalp #57 4H (RSI MR − 4H)

| Metric | Scalp 4H €20 (#57) | Scalp RSI MR 1H €20 | Δ |
|--------|-------------------:|--------------------:|--:|
| median exp € | 1.0464 | 0.5128 | -0.5336 |
| panel net € | 41.8052 | 18.2424 | -23.5628 |
| median_trades | 7.0 | 7.0 | 0.0 |
| n exp>0 / 7 | 6 | 5 | -1 |
| soft promote | PASS | **PASS** | — |

### Honesty deltas vs Scalp #58 15m (RSI MR − 15m)

| Metric | Scalp 15m €20 (#58) | Scalp RSI MR 1H €20 | Δ |
|--------|--------------------:|--------------------:|--:|
| median exp € | -0.0317 | 0.5128 | 0.5445 |
| panel net € | -32.4822 | 18.2424 | 50.7246 |
| median_trades | 161.0 | 7.0 | -154.0 |
| n exp>0 / 7 | 1 | 5 | 4 |
| soft promote | FAIL | **PASS** | — |

---

## E. Cascade compound (PASS → substitute Scalp, provisional_scalp=false)

Same cascade rules as phase1/55: window-end surplus-share 7:2:1, one-way Scalp→Mid→Core; PaperSettings 5+5 bps; next-open; place_orders false.

- **compound_id:** `rise_panel_v1_cascade_compound_721_scalp_rsi_mr_1h`
- **provisional_scalp:** `False`
- **Scalp system:** `rise_panel_v1_scalp_doge_rsi14_mr_1h_eur20` (1H RSI14 MR)
- combined net pre-cascade: **465.8511** €
- per-sleeve net (panel sum): Core **363.9983** · Mid **83.6104** · Scalp **18.2424** €

### Compare to #55 / #57 panel nets

| Sleeve | #55 (provisional Scalp) | #57 (4H Scalp) | #59 (RSI MR) | Δ vs #55 | Δ vs #57 |
|--------|------------------------:|---------------:|-------------:|---------:|---------:|
| Core | 363.9983 | 363.9983 | 363.9983 | 0.0000 | 0.0000 |
| Mid | 83.6104 | 83.6104 | 83.6104 | -0.0000 | -0.0000 |
| Scalp | 44.7022 | 41.8052 | 18.2424 | -26.4598 | -23.5628 |
| Combined | 492.3109 | 489.4139 | 465.8511 | -26.4598 | -23.5628 |

Reports: `data/reports/rise_panel_v1_cascade_compound_scalp_rsi_mr_1h.json`

---

## What this is not

- Not an EMA 12/30 twin / period grind.
- Not a change to R1–R7 window dates.
- Not a rewrite of `core_style_return` A∧B on phase1/38.
- Not a live / Phase C recommendation. Not `ga live €200`.
- Not Scalp-arming. Soft PASS ≠ Scalp-arm. Live ≤€20.
- Not a claim that past rise windows forecast the next bull.
- Mid 4H stays Mid baseline.

`not_a_forecast: true`. `place_orders: false`.
